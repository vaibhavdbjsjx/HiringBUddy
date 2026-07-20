import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Smartphone } from 'lucide-react';
import Peer from 'peerjs';
import { createStreamDeliverer } from '../services/peerConnection';
import { Button } from '../components/ui';

export default function MobileCamera() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [hasJoined, setHasJoined] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const peerRef = useRef<Peer | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('Initializing…');

  useEffect(() => {
    if (!token) setConnectionStatus('Invalid secure token.');
  }, [token]);

  const requestCamera = async () => {
    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
        if (videoRef.current) videoRef.current.srcObject = stream;
        setHasJoined(true);
        setupPeerConnection(stream);
      }
    } catch (err) {
      console.error('Error accessing mobile camera.', err);
      setConnectionStatus('Failed to access camera.');
    }
  };

  const setupPeerConnection = (stream: MediaStream) => {
    const peer = new Peer(`mobile-${id}-${token}`);
    peerRef.current = peer;
    peer.on('open', () => {
      setConnectionStatus('Connected. Streaming to dashboard…');
      const deliverer = createStreamDeliverer(peer, `hr-interview-${id}-${token}`);
      deliverer.deliver('mobile', stream);
    });
    peer.on('error', (err) => { console.error('PeerJS error:', err); setConnectionStatus(`Connection error: ${err.message}`); });
  };

  if (!hasJoined) {
    return (
      <div className="grid h-screen w-full place-items-center bg-bg p-6 text-center text-content">
        <div className="max-w-sm">
          <div className="mx-auto mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-primary/10"><Smartphone className="h-8 w-8 text-primary" /></div>
          <h1 className="mb-3 text-2xl font-bold">Secondary camera setup</h1>
          <p className="mb-8 text-sm text-content-muted">This device becomes a second monitoring angle for your interview. Position it to show your workspace.</p>
          <Button size="lg" className="w-full" onClick={requestCamera}>Enable camera</Button>
          <p className="mt-4 text-xs text-content-subtle">{connectionStatus}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-screen w-full flex-col bg-black">
      <video ref={videoRef} autoPlay playsInline muted className="h-full w-full flex-1 object-cover" />
      <div className="absolute inset-x-4 top-4 flex items-center justify-between rounded-2xl border border-white/10 bg-black/60 p-4 text-white backdrop-blur-md">
        <div className="flex items-center gap-2"><span className="h-2 w-2 animate-pulse rounded-full bg-danger" /><span className="text-sm font-semibold">LIVE</span></div>
        <div className="text-xs text-white/60">{connectionStatus}</div>
      </div>
    </div>
  );
}
