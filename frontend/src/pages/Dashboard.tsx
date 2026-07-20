import React, { useState, useEffect } from 'react';
import { Upload, Search, Filter, Activity, Briefcase, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CandidateCard from '../components/CandidateCard';
import { Card, Input, Badge, Skeleton, Dialog, useToast } from '../components/ui';
import { getCandidates, uploadResumes, getUploadStatus, type Candidate } from '../services/api';
import { useDebounce } from '../hooks/useDebounce';

const SCORE_OPTS = ['90% and above', '75% - 90%', 'Below 75%'];
const EXP_OPTS = ['0-2 Years', '3-5 Years', '5+ Years'];
const TABS = [
  { label: 'All Candidates', value: 'all candidates' },
  { label: 'Shortlisted', value: 'shortlisted' },
  { label: 'Interviews', value: 'interviews' },
  { label: 'Rejected', value: 'rejected' },
];

function CheckRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="flex cursor-pointer items-center gap-2.5 text-sm text-content-muted transition-colors hover:text-content">
      <input type="checkbox" checked={checked} onChange={onChange} className="h-4 w-4 accent-primary" />
      {label}
    </label>
  );
}

export default function Dashboard() {
  const toast = useToast();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ processing: number; completed: number; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500);
  const [activeTab, setActiveTab] = useState('all candidates');

  const [scoreFilters, setScoreFilters] = useState<string[]>([]);
  const [expFilters, setExpFilters] = useState<string[]>([]);
  const [tagFilters, setTagFilters] = useState<string[]>([]);

  const [selectedForCompare, setSelectedForCompare] = useState<number[]>([]);
  const [showCompareModal, setShowCompareModal] = useState(false);

  const fetchCandidates = async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    try {
      const params: any = {};
      if (debouncedSearch) params.q = debouncedSearch;
      if (activeTab !== 'all candidates') params.status = activeTab;
      if (scoreFilters.includes('90% and above')) params.min_score = 90;
      else if (scoreFilters.includes('75% - 90%')) { params.min_score = 75; params.max_score = 90; }
      else if (scoreFilters.includes('Below 75%')) params.max_score = 75;
      if (expFilters.includes('0-2 Years')) params.max_exp = 2;
      else if (expFilters.includes('3-5 Years')) { params.min_exp = 3; params.max_exp = 5; }
      else if (expFilters.includes('5+ Years')) params.min_exp = 5;
      if (tagFilters.includes('Has Red Flags')) params.has_warnings = true;

      let data = await getCandidates(params);
      if (tagFilters.includes('Hidden Talent')) data = data.filter((c) => c.hidden_talent_tag);
      setCandidates(data);
      setError(null);
    } catch {
      setError('Unable to connect to the backend server.');
    } finally {
      if (!quiet) setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, activeTab, scoreFilters, expFilters, tagFilters]);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await getUploadStatus();
        if (status.processing > 0) { setUploadProgress(status); fetchCandidates(true); }
        else if (uploadProgress && status.processing === 0) { setUploadProgress(null); fetchCandidates(true); }
      } catch { /* ignore */ }
    };
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadProgress]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsUploading(true);
    try {
      await uploadResumes(e.target.files);
      toast.success('Resumes uploaded', 'AI is analyzing them now.');
      await fetchCandidates();
    } catch {
      toast.error('Upload failed', 'Ensure the backend is running.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const toggle = (setter: React.Dispatch<React.SetStateAction<string[]>>, v: string) =>
    setter((prev) => (prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v]));

  const pct = uploadProgress && uploadProgress.total > 0
    ? Math.round(((uploadProgress.total - uploadProgress.processing) / uploadProgress.total) * 100) : 0;

  return (
    <div className="flex gap-6">
      {/* Filters */}
      <motion.aside initial={{ x: -12, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="hidden w-64 shrink-0 lg:block">
        <Card className="sticky top-24 p-5">
          <h2 className="mb-5 flex items-center gap-2 font-semibold text-content"><Filter className="h-4 w-4 text-primary" /> Filters</h2>
          <div className="space-y-6">
            <div className="space-y-2.5">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-content-subtle"><Activity className="h-3.5 w-3.5" /> Match score</p>
              {SCORE_OPTS.map((o) => <CheckRow key={o} label={o} checked={scoreFilters.includes(o)} onChange={() => toggle(setScoreFilters, o)} />)}
            </div>
            <div className="space-y-2.5">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-content-subtle"><Briefcase className="h-3.5 w-3.5" /> Experience</p>
              {EXP_OPTS.map((o) => <CheckRow key={o} label={o} checked={expFilters.includes(o)} onChange={() => toggle(setExpFilters, o)} />)}
            </div>
            <div className="space-y-2.5">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-content-subtle"><Star className="h-3.5 w-3.5" /> AI tags</p>
              <CheckRow label="Hidden Talent" checked={tagFilters.includes('Hidden Talent')} onChange={() => toggle(setTagFilters, 'Hidden Talent')} />
              <CheckRow label="Has Red Flags" checked={tagFilters.includes('Has Red Flags')} onChange={() => toggle(setTagFilters, 'Has Red Flags')} />
            </div>
          </div>
        </Card>
      </motion.aside>

      {/* Main */}
      <div className="min-w-0 flex-1">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="w-full max-w-md">
            <Input leftIcon={<Search className="h-4 w-4" />} placeholder="Search name, skills, or email…" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          </div>
          <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-fg shadow-glow-sm transition-colors hover:bg-primary-hover">
            <Upload className={`h-4 w-4 ${isUploading ? 'animate-pulse' : ''}`} />
            {isUploading ? 'Uploading…' : 'Upload resumes'}
            <input type="file" multiple accept=".pdf" className="hidden" onChange={handleUpload} disabled={isUploading} />
          </label>
        </div>

        {error && (
          <Card className="mb-5 flex items-center gap-3 border-danger/30 bg-danger/5 p-4 text-danger">
            <Activity className="h-5 w-5 shrink-0" /><p className="text-sm font-medium">{error}</p>
          </Card>
        )}

        {uploadProgress && uploadProgress.total > 0 && (
          <Card className="mb-5 p-4">
            <div className="mb-2 flex items-end justify-between">
              <div>
                <p className="flex items-center gap-2 text-sm font-semibold text-content"><Activity className="h-4 w-4 animate-pulse text-primary" /> Processing resumes</p>
                <p className="text-xs text-content-muted">The AI engine is analyzing candidates…</p>
              </div>
              <span className="text-xl font-bold text-primary">{pct}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-surface-2">
              <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} className="h-full rounded-full bg-primary" />
            </div>
          </Card>
        )}

        {/* Tabs */}
        <div className="mb-5 flex gap-1 border-b">
          {TABS.map((t) => {
            const active = activeTab === t.value;
            return (
              <button key={t.value} onClick={() => setActiveTab(t.value)}
                className={`relative px-4 py-2.5 text-sm font-semibold transition-colors ${active ? 'text-primary' : 'text-content-muted hover:text-content'}`}>
                {t.label}
                {active && <motion.div layoutId="tabUnderline" className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-primary" />}
              </button>
            );
          })}
        </div>

        {/* List */}
        {isLoading ? (
          <div className="space-y-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}</div>
        ) : candidates.length === 0 ? (
          <Card className="flex flex-col items-center gap-3 py-20 text-center">
            <div className="grid h-16 w-16 place-items-center rounded-full bg-surface-2"><Search className="h-7 w-7 text-content-subtle" /></div>
            <p className="font-semibold text-content">No candidates found</p>
            <p className="max-w-sm text-sm text-content-muted">Adjust your filters or upload resumes to get started.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            <AnimatePresence>
              {candidates.map((c) => (
                <CandidateCard key={c.id} candidate={c} onRefresh={fetchCandidates}
                  onReject={(id) => setCandidates((p) => p.map((x) => (x.id === id ? { ...x, status: 'rejected' } : x)))}
                  onInvite={(id) => setCandidates((p) => p.map((x) => (x.id === id ? { ...x, status: 'invited' } : x)))}
                  isSelected={selectedForCompare.includes(c.id)}
                  onToggleSelect={(id) => setSelectedForCompare((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : prev.length >= 2 ? [prev[1], id] : [...prev, id])}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Compare tray */}
      <AnimatePresence>
        {selectedForCompare.length > 0 && (
          <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 items-center gap-4 rounded-2xl border bg-surface px-5 py-3 shadow-elev-3">
            <span className="text-sm font-semibold text-content">{selectedForCompare.length}/2 selected</span>
            <div className="flex gap-2">
              <button onClick={() => setSelectedForCompare([])} className="rounded-lg border px-3 py-1.5 text-sm text-content-muted hover:bg-surface-2">Clear</button>
              <button disabled={selectedForCompare.length !== 2} onClick={() => setShowCompareModal(true)}
                className="rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-fg disabled:opacity-50">Compare</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Compare modal */}
      <Dialog open={showCompareModal && selectedForCompare.length === 2} onClose={() => setShowCompareModal(false)} title="Candidate comparison" className="max-w-3xl">
        <div className="grid gap-4 sm:grid-cols-2">
          {selectedForCompare.map((id) => {
            const c = candidates.find((x) => x.id === id);
            if (!c) return null;
            return (
              <div key={id} className="rounded-xl border bg-surface-2 p-5">
                <div className="mb-4 flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-primary-subtle font-bold text-primary">{c.name.charAt(0)}</div>
                  <div><p className="font-semibold text-content">{c.name}</p><p className="text-xs text-content-subtle">{c.role_applied}</p></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border bg-surface p-3"><p className="text-[10px] uppercase text-content-subtle">Match</p><p className="text-2xl font-bold text-primary">{Math.round(c.overall_score)}%</p></div>
                  <div className="rounded-lg border bg-surface p-3"><p className="text-[10px] uppercase text-content-subtle">Experience</p><p className="text-2xl font-bold text-content">{c.experience_years} yr</p></div>
                </div>
                <div className="mt-4 space-y-3 text-sm">
                  <div><p className="text-[10px] uppercase text-content-subtle">Recommendation</p><p className="text-content">{c.decision_data?.decision || 'N/A'}</p></div>
                  <div><p className="mb-1 text-[10px] uppercase text-content-subtle">Top skills</p><div className="flex flex-wrap gap-1.5">{c.skills.slice(0, 8).map((s) => <Badge key={s} variant="outline">{s}</Badge>)}</div></div>
                </div>
              </div>
            );
          })}
        </div>
      </Dialog>
    </div>
  );
}
