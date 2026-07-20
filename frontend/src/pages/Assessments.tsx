import { useState } from 'react';
import { ClipboardCheck, Sparkles, CheckCircle2, XCircle } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, Input, Button, Badge, Skeleton, useToast,
} from '../components/ui';
import { generateAssessment, submitAssessment, type Assessment, type AssessmentResult } from '../services/api';

const csv = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean);

export default function Assessments() {
  const toast = useToast();
  const [role, setRole] = useState('');
  const [skills, setSkills] = useState('');
  const [num, setNum] = useState('5');
  const [generating, setGenerating] = useState(false);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const generate = async () => {
    setGenerating(true);
    setResult(null);
    setAnswers({});
    try {
      const a = await generateAssessment({ role: role || undefined, skills: csv(skills), num_questions: Number(num) || 5 });
      setAssessment(a);
    } catch {
      toast.error('Could not generate assessment');
    } finally {
      setGenerating(false);
    }
  };

  const submit = async () => {
    if (!assessment) return;
    setSubmitting(true);
    try {
      const res = await submitAssessment(assessment.id, assessment.questions.map((_, i) => answers[i] ?? -1));
      setResult(res);
      toast.success(`Scored ${res.score}%`, `${res.correct}/${res.total} correct`);
    } catch {
      toast.error('Could not submit answers');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold text-content"><ClipboardCheck className="h-6 w-6 text-primary" /> Skill Assessments</h1>
        <p className="mt-1 text-sm text-content-muted">Generate role-based MCQ tests and score them instantly.</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Generate a test</CardTitle><CardDescription>AI writes questions for the role and skills you specify.</CardDescription></CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 sm:col-span-2"><span className="text-xs font-medium text-content-muted">Role</span><Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Backend Developer" /></label>
          <label className="flex flex-col gap-1.5"><span className="text-xs font-medium text-content-muted">Skills (comma-separated)</span><Input value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="python, sql" /></label>
          <label className="flex flex-col gap-1.5"><span className="text-xs font-medium text-content-muted"># Questions</span><Input type="number" value={num} onChange={(e) => setNum(e.target.value)} /></label>
          <div className="sm:col-span-2"><Button loading={generating} leftIcon={<Sparkles className="h-4 w-4" />} onClick={generate}>Generate test</Button></div>
        </CardContent>
      </Card>

      {generating && <Card><CardContent className="space-y-3 pt-5">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</CardContent></Card>}

      {assessment && !generating && (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div><CardTitle>{assessment.role || 'Assessment'}</CardTitle><CardDescription>{assessment.questions.length} questions</CardDescription></div>
            {result && <Badge variant={result.score >= 60 ? 'success' : 'danger'}>{result.score}% · {result.correct}/{result.total}</Badge>}
          </CardHeader>
          <CardContent className="space-y-5">
            {assessment.questions.map((q, qi) => {
              const chosen = answers[qi];
              const correctIdx = result?.results[qi]?.correct_index;
              return (
                <div key={qi} className="rounded-xl border bg-surface-2 p-4">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <p className="text-sm font-medium text-content">{qi + 1}. {q.question}</p>
                    {q.difficulty && <Badge>{q.difficulty}</Badge>}
                  </div>
                  <div className="space-y-2">
                    {q.options.map((opt, oi) => {
                      const isChosen = chosen === oi;
                      const isCorrect = !!result && correctIdx === oi;
                      const isWrong = !!result && isChosen && correctIdx !== oi;
                      return (
                        <button key={oi} disabled={!!result} onClick={() => setAnswers((a) => ({ ...a, [qi]: oi }))}
                          className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                            isCorrect ? 'border-success/40 bg-success/10 text-success'
                            : isWrong ? 'border-danger/40 bg-danger/10 text-danger'
                            : isChosen ? 'border-primary bg-primary/10 text-content'
                            : 'text-content-muted hover:bg-surface-3'}`}>
                          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full border text-[10px]">{String.fromCharCode(65 + oi)}</span>
                          {opt}
                          {isCorrect && <CheckCircle2 className="ml-auto h-4 w-4" />}
                          {isWrong && <XCircle className="ml-auto h-4 w-4" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
            {!result && (
              <Button className="w-full" loading={submitting} disabled={Object.keys(answers).length < assessment.questions.length} onClick={submit}>
                Submit answers
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
