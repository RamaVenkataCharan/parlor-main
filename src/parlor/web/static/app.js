const $ = id => document.getElementById(id);
const video = $('video'), cameraToggle = $('cameraToggle');
const messagesDiv = $('messages'), statusEl = $('status');
const stateDot = $('stateDot'), stateText = $('stateText');
const viewportWrap = $('viewportWrap');
const waveformCanvas = $('waveform');
const waveformCtx = waveformCanvas.getContext('2d');

const diagBtn = $('diagBtn'), diagPanel = $('diagPanel'), diagClose = $('diagClose');
const diagMic = $('diagMic'), diagVad = $('diagVad'), diagWs = $('diagWs'), diagLlm = $('diagLlm');
const toastContainer = $('toastContainer');

let ws, mediaStream, myvad;
let diagnosticsBound = false;
let cameraEnabled = true;
let audioCtx;
let state = 'loading';
let ignoreIncomingAudio = false;

// Streaming audio playback state
let streamSampleRate = 24000;
let streamNextTime = 0;         // When to schedule next chunk
let streamSources = [];         // Active AudioBufferSourceNodes

// Per-state [glow, glow-dim]. Resolved values, not nested var(): setState
// writes them into CSS custom properties and the waveform paints with them.
const STATE_COLORS = {
  listening: ['#4ade80', 'rgba(74,222,128,0.12)'],
  processing: ['#f59e0b', 'rgba(245,158,11,0.12)'],
  speaking: ['#818cf8', 'rgba(129,140,248,0.12)'],
  loading: ['#3a3d46', 'rgba(58,61,70,0.12)'],
  muted: ['#fbbf24', 'rgba(251,191,36,0.12)'],
};

// ── Toasts & Diagnostics Panel ──
function showToast(message, type = 'warning', durationMs = 6000) {
  if (!toastContainer) return;
  const toast = document.createElement('div');
  toast.className = `toast-banner ${type}`;
  toast.innerHTML = `<span>${message}</span><button class="toast-close">✕</button>`;
  const closeBtn = toast.querySelector('.toast-close');
  if (closeBtn) closeBtn.onclick = () => toast.remove();
  toastContainer.appendChild(toast);
  if (durationMs > 0) {
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, durationMs);
  }
}

function updateDiagnostics() {
  if (!diagMic) return;
  // Mic
  if (!mediaStream || !mediaStream.getAudioTracks().length) {
    diagMic.className = 'diag-val error'; diagMic.textContent = '⚫ No device';
  } else {
    const track = mediaStream.getAudioTracks()[0];
    const label = track.label ? ` (${track.label.split(' ')[0]})` : '';
    if (track.readyState === 'ended') {
      diagMic.className = 'diag-val error'; diagMic.textContent = `🔴 Disconnected${label}`;
    } else if (track.muted || !track.enabled) {
      diagMic.className = 'diag-val warning'; diagMic.textContent = `🔴 Muted${label}`;
    } else {
      diagMic.className = 'diag-val ok'; diagMic.textContent = `🟢 Live${label}`;
    }
  }
  // VAD
  if (myvad) {
    diagVad.className = 'diag-val ok'; diagVad.textContent = '🟢 Active';
  } else {
    diagVad.className = 'diag-val warning'; diagVad.textContent = '🔴 Not ready';
  }
  // WebSocket
  if (wsOpen()) {
    diagWs.className = 'diag-val ok'; diagWs.textContent = '🟢 Connected';
  } else {
    diagWs.className = 'diag-val error'; diagWs.textContent = '🔴 Disconnected';
  }
  // Server / LLM
  if (state === 'processing') {
    diagLlm.className = 'diag-val warning'; diagLlm.textContent = '🟡 Thinking...';
  } else if (state === 'speaking') {
    diagLlm.className = 'diag-val ok'; diagLlm.textContent = '🟢 Responding';
  } else {
    diagLlm.className = 'diag-val ok'; diagLlm.textContent = '🟢 Idle';
  }
}

function toggleDiagnostics(forceOpen) {
  if (!diagBtn || !diagPanel) return;
  const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : diagPanel.hidden;
  diagPanel.hidden = !shouldOpen;
  diagBtn.setAttribute('aria-expanded', String(shouldOpen));
  if (shouldOpen) updateDiagnostics();
}

function bindDiagnosticsControls() {
  if (diagnosticsBound) return;
  if (diagBtn && diagPanel) {
    diagBtn.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleDiagnostics();
    });
    if (diagClose) {
      diagClose.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleDiagnostics(false);
      });
    }
  }
  diagnosticsBound = true;
}

// ── Waveform Visualizer ──
let analyser, micSource;
const BAR_COUNT = 40;
const BAR_GAP = 3;
let waveformRAF;
let ambientPhase = 0;

function initWaveformCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const rect = waveformCanvas.getBoundingClientRect();
  waveformCanvas.width = rect.width * dpr;
  waveformCanvas.height = rect.height * dpr;
  waveformCtx.scale(dpr, dpr);
}

