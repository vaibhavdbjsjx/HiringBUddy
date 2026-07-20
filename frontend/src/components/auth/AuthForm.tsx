import React, { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { login as apiLogin, register as apiRegister } from '../../services/api';
import { Input, Button, useToast } from '../ui';

interface Props {
  onSuccess: () => void;
}

export default function AuthForm({ onSuccess }: Props) {
  const toast = useToast();
  const [isLogin, setIsLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [suggestedEmail, setSuggestedEmail] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('hiringbuddy_remembered_email');
    if (saved) setSuggestedEmail(saved);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password || (!isLogin && !name)) { setError('Please fill in all fields'); return; }
    if (!email.includes('@')) { setError('Please enter a valid email address'); return; }
    if (!isLogin && password.length < 8) { setError('Password must be at least 8 characters'); return; }

    setIsSubmitting(true);
    try {
      const res = isLogin ? await apiLogin(email, password) : await apiRegister(email, password, name);
      localStorage.setItem('hiringbuddy_auth_token', res.access_token);
      localStorage.setItem('hiringbuddy_user', JSON.stringify(res.user));
      localStorage.setItem('hiringbuddy_remembered_email', email);
      onSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Authentication failed. Please check your details and try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-content">{isLogin ? 'Welcome back' : 'Create your account'}</h1>
        <p className="mt-2 text-sm text-content-muted">{isLogin ? 'Sign in to your HiringBuddy workspace.' : 'Start hiring smarter in minutes.'}</p>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3">
        <button type="button" aria-label="Continue with Google" onClick={() => toast.info('Social sign-in is coming soon', 'Use your email to create an account for now.')} className="flex items-center justify-center gap-2 rounded-lg border py-2.5 text-sm font-medium text-content-muted transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"><GoogleIcon /> Google</button>
        <button type="button" aria-label="Continue with GitHub" onClick={() => toast.info('Social sign-in is coming soon', 'Use your email to create an account for now.')} className="flex items-center justify-center gap-2 rounded-lg border py-2.5 text-sm font-medium text-content-muted transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"><GithubIcon /> GitHub</button>
      </div>

      <div className="mb-6 flex items-center gap-3">
        <div className="flex-1 border-t" />
        <span className="text-xs uppercase tracking-wide text-content-subtle">or</span>
        <div className="flex-1 border-t" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <AnimatePresence mode="popLayout">
          {!isLogin && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <Input aria-label="Full name" autoComplete="name" placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />
            </motion.div>
          )}
        </AnimatePresence>
        <div>
          <Input type="email" aria-label="Email address" autoComplete="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} />
          {suggestedEmail && !email && (
            <button type="button" onClick={() => setEmail(suggestedEmail)} className="mt-1.5 text-xs font-medium text-primary hover:underline">Use {suggestedEmail}</button>
          )}
        </div>
        <Input type="password" aria-label="Password" autoComplete={isLogin ? 'current-password' : 'new-password'} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && <p className="text-sm font-medium text-danger">{error}</p>}

        <Button type="submit" size="lg" className="w-full" loading={isSubmitting}>{isLogin ? 'Sign in' : 'Create account'}</Button>
      </form>

      <p className="mt-6 text-center text-sm text-content-muted">
        {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
        <button type="button" onClick={() => { setIsLogin(!isLogin); setError(''); }} className="font-semibold text-primary hover:underline">
          {isLogin ? 'Sign up' : 'Sign in'}
        </button>
      </p>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="currentColor" d="M5.84 14.09A6.6 6.6 0 0 1 5.49 12c0-.73.13-1.43.35-2.09V7.07H2.18A11 11 0 0 0 1 12c0 1.78.43 3.45 1.18 4.93l3.66-2.84z" />
      <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z" />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0 0 22 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}
