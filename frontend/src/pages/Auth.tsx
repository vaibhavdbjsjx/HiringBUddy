import { useNavigate } from 'react-router-dom';
import { Cpu, Sparkles, Zap, ShieldCheck } from 'lucide-react';
import AuthForm from '../components/auth/AuthForm';
import { ThemeToggle } from '../theme/ThemeToggle';

const FEATURES = [
  { icon: Sparkles, label: 'AI screening & explainable scoring' },
  { icon: Zap, label: 'AI video interviews & assessments' },
  { icon: ShieldCheck, label: 'Live proctoring & integrity scoring' },
];

export default function Auth() {
  const navigate = useNavigate();

  return (
    <div className="grid min-h-screen bg-bg text-content lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-primary to-primary-active p-12 text-primary-fg lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute inset-0 opacity-20" style={{ background: 'radial-gradient(30rem 30rem at 15% 15%, white, transparent 60%)' }} />
        <div className="relative flex items-center gap-2.5">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/15"><Cpu className="h-6 w-6" /></div>
          <span className="text-xl font-bold">HiringBuddy</span>
        </div>
        <div className="relative">
          <h1 className="max-w-md text-4xl font-bold leading-tight">Hire better people, dramatically faster.</h1>
          <p className="mt-4 max-w-md text-primary-fg/80">Screen, interview, and assess candidates with AI — all in one premium workspace.</p>
          <div className="mt-8 space-y-3 text-sm">
            {FEATURES.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/15"><Icon className="h-4 w-4" /></span>
                {label}
              </div>
            ))}
          </div>
        </div>
        <p className="relative text-xs text-primary-fg/60">© {new Date().getFullYear()} HiringBuddy — AI Recruitment OS</p>
      </div>

      {/* Form panel */}
      <div className="relative flex items-center justify-center p-6">
        <div className="absolute right-4 top-4"><ThemeToggle /></div>
        <div className="w-full max-w-sm">
          <AuthForm onSuccess={() => navigate('/dashboard')} />
        </div>
      </div>
    </div>
  );
}
