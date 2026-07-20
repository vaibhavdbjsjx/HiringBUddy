import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Cpu, Sparkles, FileSearch, Video, ShieldCheck, MessageSquareText, ClipboardCheck,
  ArrowRight, Check, ChevronDown, Star,
} from 'lucide-react';
import { Button, Badge } from '../components/ui';
import { ThemeToggle } from '../theme/ThemeToggle';

const FEATURES = [
  { icon: FileSearch, title: 'Resume intelligence', desc: 'Parse any PDF, extract skills, detect the role, and score fit — with reasoning, never random.' },
  { icon: Sparkles, title: 'AI job creation', desc: 'Draft descriptions, interview plans, and question banks from a few fields in seconds.' },
  { icon: Video, title: 'AI video interviews', desc: 'Adaptive, role-tailored questions and follow-ups with automatic transcripts and summaries.' },
  { icon: ShieldCheck, title: 'Live proctoring', desc: 'Integrity scoring that starts at 100 and deducts on tab-switches, missing faces, and more.' },
  { icon: ClipboardCheck, title: 'Skill assessments', desc: 'Auto-generated, role-based MCQ tests that grade themselves — answers stay server-side.' },
  { icon: MessageSquareText, title: 'HR Copilot', desc: 'Ask in plain English: “top 5 React devs”, “compare A and B”, “who’s below 70%”.' },
];

const STEPS = [
  { n: '01', title: 'Post a role', desc: 'Enter the essentials — AI writes the full posting and interview plan.' },
  { n: '02', title: 'Screen automatically', desc: 'Resumes are parsed, scored, and ranked the moment they arrive.' },
  { n: '03', title: 'Interview & decide', desc: 'Run proctored AI interviews and hire with confidence — faster.' },
];

const PLANS = [
  { name: 'Starter', price: '$0', tagline: 'For trying it out', features: ['1 recruiter', 'Up to 50 candidates', 'AI screening & scoring', 'Email automation'], cta: 'Start free', highlight: false },
  { name: 'Growth', price: '$49', tagline: 'For growing teams', features: ['5 recruiters', 'Unlimited candidates', 'AI video interviews', 'Skill assessments', 'HR Copilot'], cta: 'Start free trial', highlight: true },
  { name: 'Enterprise', price: 'Custom', tagline: 'For scale & security', features: ['Unlimited seats', 'SSO & audit logs', 'Custom integrations', 'Dedicated support'], cta: 'Contact sales', highlight: false },
];

const FAQS = [
  { q: 'Do I need an AI API key to try it?', a: 'No. The whole pipeline is offline-first — deterministic parsing, scoring, and interviews work without any key. Add a Groq key to unlock AI-refined content.' },
  { q: 'Is candidate data isolated?', a: 'Yes. Every recruiter belongs to an organization, and all jobs, candidates, and assessments are scoped to that org with JWT-secured access.' },
  { q: 'Which model powers the AI features?', a: 'HiringBuddy uses Groq (Llama 3.3 70B) through an OpenAI-compatible provider layer, so you can swap providers without code changes.' },
  { q: 'Can candidates apply without an account?', a: 'Yes — each job gets a public careers link where candidates upload a resume and apply directly.' },
];

