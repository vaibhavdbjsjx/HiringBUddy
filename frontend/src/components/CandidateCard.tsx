import { useState, type ComponentType } from 'react';
import {
  Mail, Video, UserX, AlertTriangle, Star, Briefcase, ChevronDown, Check, Eye,
  Phone, Link as LinkIcon, Globe,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { getResumeUrl, sendEmailAction, startAIInterview, type Candidate } from '../services/api';
import CandidateProfilePanel from './CandidateProfilePanel';
import { Card, Badge, Button, Dialog, useToast, type BadgeVariant } from './ui';

interface Props {
  candidate: Candidate;
  onReject: (id: number) => void;
  onInvite: (id: number) => void;
  onRefresh: () => void;
  isSelected?: boolean;
  onToggleSelect?: (id: number) => void;
}

const CATEGORY_VARIANT: Record<string, BadgeVariant> = {
  'Top Talent': 'success', 'Top Candidate': 'success',
  'Strong Candidate': 'primary', 'High Potential': 'primary',
  'Potential Fit': 'warning', 'Needs Review': 'warning',
};

const STATUS_DOT: Record<string, string> = {
  invited: 'bg-primary', rejected: 'bg-danger', shortlisted: 'bg-success', processing: 'bg-warning animate-pulse',
};

function StatusDot({ status }: { status: string }) {
  if (!STATUS_DOT[status]) return null;
  return <span className={`absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-surface ${STATUS_DOT[status]}`} title={status} />;
}

function EmailAction({ icon: Icon, tone, title, desc, onClick, disabled }: {
  icon: ComponentType<{ className?: string }>; tone: string; title: string; desc: string; onClick: () => void; disabled?: boolean;
}) {
  return (
    <button onClick={onClick} disabled={disabled} className="flex items-center gap-3 rounded-xl border p-3 text-left transition-colors hover:bg-surface-2 disabled:opacity-50">
      <span className={`grid h-9 w-9 place-items-center rounded-lg ${tone}`}><Icon className="h-4 w-4" /></span>
      <div><p className="text-sm font-semibold text-content">{title}</p><p className="text-xs text-content-muted">{desc}</p></div>
    </button>
  );
}

export default function CandidateCard({ candidate, onReject, onInvite, onRefresh, isSelected, onToggleSelect }: Props) {
  const navigate = useNavigate();
  const toast = useToast();
  const [showWarnings, setShowWarnings] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSendEmail = async (type: 'invite' | 'reject' | 'shortlist') => {
    setLoading(true);
    try {
      const res = await sendEmailAction(type, candidate.email);
      const delivered = res.email_status !== 'failed' && res.email_status !== 'no_email';
      if (delivered) toast.success(`Sent ${type} email to ${candidate.name}`);
      else if (res.email_status === 'no_email') toast.error('Candidate has no email on file');
      else toast.error('Email could not be delivered', 'Check your SMTP settings.');
      if (type === 'invite') onInvite(candidate.id);
      if (type === 'reject') onReject(candidate.id);
      onRefresh();
    } catch {
      toast.error('Failed to send email');
    }
    setLoading(false);
    setShowEmailModal(false);
  };

  const handleStartAIInterview = async () => {
    setLoading(true);
    try {
      const res = await startAIInterview(candidate.email);
      toast.success('Interview session started');
      navigate(`/interview/${res.interview_id}`);
    } catch {
      toast.error('Failed to start AI interview');
    }
    setLoading(false);
  };

  const skills = Array.isArray(candidate.skills) ? candidate.skills : [];
  const conf = candidate.decision_data?.confidence_score;
  const confTone = conf == null ? '' : conf >= 70 ? 'text-success' : conf >= 40 ? 'text-warning' : 'text-danger';
  const warnCount = (candidate.detailed_warnings?.length || 0) + (candidate.red_flags?.length || 0);

  return (
    <>
      <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97 }}>
        <Card className="p-5 transition-shadow hover:shadow-elev-2">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center">
            {/* Identity */}
            <div className="flex min-w-0 flex-1 items-start gap-4">
              {onToggleSelect && (
                <input type="checkbox" checked={isSelected} onChange={() => onToggleSelect(candidate.id)}
                  className="mt-3 h-4 w-4 accent-primary" title="Select to compare" />
              )}
              <div className="relative grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary-subtle text-lg font-bold text-primary">
                {candidate.name.charAt(0).toUpperCase()}
                <StatusDot status={candidate.status} />
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold text-content">{candidate.name}</h3>
                  {candidate.candidate_category && (
                    <Badge variant={CATEGORY_VARIANT[candidate.candidate_category] || 'default'}>{candidate.candidate_category}</Badge>
                  )}
                  {candidate.hidden_talent_tag && <Badge variant="primary"><Star className="h-3 w-3" /> Hidden talent</Badge>}
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-content-muted">
                  {candidate.role_applied && <span className="font-medium text-primary">{candidate.role_applied}</span>}
                  <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> {candidate.experience_years} yrs</span>
                  {candidate.email ? (
                    <a href={`mailto:${candidate.email}`} className="flex items-center gap-1 hover:text-content"><Mail className="h-3.5 w-3.5" /> {candidate.email}</a>
                  ) : (
                    <span className="flex items-center gap-1 text-warning"><AlertTriangle className="h-3.5 w-3.5" /> No email — review</span>
                  )}
                  {candidate.phone && <a href={`tel:${candidate.phone}`} className="flex items-center gap-1 hover:text-content"><Phone className="h-3.5 w-3.5" /> {candidate.phone}</a>}
                  {candidate.linkedin && <a href={candidate.linkedin} target="_blank" rel="noreferrer" className="text-content-subtle hover:text-primary" title="LinkedIn"><LinkIcon className="h-4 w-4" /></a>}
                  {candidate.github && <a href={candidate.github} target="_blank" rel="noreferrer" className="text-content-subtle hover:text-primary" title="GitHub"><LinkIcon className="h-4 w-4" /></a>}
                  {candidate.portfolio && <a href={candidate.portfolio} target="_blank" rel="noreferrer" className="text-content-subtle hover:text-primary" title="Portfolio"><Globe className="h-4 w-4" /></a>}
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {skills.slice(0, 6).map((s) => <Badge key={s} variant="outline">{s}</Badge>)}
                  {skills.length > 6 && <Badge>+{skills.length - 6}</Badge>}
                  {skills.length === 0 && <span className="text-xs italic text-content-subtle">No skills extracted</span>}
                </div>
                <a href={getResumeUrl(candidate.id)} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-info hover:underline">
                  <Eye className="h-3.5 w-3.5" /> View resume
                </a>
              </div>
            </div>

            {/* Scores */}
            <div className="flex w-full flex-col gap-2 xl:w-56 xl:shrink-0">
              {conf != null && (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-content-subtle">Confidence</p>
                    <p className={`text-xl font-bold ${confTone}`}>{Math.round(conf)}%</p>
                  </div>
                  {candidate.decision_data?.risk_level && (
                    <Badge variant={candidate.decision_data.risk_level === 'Low' ? 'info' : candidate.decision_data.risk_level === 'Medium' ? 'warning' : 'danger'}>
                      Risk: {candidate.decision_data.risk_level}
                    </Badge>
                  )}
                </div>
              )}
              {candidate.role_match_data && (
                <div>
                  <div className="mb-0.5 flex justify-between text-[10px] uppercase text-content-subtle">
                    <span>Role match</span><span>{candidate.role_match_data.role_match}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${candidate.role_match_data.role_match}%` }} />
                  </div>
                </div>
              )}
              {warnCount > 0 && (
                <div>
                  <button onClick={() => setShowWarnings(!showWarnings)} className="flex items-center gap-1.5 rounded-lg bg-danger/10 px-2 py-1 text-xs font-medium text-danger">
                    <AlertTriangle className="h-3.5 w-3.5" /> {showWarnings ? 'Hide' : `${warnCount} warning${warnCount > 1 ? 's' : ''}`}
                    <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showWarnings ? 'rotate-180' : ''}`} />
                  </button>
                  <AnimatePresence>
                    {showWarnings && (
                      <motion.ul initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                        className="mt-2 space-y-1.5 overflow-hidden rounded-lg border bg-surface-2 p-3 text-[11px]">
                        {candidate.detailed_warnings?.map((w, i) => <li key={`w${i}`} className="text-danger"><span className="font-semibold">{w.skill}:</span> {w.reason}</li>)}
                        {candidate.red_flags?.map((f, i) => <li key={`f${i}`} className="text-danger">• {f}</li>)}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex w-full items-center gap-2 border-t pt-4 xl:w-auto xl:border-l xl:border-t-0 xl:pl-5 xl:pt-0">
              <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => setShowProfile(true)}>Profile</Button>
              <Button variant="ghost" size="icon" title={candidate.email ? 'Email actions' : 'No email'}
                onClick={() => { if (!candidate.email) { toast.error('Candidate has no email'); return; } setShowEmailModal(true); }}>
                <Mail className="h-4 w-4" />
              </Button>
              <Button size="sm" leftIcon={<Video className="h-4 w-4" />} loading={loading} disabled={!candidate.email}
                onClick={handleStartAIInterview} title={candidate.email ? 'Start AI interview' : 'No email'}>
                Interview
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>

      <Dialog open={showEmailModal} onClose={() => setShowEmailModal(false)} title={`Email ${candidate.name}`}>
        <div className="flex flex-col gap-3">
          <EmailAction icon={Mail} tone="text-info bg-info/10" title="Interview invite" desc="Send the invitation template" onClick={() => handleSendEmail('invite')} disabled={loading} />
          <EmailAction icon={Check} tone="text-success bg-success/10" title="Shortlist notice" desc="Let them know they're shortlisted" onClick={() => handleSendEmail('shortlist')} disabled={loading} />
          <EmailAction icon={UserX} tone="text-danger bg-danger/10" title="Rejection" desc="Send the rejection template" onClick={() => handleSendEmail('reject')} disabled={loading} />
        </div>
      </Dialog>

      <AnimatePresence>
        {showProfile && <CandidateProfilePanel candidate={candidate} onClose={() => setShowProfile(false)} />}
      </AnimatePresence>
    </>
  );
}
