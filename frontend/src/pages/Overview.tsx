import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Users, CheckCircle2, XCircle, Activity, Code2, Briefcase, ArrowRight, TrendingUp,
} from 'lucide-react';
import { Card, Button, Skeleton, Badge } from '../components/ui';
import { getAnalytics, type Analytics } from '../services/api';

const STAT_META = [
  { key: 'total_candidates', label: 'Total Candidates', icon: Users, tone: 'text-primary bg-primary/10' },
  { key: 'shortlisted_count', label: 'Shortlisted', icon: CheckCircle2, tone: 'text-success bg-success/10' },
  { key: 'rejected_count', label: 'Rejected', icon: XCircle, tone: 'text-danger bg-danger/10' },
  { key: 'avg_score', label: 'Avg Match Score', icon: Activity, tone: 'text-info bg-info/10', suffix: '%' },
] as const;

export default function Overview() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch(() => setError('Unable to load analytics. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-content">Dashboard</h1>
            <Badge variant="success">
              <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-success" />
              Engine online
            </Badge>
          </div>
          <p className="mt-1 text-sm text-content-muted">Real-time AI analytics across your talent pool.</p>
        </div>
        <div className="flex gap-2">
          <Link to="/jobs"><Button variant="secondary" leftIcon={<Briefcase className="h-4 w-4" />}>Jobs</Button></Link>
          <Link to="/candidates"><Button rightIcon={<ArrowRight className="h-4 w-4" />}>Talent Pool</Button></Link>
        </div>
      </div>

      {error ? (
        <Card className="flex flex-col items-center gap-2 py-14 text-center">
          <XCircle className="h-8 w-8 text-danger" />
          <p className="font-semibold text-content">Analytics failed to load</p>
          <p className="max-w-md text-sm text-content-muted">{error}</p>
        </Card>
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STAT_META.map((s, i) => (
              <motion.div key={s.key} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Card className="p-5">
                  <div className="flex items-center justify-between">
                    <div className={`grid h-11 w-11 place-items-center rounded-xl ${s.tone}`}>
                      <s.icon className="h-5 w-5" />
                    </div>
                    <TrendingUp className="h-4 w-4 text-content-subtle" />
                  </div>
                  <p className="mt-4 text-xs font-medium uppercase tracking-wide text-content-subtle">{s.label}</p>
                  {loading || !analytics ? (
                    <Skeleton className="mt-1 h-8 w-20" />
                  ) : (
                    <p className="mt-1 text-3xl font-bold text-content">
                      {(analytics as any)[s.key]}
                      {'suffix' in s ? s.suffix : ''}
                    </p>
                  )}
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Top skills */}
          <Card className="p-6">
            <h2 className="mb-6 flex items-center gap-2 text-base font-semibold text-content">
              <Code2 className="h-5 w-5 text-primary" /> Top skills in your talent pool
            </h2>
            {loading || !analytics ? (
              <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : analytics.top_skills.length === 0 ? (
              <p className="py-6 text-center text-sm text-content-muted">
                No skills extracted yet. Upload resumes to see analytics.
              </p>
            ) : (
              <div className="space-y-4">
                {analytics.top_skills.map((item) => {
                  const max = analytics.top_skills[0]?.count || 1;
                  const pct = Math.round((item.count / max) * 100);
                  return (
                    <div key={item.skill} className="flex flex-col gap-1.5">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium capitalize text-content">{item.skill}</span>
                        <span className="text-content-subtle">{item.count}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-surface-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.6, ease: 'easeOut' }}
                          className="h-full rounded-full bg-gradient-to-r from-primary to-primary-hover"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </>
      )}
    </motion.div>
  );
}
