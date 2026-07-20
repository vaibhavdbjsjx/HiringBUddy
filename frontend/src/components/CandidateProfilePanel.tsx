import { X, CheckCircle, ShieldAlert, Cpu, Briefcase, FileText, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Candidate } from '../services/api';
import { Badge, type BadgeVariant } from './ui';

interface Props {
  candidate: Candidate;
  onClose: () => void;
}

const confVariant = (c?: string): BadgeVariant => (c === 'High' ? 'success' : c === 'Medium' ? 'warning' : 'danger');
const riskVariant = (r?: string): BadgeVariant => (r === 'Low' ? 'info' : r === 'Medium' ? 'warning' : 'danger');
const cplxVariant = (c?: string): BadgeVariant => (c === 'High' ? 'primary' : c === 'Medium' ? 'info' : 'default');
const recVariant = (r = ''): BadgeVariant => {
  const l = r.toLowerCase();
  if (l.includes('shortlist') || l.includes('proceed') || l.includes('recommend')) return 'success';
  if (l.includes('reject') || l.includes('no hire')) return 'danger';
  return 'warning';
};

function SectionTitle({ icon: Icon, children }: { icon: any; children: React.ReactNode }) {
  return (
    <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-content-subtle">
      <Icon className="h-4 w-4 text-primary" /> {children}
    </h3>
  );
}