function drawWaveform() {
  const { width: w, height: h } = waveformCanvas.getBoundingClientRect();
  waveformCtx.clearRect(0, 0, w, h);

  const barWidth = (w - (BAR_COUNT - 1) * BAR_GAP) / BAR_COUNT;
  waveformCtx.fillStyle = (STATE_COLORS[state] || STATE_COLORS.loading)[0];

  let dataArray = null;
  if (analyser) {
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
  }

  for (let i = 0; i < BAR_COUNT; i++) {
    let amplitude;
    if (dataArray) {
      // Map bar index to frequency bin
      const binIndex = Math.floor((i / BAR_COUNT) * dataArray.length * 0.6);
      amplitude = dataArray[binIndex] / 255;
    }

    // If no real audio data or very quiet, use ambient drift
    if (!dataArray || amplitude < 0.02) {
      ambientPhase += 0.0001;
      const drift = Math.sin(ambientPhase * 3 + i * 0.4) * 0.5 + 0.5;
      amplitude = 0.03 + drift * 0.04;
    }

    const barH = Math.max(2, amplitude * (h - 4));
    const x = i * (barWidth + BAR_GAP);
    const y = (h - barH) / 2;

    waveformCtx.globalAlpha = 0.3 + amplitude * 0.7;
    waveformCtx.beginPath();
    const r = Math.min(barWidth / 2, barH / 2, 3);
    waveformCtx.roundRect(x, y, barWidth, barH, r);
    waveformCtx.fill();
  }

  waveformCtx.globalAlpha = 1;
  waveformRAF = requestAnimationFrame(drawWaveform);
}

