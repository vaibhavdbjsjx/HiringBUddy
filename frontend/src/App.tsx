import { Suspense, lazy, type ComponentType } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { ThemeToggle } from './theme/ThemeToggle';
import { logout as apiLogout } from './services/api';
import { Cpu, Users, LayoutDashboard, Settings, LogOut, Briefcase, ClipboardCheck, Sparkles } from 'lucide-react';

// Route components are code-split so heavy pages load on demand.
const Landing = lazy(() => import('./pages/Landing'));
const Overview = lazy(() => import('./pages/Overview'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Jobs = lazy(() => import('./pages/Jobs'));
const Assessments = lazy(() => import('./pages/Assessments'));
const Copilot = lazy(() => import('./pages/Copilot'));
const InterviewRoom = lazy(() => import('./pages/InterviewRoom'));
const CandidateInterview = lazy(() => import('./pages/CandidateInterview'));
const MobileCamera = lazy(() => import('./pages/MobileCamera'));
const SettingsPage = lazy(() => import('./pages/Settings'));
const Auth = lazy(() => import('./pages/Auth'));
const Careers = lazy(() => import('./pages/Careers'));

const NAV: { to: string; icon: ComponentType<{ className?: string }>; label: string }[] = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/candidates', icon: Users, label: 'Talent Pool' },
  { to: '/jobs', icon: Briefcase, label: 'Jobs' },
  { to: '/assessments', icon: ClipboardCheck, label: 'Assessments' },
  { to: '/copilot', icon: Sparkles, label: 'Copilot' },
];

function NavItem({ to, icon: Icon, label }: (typeof NAV)[number]) {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
        active ? 'bg-primary/10 text-primary' : 'text-content-muted hover:bg-surface-2 hover:text-content'
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </Link>
  );
}

function Navigation() {
  const navigate = useNavigate();
  const handleLogout = () => {
    apiLogout();
    navigate('/auth');
  };
  return (
    <div className="sticky top-0 z-50 px-4 pt-4 sm:px-6">
      <nav className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 rounded-2xl border bg-surface/80 px-4 py-2.5 shadow-elev-1 backdrop-blur-xl">
        <div className="flex items-center gap-6">
          <Link to="/dashboard" className="flex items-center gap-2.5">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-primary-active text-primary-fg shadow-glow-sm">
              <Cpu className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight text-content">HiringBuddy</span>
          </Link>
          <div className="hidden items-center gap-1 md:flex">
            {NAV.map((n) => <NavItem key={n.to} {...n} />)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            to="/settings"
            className="grid h-9 w-9 place-items-center rounded-lg border text-content-muted transition-colors hover:bg-surface-2 hover:text-content"
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </Link>
          <button
            onClick={handleLogout}
            title="Log out"
            className="grid h-9 w-9 place-items-center rounded-lg border text-content-muted transition-colors hover:border-danger/40 hover:bg-danger/10 hover:text-danger"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </nav>
      <div className="mx-auto mt-2 flex max-w-[1600px] items-center gap-1 overflow-x-auto pb-1 md:hidden">
        {NAV.map((n) => <NavItem key={n.to} {...n} />)}
      </div>
    </div>
  );
}

function AppChrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg text-content">
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{ background: 'radial-gradient(55rem 40rem at 85% -10%, rgb(var(--primary) / 0.08), transparent 70%)' }}
      />
      <div className="relative z-10">
        <Navigation />
        <main className="mx-auto max-w-[1600px] p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}

function Shell() {
  const { pathname } = useLocation();
  const isFullscreen =
    pathname === '/' ||
    pathname === '/auth' ||
    pathname.includes('/c-interview') ||
    pathname.includes('/mobile-cam') ||
    pathname.includes('/careers') ||
    pathname.includes('/interview');

  const routes = (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<Auth />} />
      <Route path="/c-interview/:id" element={<CandidateInterview />} />
      <Route path="/mobile-cam/:id" element={<MobileCamera />} />
      <Route path="/careers/:slug" element={<Careers />} />
      <Route path="/dashboard" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
      <Route path="/candidates" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/jobs" element={<ProtectedRoute><Jobs /></ProtectedRoute>} />
      <Route path="/assessments" element={<ProtectedRoute><Assessments /></ProtectedRoute>} />
      <Route path="/copilot" element={<ProtectedRoute><Copilot /></ProtectedRoute>} />
      <Route path="/interview/:id" element={<ProtectedRoute><InterviewRoom /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
    </Routes>
  );

  return (
    <Suspense fallback={<div className="grid min-h-screen place-items-center bg-bg text-content-subtle">Loading…</div>}>
      {isFullscreen ? routes : <AppChrome>{routes}</AppChrome>}
    </Suspense>
  );
}

export default function App() {
  return (
    <Router>
      <Shell />
    </Router>
  );
}
