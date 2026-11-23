'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

type Note = { note: string; time: number; duration: number; velocity: number };
type Region = { id: string; startTime: number; duration: number; notes: Note[]; audioUrl?: string };
type FX = { id: string; type: 'bitcrusher'; bits: number; reduction: number; bypass: boolean };
type Track = { id: string; name: string; type: 'audio' | 'midi'; volume: number; pan: number; isMuted: boolean; isSoloed: boolean; pluginChain: FX[]; regions: Region[] };
type StudioState = { schemaVersion: 'sonic.studio/1'; revision: number; project: { id: string; bpm: number; sampleRate: number; timeSignature: string }; tracks: Track[] };
type Log = { by: 'You' | 'Sonic' | 'System'; text: string };
const PXS = 75, LANE = 96, SECONDS = 12;

function pitchToHz(note: string): number {
  const m = /^([A-G])([#b]?)([0-8])$/.exec(note);
  if (!m) return 0;
  const pitches: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  const midi = (Number(m[3]) + 1) * 12 + pitches[m[1]] + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0);
  return 440 * Math.pow(2, (midi - 69) / 12);
}

function draw(canvas: HTMLCanvasElement, studio: StudioState | null, playhead: number) {
  const c = canvas.getContext('2d');
  if (!c) return;
  const ratio = window.devicePixelRatio || 1;
  const w = PXS * SECONDS, h = Math.max(200, 32 + (studio?.tracks.length || 2) * LANE);
  if (canvas.width !== Math.round(w * ratio) || canvas.height !== Math.round(h * ratio)) {
    canvas.width = Math.round(w * ratio); canvas.height = Math.round(h * ratio);
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
  }
  c.setTransform(ratio, 0, 0, ratio, 0, 0);
  c.fillStyle = '#111827'; c.fillRect(0, 0, w, h);
  c.font = '12px Arial, sans-serif';
  const secondsPerBeat = 60 / (studio?.project.bpm || 128);
  for (let beat = 0; beat * secondsPerBeat < SECONDS; beat++) {
    const x = beat * secondsPerBeat * PXS;
    c.strokeStyle = beat % 4 === 0 ? '#506079' : '#293549';
    c.lineWidth = beat % 4 === 0 ? 1.5 : 0.7;
    c.beginPath(); c.moveTo(x, 24); c.lineTo(x, h); c.stroke();
    if (beat % 4 === 0) { c.fillStyle = '#afbdd7'; c.fillText(String(1 + beat / 4), x + 4, 17); }
  }
  studio?.tracks.forEach((t, lane) => {
    const y = 30 + lane * LANE;
    c.fillStyle = lane % 2 ? '#202b40' : '#182236'; c.fillRect(0, y, w, LANE - 2);
    t.regions.forEach(r => {
      const x = r.startTime * PXS, width = r.duration * PXS;
      if (x >= w || x + width < 0) return;
      c.fillStyle = t.isMuted ? '#5b6270' : t.type === 'midi' ? '#7954b8' : '#2876c2';
      c.fillRect(x + 1, y + 8, Math.max(1, width - 2), LANE - 20);
      c.strokeStyle = '#c5b5ec'; c.strokeRect(x + 1, y + 8, Math.max(1, width - 2), LANE - 20);
      c.fillStyle = 'white'; c.fillText(t.name + ' • ' + r.id, x + 8, y + 26, Math.max(0, width - 16));
      (r.notes || []).forEach(n => {
        c.fillStyle = '#e1cdff';
        c.fillRect(x + n.time * PXS, y + 38 + (n.note.charCodeAt(0) % 5) * 7, Math.max(2, n.duration * PXS - 2), 4);
      });
    });
  });
  c.strokeStyle = '#ff778b'; c.lineWidth = 2;
  c.beginPath(); c.moveTo(playhead * PXS, 0); c.lineTo(playhead * PXS, h); c.stroke();
}

export default function SonicOpenStudio() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const socket = useRef<WebSocket | null>(null);
  const latest = useRef<StudioState | null>(null);
  const audio = useRef<AudioContext | null>(null);
  const activeVoices = useRef<OscillatorNode[]>([]);
  const channels = useRef<Map<string, { gain: GainNode; pan: StereoPannerNode }>>(new Map());
  const frame = useRef(0), clockStart = useRef(0), seconds = useRef(0), playingRef = useRef(false);
  const [studio, setStudio] = useState<StudioState | null>(null);
  const [key, setKey] = useState(''), [connection, setConnection] = useState('Offline');
  const [text, setText] = useState('make drums quieter and pan left');
  const [busy, setBusy] = useState(false), [playing, setPlaying] = useState(false);
  const [log, setLog] = useState<Log[]>([{ by: 'System', text: 'Experimental local-only studio. No source DAW session is changed.' }]);
  const append = useCallback((by: Log['by'], value: string) => setLog(old => [...old.slice(-30), { by, text: value }]), []);

  const accept = useCallback((next: StudioState) => {
    if (!next || next.schemaVersion !== 'sonic.studio/1' || !Number.isInteger(next.revision) || !Array.isArray(next.tracks)) {
      append('System', 'Invalid studio state rejected'); return;
    }
    latest.current = next; setStudio(next);
    const ctx = audio.current;
    if (ctx) for (const track of next.tracks) {
      const channel = channels.current.get(track.id);
      if (channel) {
        channel.gain.gain.setTargetAtTime(track.isMuted ? 0 : track.volume, ctx.currentTime, 0.02);
        channel.pan.pan.setTargetAtTime(track.pan, ctx.currentTime, 0.02);
      }
    }
    if (canvas.current) draw(canvas.current, next, seconds.current);
  }, [append]);

  const connect = () => {
    socket.current?.close();
    if (!key.trim()) { append('System', 'Enter your local Sonic token'); return; }
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/studio');
    socket.current = ws; setConnection('Connecting');
    ws.onopen = () => ws.send(JSON.stringify({ type: 'AUTH', token: key.trim() }));
    ws.onmessage = event => {
      let data: any;
      try { data = JSON.parse(event.data); } catch { append('System', 'Malformed response'); return; }
      if (data.type === 'SESSION_STATE') { accept(data.studio_state); setConnection('Connected'); append('System', 'Authorized synthetic session loaded'); }
      if (data.type === 'STATUS_UPDATE') setConnection('Processing');
      if (data.type === 'STATE_MUTATION_SUCCESS') {
        accept(data.studio_state); append('Sonic', data.message || 'State updated'); setConnection('Connected'); setBusy(false);
      }
      if (data.type === 'REVISION_CONFLICT') {
        accept(data.studio_state); append('System', 'Session changed; retry against the new revision'); setConnection('Connected'); setBusy(false);
      }
      if (data.type === 'ENGINE_ERROR') {
        append('System', Array.isArray(data.errors) ? data.errors.join('; ') : 'Command rejected');
        setConnection('Connected'); setBusy(false);
      }
    };
    ws.onerror = () => append('System', 'Local Sonic API is unreachable on port 8000');
    ws.onclose = () => { if (socket.current === ws) { setConnection('Offline'); setBusy(false); } };
  };

  const send = () => {
    if (!latest.current || connection !== 'Connected' || busy || !text.trim() || socket.current?.readyState !== WebSocket.OPEN) return;
    socket.current.send(JSON.stringify({
      type: 'COMMAND', request_id: crypto.randomUUID(), prompt: text.trim(), expected_revision: latest.current.revision
    }));
    append('You', text.trim()); setBusy(true); setText('');
  };

  const stop = useCallback(() => {
    playingRef.current = false; setPlaying(false); cancelAnimationFrame(frame.current);
    activeVoices.current.forEach(voice => { try { voice.stop(); } catch { /* ended */ } voice.disconnect(); });
    activeVoices.current = [];
    channels.current.forEach(channel => { channel.gain.disconnect(); channel.pan.disconnect(); });
    channels.current.clear(); seconds.current = 0;
    if (canvas.current) draw(canvas.current, latest.current, 0);
  }, []);

  const play = async () => {
    if (!latest.current) return;
    stop();
    const ctx = audio.current || new AudioContext();
    audio.current = ctx;
    await ctx.resume();
    const start = ctx.currentTime + 0.08;
    clockStart.current = start;
    const soloed = latest.current.tracks.some(t => t.isSoloed);
    for (const track of latest.current.tracks) {
      const gain = ctx.createGain();
      gain.gain.value = track.isMuted || (soloed && !track.isSoloed) ? 0 : track.volume;
      const pan = ctx.createStereoPanner(); pan.pan.value = track.pan;
      gain.connect(pan).connect(ctx.destination);
      channels.current.set(track.id, { gain, pan });
      if (track.type !== 'midi') continue;
      track.regions.forEach(region => (region.notes || []).forEach(note => {
        const hz = pitchToHz(note.note); if (!hz) return;
        const at = start + region.startTime + note.time;
        const duration = Math.max(0.03, note.duration);
        const voice = ctx.createOscillator(), envelope = ctx.createGain();
        voice.type = track.id === 'drums' ? 'triangle' : 'sine';
        voice.frequency.value = hz;
        envelope.gain.setValueAtTime(0.0001, at);
        envelope.gain.exponentialRampToValueAtTime(Math.max(0.001, note.velocity * 0.2), at + 0.01);
        envelope.gain.exponentialRampToValueAtTime(0.0001, at + duration);
        voice.connect(envelope).connect(gain);
        voice.start(at); voice.stop(at + duration + 0.02);
        activeVoices.current.push(voice);
      }));
    }
    playingRef.current = true; setPlaying(true);
    const animation = () => {
      if (!playingRef.current) return;
      seconds.current = Math.max(0, ctx.currentTime - clockStart.current);
      if (canvas.current) draw(canvas.current, latest.current, seconds.current);
      if (seconds.current >= SECONDS) { stop(); return; }
      frame.current = requestAnimationFrame(animation);
    };
    frame.current = requestAnimationFrame(animation);
  };

  useEffect(() => { if (canvas.current) draw(canvas.current, studio, seconds.current); }, [studio]);
  useEffect(() => () => {
    socket.current?.close(); playingRef.current = false; cancelAnimationFrame(frame.current);
    activeVoices.current.forEach(v => { try { v.stop(); } catch { /* ended */ } });
    void audio.current?.close();
  }, []);

  const button: React.CSSProperties = { background: '#3664bc', color: 'white', border: 0, borderRadius: 8, padding: '10px 15px', cursor: 'pointer' };
  return <main style={{ maxWidth: 1200, margin: 'auto', padding: 24, color: '#e7ecfa', fontFamily: 'system-ui' }}>
    <header><h1 style={{ marginBottom: 4 }}>Sonic · Open Studio</h1><p style={{ color: '#a4b4cf' }}>Browser timeline / WebSocket commands / local synthetic MIDI audition</p></header>
    <p aria-live="polite"><b>{connection}</b> · Session revision {studio?.revision ?? '—'}</p>
    <section style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 22 }}>
      <label>Local Sonic token <input type="password" autoComplete="off" value={key} onChange={e => setKey(e.target.value)} style={{ padding: 9, marginLeft: 8 }} /></label>
      <button style={button} onClick={connect}>Connect</button>
      <button style={button} disabled={!studio} onClick={playing ? stop : play}>{playing ? '■ Stop' : '▶ Audition MIDI'}</button>
    </section>
    <section style={{ background: '#121b2c', border: '1px solid #3e4f67', borderRadius: 12, padding: 15, marginBottom: 20 }}>
      <h2>Studio timeline</h2>
      <div style={{ overflowX: 'auto' }}><canvas ref={canvas} role="img" aria-label="Studio tracks and MIDI regions with synchronized playhead" /></div>
      {studio?.tracks.map(t => <div key={t.id} style={{ borderTop: '1px solid #32425b', padding: 12, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <strong>{t.name}</strong><span>{t.isMuted ? 'Muted' : 'Active'}</span><span>Level {t.volume.toFixed(2)}</span>
        <span>Pan {t.pan.toFixed(2)}</span><span>Bitcrusher {t.pluginChain[0] ? String(t.pluginChain[0].bits) + ' bits (settings only)' : 'none'}</span>
      </div>)}
      <small>Audio files and WASM DSP are not connected. Region edits made during playback take effect on the next audition.</small>
    </section>
    <section style={{ background: '#121b2c', border: '1px solid #3e4f67', borderRadius: 12, padding: 15 }}>
      <h2>Studio command chat</h2>
      <div aria-live="polite" style={{ maxHeight: 260, overflowY: 'auto', marginBottom: 16 }}>
        {log.map((line, i) => <p key={i}><b>{line.by}:</b> {line.text}</p>)}
      </div>
      <form onSubmit={e => { e.preventDefault(); send(); }} style={{ display: 'flex', gap: 8 }}>
        <input aria-label="Studio command" value={text} onChange={e => setText(e.target.value)} maxLength={500} style={{ flex: 1, minWidth: 0, padding: 12 }} />
        <button style={button} disabled={connection !== 'Connected' || busy || !text.trim()} type="submit">{busy ? 'Checking…' : 'Apply'}</button>
      </form>
      <p style={{ color: '#a4b4cf' }}>Try “mute drums”, “crush drums hard”, “make drums quieter and pan left”, or “move bass 2 seconds later”. This prototype uses deterministic commands, not an LLM.</p>
    </section>
  </main>;
}