// ── Dynamic glow intensity for speaking state ──
function updateSpeakingGlow() {
  if (state !== 'speaking' || !analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(data);
  let sum = 0;
  for (let i = 0; i < data.length; i++) sum += data[i];
  const avg = sum / data.length / 255;
  // Modulate the glow layers based on audio amplitude
  const intensity = 0.3 + avg * 0.7;
  viewportWrap.style.setProperty('--speak-intensity', intensity);
  const spread = 20 + avg * 60;
  const inner = 15 + avg * 25;
  viewportWrap.querySelector('.viewport-glow').style.boxShadow =
    `0 0 ${spread}px ${spread * 0.4}px rgba(129,140,248,${intensity * 0.25})`;
  viewportWrap.style.boxShadow =
    `inset 0 0 ${inner}px rgba(129,140,248,${intensity * 0.15}), 0 0 ${inner}px rgba(129,140,248,${intensity * 0.2})`;
  requestAnimationFrame(updateSpeakingGlow);
}

// ── State Machine ──
let processingWatchdog = null;
let speakingWatchdog = null;

function setState(newState) {
  console.log(`[STATE] ${state} -> ${newState}`);
  state = newState;

  stateDot.className = `dot ${newState}`;
  const labels = { loading: 'Loading...', listening: 'Listening', processing: 'Thinking...', speaking: 'Speaking', muted: 'Mic Muted (Check device)' };
  stateText.textContent = labels[newState] || newState;

  viewportWrap.className = `viewport-wrap ${newState}`;

  // Reset inline styles from speaking glow
  if (newState !== 'speaking') {
    viewportWrap.style.boxShadow = '';
    viewportWrap.querySelector('.viewport-glow').style.boxShadow = '';
  }

  const [glow, glowDim] = STATE_COLORS[newState] || STATE_COLORS.loading;
  document.documentElement.style.setProperty('--glow', glow);
  document.documentElement.style.setProperty('--glow-dim', glowDim);

  if (newState === 'speaking') requestAnimationFrame(updateSpeakingGlow);

  // Raise the VAD's own segmentation threshold while TTS plays so echo
  // rarely opens a speech segment. (Barge-in reads raw probabilities in
  // handleVadFrame — this threshold does not gate it.)
  if (myvad) {
    if (typeof myvad.setOptions === 'function') {
      myvad.setOptions({ positiveSpeechThreshold: newState === 'speaking' ? 0.92 : 0.5 });
    } else if (myvad.options) {
      myvad.options.positiveSpeechThreshold = newState === 'speaking' ? 0.92 : 0.5;
    }
  }

  if (newState === 'listening' && mediaStream && audioCtx && analyser) {
    if (!micSource) {
      micSource = audioCtx.createMediaStreamSource(mediaStream);
    }
    try { micSource.connect(analyser); } catch { }
  } else if (micSource && newState !== 'listening') {
    try { micSource.disconnect(analyser); } catch { }
  }

  // Watchdog: never let 'processing' or 'speaking' become a terminal state
  clearTimeout(processingWatchdog);
  clearTimeout(speakingWatchdog);
  if (newState === 'processing') {
    processingWatchdog = setTimeout(() => {
      if (state === 'processing') {
        console.warn('[WATCHDOG] Processing state timed out (10s) — forcing return to listening');
        showToast('Server response timed out — returning to listening state', 'warning');
        goListening();
      }
    }, 10000);
  } else if (newState === 'speaking') {
    speakingWatchdog = setTimeout(() => {
      if (state === 'speaking') {
        console.warn('[WATCHDOG] Speaking state timed out (10s) — forcing return to listening');
        showToast('Playback timed out — returning to listening state', 'warning');
        stopPlayback();
        goListening();
      }
    }, 10000);
  }

  updateDiagnostics();
}

// announce=false when the mic may be live (barge-in): 'ready' tells the
// server the floor is free, so it must only be sent from genuine idle.
// Clearing ignoreIncomingAudio in the same breath keeps the two ends
// aligned: a server that may now deliver ⇔ a client that will play it.
function goListening(announce = true) {
  setState('listening');
  setStatus('connected', 'Connected');
  if (announce && !speechActive) {
    ignoreIncomingAudio = false;
    wsSend({ type: 'ready' });
  }
}
function goProcessing() { setState('processing'); setStatus('processing', 'Processing'); }

// ── WebSocket ──
function wsOpen() { return ws && ws.readyState === WebSocket.OPEN; }

function wsSend(payload) {
  if (payload.type !== 'speech_chunk') {
    console.log('[STAGE 1] [WS SEND]', payload.type || (payload.audio ? 'audio_turn' : 'payload'), 'payload size:', JSON.stringify(payload).length);
  }
  if (wsOpen()) ws.send(JSON.stringify(payload));
}

function connect() {
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
  ws.onopen = () => {
    setStatus('connected', 'Connected');
    if (state !== 'loading') setState('listening');
    updateDiagnostics();
  };
  ws.onerror = () => {
    updateDiagnostics();
    showToast('WebSocket connection error', 'error', 3000);
  };
  ws.onclose = (evt) => {
    // A reconnect gets a brand-new server conversation — reset per-turn state.
    framePrefetched = false;
    serverHoldingAudio = false;
    removePendingUserBubble();
    delegationChips.forEach(chip => chip.remove());  // tasks died with the server
    delegationChips.clear();
    clearTimerChips();  // timers died with it too
    setSessionMode('conversation');  // a reconnect starts a fresh session
    clearFlushTimer();

    if (evt && evt.code === 4001) {
      setStatus('disconnected', 'Session Rejected');
      setState('muted');
      updateDiagnostics();
      showToast('Connection rejected — another session is already active in another tab or window', 'error', 15000);
      console.warn('[SINGLE SESSION POLICY] Connection closed (code 4001): another tab is active.');
      return; // Do NOT auto-reconnect in a loop
    }
    if (evt && evt.code === 1011) {
      setStatus('disconnected', 'Server Error');
      setState('muted');
      updateDiagnostics();
      showToast('Server initialization failed — check server logs and configuration', 'error', 15000);
      console.warn('[SERVER INIT ERROR] Connection closed (code 1011): server model load failed.');
      return;
    }

    setStatus('disconnected', 'Disconnected');
    updateDiagnostics();
    showToast('Disconnected from server — reconnecting...', 'warning', 3000);
    setTimeout(connect, 2000);
  };
  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    if (msg.type !== 'audio_chunk') {
      console.log('[WS RECV]', msg.type, msg);
    }
    if (msg.type === 'error') {
      console.error('[SERVER ERROR]', msg.message);
      showToast(msg.message || 'Server error occurred', 'error', 10000);
      if (state === 'processing' || state === 'speaking') {
        goListening();
      }
      return;
    }
    if (msg.type === 'intervention_triggered') {
      showInterventionCard(msg.intervention);
      return;
    }
    if (msg.type === 'text_delta') {
      if (ignoreIncomingAudio) return;
      appendAssistantText(msg.text);
    } else if (msg.type === 'turn_incomplete') {
      // The classifier judged the user unfinished — keep listening; if they
      // stay silent, flush the held audio so the model answers anyway.
      if (ignoreIncomingAudio) { ignoreIncomingAudio = false; return; }
      // Keep the pending bubble: the held audio is still this utterance,
      // and the eventual merged transcript will fill it.
      serverHoldingAudio = true;
      const bubble = pendingUserBubble();
      if (bubble) setBubbleMeta(bubble,
        `sounds unfinished (${Math.round((msg.p_complete ?? 0) * 100)}%) — still listening`);
      goListening();
      startFlushTimer();
    } else if (msg.type === 'transcript') {
      // The transcript line leads the model's reply, so what you said
      // appears while the response is still decoding.
      if (ignoreIncomingAudio) return;
      fillUserBubble(msg.transcription);
    } else if (msg.type === 'turn_final') {
      if (ignoreIncomingAudio) return;
      if (msg.proactive) {
        // Server-initiated delivery: its "transcript" is the model's own
        // echo, and there is no pending user bubble to fill or remove.
      } else if (!msg.spoke && !msg.transcription) {
        removePendingUserBubble();  // glitch/empty turn — nothing was heard
      } else {
        fillUserBubble(msg.transcription);
      }
      const t = msg.timings || {};
      if (t.llm_time) {
        setAssistantMeta((t.ttfa_s ? `first audio ${t.ttfa_s}s · ` : '') + `model ${t.llm_time}s`);
      }
      currentAssistantEl = null;  // the next turn gets its own bubble
      if (!msg.spoke) goListening();  // no audio will follow
    } else if (msg.type === 'audio_start') {
      if (ignoreIncomingAudio) return;
      streamSampleRate = msg.sample_rate || 24000;
      startStreamPlayback();
    } else if (msg.type === 'audio_chunk') {
      if (ignoreIncomingAudio) return;
      queueAudioChunk(msg.audio);
    } else if (msg.type === 'audio_end') {
      audioEndReceived = true;
      if (ignoreIncomingAudio) {
        ignoreIncomingAudio = false;
        stopPlayback();
        goListening();
        return;
      }
      const meta = messagesDiv.querySelector('.msg.assistant:last-child .meta');
      if (meta) meta.textContent += ` · tts ${msg.tts_time}s`;
      if (streamSources.length === 0 && state === 'speaking') {
        goListening();
      }
    } else if (msg.type === 'mode_changed') {
      setSessionMode(msg.mode);
    } else if (msg.type === 'delegation_started') {
      addDelegationChip(msg.id, msg.task);
    } else if (msg.type === 'delegation_parked') {
      // Finished, but delivery waits out translation mode — the chip must
      // stop implying work in progress.
      const chip = delegationChips.get(msg.id);
      if (chip) {
        chip.classList.add('parked');
        chip.querySelector('.task').textContent =
          'ready — ' + chip.querySelector('.task').textContent;
      }
    } else if (msg.type === 'delegation_resolved') {
      // The delivery turn follows immediately as a normal spoken turn —
      // give it a fresh assistant bubble, and show it as thinking (which
      // also arms the processing watchdog) if we were sitting idle.
      currentAssistantEl = null;
      removeDelegationChip(msg.id);
      if (state === 'listening') goProcessing();
    } else if (msg.type === 'timer_started') {
      addTimerChip(msg.id, msg.label, msg.seconds);
    } else if (msg.type === 'timer_resolved') {
      removeTimerChip(msg.id);
      if (!msg.cancelled) {
        // The ring follows immediately as a spoken turn, like a delivery.
        currentAssistantEl = null;
        if (state === 'listening') goProcessing();
      }
    }
  };
}