export default function CandidateProfilePanel({ candidate, onClose }: Props) {
  const rm = candidate.role_match_data;
  const dd = candidate.decision_data;

  return (
    <div className="fixed inset-0 z-[80] flex justify-end bg-overlay/60 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 26, stiffness: 220 }}
        onClick={(e) => e.stopPropagation()}
        className="flex h-full w-full max-w-2xl flex-col overflow-y-auto border-l bg-surface shadow-elev-3"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b bg-surface/90 p-6 backdrop-blur-md">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-content">{candidate.name}</h2>
              <Badge variant={riskVariant(dd?.risk_level)}>Risk: {dd?.risk_level || 'Unknown'}</Badge>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-content-muted">
              <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> {candidate.experience_years} yrs</span>
              {candidate.email && <span className="flex items-center gap-1"><FileText className="h-3.5 w-3.5" /> {candidate.email}</span>}
            </div>
          </div>
          <button onClick={onClose} className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-content-muted transition-colors hover:bg-surface-2 hover:text-content">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-8 p-6">
          {/* HR Insights */}
          {candidate.hr_insights && (
            <section>
              <SectionTitle icon={Activity}>Final HR insights</SectionTitle>
              <div className="rounded-xl border border-primary/30 bg-primary-subtle p-5">
                <p className="text-[15px] font-medium leading-relaxed text-content">“{candidate.hr_insights.summary}”</p>
                <div className="mt-4 flex flex-col gap-4 border-t border-primary/20 pt-4 sm:flex-row">
                  <div className="flex-1">
                    <span className="mb-1 block text-xs font-semibold uppercase text-content-subtle">Recommendation</span>
                    <Badge variant={recVariant(candidate.hr_insights.recommendation)}>{candidate.hr_insights.recommendation}</Badge>
                  </div>
                  <div className="flex-[2]">
                    <span className="mb-1 block text-xs font-semibold uppercase text-content-subtle">Next action</span>
                    <span className="text-sm font-semibold text-primary">{candidate.hr_insights.next_action}</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Projects */}
          {candidate.projects_analysis?.projects && candidate.projects_analysis.projects.length > 0 && (
            <section>
              <SectionTitle icon={Cpu}>Project intelligence</SectionTitle>
              <div className="space-y-3">
                {candidate.projects_analysis.projects.map((p, i) => (
                  <div key={i} className="rounded-xl border bg-surface-2 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="font-semibold text-content">{p.name}</h4>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">{p.tech.map((t, j) => <Badge key={j} variant="outline">{t}</Badge>)}</div>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1.5">
                        <Badge variant={cplxVariant(p.complexity)}>{p.complexity}</Badge>
                        <span className="text-xs font-semibold text-content-subtle">{p.score} pts</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Smart questions */}
          {candidate.smart_questions?.questions && candidate.smart_questions.questions.length > 0 && (
            <section>
              <SectionTitle icon={ShieldAlert}>AI interview questions</SectionTitle>
              <div className="rounded-xl border bg-surface-2 p-5">
                <p className="mb-4 text-xs text-content-muted">Targeted at this candidate's weak points and core role requirements.</p>
                <ul className="space-y-3">
                  {candidate.smart_questions.questions.map((q, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-content">
                      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary-subtle text-xs font-bold text-primary">{i + 1}</span>
                      <span className="leading-relaxed">{q}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          )}

          {/* Executive summary */}
          <section>
            <SectionTitle icon={Cpu}>AI executive summary</SectionTitle>
            <div className="rounded-xl border bg-surface-2 p-5">
              <p className="text-[15px] font-medium leading-relaxed text-content">{dd?.summary || 'No summary generated.'}</p>
              <div className="mt-4 flex items-center gap-5">
                <div>
                  <span className="block text-xs font-semibold uppercase text-content-subtle">Decision</span>
                  <span className="text-lg font-bold text-content">{dd?.decision || 'Pending'}</span>
                </div>
                <div className="h-8 w-px bg-border" />
                <div>
                  <span className="block text-xs font-semibold uppercase text-content-subtle">Confidence</span>
                  <span className="text-lg font-bold text-primary">{Math.round(dd?.confidence_score || 0)}%</span>
                </div>
              </div>
            </div>
          </section>

          {/* Role match */}
          {rm && (
            <section>
              <SectionTitle icon={Activity}>Role match analysis</SectionTitle>
              <div className="space-y-4 rounded-xl border bg-surface-2 p-5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-content">{rm.role_applied || candidate.role_applied || 'Role'} match</span>
                  <span className="font-bold text-primary">{rm.overall_match ?? rm.role_match}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface"><div className="h-full rounded-full bg-primary" style={{ width: `${rm.overall_match ?? rm.role_match}%` }} /></div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { label: 'Skills', value: rm.skills_match },
                    { label: 'Experience', value: rm.experience_match },
                    { label: 'Projects', value: rm.project_match },
                    { label: 'Certs', value: rm.certification_match },
                  ].filter((m) => m.value !== undefined).map((m) => (
                    <div key={m.label} className="rounded-lg border bg-surface p-3 text-center">
                      <div className="text-lg font-bold text-content">{Math.round(m.value as number)}%</div>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-content-subtle">{m.label}</div>
                    </div>
                  ))}
                </div>
                {rm.recommendation && <div className="rounded-lg bg-primary-subtle px-3 py-2 text-xs font-medium text-primary">{rm.recommendation}</div>}
                <div className="grid grid-cols-2 gap-4 border-t pt-4">
                  <div>
                    <span className="mb-2 block text-xs font-semibold uppercase text-success">Matched</span>
                    <ul className="space-y-1">{rm.matched_skills.map((s, i) => <li key={i} className="flex items-center gap-1.5 text-xs text-content-muted"><CheckCircle className="h-3 w-3 text-success" /> {s}</li>)}</ul>
                  </div>
                  <div>
                    <span className="mb-2 block text-xs font-semibold uppercase text-danger">Missing</span>
                    <ul className="space-y-1">{rm.missing_skills.map((s, i) => <li key={i} className="flex items-center gap-1.5 text-xs text-content-muted"><X className="h-3 w-3 text-danger" /> {s}</li>)}</ul>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Verified skills */}
          {candidate.multi_signal_skills && candidate.multi_signal_skills.length > 0 && (
            <section>
              <SectionTitle icon={CheckCircle}>Verified skills</SectionTitle>
              <div className="space-y-3">
                {candidate.multi_signal_skills.map((s, i) => (
                  <div key={i} className="rounded-xl border bg-surface-2 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-semibold text-content">{s.name}</span>
                      <Badge variant={confVariant(s.confidence)}>{s.confidence} confidence</Badge>
                    </div>
                    <div className="mb-3 flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface"><div className="h-full bg-primary" style={{ width: `${s.score}%` }} /></div>
                      <span className="text-xs font-semibold text-content-subtle">{s.score} pts</span>
                    </div>
                    <ul className="space-y-1 border-l pl-2">{s.evidence.map((ev, j) => <li key={j} className="text-[11px] text-content-muted">{ev}</li>)}</ul>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Warnings */}
          {candidate.detailed_warnings && candidate.detailed_warnings.length > 0 && (
            <section>
              <SectionTitle icon={ShieldAlert}>Integrity warnings</SectionTitle>
              <div className="space-y-3">
                {candidate.detailed_warnings.map((w, i) => (
                  <div key={i} className="rounded-xl border border-danger/20 bg-danger/5 p-4">
                    <div className="text-sm font-semibold text-danger">{w.skill}</div>
                    <p className="text-xs leading-relaxed text-content-muted">{w.reason}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Consistency */}
          {candidate.consistency_data && (
            <section>
              <SectionTitle icon={Briefcase}>Experience consistency</SectionTitle>
              <div className="rounded-xl border bg-surface-2 p-5">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-sm font-semibold text-content-muted">Consistency score</span>
                  <span className="font-bold text-content">{candidate.consistency_data.consistency_score}%</span>
                </div>
                {candidate.consistency_data.issues && candidate.consistency_data.issues.length > 0 ? (
                  <ul className="space-y-2">{candidate.consistency_data.issues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2 rounded-lg border border-warning/20 bg-warning/10 p-2.5 text-xs text-warning">• {issue}</li>
                  ))}</ul>
                ) : (
                  <div className="flex items-center gap-2 text-xs text-success"><CheckCircle className="h-4 w-4" /> Experience matches claimed skills.</div>
                )}
              </div>
            </section>
          )}
        </div>
      </motion.div>
    </div>
  );
}
