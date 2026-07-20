import type Peer from 'peerjs';

/**
 * Reliable stream delivery for candidate / mobile peers.
 *
 * Problem: the candidate often opens the interview link BEFORE the HR opens the
 * dashboard, so an immediate `peer.call(hrId)` fails with `peer-unavailable` and
 * the stream never connects. This deliverer retries every few seconds until the
 * HR side acknowledges receipt (via a data-channel `ack`), then stops.
 */
export interface StreamDeliverer {
  deliver: (type: string, stream: MediaStream) => void;
  stopAll: () => void;
}

export function createStreamDeliverer(peer: Peer, hrId: string, retryMs = 3000): StreamDeliverer {
  const acked = new Set<string>();
  const timers = new Map<string, ReturnType<typeof setInterval>>();

  // HR acknowledges each received stream over a data connection.
  peer.on('connection', (conn) => {
    conn.on('data', (data: any) => {
      if (data && data.type === 'ack' && data.streamType) {
        acked.add(data.streamType);
        const t = timers.get(data.streamType);
        if (t) { clearInterval(t); timers.delete(data.streamType); }
      }
    });
  });

  const attempt = (type: string, stream: MediaStream) => {
    if (acked.has(type)) return;
    try {
      peer.call(hrId, stream, { metadata: { type } });
    } catch {
      /* peer not ready yet; the interval will retry */
    }
  };

  return {
    deliver(type: string, stream: MediaStream) {
      acked.delete(type);
      attempt(type, stream);
      const existing = timers.get(type);
      if (existing) clearInterval(existing);
      timers.set(type, setInterval(() => attempt(type, stream), retryMs));
    },
    stopAll() {
      timers.forEach((t) => clearInterval(t));
      timers.clear();
    },
  };
}

/** HR side: acknowledge a received media call so the sender stops retrying. */
export function acknowledgeStream(peer: Peer, callerId: string, streamType: string) {
  try {
    const conn = peer.connect(callerId);
    conn.on('open', () => {
      conn.send({ type: 'ack', streamType });
      setTimeout(() => conn.close(), 800);
    });
  } catch {
    /* best-effort ack */
  }
}