// ── Streamed assistant message helpers ──
const LOADING_DOTS = '<span class="loading-dots"><span></span><span></span><span></span></span>';
let currentAssistantEl = null;
let currentAssistantBodyEl = null;

function appendAssistantText(text) {
  if (!currentAssistantEl) {
    currentAssistantEl = document.createElement('div');
    currentAssistantEl.className = 'msg assistant';
    currentAssistantEl.innerHTML = '<span class="body"></span>';
    currentAssistantBodyEl = currentAssistantEl.querySelector('.body');
    messagesDiv.appendChild(currentAssistantEl);
  }
  currentAssistantBodyEl.textContent += text;
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function setAssistantMeta(text) {
  if (!currentAssistantEl) return;
  let meta = currentAssistantEl.querySelector('.meta');
  if (!meta) {
    meta = document.createElement('div');
    meta.className = 'meta';
    currentAssistantEl.appendChild(meta);
  }
  meta.textContent = text;
}

// ── Session mode (server-driven; the chip's stop button is the escape
// hatch for when the spoken exit command gets misheard) ──
const MODE_LABELS = { translate: 'Translating → English', listen: 'Just listening' };

function setSessionMode(mode) {
  $('modeChip').hidden = mode === 'conversation';
  $('modeLabel').textContent = MODE_LABELS[mode] || mode;
}

// ── Delegation chips: a background research task in flight, shown until
// its answer arrives as a normal spoken turn. ──
const delegationChips = new Map();

function addDelegationChip(id, task) {
  const div = document.createElement('div');
  div.className = 'delegation-chip';
  div.innerHTML = `${LOADING_DOTS}<span class="task"></span>`;
  div.querySelector('.task').textContent = task;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  delegationChips.set(id, div);
}

function removeDelegationChip(id) {
  const chip = delegationChips.get(id);
  delegationChips.delete(id);
  if (chip) chip.remove();
}

// ── Timer chips: a running countdown with a cancel button; the ring
// arrives later as a normal spoken turn (timer_resolved precedes it). ──
const timerChips = new Map();  // id → { el, deadline }
let timerTicker = null;

function addTimerChip(id, label, seconds) {
  const div = document.createElement('div');
  div.className = 'timer-chip';
  div.innerHTML = '<span class="countdown"></span><span class="task"></span>' +
    '<button class="timer-cancel" title="Cancel timer">✕</button>';
  div.querySelector('.task').textContent = label;
  div.querySelector('.timer-cancel').onclick = () => wsSend({ type: 'cancel_timer', id });
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  timerChips.set(id, { el: div, deadline: Date.now() + seconds * 1000 });
  if (!timerTicker) timerTicker = setInterval(tickTimers, 500);
  tickTimers();
}

function removeTimerChip(id) {
  const chip = timerChips.get(id);
  timerChips.delete(id);
  if (chip) chip.el.remove();
}

function clearTimerChips() {
  timerChips.forEach(({ el }) => el.remove());
  timerChips.clear();
}

function tickTimers() {
  // The ticker stops itself once the last chip is gone, so removing one is
  // just a map delete. Countdowns clamp at 0:00 — a ring parked behind a
  // busy floor shows a finished countdown until the announcement lands.
  if (!timerChips.size) { clearInterval(timerTicker); timerTicker = null; return; }
  timerChips.forEach(({ el, deadline }) => {
    const left = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    el.querySelector('.countdown').textContent =
      `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
  });
}

function pendingUserBubble() {
  const userMsgs = messagesDiv.querySelectorAll('.msg.user');
  const last = userMsgs[userMsgs.length - 1];
  return last && last.querySelector('.loading-dots') ? last : null;
}

function removePendingUserBubble() {
  const bubble = pendingUserBubble();
  if (bubble) bubble.remove();
}

// One pending bubble per utterance-group: a continuation after a hold (or a
// flush) belongs to the same bubble the first segment created. The base
// meta ('with camera') is kept in dataset so later info can extend it.
function addUserLoadingBubble(meta = '') {
  if (pendingUserBubble()) return;
  addMessage('user', LOADING_DOTS, meta).dataset.base = meta;
}

function setBubbleMeta(bubble, extra) {
  const parts = [bubble.dataset.base, extra].filter(Boolean);
  let meta = bubble.querySelector('.meta');
  if (!parts.length) { if (meta) meta.remove(); return; }
  if (!meta) {
    meta = document.createElement('div');
    meta.className = 'meta';
    bubble.appendChild(meta);
  }
  meta.textContent = parts.join(' · ');
}

// Replace the last user bubble's loading dots with the heard words (no-op
// if already filled — the early 'transcript' frame wins over turn_final's
// copy). Also clears any 'sounds unfinished' hold meta: the turn resolved.
function fillUserBubble(transcription) {
  const bubble = pendingUserBubble();
  if (!bubble) return;
  bubble.textContent = transcription || '…';
  setBubbleMeta(bubble, '');
}

// ── Flush timer: an incomplete turn went quiet — have the model answer the
// held audio anyway (it asks the user to continue if the words really are
// unfinished). Self-limiting: one flush per hold. serverHoldingAudio tracks
// the held state so a cleared timer (VAD misfire, barge-in) can re-arm —
// otherwise a cough after a false hold strands the question in silence.
let flushTimer = null;
let serverHoldingAudio = false;

function startFlushTimer() {
  clearFlushTimer();
  flushTimer = setTimeout(() => {
    flushTimer = null;
    // Never flush over live speech — that utterance will consume the held
    // audio itself when it ends.
    if (state === 'listening' && !speechActive && wsOpen()) {
      serverHoldingAudio = false;
      currentAssistantEl = null;
      ignoreIncomingAudio = false;
      addUserLoadingBubble();
      setBubbleMeta(pendingUserBubble(), '');  // hold resolved — drop its meta
      wsSend({ type: 'flush' });
      goProcessing();
    }
  }, 2500);
}

function clearFlushTimer() {
  if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
}

function setStatus(cls, text) { statusEl.className = `status-pill ${cls}`; statusEl.textContent = text; }

// ── Camera ──
const VIDEO_CONSTRAINTS = { width: 640, height: 480, facingMode: 'user' };
const AUDIO_CONSTRAINTS = { echoCancellation: true, noiseSuppression: true, autoGainControl: true };

let audioTrack = null;

function checkAudioTrackMuteState() {
  if (!mediaStream) return false;
  const audioTracks = mediaStream.getAudioTracks();
  if (!audioTracks.length) return false;
  const track = audioTracks[0];
  return track.muted || !track.enabled;
}

function updateMicMuteUI(muted) {
  if (muted) {
    setStatus('muted', 'Mic Muted');
    setState('muted');
    console.warn('[MIC MUTE DETECTED] Hardware/OS mic track is MUTED! Pausing speech detection.');
  } else {
    setStatus('connected', 'Connected');
    if (state !== 'loading') setState('listening');
    console.log('[MIC UNMUTE DETECTED] Mic track is active and unmuted.');
  }
}

function setupAudioTrackListeners(track) {
  if (!track) return;
  audioTrack = track;
  track.onmute = () => {
    updateMicMuteUI(true);
    updateDiagnostics();
    showToast('Microphone is muted — check input device or OS settings', 'warning');
  };
  track.onunmute = () => {
    updateMicMuteUI(false);
    updateDiagnostics();
    showToast('Microphone unmuted and active', 'success', 3000);
  };
  track.onended = () => {
    setStatus('disconnected', 'Mic Disconnected');
    setState('muted');
    updateDiagnostics();
    showToast('Microphone device disconnected', 'error');
  };
}

async function startCamera() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: VIDEO_CONSTRAINTS, audio: AUDIO_CONSTRAINTS,
    });
    video.srcObject = mediaStream;
    cameraEnabled = true;
  } catch (e) {
    console.warn('Video+audio getUserMedia failed, attempting audio-only fallback:', e.message);
    cameraEnabled = false;
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: AUDIO_CONSTRAINTS });
      showToast('Camera unavailable or permission denied — continuing in audio-only mode', 'warning', 6000);
    } catch (audioErr) {
      console.error('Audio-only getUserMedia failed:', audioErr.message);
      setStatus('disconnected', 'Mic Access Denied');
      setState('muted');
      updateDiagnostics();
      showToast('Microphone access required — check browser permissions or input device connection', 'error', 10000);
      return;
    }
  }

  const audioTracks = mediaStream ? mediaStream.getAudioTracks() : [];
  if (audioTracks.length > 0) {
    const track = audioTracks[0];
    setupAudioTrackListeners(track);
    console.log(`[MIC DEVICE] Label: "${track.label || 'Default Microphone'}", Enabled: ${track.enabled}, Muted: ${track.muted}, State: ${track.readyState}`, track.getSettings ? track.getSettings() : {});
    if (state === 'loading') setState('listening');
  } else {
    console.warn('[MIC DEVICE] NO AUDIO TRACKS FOUND!');
    setStatus('disconnected', 'No Mic Device');
    setState('muted');
    showToast('No microphone device found on system', 'error', 10000);
  }
  updateDiagnostics();
}

function captureFrame() {
  if (!cameraEnabled || !video.videoWidth) return null;
  const canvas = document.createElement('canvas');
  const scale = 320 / video.videoWidth;
  canvas.width = 320; canvas.height = video.videoHeight * scale;
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', 0.7).split(',')[1];
}

// ── VAD Handlers ──
let speakingStartedAt = 0;
let framePrefetched = false; // server holds an unconsumed camera frame
const BARGE_IN_GRACE_MS = 800; // Ignore VAD triggers shortly after TTS starts (echo)

// ── Speech chunk streaming ──
// While the user talks, ship ~3s audio chunks so the server can prefill
// them into the LLM cache; at speech end only the tail remains to process.
const CHUNK_SECONDS = 3.0;
const PRE_FRAMES = 16; // ~512ms of pre-speech context
let uttFrames = [];    // frames of the current utterance
let preFrames = [];    // rolling pre-speech buffer
let uttSamplesSent = 0;
let chunkSeq = 0;
let speechActive = false;

// Barge-in gate: BARGE_HITS of the last BARGE_WINDOW frames must read as
// speech (≈200-320ms of mostly-speech). It must be SUSTAINED, not a single
// loud frame, or the mic catching our own TTS interrupts the reply (echo) —
// but real speech dips at every consonant and word boundary, so a
// consecutive-frames counter never fires on a live mic.
const BARGE_WINDOW = 10;
const BARGE_HITS = 6;
const BARGE_SPEECH_P = 0.85;
let bargeWindow = []; // 1/0 per recent frame, while TTS plays

let vadFrameCount = 0;
let silentListeningFrames = 0;
let stuckToastShown = false;

function handleVadFrame(probs, frame) {
  vadFrameCount++;
  const speechProb = probs ? (probs.isSpeech ?? 0) : 0;
  let sum = 0;
  for (let i = 0; i < frame.length; i++) sum += frame[i] * frame[i];
  const rms = Math.sqrt(sum / frame.length);

  // Stuck-state check: 30s in listening with near-zero RMS volume
  if (state === 'listening' && rms < 0.005 && speechProb < 0.25) {
    silentListeningFrames++;
    if (silentListeningFrames >= 1000 && !stuckToastShown) { // ~30s (1000 frames @ 30ms)
      stuckToastShown = true;
      showToast("Not hearing anything — check that your microphone isn't muted.", 'warning', 10000);
    }
  } else if (speechProb > 0.4 || rms > 0.01) {
    silentListeningFrames = 0;
    stuckToastShown = false;
  }

  if (vadFrameCount % 30 === 0 || speechProb > 0.3 || rms > 0.005) {
    const thresh = (myvad && myvad.options) ? myvad.options.positiveSpeechThreshold : 0.5;
    console.log(`[MIC METER] Frame #${vadFrameCount} | RMS Vol: ${rms.toFixed(4)} | SpeechProb: ${speechProb.toFixed(3)} | Thresh: ${thresh} | State: ${state}`);
  }

  if (state === 'speaking') {
    bargeWindow.push(probs && probs.isSpeech > BARGE_SPEECH_P ? 1 : 0);
    if (bargeWindow.length > BARGE_WINDOW) bargeWindow.shift();
    if (bargeWindow.reduce((a, b) => a + b, 0) >= BARGE_HITS) {
      bargeWindow = [];
      triggerBargeIn();
    }
    return;
  }
  bargeWindow = [];
  if (speechActive && state === 'listening') {
    // Watchdog: barge-in starts capture outside the VAD's own state machine
    // (startUtteranceCapture in triggerBargeIn). If the VAD never actually
    // enters speech — an echo burst in the (BARGE_SPEECH_P, 0.92] band can
    // trip the gate alone — no speech-end will ever arrive, and without
    // this reset we'd stream silence chunks to the server forever.
    phantomQuiet = probs && probs.isSpeech < 0.25 ? phantomQuiet + 1 : 0;
    if (phantomQuiet >= 30) {  // ~1s below the negative threshold
      phantomQuiet = 0;
      speechActive = false;
      uttFrames = [];
      uttSamplesSent = 0;
      // The barge-in was a false alarm: re-announce idle so the server's
      // interrupted flag doesn't strand a queued delegation delivery.
      goListening();
      console.log('phantom capture reset (no speech after barge-in)');
      return;
    }
    uttFrames.push(frame);
    const total = totalSamples(uttFrames);
    if (total - uttSamplesSent >= CHUNK_SECONDS * 16000) sendSpeechChunk(total);
  } else if (!speechActive) {
    phantomQuiet = 0;
    preFrames.push(frame);
    if (preFrames.length > PRE_FRAMES) preFrames.shift();
  }
}

function totalSamples(frames) {
  let total = 0;
  for (const f of frames) total += f.length;
  return total;
}

function concatFrames(frames) {
  const out = new Float32Array(totalSamples(frames));
  let off = 0;
  for (const f of frames) { out.set(f, off); off += f.length; }
  return out;
}

function sendSpeechChunk(upTo) {
  if (!wsOpen()) return;
  const chunk = concatFrames(uttFrames).subarray(uttSamplesSent, upTo);
  if (chunk.length < 4800) return; // <300ms — not worth a priming request
  wsSend({ type: 'speech_chunk', seq: chunkSeq++, audio: float32ToWavBase64(chunk) });
  uttSamplesSent = upTo;
}

let phantomQuiet = 0; // capture frames below the negative VAD threshold

function startUtteranceCapture() {
  phantomQuiet = 0;
  speechActive = true;
  uttFrames = [...preFrames];
  uttSamplesSent = 0;
  chunkSeq = 0;
}

// Send the camera frame the moment speech STARTS: the server prefills the
// image tokens while the user is still talking, so the audio turn only pays
// for the audio (~75% faster first token on camera turns).
function prefetchFrame() {
  if (framePrefetched || !cameraEnabled || !wsOpen()) return;
  const image = captureFrame();
  if (!image) return;
  wsSend({ type: 'frame', image });
  framePrefetched = true;
}

function handleSpeechStart() {
  console.log(`[STAGE 1] [VAD START] Speech started (state=${state}, speechActive=${speechActive})`);
  if (checkAudioTrackMuteState()) {
    updateMicMuteUI(true);
    return;
  }
  clearFlushTimer();
  if (state === 'listening') { prefetchFrame(); startUtteranceCapture(); }
  else { console.warn(`[STAGE 1] [VAD START IGNORED] State is ${state}, expected 'listening'`); }
}

function triggerBargeIn() {
  if (Date.now() - speakingStartedAt < BARGE_IN_GRACE_MS) {
    console.log('Barge-in suppressed (echo grace period)');
    return;
  }
  stopPlayback();
  ignoreIncomingAudio = true;
  wsSend({ type: 'interrupt' });
  goListening(false);  // the mic is live — the floor is NOT free
  prefetchFrame();
  startUtteranceCapture();
  console.log('[STAGE 1] Barge-in: interrupted playback');
}

function handleSpeechEnd(audio) {
  console.log(`[STAGE 1] [VAD END] Speech ended (state=${state}, speechActive=${speechActive}, audioLen=${audio ? audio.length : 0})`);
  const wasStreaming = speechActive && uttSamplesSent > 0;
  speechActive = false; // always reset — a leak here streams mic audio forever
  if (state !== 'listening' || !wsOpen()) {
    console.warn(`[STAGE 1] [VAD DROPPED] Utterance dropped: state=${state}, wsOpen=${wsOpen()}`);
    framePrefetched = false;
    return;
  }

  clearFlushTimer();
  serverHoldingAudio = false;
  // Frame already prefetched at speech start; capture now only as fallback.
  const imageBase64 = framePrefetched ? null : captureFrame();
  const withCamera = framePrefetched || !!imageBase64;
  framePrefetched = false;

  goProcessing();
  addUserLoadingBubble(withCamera ? 'with camera' : '');
  setBubbleMeta(pendingUserBubble(), '');  // hold resolved — drop its meta

  currentAssistantEl = null;
  ignoreIncomingAudio = false;
  const payload = {};
  if (wasStreaming) {
    // Chunks already streamed — send only the un-sent tail (may be empty;
    // the server then responds from the streamed chunks alone).
    const tail = concatFrames(uttFrames).subarray(uttSamplesSent);
    if (tail.length >= 1600) payload.audio = float32ToWavBase64(tail);
    payload.chunked = true;
  } else {
    payload.audio = float32ToWavBase64(audio);
  }
  if (imageBase64) payload.image = imageBase64;
  wsSend(payload);
}

// ── Float32 @ 16kHz → WAV base64 ──
function float32ToWavBase64(samples) {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); v.setUint32(4, 36 + samples.length * 2, true); w(8, 'WAVE'); w(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, 16000, true); v.setUint32(28, 32000, true); v.setUint16(32, 2, true);
  v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  const bytes = new Uint8Array(buf);
  let bin = ''; for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

// ── Streaming Playback ──
let audioEndReceived = false;

function stopPlayback() {
  for (const src of streamSources) {
    try { src.stop(); } catch { }
  }
  streamSources = [];
  streamNextTime = 0;
  audioEndReceived = false;
}

// TTS plays straight to the WebAudio destination. We tried routing it
// through a MediaStreamDestination + <audio> element so Chrome's echo
// canceller would get a reference signal (crbug 687574) — but on macOS
// that engages system voice processing, which audibly colors the TTS
// voice per turn AND suppresses the user's mic while playback is active,
// killing barge-in. Raw output keeps the voice clean and the mic honest;
// echo defense is the sustained-speech barge-in gate, the post-TTS grace
// period, and the prompt's echo rule (headphones make it moot).
function ensureAudioCtx() {
  if (!audioCtx) {
    audioCtx = new AudioContext();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.75;
  }
}

function startStreamPlayback() {
  stopPlayback();
  ensureAudioCtx();
  if (audioCtx.state === 'suspended') audioCtx.resume();
  streamNextTime = audioCtx.currentTime + 0.05; // Small initial buffer
  speakingStartedAt = Date.now();
  audioEndReceived = false;
  setState('speaking');
}

function queueAudioChunk(base64Pcm) {
  ensureAudioCtx();

  // Decode base64 -> Int16 PCM -> Float32
  const bin = atob(base64Pcm);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  const int16 = new Int16Array(bytes.buffer);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

  const audioBuffer = audioCtx.createBuffer(1, float32.length, streamSampleRate);
  audioBuffer.getChannelData(0).set(float32);

  const source = audioCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioCtx.destination);
  source.connect(analyser);

  // Schedule gapless playback
  const startAt = Math.max(streamNextTime, audioCtx.currentTime);
  source.start(startAt);
  streamNextTime = startAt + audioBuffer.duration;

  streamSources.push(source);

  source.onended = () => {
    const idx = streamSources.indexOf(source);
    if (idx !== -1) streamSources.splice(idx, 1);
    if (streamSources.length === 0 && audioEndReceived && state === 'speaking') {
      goListening();
    }
  };
}

// ── UI ──
function addMessage(role, text, meta) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `${text}${meta ? `<div class="meta">${meta}</div>` : ''}`;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  return div;
}

