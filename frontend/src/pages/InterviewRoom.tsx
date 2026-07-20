import { useState, useEffect, useRef, type ComponentType, type RefObject } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Video, MonitorUp, Smartphone, VideoOff, ShieldAlert, ArrowLeft, ToggleLeft, ToggleRight } from 'lucide-react';
import Peer from 'peerjs';
import type { Candidate } from '../services/api';
import { getCandidate, getInterviewReport } from '../services/api';
import { acknowledgeStream } from '../services/peerConnection';

type StreamType = 'camera' | 'screen' | 'mobile';

export default function InterviewRoom() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [showFrontCam, setShowFrontCam] = useState(true);
  const [showScreen, setShowScreen] = useState(true);
  const [showMobileCam, setShowMobileCam] = useState(true);
  const [hasFrontCam, setHasFrontCam] = useState(false);
  const [hasScreen, setHasScreen] = useState(false);
  const [hasMobileCam, setHasMobileCam] = useState(false);
  const [alerts, setAlerts] = useState<{ time: string; msg: string }[]>([]);
  const [integrity, setIntegrity] = useState(100);
  const [connectionStatus, setConnectionStatus] = useState('Fetching candidate details…');

  const frontVideoRef = useRef<HTMLVideoElement>(null);
  const screenVideoRef = useRef<HTMLVideoElement>(null);
  const mobileVideoRef = useRef<HTMLVideoElement>(null);
  const peerRef = useRef<Peer | null>(null);

  useEffect(() => {
    if (id) {
      getCandidate(Number(id)).then((c) => {
        setCandidate(c);
        if (c.interview_token) setupPeerConnection(c.interview_token);
        else setConnectionStatus('Candidate has no active interview session.');
      });
    }
    return () => { if (peerRef.current) peerRef.current.destroy(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const poll = async () => {
      try {
        const r = await getInterviewReport(Number(id));
        if (typeof r.integrity_score === 'number') setIntegrity(r.integrity_score);
        if (Array.isArray(r.warnings) && r.warnings.length) {
          setAlerts(r.warnings.slice().reverse().map((w: any) => ({
            time: new Date(w.time).toLocaleTimeString(), msg: w.message,
          })));
        }
      } catch { /* interview may not have started yet */ }
    };
    poll();
    const t = setInterval(poll, 5000);
    return () => clearInterval(t);
  }, [id]);

  const setupPeerConnection = (token: string) => {
    const peer = new Peer(`hr-interview-${id}-${token}`);
    peerRef.current = peer;
    peer.on('open', () => setConnectionStatus('Listening for candidate streams…'));
    peer.on('call', (call) => {
      call.answer();
      const type = call.metadata?.type as StreamType | undefined;
      if (call.peer && type) acknowledgeStream(peer, call.peer, type);
      call.on('stream', (stream) => {
        if (type === 'camera') { if (frontVideoRef.current) frontVideoRef.current.srcObject = stream; setHasFrontCam(true); }
        else if (type === 'screen') { if (screenVideoRef.current) screenVideoRef.current.srcObject = stream; setHasScreen(true); }
        else if (type === 'mobile') { if (mobileVideoRef.current) mobileVideoRef.current.srcObject = stream; setHasMobileCam(true); }
      });
      call.on('close', () => {
        if (type === 'camera') setHasFrontCam(false);
        else if (type === 'screen') setHasScreen(false);
        else if (type === 'mobile') setHasMobileCam(false);
      });
    });
    peer.on('connection', (conn) => {
      conn.on('data', (data: any) => {
        if (data?.type === 'alert') setAlerts((prev) => [{ time: new Date().toLocaleTimeString(), msg: data.message }, ...prev]);
      });
    });
    peer.on('error', (err) => { console.error(err); setConnectionStatus('Error connecting to signaling server.'); });
  };

  const frontActive = showFrontCam && hasFrontCam;
  const screenActive = showScreen && hasScreen;
  const mobileActive = showMobileCam && hasMobileCam;
  const numPanels = [frontActive, screenActive, mobileActive].filter(Boolean).length;
  const anyConnected = hasFrontCam || hasScreen || hasMobileCam;

  const layoutClass = numPanels <= 1 ? 'grid-cols-1'
    : numPanels === 2 ? 'grid-cols-1 lg:grid-cols-2'
    : 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3';

  const integrityTone = integrity >= 80 ? 'text-success' : integrity >= 50 ? 'text-warning' : 'text-danger';
  const integrityBar = integrity >= 80 ? 'bg-success' : integrity >= 50 ? 'bg-warning' : 'bg-danger';

  const Panel = (title: string, Icon: ComponentType<{ className?: string }>, ref: RefObject<HTMLVideoElement | null>, hasStream: boolean, contain?: boolean) => (
    <motion.div layout initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.96 }} transition={{ duration: 0.35 }}
      className="relative flex min-h-[300px] flex-col overflow-hidden rounded-2xl border bg-surface-2 shadow-elev-2">
      <video ref={ref} autoPlay playsInline muted
        className={`absolute inset-0 z-0 h-full w-full ${contain ? 'object-contain' : 'object-cover'} transition-opacity duration-500 ${hasStream ? 'opacity-100' : 'opacity-0'}`} />
      {!hasStream && (
        <div className="absolute inset-0 z-0 flex flex-col items-center justify-center text-content-subtle">
          <Icon className="mb-3 h-14 w-14 opacity-50" />
          <p className="text-xs font-semibold uppercase tracking-widest">{title} offline</p>
        </div>
      )}
      <div className="absolute left-3 top-3 z-10 flex items-center gap-2 rounded-lg border bg-bg/70 px-2.5 py-1.5 backdrop-blur-md">
        <Icon className={`h-4 w-4 ${hasStream ? 'text-success' : 'text-danger'}`} />
        <span className="text-xs font-semibold text-content">{title}</span>
      </div>
    </motion.div>
  );

  const Toggle = (on: boolean, set: () => void, label: string) => (
    <button onClick={set} className="flex items-center gap-2">
      {on ? <ToggleRight className="h-6 w-6 text-primary" /> : <ToggleLeft className="h-6 w-6 text-content-subtle" />}
      <span className={`text-xs font-semibold uppercase tracking-wide ${on ? 'text-content' : 'text-content-subtle'}`}>{label}</span>
    </button>
  );

  return (
    <div className="relative flex h-screen w-full flex-col bg-bg text-content">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b bg-surface/80 px-6 py-3.5 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/candidates')} className="grid h-9 w-9 place-items-center rounded-lg border text-content-muted transition-colors hover:bg-surface-2 hover:text-content">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="flex items-center gap-2 font-bold text-content"><ShieldAlert className="h-5 w-5 text-primary" /> Live proctoring</h1>
            <p className="text-xs text-content-muted">{candidate ? `Monitoring ${candidate.name}` : connectionStatus}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3 rounded-xl border bg-surface-2 px-4 py-2">
            <div className="text-right">
              <div className="text-[10px] font-bold uppercase tracking-wide text-content-subtle">Integrity</div>
              <div className={`text-lg font-bold leading-none ${integrityTone}`}>{Math.round(integrity)}%</div>
            </div>
            <div className="h-1.5 w-14 overflow-hidden rounded-full bg-surface">
              <div className={`h-full transition-all duration-500 ${integrityBar}`} style={{ width: `${integrity}%` }} />
            </div>
          </div>
          <div className="flex items-center gap-5 rounded-xl border bg-surface-2 px-4 py-2">
            {Toggle(showFrontCam, () => setShowFrontCam(!showFrontCam), 'Front')}
            {Toggle(showScreen, () => setShowScreen(!showScreen), 'Screen')}
            {Toggle(showMobileCam, () => setShowMobileCam(!showMobileCam), 'Mobile')}
          </div>
        </div>
      </div>

      {/* Main */}
      <div className="relative flex flex-1 flex-col overflow-hidden p-6">
        {numPanels === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center text-content-subtle">
            <VideoOff className="mb-5 h-16 w-16 opacity-50" />
            <h2 className="text-xl font-bold uppercase tracking-widest">{anyConnected ? 'All streams hidden' : 'Waiting for candidate'}</h2>
            <p className="mt-2 text-sm text-content-muted">{anyConnected ? 'Use the controls above to enable feeds.' : connectionStatus}</p>
          </div>
        ) : (
          <motion.div layout className={`grid flex-1 auto-rows-fr gap-6 ${layoutClass}`}>
            <AnimatePresence mode="popLayout">
              {frontActive && <div key="front">{Panel('Laptop camera', Video, frontVideoRef, hasFrontCam)}</div>}
              {screenActive && <div key="screen">{Panel('Screen share', MonitorUp, screenVideoRef, hasScreen, true)}</div>}
              {mobileActive && <div key="mobile">{Panel('Mobile camera', Smartphone, mobileVideoRef, hasMobileCam)}</div>}
            </AnimatePresence>
          </motion.div>
        )}

        <AnimatePresence>
          {alerts.length > 0 && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
              className="absolute right-6 top-6 z-40 max-h-96 w-80 overflow-y-auto rounded-2xl border border-danger/30 bg-surface/95 p-4 shadow-elev-3 backdrop-blur-xl">
              <h3 className="mb-3 flex items-center gap-2 font-semibold text-danger"><ShieldAlert className="h-4 w-4" /> Security alerts</h3>
              <div className="space-y-2">
                {alerts.map((a, i) => (
                  <div key={i} className="rounded-lg border border-danger/20 bg-danger/5 p-2 text-xs">
                    <div className="mb-0.5 text-content-subtle">{a.time}</div>
                    <div className="text-content">{a.msg}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
