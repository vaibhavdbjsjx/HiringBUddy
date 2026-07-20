import { useEffect, useState, type FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { Cpu, MapPin, Briefcase, Upload, CheckCircle2, Building2 } from 'lucide-react';
import { Button, Input, Textarea, Badge } from '../components/ui';
import { ThemeToggle } from '../theme/ThemeToggle';
import { getPublicJob, applyToJob, type Job } from '../services/api';

const titleCase = (s?: string | null) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function List({ title, items }: { title: string; items?: string[] | null }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-content-subtle">{title}</h3>
      <ul className="space-y-1.5">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2 text-sm text-content-muted"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />{it}</li>
        ))}
      </ul>
    </div>
  );
}

export default function Careers() {
  const { slug } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [cover, setCover] = useState('');
  const [salary, setSalary] = useState('');
  const [notice, setNotice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!slug) return;
    getPublicJob(slug).then(setJob).catch(() => setNotFound(true)).finally(() => setLoading(false));
  }, [slug]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (!file) { setError('Please attach your resume (PDF).'); return; }
    if (!file.name.toLowerCase().endsWith('.pdf')) { setError('Your resume must be a PDF.'); return; }
    setSubmitting(true);
    try {
      const form = new FormData();
      form.append('resume', file);
      if (cover) form.append('cover_letter', cover);
      if (salary) form.append('expected_salary', salary);
      if (notice) form.append('notice_period', notice);
      await applyToJob(slug!, form);
      setDone(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not submit your application. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg text-content">
      <header className="border-b bg-bg/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-primary-active text-primary-fg shadow-glow-sm"><Cpu className="h-5 w-5" /></div>
            <span className="text-lg font-bold tracking-tight">HiringBuddy</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        {loading ? (
          <p className="text-center text-content-muted">Loading…</p>
        ) : notFound || !job ? (
          <div className="mx-auto max-w-md rounded-2xl border bg-surface p-10 text-center">
            <h1 className="text-xl font-bold">Position not available</h1>
            <p className="mt-2 text-sm text-content-muted">This job posting isn't open or the link is invalid.</p>
          </div>
        ) : done ? (
          <div className="mx-auto max-w-md rounded-2xl border bg-surface p-10 text-center">
            <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-success/10"><CheckCircle2 className="h-7 w-7 text-success" /></div>
            <h1 className="text-2xl font-bold">Application received!</h1>
            <p className="mt-2 text-sm text-content-muted">Thanks for applying to <span className="font-medium text-content">{job.title}</span>. The team will review your profile and be in touch.</p>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-5">
            {/* Job details */}
            <div className="lg:col-span-3">
              <h1 className="text-3xl font-bold tracking-tight">{job.title}</h1>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {job.department && <Badge variant="outline">{job.department}</Badge>}
                {job.employment_type && <Badge variant="outline">{titleCase(job.employment_type)}</Badge>}
                {job.work_mode && <Badge variant="outline">{titleCase(job.work_mode)}</Badge>}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-content-muted">
                {job.company && <span className="flex items-center gap-1"><Building2 className="h-4 w-4" /> {job.company}</span>}
                {job.location && <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {job.location}</span>}
                <span className="flex items-center gap-1"><Briefcase className="h-4 w-4" /> {job.experience_min || 0}+ yrs</span>
              </div>

              {job.description && <p className="mt-6 leading-relaxed text-content-muted">{job.description}</p>}

              <div className="mt-6 space-y-6">
                <List title="Responsibilities" items={job.responsibilities} />
                <List title="Requirements" items={job.requirements} />
                <List title="Preferred qualifications" items={job.preferred_qualifications} />
                <List title="Benefits" items={job.benefits} />
              </div>

              {(job.required_skills?.length ?? 0) > 0 && (
                <div className="mt-6">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-content-subtle">Skills</h3>
                  <div className="flex flex-wrap gap-1.5">{job.required_skills!.map((s) => <Badge key={s} variant="primary">{s}</Badge>)}</div>
                </div>
              )}
            </div>

            {/* Apply form */}
            <div className="lg:col-span-2">
              <form onSubmit={submit} className="sticky top-24 space-y-4 rounded-2xl border bg-surface p-6 shadow-elev-1">
                <h2 className="text-lg font-semibold">Apply now</h2>
                <label className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border border-dashed p-6 text-center transition-colors hover:bg-surface-2">
                  <Upload className="h-6 w-6 text-content-subtle" />
                  <span className="text-sm font-medium text-content">{file ? file.name : 'Upload your resume (PDF)'}</span>
                  <span className="text-xs text-content-subtle">Click to browse</span>
                  <input type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                </label>
                <label className="flex flex-col gap-1.5"><span className="text-xs font-medium text-content-muted">Cover note (optional)</span>
                  <Textarea rows={3} value={cover} onChange={(e) => setCover(e.target.value)} placeholder="A few lines on why you're a great fit…" /></label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex flex-col gap-1.5"><span className="text-xs font-medium text-content-muted">Expected salary</span><Input value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="e.g. 120k" /></label>
                  <label className="flex flex-col gap-1.5"><span className="text-xs font-medium text-content-muted">Notice period</span><Input value={notice} onChange={(e) => setNotice(e.target.value)} placeholder="e.g. 30 days" /></label>
                </div>
                {error && <p className="text-sm font-medium text-danger">{error}</p>}
                <Button type="submit" className="w-full" size="lg" loading={submitting}>Submit application</Button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
