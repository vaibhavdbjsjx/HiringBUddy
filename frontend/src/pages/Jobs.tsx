import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Briefcase, Plus, Sparkles, MapPin, Users, Trash2, Globe, Lock, Loader2, Copy,
} from 'lucide-react';
import {
  Button, Card, Input, Textarea, Select, Badge, Dialog, Skeleton, useToast,
} from '../components/ui';
import {
  getJobs, createJob, generateJobContent, updateJob, deleteJob,
  type Job, type JobCreatePayload,
} from '../services/api';

const EMPLOYMENT = ['full_time', 'part_time', 'contract', 'internship', 'temporary'];
const WORK_MODE = ['remote', 'hybrid', 'onsite'];

const STATUS_VARIANT: Record<string, 'default' | 'success' | 'warning' | 'primary'> = {
  draft: 'default',
  open: 'success',
  on_hold: 'warning',
  closed: 'default',
};

const csv = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean);
const titleCase = (s?: string | null) =>
  (s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const EMPTY_FORM = {
  title: '', department: '', company: '', employment_type: 'full_time',
  work_mode: 'remote', location: '', experience_min: '', experience_max: '',
  salary_min: '', salary_max: '', required_skills: '', preferred_skills: '', education: '',
};

export default function Jobs() {
  const toast = useToast();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [selected, setSelected] = useState<Job | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = async () => {
    try {
      setJobs(await getJobs());
    } catch {
      toast.error('Could not load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    if (!form.title.trim()) {
      toast.error('Job title is required');
      return;
    }
    setSaving(true);
    try {
      const payload: JobCreatePayload = {
        title: form.title.trim(),
        department: form.department || undefined,
        company: form.company || undefined,
        employment_type: form.employment_type,
        work_mode: form.work_mode,
        location: form.location || undefined,
        experience_min: form.experience_min ? Number(form.experience_min) : undefined,
        experience_max: form.experience_max ? Number(form.experience_max) : undefined,
        salary_min: form.salary_min ? Number(form.salary_min) : undefined,
        salary_max: form.salary_max ? Number(form.salary_max) : undefined,
        required_skills: csv(form.required_skills),
        preferred_skills: csv(form.preferred_skills),
        education: form.education || undefined,
      };
      const job = await createJob(payload);
      toast.success('Job created', 'Generating posting content…');
      setCreateOpen(false);
      setForm({ ...EMPTY_FORM });
      // Auto-generate the full posting.
      try {
        const full = await generateJobContent(job.id);
        setJobs((prev) => [full, ...prev]);
        setSelected(full);
      } catch {
        setJobs((prev) => [job, ...prev]);
      }
    } catch (e: any) {
      toast.error('Could not create job', e?.response?.data?.detail);
    } finally {
      setSaving(false);
    }
  };

  const regenerate = async (job: Job) => {
    setGenerating(true);
    try {
      const full = await generateJobContent(job.id);
      setSelected(full);
      setJobs((prev) => prev.map((j) => (j.id === full.id ? full : j)));
      toast.success('Posting regenerated');
    } catch {
      toast.error('Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const toggleStatus = async (job: Job) => {
    const next = job.status === 'open' ? 'closed' : 'open';
    try {
      const updated = await updateJob(job.id, { status: next });
      setJobs((prev) => prev.map((j) => (j.id === job.id ? updated : j)));
      setSelected((s) => (s && s.id === job.id ? updated : s));
      toast.success(next === 'open' ? 'Job published' : 'Job closed');
    } catch {
      toast.error('Could not update status');
    }
  };

  const remove = async (job: Job) => {
    try {
      await deleteJob(job.id);
      setJobs((prev) => prev.filter((j) => j.id !== job.id));
      setSelected(null);
      toast.success('Job deleted');
    } catch {
      toast.error('Could not delete job');
    }
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-content">
            <Briefcase className="h-6 w-6 text-primary" /> Jobs
          </h1>
          <p className="mt-1 text-sm text-content-muted">
            Create roles and let AI draft the full posting, interview plan, and questions.
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
          New Job
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <Card className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <Briefcase className="h-10 w-10 text-content-subtle" />
          <p className="text-content-muted">No jobs yet. Create your first role to get started.</p>
          <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
            New Job
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card
                className="cursor-pointer p-5 transition-shadow hover:shadow-elev-2"
                onClick={() => setSelected(job)}
              >
                <div className="mb-3 flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-content">{job.title}</h3>
                  <Badge variant={STATUS_VARIANT[job.status] || 'default'}>
                    {titleCase(job.status)}
                  </Badge>
                </div>
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {job.employment_type && <Badge variant="outline">{titleCase(job.employment_type)}</Badge>}
                  {job.work_mode && <Badge variant="outline">{titleCase(job.work_mode)}</Badge>}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(job.required_skills || []).slice(0, 4).map((s) => (
                    <Badge key={s} variant="primary">{s}</Badge>
                  ))}
                </div>
                <div className="mt-4 flex items-center gap-4 text-xs text-content-subtle">
                  {job.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {job.location}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Users className="h-3.5 w-3.5" /> {job.application_count ?? 0} applicants
                  </span>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create dialog */}
      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New Job"
        description="Enter the essentials — AI fills in the rest."
        className="max-w-2xl"
      >
        <div className="grid grid-cols-2 gap-3">
          <Field label="Title *" className="col-span-2">
            <Input value={form.title} onChange={(e) => set('title', e.target.value)} placeholder="Senior Backend Engineer" />
          </Field>
          <Field label="Department">
            <Input value={form.department} onChange={(e) => set('department', e.target.value)} placeholder="Engineering" />
          </Field>
          <Field label="Company">
            <Input value={form.company} onChange={(e) => set('company', e.target.value)} placeholder="Acme Inc" />
          </Field>
          <Field label="Employment type">
            <Select value={form.employment_type} onChange={(e) => set('employment_type', e.target.value)}>
              {EMPLOYMENT.map((v) => <option key={v} value={v}>{titleCase(v)}</option>)}
            </Select>
          </Field>
          <Field label="Work mode">
            <Select value={form.work_mode} onChange={(e) => set('work_mode', e.target.value)}>
              {WORK_MODE.map((v) => <option key={v} value={v}>{titleCase(v)}</option>)}
            </Select>
          </Field>
          <Field label="Location">
            <Input value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="Remote / Bengaluru" />
          </Field>
          <Field label="Education">
            <Input value={form.education} onChange={(e) => set('education', e.target.value)} placeholder="B.Tech CS or equivalent" />
          </Field>
          <Field label="Min experience (yrs)">
            <Input type="number" value={form.experience_min} onChange={(e) => set('experience_min', e.target.value)} placeholder="2" />
          </Field>
          <Field label="Max experience (yrs)">
            <Input type="number" value={form.experience_max} onChange={(e) => set('experience_max', e.target.value)} placeholder="5" />
          </Field>
          <Field label="Required skills (comma-separated)" className="col-span-2">
            <Input value={form.required_skills} onChange={(e) => set('required_skills', e.target.value)} placeholder="python, fastapi, postgresql" />
          </Field>
          <Field label="Preferred skills (comma-separated)" className="col-span-2">
            <Textarea rows={2} value={form.preferred_skills} onChange={(e) => set('preferred_skills', e.target.value)} placeholder="docker, aws, graphql" />
          </Field>
        </div>
        <div className="mt-5 flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button loading={saving} leftIcon={<Sparkles className="h-4 w-4" />} onClick={submit}>
            Create & generate
          </Button>
        </div>
      </Dialog>

      {/* Detail dialog */}
      <Dialog
        open={!!selected}
        onClose={() => setSelected(null)}
        className="max-w-2xl"
      >
        {selected && (
          <div>
            <div className="mb-4 flex items-start justify-between gap-3 pr-6">
              <div>
                <h2 className="text-xl font-bold text-content">{selected.title}</h2>
                <p className="mt-1 text-sm text-content-muted">
                  {[titleCase(selected.employment_type), titleCase(selected.work_mode), selected.location]
                    .filter(Boolean).join(' · ')}
                </p>
              </div>
              <Badge variant={STATUS_VARIANT[selected.status] || 'default'}>{titleCase(selected.status)}</Badge>
            </div>

            <div className="mb-4 flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" loading={generating}
                leftIcon={<Sparkles className="h-4 w-4" />} onClick={() => regenerate(selected)}>
                Regenerate
              </Button>
              <Button size="sm" variant={selected.status === 'open' ? 'outline' : 'primary'}
                leftIcon={selected.status === 'open' ? <Lock className="h-4 w-4" /> : <Globe className="h-4 w-4" />}
                onClick={() => toggleStatus(selected)}>
                {selected.status === 'open' ? 'Close' : 'Publish'}
              </Button>
              {selected.status === 'open' && selected.public_slug && (
                <Button size="sm" variant="outline" leftIcon={<Copy className="h-4 w-4" />}
                  onClick={() => {
                    navigator.clipboard?.writeText(`${window.location.origin}/careers/${selected.public_slug}`);
                    toast.success('Application link copied');
                  }}>
                  Copy link
                </Button>
              )}
              <Button size="sm" variant="danger" leftIcon={<Trash2 className="h-4 w-4" />}
                onClick={() => remove(selected)}>
                Delete
              </Button>
            </div>

            {generating && (
              <div className="flex items-center gap-2 text-sm text-content-muted">
                <Loader2 className="h-4 w-4 animate-spin" /> Generating…
              </div>
            )}

            <div className="max-h-[55vh] space-y-5 overflow-y-auto pr-1">
              {selected.description && (
                <Section title="Description">
                  <p className="text-sm leading-relaxed text-content-muted">{selected.description}</p>
                </Section>
              )}
              <ListSection title="Responsibilities" items={selected.responsibilities} />
              <ListSection title="Requirements" items={selected.requirements} />
              <ListSection title="Preferred qualifications" items={selected.preferred_qualifications} />
              <ListSection title="Benefits" items={selected.benefits} />
              <ListSection title="Technical questions" items={selected.technical_questions} />
              <ListSection title="HR questions" items={selected.hr_questions} />
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}

function Field({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <label className={`flex flex-col gap-1.5 ${className}`}>
      <span className="text-xs font-medium text-content-muted">{label}</span>
      {children}
    </label>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-content-subtle">{title}</h4>
      {children}
    </div>
  );
}

function ListSection({ title, items }: { title: string; items?: string[] | null }) {
  if (!items || items.length === 0) return null;
  return (
    <Section title={title}>
      <ul className="space-y-1.5">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2 text-sm text-content-muted">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />
            {it}
          </li>
        ))}
      </ul>
    </Section>
  );
}
