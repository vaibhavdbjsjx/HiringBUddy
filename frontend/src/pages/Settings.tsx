import { useEffect, useState } from 'react';
import { Mail, Save, Palette, Building2, Server, Info } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
  Input, Textarea, Button, Skeleton, useToast,
} from '../components/ui';
import { ThemeToggle } from '../theme/ThemeToggle';
import { getSettings, updateSettings, type Settings as SettingsType } from '../services/api';

const TOKENS = ['candidate_name', 'company_name', 'hr_name', 'job_role', 'interview_date', 'interview_time', 'interview_link'];

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-content-muted">{label}</span>
      {children}
    </label>
  );
}

export default function SettingsPage() {
  const toast = useToast();
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => toast.error('Could not load settings')).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (patch: Partial<SettingsType>) => setSettings((s) => (s ? { ...s, ...patch } : s));

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await updateSettings(settings);
      toast.success('Settings saved');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-content">Settings</h1>
        <p className="mt-1 text-sm text-content-muted">Manage appearance, branding, email delivery, and templates.</p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Palette className="h-4 w-4 text-primary" /> Appearance</CardTitle>
          <CardDescription>Choose light, dark, or match your system.</CardDescription>
        </CardHeader>
        <CardContent><ThemeToggle /></CardContent>
      </Card>

      {loading || !settings ? (
        <Card><CardContent className="space-y-3 pt-5"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></CardContent></Card>
      ) : (
        <>
          {/* Company */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Building2 className="h-4 w-4 text-primary" /> Company & sender</CardTitle>
              <CardDescription>Used in outgoing email signatures.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Labeled label="Company name">
                <Input value={settings.company_name || ''} onChange={(e) => set({ company_name: e.target.value })} placeholder="Acme Corp" />
              </Labeled>
              <Labeled label="Sender name (HR)">
                <Input value={settings.sender_name || ''} onChange={(e) => set({ sender_name: e.target.value })} placeholder="Dana from HR" />
              </Labeled>
            </CardContent>
          </Card>

          {/* SMTP */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Server className="h-4 w-4 text-primary" /> Email delivery (SMTP)</CardTitle>
              <CardDescription>Leave blank to use the server default / mock mode.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Labeled label="SMTP email">
                <Input type="email" value={settings.smtp_email || ''} onChange={(e) => set({ smtp_email: e.target.value })} placeholder="hr@company.com" />
              </Labeled>
              <Labeled label="SMTP password / app password">
                <Input type="password" value={settings.smtp_password || ''} onChange={(e) => set({ smtp_password: e.target.value })} placeholder="••••••••" />
              </Labeled>
            </CardContent>
          </Card>

          {/* Templates */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Mail className="h-4 w-4 text-primary" /> Email templates</CardTitle>
              <CardDescription>Customize the messages candidates receive.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex items-start gap-2 rounded-lg bg-primary-subtle p-3 text-sm text-primary">
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
                <p className="flex flex-wrap gap-1">
                  Variables:
                  {TOKENS.map((t) => (
                    <code key={t} className="rounded bg-primary/15 px-1.5 py-0.5 text-xs">{`{{${t}}}`}</code>
                  ))}
                </p>
              </div>
              <Labeled label="Interview invitation">
                <Textarea rows={7} className="font-mono text-xs" value={settings.invite_template || ''} onChange={(e) => set({ invite_template: e.target.value })} />
              </Labeled>
              <Labeled label="Shortlisted">
                <Textarea rows={5} className="font-mono text-xs" value={settings.shortlist_template || ''} onChange={(e) => set({ shortlist_template: e.target.value })} />
              </Labeled>
              <Labeled label="Rejection">
                <Textarea rows={5} className="font-mono text-xs" value={settings.reject_template || ''} onChange={(e) => set({ reject_template: e.target.value })} />
              </Labeled>
            </CardContent>
            <CardFooter className="justify-end">
              <Button loading={saving} leftIcon={<Save className="h-4 w-4" />} onClick={save}>Save changes</Button>
            </CardFooter>
          </Card>
        </>
      )}
    </div>
  );
}
