import { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, User, Cpu } from 'lucide-react';
import { Card, Button, Input, Badge } from '../components/ui';
import { copilotQuery, type CopilotResult } from '../services/api';

interface Msg {
  role: 'user' | 'assistant';
  text: string;
  candidates?: CopilotResult['candidates'];
}

const SUGGESTIONS = [
  'Show me the top 5 candidates',
  'Find candidates who know React',
  "Who's below 70%?",
  'How many candidates do I have?',
];

export default function Copilot() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'assistant', text: "Hi! I'm your HR copilot. Ask me to find, rank, or compare candidates in plain English." },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || loading) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text: q }]);
    setLoading(true);
    try {
      const res = await copilotQuery(q);
      setMessages((m) => [...m, { role: 'assistant', text: res.answer, candidates: res.candidates }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', text: 'Sorry, I hit an error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col">
      <div className="mb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-content"><Sparkles className="h-6 w-6 text-primary" /> HR Copilot</h1>
        <p className="mt-1 text-sm text-content-muted">Ask about your candidates in plain English.</p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${m.role === 'user' ? 'bg-surface-3 text-content' : 'bg-primary text-primary-fg'}`}>
                {m.role === 'user' ? <User className="h-4 w-4" /> : <Cpu className="h-4 w-4" />}
              </div>
              <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${m.role === 'user' ? 'bg-primary text-primary-fg' : 'border bg-surface-2 text-content'}`}>
                <p className="leading-relaxed">{m.text}</p>
                {m.candidates && m.candidates.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.candidates.map((c) => (
                      <Badge key={c.id} variant="primary">{c.name}{c.overall_score != null ? ` · ${Math.round(c.overall_score)}%` : ''}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-fg"><Cpu className="h-4 w-4" /></div>
              <div className="flex items-center gap-1 rounded-xl border bg-surface-2 px-4 py-3">
                {[0, 1, 2].map((i) => <span key={i} className="h-1.5 w-1.5 animate-pulse rounded-full bg-content-subtle" style={{ animationDelay: `${i * 0.15}s` }} />)}
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {messages.length <= 1 && (
          <div className="flex flex-wrap gap-2 px-5 pb-3">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} className="rounded-full border bg-surface-2 px-3 py-1.5 text-xs text-content-muted transition-colors hover:bg-surface-3 hover:text-content">{s}</button>
            ))}
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2 border-t p-3">
          <Input placeholder="Ask your copilot…" value={input} onChange={(e) => setInput(e.target.value)} />
          <Button type="submit" size="icon" disabled={!input.trim() || loading}><Send className="h-4 w-4" /></Button>
        </form>
      </Card>
    </div>
  );
}
