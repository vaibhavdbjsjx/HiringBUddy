import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { ShieldAlert, Video, MonitorUp, CheckCircle2, AlertTriangle, Play, Smartphone } from 'lucide-react';
import Peer from 'peerjs';
import { QRCodeSVG } from 'qrcode.react';
import { createStreamDeliverer, type StreamDeliverer } from '../services/peerConnection';
import { verifyInterviewToken, getInterviewQuestions, startInterview, recordProctoring, type InterviewQuestion } from '../services/api';
import { Button, Badge } from '../components/ui';

export default function CandidateInterview() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [hasJoined, setHasJoined] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [screenEnabled, setScreenEnabled] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const screenRef = useRef<HTMLVideoElement>(null);
  const peerRef = useRef<Peer | null>(null);
  const delivererRef = useRef<StreamDeliverer | null>(null);

  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [integrity, setIntegrity] = useState(100);
  const [connectionStatus, setConnectionStatus] = useState<string>('Initializing secure connection…');

  const mobileJoinUrl = `${window.location.origin}/mobile-cam/${id}?token=${token}`;

  useEffect(() => {
    if (!token || !id) {
      setTokenValid(false);
      setConnectionStatus('Invalid secure token.');
      return;
    }
    verifyInterviewToken(Number(id), token)
      .then((r) => setTokenValid(r.valid))
      .catch(() => { setTokenValid(false); setConnectionStatus('This interview link is invalid or has expired.'); });
  }, [token, id]);

  const reportProctoring = (type: string, message: string, severity: 'low' | 'medium' | 'high') => {
    if (id) recordProctoring(Number(id), type, message, severity).then((r) => setIntegrity(r.integrity_score)).catch(() => {});
    if (peerRef.current) {
      try {
        const conn = peerRef.current.connect(`hr-interview-${id}-${token}`);
        conn.on('open', () => { conn.send({ type: 'alert', message }); setTimeout(() => conn.close(), 1000); });
      } catch { /* best-effort */ }
    }
  };

  const requestFullscreen = async () => {
    try {
      if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
      else if ((document.documentElement as any).webkitRequestFullscreen) await (document.documentElement as any).webkitRequestFullscreen();
    } catch (e) { console.log('Fullscreen request failed', e); }
    setHasJoined(true);
    if (id) {
      startInterview(Number(id)).catch(() => {});
      getInterviewQuestions(Number(id)).then((r) => setQuestions(r.questions)).catch(() => {});
    }
    initializeStreams();
  };

  const initializeStreams = async () => {
    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraEnabled(true);
      }
    } catch (err) {
      console.error('Error accessing media devices.', err);
      reportProctoring('camera_disabled', 'Camera/microphone access was denied.', 'high');
    }
    setupPeerConnection();
  };

  const startScreenShare = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      if (screenRef.current) screenRef.current.srcObject = stream;
      setScreenEnabled(true);
      stream.getVideoTracks()[0]?.addEventListener('ended', () => {
        setScreenEnabled(false);
        reportProctoring('screen_share_stopped', 'Screen share was stopped.', 'medium');
      });
      delivererRef.current?.deliver('screen', stream);
    } catch (err) { console.error('Error accessing screen share.', err); }
  };

  const setupPeerConnection = () => {
    const peer = new Peer(`candidate-${id}-${token}`);
    peerRef.current = peer;
    peer.on('open', () => {
      setConnectionStatus('Connected. Streaming to interviewer…');
      const deliverer = createStreamDeliverer(peer, `hr-interview-${id}-${token}`);
      delivererRef.current = deliverer;
      if (videoRef.current?.srcObject) deliverer.deliver('camera', videoRef.current.srcObject as MediaStream);
      if (screenRef.current?.srcObject) deliverer.deliver('screen', screenRef.current.srcObject as MediaStream);
    });
    peer.on('error', (err) => {
      console.error('PeerJS error:', err);
      if ((err as any).type !== 'peer-unavailable') setConnectionStatus(`Connection error: ${err.message}`);
    });
  };

  useEffect(() => {
    if (!hasJoined) return;
    const onVisibility = () => { if (document.hidden) reportProctoring('tab_switch', 'Tab switch detected — candidate left the interview window.', 'medium'); };
    const onFullscreen = () => { if (!document.fullscreenElement) reportProctoring('fullscreen_exit', 'Exited fullscreen — candidate may be opening other applications.', 'medium'); };
    const onBlur = () => reportProctoring('window_blur', 'Interview window lost focus.', 'low');
    const onCopy = () => reportProctoring('copy_detected', 'Copy action detected during interview.', 'low');
    const onPaste = () => reportProctoring('paste_detected', 'Paste action detected during interview.', 'low');
    document.addEventListener('visibilitychange', onVisibility);
    document.addEventListener('fullscreenchange', onFullscreen);
    window.addEventListener('blur', onBlur);
    document.addEventListener('copy', onCopy);
    document.addEventListener('paste', onPaste);
    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      document.removeEventListener('fullscreenchange', onFullscreen);
      window.removeEventListener('blur', onBlur);
      document.removeEventListener('copy', onCopy);
      document.removeEventListener('paste', onPaste);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasJoined, id, token]);

  useEffect(() => () => { delivererRef.current?.stopAll(); peerRef.current?.destroy(); }, []);

  const integrityTone = integrity >= 80 ? 'text-success' : integrity >= 50 ? 'text-warning' : 'text-danger';
  const integrityBar = integrity >= 80 ? 'bg-success' : integrity >= 50 ? 'bg-warning' : 'bg-danger';

  if (tokenValid === false) {
    return (
      <div className="grid h-screen w-full place-items-center bg-bg p-6 text-center text-content">
        <div className="max-w-md rounded-2xl border border-danger/20 bg-surface p-10 shadow-elev-2">
          <div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-danger/10"><AlertTriangle className="h-8 w-8 text-danger" /></div>
          <h1 className="mb-2 text-2xl font-bold">Invalid interview link</h1>
          <p className="text-sm text-content-muted">{connectionStatus}</p>
        </div>
      </div>
    );
  }

  if (!hasJoined) {
    return (
      <div className="relative grid h-screen w-full place-items-center overflow-hidden bg-bg p-6 text-center text-content">
        <div className="pointer-events-none absolute inset-0" style={{ background: 'radial-gradient(45rem 30rem at 50% 0%, rgb(var(--primary) / 0.12), transparent 70%)' }} />
        <div className="relative z-10 max-w-xl rounded-2xl border bg-surface p-10 shadow-elev-3">
          <div className="mx-auto mb-6 grid h-20 w-20 place-items-center rounded-2xl bg-primary/10 shadow-glow-sm"><ShieldAlert className="h-10 w-10 text-primary" /></div>
          <h1 className="mb-3 text-3xl font-bold">Secure AI interview</h1>
          <p className="mb-8 leading-relaxed text-content-muted">
            You're about to enter a proctored interview. Your camera, microphone, and screen will be monitored for the duration.
          </p>
          <div className="mb-8 space-y-3 text-left text-sm">
            <div className="flex items-center gap-3 rounded-xl border bg-surface-2 p-3"><CheckCircle2 className="h-5 w-5 text-success" /> Ensure you're in a quiet, well-lit room.</div>
            <div className="flex items-center gap-3 rounded-xl border bg-surface-2 p-3"><AlertTriangle className="h-5 w-5 text-warning" /> Tab switching will be recorded as malpractice.</div>
          </div>
          <Button size="lg" className="w-full" leftIcon={<Play className="h-5 w-5" />} onClick={requestFullscreen}>
            Enter fullscreen & join
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full flex-col gap-6 bg-bg p-6 text-content xl:flex-row">
      {/* Streams */}
      <div className="flex flex-1 flex-col gap-6">
        <div className="flex flex-1 flex-col gap-4 rounded-2xl border bg-surface p-4 md:flex-row">
          {/* Camera */}
          <div className="relative flex flex-1 flex-col overflow-hidden rounded-xl border bg-surface-2">
            <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
            <div className="absolute left-3 top-3 flex items-center gap-2 rounded-lg border bg-bg/70 px-2.5 py-1.5 backdrop-blur-md">
              <Video className={`h-4 w-4 ${cameraEnabled ? 'text-success' : 'text-danger'}`} /><span className="text-xs font-semibold">Front camera</span>
            </div>
          </div>
          {/* Screen */}
          <div className="relative flex flex-1 flex-col items-center justify-center overflow-hidden rounded-xl border bg-surface-2">
            {screenEnabled ? (
              <video ref={screenRef} autoPlay playsInline muted className="h-full w-full object-contain" />
            ) : (
              <div className="p-6 text-center">
                <MonitorUp className="mx-auto mb-4 h-12 w-12 text-info/60" />
                <h3 className="mb-2 font-semibold">Screen share required</h3>
                <p className="mx-auto mb-4 max-w-[200px] text-xs text-content-muted">Please share your entire screen for coding tasks.</p>
                <Button variant="secondary" size="sm" onClick={startScreenShare}>Start screen share</Button>
              </div>
            )}
            <div className="absolute left-3 top-3 flex items-center gap-2 rounded-lg border bg-bg/70 px-2.5 py-1.5 backdrop-blur-md">
              <MonitorUp className={`h-4 w-4 ${screenEnabled ? 'text-info' : 'text-content-subtle'}`} /><span className="text-xs font-semibold">Screen share</span>
            </div>
          </div>
        </div>

        {/* Mobile QR */}
        <div className="flex items-center justify-between gap-6 rounded-2xl border border-primary/20 bg-primary-subtle p-6">
          <div className="flex items-start gap-4">
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/10"><Smartphone className="h-7 w-7 text-primary" /></div>
            <div>
              <h3 className="mb-1 font-bold text-content">Secondary mobile camera</h3>
              <p className="max-w-md text-sm text-content-muted">Scan the QR code with your phone to add a second angle — required to prevent malpractice.</p>
            </div>
          </div>
          <div className="grid h-28 w-28 shrink-0 place-items-center rounded-xl bg-white p-2"><QRCodeSVG value={mobileJoinUrl} size={100} level="M" /></div>
        </div>
      </div>

      {/* AI interviewer panel */}
      <div className="flex w-full flex-col overflow-hidden rounded-2xl border bg-surface shadow-elev-2 xl:w-[380px]">
        <div className="border-b p-5">
          <h2 className="flex items-center gap-2.5 font-bold text-content">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-primary" /> AI interviewer
          </h2>
          <p className="mt-1 text-xs text-content-muted">{connectionStatus}</p>
        </div>
        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          <div className="rounded-xl border bg-surface-2 p-4">
            <div className="mb-1.5 flex justify-between text-[10px] font-bold uppercase tracking-wide">
              <span className="text-content-subtle">Integrity score</span><span className={integrityTone}>{integrity}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-surface"><div className={`h-full transition-all duration-500 ${integrityBar}`} style={{ width: `${integrity}%` }} /></div>
          </div>

          {questions.length > 0 ? (
            <div className="rounded-xl border border-primary/20 bg-primary-subtle p-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wide text-primary">Question {currentQ + 1} of {questions.length}</span>
                <Badge>{questions[currentQ].difficulty}</Badge>
              </div>
              <p className="text-sm leading-relaxed text-content">{questions[currentQ].question}</p>
            </div>
          ) : (
            <p className="text-xs italic text-content-subtle">Preparing your personalized questions…</p>
          )}

          {questions.length > 0 && (
            <Button variant="secondary" className="w-full" disabled={currentQ >= questions.length - 1}
              onClick={() => setCurrentQ((q) => Math.min(q + 1, questions.length - 1))}>
              {currentQ >= questions.length - 1 ? 'Final question' : 'Next question'}
            </Button>
          )}

          <div className="flex items-center gap-2 text-xs italic text-content-subtle">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-info" /> Recording your response…
          </div>
        </div>
      </div>
    </div>
  );
}