$('modeStop').addEventListener('click', () => {
  stopPlayback();
  wsSend({ type: 'set_mode', mode: 'conversation' });
  goListening();
});

cameraToggle.addEventListener('click', () => {
  cameraEnabled = !cameraEnabled;
  cameraToggle.classList.toggle('active', cameraEnabled);
  cameraToggle.textContent = cameraEnabled ? 'Camera On' : 'Camera Off';
  video.style.opacity = cameraEnabled ? 1 : 0.3;
});

// ── Init ──
async function init() {
  initWaveformCanvas();
  window.addEventListener('resize', initWaveformCanvas);

  await startCamera();
  connect();
  bindDiagnosticsControls();

  try {
    myvad = await vad.MicVAD.new({
      getStream: async () => new MediaStream(mediaStream.getAudioTracks()),
      positiveSpeechThreshold: 0.5,
      negativeSpeechThreshold: 0.25,
      // Short redemption for fast turn-taking; the server's smart-turn
      // classifier catches the cases where the user was merely pausing.
      redemptionMs: 300,
      minSpeechMs: 300,
      preSpeechPadMs: 500,
      onSpeechStart: handleSpeechStart,
      onSpeechEnd: handleSpeechEnd,
      onVADMisfire: () => {
        // No speech-end will follow — let the next real utterance send a
        // fresh frame instead of pointing the model at this stale one.
        framePrefetched = false;
        speechActive = false;
        if (serverHoldingAudio) startFlushTimer();
        // A false barge-in ends here: re-announce idle so a delegation
        // result deferred by the interrupt isn't stranded.
        if (state === 'listening') goListening();
        console.log('VAD misfire (too short)');
      },
      onFrameProcessed: (probs, frame) => handleVadFrame(probs, Float32Array.from(frame)),
      onnxWASMBasePath: "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0/dist/",
      baseAssetPath: "https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.29/dist/",
    });
    myvad.start();
  } catch (e) {
    console.error('VAD init failed:', e);
    showToast('Failed to initialize VAD engine', 'error');
  }

  // Init audio context on first user gesture for mic visualizer
  // (browsers require user interaction to create AudioContext)
  const initAudio = () => {
    ensureAudioCtx();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    document.removeEventListener('click', initAudio);
    document.removeEventListener('keydown', initAudio);
  };
  document.addEventListener('click', initAudio);
  document.addEventListener('keydown', initAudio);
  // Also try immediately (may work if page had prior interaction)
  ensureAudioCtx();

  if (checkAudioTrackMuteState()) {
    updateMicMuteUI(true);
  } else {
    setState('listening');
  }
  drawWaveform();
  updateDiagnostics();

  console.log('VAD initialized');
}