function Section({ id, className = '', children }: { id?: string; className?: string; children: React.ReactNode }) {
  return <section id={id} className={`mx-auto w-full max-w-6xl px-6 ${className}`}>{children}</section>;
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button onClick={() => setOpen((o) => !o)} className="w-full rounded-xl border bg-surface p-5 text-left transition-colors hover:bg-surface-2">
      <div className="flex items-center justify-between gap-4">
        <span className="font-medium text-content">{q}</span>
        <ChevronDown className={`h-5 w-5 shrink-0 text-content-subtle transition-transform ${open ? 'rotate-180' : ''}`} />
      </div>
      {open && <p className="mt-3 text-sm leading-relaxed text-content-muted">{a}</p>}
    </button>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-bg text-content">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-bg/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-primary-active text-primary-fg shadow-glow-sm">
              <Cpu className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">HiringBuddy</span>
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-content-muted md:flex">
            <a href="#features" className="hover:text-content">Features</a>
            <a href="#how" className="hover:text-content">How it works</a>
            <a href="#pricing" className="hover:text-content">Pricing</a>
            <a href="#faq" className="hover:text-content">FAQ</a>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle className="hidden sm:inline-flex" />
            <Link to="/auth"><Button variant="ghost" size="sm">Sign in</Button></Link>
            <Link to="/auth"><Button size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>Get started</Button></Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0" style={{ background: 'radial-gradient(50rem 30rem at 50% -10%, rgb(var(--primary) / 0.14), transparent 70%)' }} />
        <Section className="relative py-20 text-center sm:py-28">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="mb-6 flex justify-center">
              <Badge variant="primary" className="gap-1.5 px-3 py-1"><Sparkles className="h-3.5 w-3.5" /> The AI Recruitment OS</Badge>
            </div>
            <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight sm:text-6xl">
              Hire better people, <span className="bg-gradient-to-r from-primary to-primary-hover bg-clip-text text-transparent">dramatically faster</span>.
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-content-muted">
              Screen resumes, run proctored AI interviews, generate assessments, and manage your whole
              pipeline — with a natural-language copilot doing the busywork.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link to="/auth"><Button size="lg" rightIcon={<ArrowRight className="h-4 w-4" />}>Start free</Button></Link>
              <a href="#how"><Button size="lg" variant="outline">See how it works</Button></a>
            </div>
            <p className="mt-4 text-xs text-content-subtle">No credit card · Works offline · Deploy on Render + Vercel</p>
          </motion.div>

          {/* Mock preview */}
          <motion.div
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.6 }}
            className="mx-auto mt-16 max-w-4xl rounded-2xl border bg-surface p-3 shadow-elev-3"
          >
            <div className="rounded-xl border bg-surface-2 p-5">
              <div className="grid gap-4 sm:grid-cols-4">
                {[['Candidates', '248'], ['Shortlisted', '37'], ['Avg score', '74%'], ['Interviews', '19']].map(([l, v]) => (
                  <div key={l} className="rounded-lg border bg-surface p-4 text-left">
                    <p className="text-xs uppercase tracking-wide text-content-subtle">{l}</p>
                    <p className="mt-1 text-2xl font-bold text-content">{v}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 space-y-2">
                {[['Priya Sharma', 'Backend Developer', 88], ['Arjun Mehta', 'Full Stack', 76], ['Neha Kapoor', 'Data Scientist', 64]].map(([n, r, s]) => (
                  <div key={n as string} className="flex items-center gap-3 rounded-lg border bg-surface p-3 text-left">
                    <div className="grid h-9 w-9 place-items-center rounded-full bg-primary-subtle text-xs font-bold text-primary">{(n as string).split(' ').map((x) => x[0]).join('')}</div>
                    <div className="flex-1"><p className="text-sm font-medium text-content">{n}</p><p className="text-xs text-content-subtle">{r}</p></div>
                    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-2"><div className="h-full rounded-full bg-gradient-to-r from-primary to-primary-hover" style={{ width: `${s}%` }} /></div>
                    <span className="w-10 text-right text-sm font-semibold text-content">{s}%</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </Section>
      </div>

      {/* Features */}
      <Section id="features" className="py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">Everything a recruiter needs</h2>
          <p className="mt-3 text-content-muted">One platform for the whole hiring lifecycle — designed to save you hours every week.</p>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div key={f.title} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
              className="rounded-xl border bg-surface p-6 transition-shadow hover:shadow-elev-2">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary"><f.icon className="h-5 w-5" /></div>
              <h3 className="mt-4 font-semibold text-content">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-content-muted">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* How it works */}
      <div className="border-y bg-surface/50">
        <Section id="how" className="py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">From open role to hire in three steps</h2>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="rounded-xl border bg-surface p-6">
                <span className="text-sm font-bold text-primary">{s.n}</span>
                <h3 className="mt-2 text-lg font-semibold text-content">{s.title}</h3>
                <p className="mt-1.5 text-sm text-content-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </Section>
      </div>

      {/* Pricing */}
      <Section id="pricing" className="py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">Simple, scalable pricing</h2>
          <p className="mt-3 text-content-muted">Start free. Upgrade as your team grows.</p>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {PLANS.map((p) => (
            <div key={p.name} className={`relative rounded-2xl border p-6 ${p.highlight ? 'border-primary bg-surface shadow-glow' : 'bg-surface'}`}>
              {p.highlight && <div className="absolute -top-3 left-1/2 -translate-x-1/2"><Badge variant="primary" className="gap-1"><Star className="h-3 w-3" /> Most popular</Badge></div>}
              <h3 className="font-semibold text-content">{p.name}</h3>
              <p className="text-sm text-content-subtle">{p.tagline}</p>
              <p className="mt-4 text-3xl font-bold text-content">{p.price}<span className="text-sm font-normal text-content-subtle">{p.price !== 'Custom' ? '/mo' : ''}</span></p>
              <ul className="mt-5 space-y-2.5">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-content-muted"><Check className="h-4 w-4 text-success" /> {f}</li>
                ))}
              </ul>
              <Link to="/auth" className="mt-6 block"><Button className="w-full" variant={p.highlight ? 'primary' : 'secondary'}>{p.cta}</Button></Link>
            </div>
          ))}
        </div>
      </Section>

      {/* FAQ */}
      <Section id="faq" className="py-20">
        <div className="mx-auto max-w-2xl text-center"><h2 className="text-3xl font-bold tracking-tight">Frequently asked questions</h2></div>
        <div className="mx-auto mt-10 max-w-2xl space-y-3">{FAQS.map((f) => <FaqItem key={f.q} {...f} />)}</div>
      </Section>

      {/* CTA */}
      <Section className="pb-20">
        <div className="relative overflow-hidden rounded-3xl border bg-gradient-to-br from-primary to-primary-active p-10 text-center text-primary-fg sm:p-16">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Ready to hire smarter?</h2>
          <p className="mx-auto mt-3 max-w-xl text-primary-fg/90">Set up your workspace in minutes. Your first job posting is on us.</p>
          <Link to="/auth" className="mt-8 inline-block">
            <button className="rounded-xl bg-white px-7 py-3 font-semibold text-primary transition-transform hover:scale-[1.02] active:scale-[0.98]">Get started free</button>
          </Link>
        </div>
      </Section>

      {/* Footer */}
      <footer className="border-t">
        <Section className="flex flex-col items-center justify-between gap-4 py-8 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-content-muted">
            <Cpu className="h-4 w-4 text-primary" /> HiringBuddy — AI Recruitment OS
          </div>
          <p className="text-xs text-content-subtle">© {new Date().getFullYear()} HiringBuddy. All rights reserved.</p>
        </Section>
      </footer>
    </div>
  );
}