function showInterventionCard(data) {
  if (!data) return;
  const card = document.getElementById('interventionCard');
  if (!card) return;

  document.getElementById('interventionIcon').textContent = data.icon || '🫁';
  document.getElementById('interventionTitle').textContent = data.title || 'Micro-Intervention';
  document.getElementById('interventionCategory').textContent = data.category || 'Wellness';
  document.getElementById('interventionNote').textContent = data.personalized_note || '';

  const stepsUl = document.getElementById('interventionSteps');
  stepsUl.innerHTML = '';
  (data.steps || []).forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    stepsUl.appendChild(li);
  });

  const reasoningDiv = document.getElementById('interventionReasoning');
  reasoningDiv.textContent = `${data.slm_reasoning || ''} (Stress Level: ${data.stress_level || 'Moderate'}, Confidence: ${data.confidence_score || '0.90'})`;

  const actionBtn = document.getElementById('interventionAction');
  actionBtn.textContent = data.action_label || 'Start Exercise';

  card.hidden = false;
}

function hideInterventionCard() {
  const card = document.getElementById('interventionCard');
  if (card) card.hidden = true;
}

document.addEventListener('DOMContentLoaded', () => {
  bindDiagnosticsControls();

  const closeBtn = document.getElementById('interventionClose');
  if (closeBtn) closeBtn.addEventListener('click', hideInterventionCard);

  const actionBtn = document.getElementById('interventionAction');
  if (actionBtn) actionBtn.addEventListener('click', () => {
    showToast('Starting guided exercise...', 'success', 4000);
    hideInterventionCard();
  });

  const snoozeBtn = document.getElementById('interventionSnooze');
  if (snoozeBtn) snoozeBtn.addEventListener('click', () => {
    showToast('Interventions snoozed for 10 minutes', 'warning', 4000);
    hideInterventionCard();
  });
});

init();
