const $ = id => document.getElementById(id);
const video = $('video'), cameraToggle = $('cameraToggle');
const messagesDiv = $('messages'), statusEl = $('status');
const stateDot = $('stateDot'), stateText = $('stateText');
const viewportWrap = $('viewportWrap');
const waveformCanvas = $('waveform');
const waveformCtx = waveformCanvas ? waveformCanvas.getContext('2d') : null;

const diagBtn = $('diagBtn'), diagPanel = $('diagPanel'), diagClose = $('diagClose');
const diagMic = $('diagMic'), diagVad = $('diagVad'), diagWs = $('diagWs'), diagLlm = $('diagLlm');
const wellnessBtn = $('wellnessBtn'), wellnessPanel = $('wellnessPanel'), wellnessClose = $('wellnessClose');
const wellnessSensitivity = $('wellnessSensitivity'), wellnessMuteToggle = $('wellnessMuteToggle');
const toastContainer = $('toastContainer');

// Modern Futuristic Diagnostics & View Elements
const viewWellnessBtn = $('viewWellnessBtn'), viewDiagnosticsBtn = $('viewDiagnosticsBtn');
const wellnessRail = $('wellnessRail'), diagnosticsRail = $('diagnosticsRail');
const landmarkCanvas = $('landmarkOverlay');
const landmarkCtx = landmarkCanvas ? landmarkCanvas.getContext('2d') : null;
const voiceSparklineCanvas = $('voiceSparkline');
const voiceSparklineCtx = voiceSparklineCanvas ? voiceSparklineCanvas.getContext('2d') : null;
const videoLiveBadge = $('videoLiveBadge');
const micBtn = $('micBtn');
const msgCountBadge = $('msgCountBadge');
const diagFaceDemoBadge = $('diagFaceDemoBadge');
const diagVoiceDemoBadge = $('diagVoiceDemoBadge');
const diagReasonerDemoBadge = $('diagReasonerDemoBadge');
const wellnessSensitivityQuick = $('wellnessSensitivityQuick');
const wellnessMuteToggleQuick = $('wellnessMuteToggleQuick');
const startExerciseQuick = $('startExerciseQuick');
const modelReadyVal = $('modelReadyVal');
const schemaValidVal = $('schemaValidVal');
const baselineActiveVal = $('baselineActiveVal');
const privateStateVal = $('privateStateVal');

// Canonical reference dataset matching futuristic visual specification
const DEMO_DIAGNOSTICS = {
  face: {
    au04_brow_furrow: 0.26,
    au07_lid_tightener: 0.18,
    au15_lip_depressor: 0.32,
    au20_lip_stretcher: 0.11,
    ear: 0.28,
    head_pitch: 1.9,
    head_yaw: -2.8,
    head_roll: 0.6,
    face_confidence: 0.99,
    face_detected: true,
    // MediaPipe 478-mesh normalized key landmarks for overlay
    mesh_points: [
      [0.32, 0.24], [0.38, 0.22], [0.44, 0.24], [0.50, 0.25], [0.56, 0.24], [0.62, 0.22], [0.68, 0.24],
      [0.33, 0.30], [0.37, 0.28], [0.42, 0.29], [0.44, 0.32], [0.39, 0.33], [0.34, 0.32],
      [0.56, 0.32], [0.58, 0.29], [0.63, 0.28], [0.67, 0.30], [0.66, 0.32], [0.61, 0.33],
      [0.50, 0.31], [0.50, 0.36], [0.50, 0.41], [0.46, 0.43], [0.50, 0.45], [0.54, 0.43],
      [0.40, 0.51], [0.45, 0.49], [0.50, 0.50], [0.55, 0.49], [0.60, 0.51],
      [0.56, 0.54], [0.50, 0.55], [0.44, 0.54],
      [0.26, 0.34], [0.27, 0.44], [0.30, 0.53], [0.35, 0.61], [0.42, 0.67], [0.50, 0.71],
      [0.58, 0.67], [0.65, 0.61], [0.70, 0.53], [0.73, 0.44], [0.74, 0.34],
      [0.38, 0.41], [0.62, 0.41], [0.36, 0.47], [0.64, 0.47],
      [0.42, 0.20], [0.50, 0.19], [0.58, 0.20]
    ]
  },
  vocal: {
    speech_detected: true,
    voice_activity_pct: 78,
    pitch_relative_pct: 54,
    pitch_raw: 0.19,
    speech_pace_ws: 4.7,
    speech_pace_pct: 67,
    steadiness_pct: 82,
    steadiness_raw: 0.83
  }
};

let ws, mediaStream, myvad;
let diagnosticsBound = false;
let wellnessControlsBound = false;
let cameraEnabled = true;
let lastFaceSnapshotAt = 0;
let lastFaceDetectionState = null;
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
  if (!toastContainer) return null;
  // De-duplicate: If a toast with this exact message already exists, update and refresh its timer
  const existing = Array.from(toastContainer.querySelectorAll('.toast-banner')).find(
    el => el.querySelector('span')?.textContent === message
  );
  if (existing) {
    existing.className = `toast-banner ${type}`;
    if (existing._dismissTimer) clearTimeout(existing._dismissTimer);
    if (durationMs > 0) {
      existing._dismissTimer = setTimeout(() => { if (existing.parentNode) existing.remove(); }, durationMs);
    }
    return existing;
  }
  const toast = document.createElement('div');
  toast.className = `toast-banner ${type}`;
  toast.innerHTML = `<span>${message}</span><button class="toast-close">✕</button>`;
  const closeBtn = toast.querySelector('.toast-close');
  if (closeBtn) closeBtn.onclick = () => {
    if (toast._dismissTimer) clearTimeout(toast._dismissTimer);
    toast.remove();
  };
  toastContainer.appendChild(toast);
  if (durationMs > 0) {
    toast._dismissTimer = setTimeout(() => { if (toast.parentNode) toast.remove(); }, durationMs);
  }
  return toast;
}

function setFaceRailStatus(kind, label) {
  const status = document.getElementById('faceRailStatus');
  if (!status) return;
  status.className = `face-rail-status ${kind}`;
  const text = status.querySelector('span');
  if (text) text.textContent = label;
}

let landmarksVisible = true;

function initLandmarkCanvas() {
  if (!landmarkCanvas || !landmarkCtx) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = landmarkCanvas.getBoundingClientRect();
  const w = rect.width || 640;
  const h = rect.height || 480;
  landmarkCanvas.width = w * dpr;
  landmarkCanvas.height = h * dpr;
  landmarkCtx.setTransform(1, 0, 0, 1, 0, 0);
  landmarkCtx.scale(dpr, dpr);
}

// ── Pure Landmark Coordinate Transform (Step 3 Parity with Python overlay.py) ──
function mapLandmarkToCanvas(normX, normY, srcW, srcH, dstW, dstH, objectFit = 'cover', mirrored = false, crop = null) {
  if (srcW <= 0 || srcH <= 0 || dstW <= 0 || dstH <= 0) return [0, 0];
  let xSrc = normX;
  let ySrc = normY;
  if (crop) {
    const cx = crop.x ?? crop[0] ?? 0;
    const cy = crop.y ?? crop[1] ?? 0;
    const cw = crop.w ?? crop.width ?? crop[2] ?? 1;
    const ch = crop.h ?? crop.height ?? crop[3] ?? 1;
    xSrc = cx + normX * cw;
    ySrc = cy + normY * ch;
  }
  if (mirrored) {
    xSrc = 1.0 - xSrc;
  }
  const scaleX = dstW / srcW;
  const scaleY = dstH / srcH;
  const scale = objectFit === 'contain' ? Math.min(scaleX, scaleY) : Math.max(scaleX, scaleY);
  const renderedW = srcW * scale;
  const renderedH = srcH * scale;
  const offsetX = (dstW - renderedW) / 2.0;
  const offsetY = (dstH - renderedH) / 2.0;
  return [offsetX + xSrc * renderedW, offsetY + ySrc * renderedH];
}
window.mapLandmarkToCanvas = mapLandmarkToCanvas;

let isDocumentVisible = true;
document.addEventListener('visibilitychange', () => {
  isDocumentVisible = document.visibilityState === 'visible';
  if (!isDocumentVisible) {
    clearLandmarkOverlay();
  }
});

let cachedLandmarkW = 640;
let cachedLandmarkH = 360;

function clearLandmarkOverlay() {
  if (!landmarkCanvas || !landmarkCtx) return;
  landmarkCtx.clearRect(0, 0, cachedLandmarkW, cachedLandmarkH);
}

function initLandmarkCanvas() {
  if (!landmarkCanvas || !landmarkCtx) return;
  const dpr = window.devicePixelRatio || 1;
  cachedLandmarkW = landmarkCanvas.clientWidth || 640;
  cachedLandmarkH = landmarkCanvas.clientHeight || 360;
  landmarkCanvas.width = cachedLandmarkW * dpr;
  landmarkCanvas.height = cachedLandmarkH * dpr;
  landmarkCtx.setTransform(1, 0, 0, 1, 0, 0);
  landmarkCtx.scale(dpr, dpr);
}

const faceMiniCanvas = $('faceMiniCanvas');
const faceMiniCtx = faceMiniCanvas ? faceMiniCanvas.getContext('2d') : null;
const faceEmptyState = $('faceEmptyState');

function drawMiniFaceMesh(meshPoints) {
  if (!faceMiniCanvas || !faceMiniCtx) return;
  if (!meshPoints || !meshPoints.length) {
    if (faceEmptyState) faceEmptyState.hidden = false;
    faceMiniCanvas.hidden = true;
    return;
  }
  if (faceEmptyState) faceEmptyState.hidden = true;
  faceMiniCanvas.hidden = false;

  const w = faceMiniCanvas.width;
  const h = faceMiniCanvas.height;
  faceMiniCtx.clearRect(0, 0, w, h);

  const pts = meshPoints.map(([nx, ny]) => [nx * w, ny * h]);

  // Connect contour lines
  faceMiniCtx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
  faceMiniCtx.lineWidth = 1.0;
  faceMiniCtx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const dx = pts[i][0] - pts[j][0];
      const dy = pts[i][1] - pts[j][1];
      if (Math.hypot(dx, dy) < w * 0.16) {
        faceMiniCtx.moveTo(pts[i][0], pts[i][1]);
        faceMiniCtx.lineTo(pts[j][0], pts[j][1]);
      }
    }
  }
  faceMiniCtx.stroke();

  // Draw node vertices
  faceMiniCtx.fillStyle = 'rgba(240, 246, 255, 0.9)';
  for (let i = 0; i < pts.length; i++) {
    faceMiniCtx.beginPath();
    faceMiniCtx.arc(pts[i][0], pts[i][1], 1.2, 0, 2 * Math.PI);
    faceMiniCtx.fill();
  }
}

let lastMeshDrawTimestamp = 0;
const MESH_THROTTLE_INTERVAL = 66; // 15 fps budget

function drawLandmarkOverlay(meshPoints) {
  if (!landmarkCanvas || !landmarkCtx || !isDocumentVisible) return;
  if (!landmarksVisible || (!cameraEnabled && !demoModeActive)) {
    clearLandmarkOverlay();
    return;
  }
  if (!meshPoints || !meshPoints.length) {
    clearLandmarkOverlay();
    return;
  }

  const now = Date.now();
  if (now - lastMeshDrawTimestamp < MESH_THROTTLE_INTERVAL) {
    return;
  }
  lastMeshDrawTimestamp = now;

  // Fade out / clear if face data is > 1.5s stale
  if (!demoModeActive && lastFaceSnapshotAt > 0 && (now - lastFaceSnapshotAt > 1500)) {
    clearLandmarkOverlay();
    return;
  }

  const dstW = cachedLandmarkW;
  const dstH = cachedLandmarkH;
  landmarkCtx.clearRect(0, 0, dstW, dstH);

  // Source camera aspect ratio (default 16:9 1280x720)
  const srcW = (video && video.videoWidth > 0) ? video.videoWidth : 1280;
  const srcH = (video && video.videoHeight > 0) ? video.videoHeight : 720;

  // Map landmarks to canvas with cover and horizontal mirror parity
  const pts = meshPoints.map(([nx, ny]) => {
    return mapLandmarkToCanvas(nx, ny, srcW, srcH, dstW, dstH, 'cover', true);
  });

  // Connect adjacent points with subtle glowing triangulation lines (1px)
  landmarkCtx.strokeStyle = 'rgba(56, 189, 248, 0.38)';
  landmarkCtx.lineWidth = 1.0;
  landmarkCtx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const dx = pts[i][0] - pts[j][0];
      const dy = pts[i][1] - pts[j][1];
      const dist = Math.hypot(dx, dy);
      if (dist < dstW * 0.10) {
        landmarkCtx.moveTo(pts[i][0], pts[i][1]);
        landmarkCtx.lineTo(pts[j][0], pts[j][1]);
      }
    }
  }
  landmarkCtx.stroke();

  // Draw delicate glowing landmark node vertices
  landmarkCtx.fillStyle = 'rgba(240, 246, 255, 0.95)';
  landmarkCtx.shadowColor = 'rgba(56, 189, 248, 0.85)';
  landmarkCtx.shadowBlur = 4;

  for (let i = 0; i < pts.length; i++) {
    const [px, py] = pts[i];
    landmarkCtx.beginPath();
    landmarkCtx.arc(px, py, 1.4, 0, 2 * Math.PI);
    landmarkCtx.fill();
  }
  landmarkCtx.shadowBlur = 0;

  // Mirror onto mini wireframe canvas
  drawMiniFaceMesh(meshPoints);
}

function clearFaceMetrics() {
  lastFaceSnapshotAt = 0;
  lastFaceDetectionState = null;
  for (const key of ['AU04', 'AU07', 'AU15', 'AU20']) {
    const value = document.getElementById(`face${key}Value`);
    const bar = document.getElementById(`face${key}Bar`);
    if (value) value.textContent = '—';
    if (bar) bar.style.width = '0%';
  }
  const pose = document.getElementById('facePoseValue');
  if (pose) pose.textContent = 'Yaw —°  Pitch —°  Roll —°';
  const liveBadge = document.getElementById('faceLiveTag') || document.getElementById('diagFaceLiveStatus');
  if (liveBadge) {
    liveBadge.className = 'diag-badge idle';
    liveBadge.innerHTML = '<span class="badge-dot"></span> IDLE';
  }
  clearLandmarkOverlay();
  if (faceEmptyState) faceEmptyState.hidden = false;
  if (faceMiniCanvas) faceMiniCanvas.hidden = true;
}

let lastFaceUpdateTimestamp = 0;
const METRICS_THROTTLE_INTERVAL = 250; // 4 Hz update budget

function updateFaceMetrics(face, simulated = false) {
  if (!face || !face.face_detected) {
    clearFaceMetrics();
    lastFaceSnapshotAt = Date.now();
    lastFaceDetectionState = 'no-face';
    setFaceRailStatus('no-face', cameraEnabled ? 'Face not detected · adjust position' : 'Camera paused');
    const liveBadge = document.getElementById('faceLiveTag') || document.getElementById('diagFaceLiveStatus');
    if (liveBadge) {
      liveBadge.className = 'diag-badge idle';
      liveBadge.innerHTML = '<span class="badge-dot"></span> IDLE';
    }
    return;
  }

  const now = Date.now();
  const isSim = Boolean(simulated || demoModeActive);
  if (!simulated && !isSim && now - lastFaceUpdateTimestamp < METRICS_THROTTLE_INTERVAL) {
    return;
  }
  lastFaceUpdateTimestamp = now;

  lastFaceSnapshotAt = now;
  lastFaceDetectionState = 'face';

  if (face.baseline) {
    updateBaselineUI(face.baseline);
  }
  const fields = [
    ['AU04', face.au04_brow_furrow],
    ['AU07', face.au07_lid_tightener],
    ['AU15', face.au15_lip_depressor],
    ['AU20', face.au20_lip_stretcher],
  ];
  for (const [key, raw] of fields) {
    const value = Number(raw);
    const scorePct = Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value * 100))) : 0;
    const valueEl = document.getElementById(`face${key}Value`);
    const bar = document.getElementById(`face${key}Bar`);
    if (valueEl) valueEl.textContent = Number.isFinite(value) ? value.toFixed(2) : '—';
    if (bar) bar.style.width = `${scorePct}%`;
  }
  const pose = document.getElementById('facePoseValue');
  if (pose) {
    const fmtDeg = (val) => {
      const n = Number(val);
      if (!Number.isFinite(n)) return '—°';
      return (n >= 0 ? `+${n.toFixed(1)}°` : `${n.toFixed(1)}°`);
    };
    pose.textContent = `Yaw ${fmtDeg(face.head_yaw)}  Pitch ${fmtDeg(face.head_pitch)}  Roll ${fmtDeg(face.head_roll)}`;
  }

  const liveBadge = document.getElementById('faceLiveTag') || document.getElementById('diagFaceLiveStatus');
  if (liveBadge) {
    liveBadge.className = 'diag-badge live';
    liveBadge.innerHTML = '<span class="badge-dot"></span> LIVE';
  }

  document.querySelectorAll('.demo-tag').forEach(tag => tag.hidden = !isSim);

  if (face.mesh_points && Array.isArray(face.mesh_points)) {
    drawLandmarkOverlay(face.mesh_points);
  } else if (isSim) {
    drawLandmarkOverlay(DEMO_DIAGNOSTICS.face.mesh_points);
  } else {
    clearLandmarkOverlay();
  }

  setFaceRailStatus(isSim ? 'demo' : 'active', isSim ? 'Simulated sample · demo mode' : 'Local face features · updated now');
}

let lastVoiceSnapshotAt = 0;

function clearVocalMetrics() {
  lastVoiceSnapshotAt = 0;
  const actEl = $('voiceActivityValue') || $('voiceActivityVal');
  const actBar = $('voiceActivityBar');
  const pitchEl = $('voicePitchValue') || $('pitchVal');
  const pitchBar = $('voicePitchBar') || $('pitchBar');
  const paceEl = $('voicePaceValue') || $('speechPaceVal');
  const paceBar = $('voicePaceBar') || $('speechPaceBar');
  const steadyEl = $('voiceSteadinessValue') || $('steadinessVal');
  const steadyBar = $('voiceSteadinessBar') || $('steadinessBar');

  if (actEl) actEl.textContent = '—';
  if (actBar) actBar.style.width = '0%';
  if (pitchEl) pitchEl.textContent = '—';
  if (pitchBar) pitchBar.style.width = '0%';
  if (paceEl) paceEl.textContent = '—';
  if (paceBar) paceBar.style.width = '0%';
  if (steadyEl) steadyEl.textContent = '—';
  if (steadyBar) steadyBar.style.width = '0%';

  const liveBadge = document.getElementById('voiceLiveTag');
  if (liveBadge) {
    liveBadge.className = 'diag-badge idle';
    liveBadge.innerHTML = '<span class="badge-dot"></span> IDLE';
  }
}

let lastVocalUpdateTimestamp = 0;

function updateVocalMetrics(vocal, simulated = false) {
  if (!vocal) return;
  const isSim = Boolean(simulated || demoModeActive);
  document.querySelectorAll('.demo-tag').forEach(tag => tag.hidden = !isSim);

  const now = Date.now();
  if (!simulated && !isSim && now - lastVocalUpdateTimestamp < METRICS_THROTTLE_INTERVAL) {
    return;
  }
  lastVocalUpdateTimestamp = now;

  if (vocal.baseline) {
    updateBaselineUI(vocal.baseline);
  }

  const actEl = $('voiceActivityValue') || $('voiceActivityVal');
  const actBar = $('voiceActivityBar');
  const pitchEl = $('voicePitchValue') || $('pitchVal');
  const pitchBar = $('voicePitchBar') || $('pitchBar');
  const paceEl = $('voicePaceValue') || $('speechPaceVal');
  const paceBar = $('voicePaceBar') || $('speechPaceBar');
  const steadyEl = $('voiceSteadinessValue') || $('steadinessVal');
  const steadyBar = $('voiceSteadinessBar') || $('steadinessBar');

  const speechActive = Boolean(vocal.speech_detected || isSim);

  // 1. Voice activity %
  let voiceAct = null;
  if (vocal.voice_activity_pct !== undefined) {
    voiceAct = vocal.voice_activity_pct;
  } else if (vocal.speech_detected) {
    voiceAct = Math.round((1.0 - (vocal.pause_ratio ?? 0.22)) * 100);
  } else if (isSim) {
    voiceAct = DEMO_DIAGNOSTICS.vocal.voice_activity_pct;
  }

  if (actEl) actEl.textContent = (speechActive && voiceAct !== null) ? `${Math.max(0, Math.min(100, voiceAct))}%` : '—';
  if (actBar) actBar.style.width = (speechActive && voiceAct !== null) ? `${Math.max(0, Math.min(100, voiceAct))}%` : '0%';

  // 2. Pitch variability
  let pitchScore = 0;
  let pitchDisplay = '—';
  if (speechActive) {
    if (vocal.f0_std_hz !== undefined && vocal.f0_std_hz > 0) {
      pitchScore = Math.max(0, Math.min(100, Math.round((vocal.f0_std_hz / 50.0) * 100)));
      pitchDisplay = `${vocal.f0_std_hz.toFixed(1)} Hz`;
    } else if (vocal.pitch_relative_pct !== undefined) {
      pitchScore = vocal.pitch_relative_pct;
      pitchDisplay = vocal.pitch_raw !== undefined ? `${vocal.pitch_raw.toFixed(2)}` : `${pitchScore}%`;
    } else if (isSim) {
      pitchScore = DEMO_DIAGNOSTICS.vocal.pitch_relative_pct;
      pitchDisplay = `${DEMO_DIAGNOSTICS.vocal.pitch_raw.toFixed(2)}`;
    }
  }

  if (pitchEl) {
    pitchEl.textContent = pitchDisplay;
    pitchEl.title = "Pitch variability: standard deviation of fundamental frequency (F0) across speech frames in Hz";
  }
  if (pitchBar) pitchBar.style.width = `${pitchScore}%`;

  // 3. Speech pace (relative bursts/s)
  let pacePct = 0;
  let paceDisplay = '—';
  if (speechActive) {
    if (vocal.speech_pace_relative !== undefined && vocal.speech_pace_relative > 0) {
      const paceVal = vocal.speech_pace_relative;
      pacePct = Math.min(100, Math.round((paceVal / 6.0) * 100));
      paceDisplay = `${paceVal.toFixed(1)} bursts/s`;
    } else if (vocal.speech_pace_ws !== undefined && vocal.speech_pace_ws > 0) {
      const paceVal = vocal.speech_pace_ws;
      pacePct = vocal.speech_pace_pct ?? Math.min(100, Math.round((paceVal / 6.0) * 100));
      paceDisplay = `${paceVal.toFixed(1)} bursts/s`;
    } else if (isSim) {
      const paceVal = DEMO_DIAGNOSTICS.vocal.speech_pace_ws;
      pacePct = DEMO_DIAGNOSTICS.vocal.speech_pace_pct;
      paceDisplay = `${paceVal.toFixed(1)} bursts/s`;
    }
  }

  if (paceEl) {
    paceEl.textContent = paceDisplay;
    paceEl.title = "Speech pace: energy envelope syllable burst rate (relative bursts/s)";
  }
  if (paceBar) paceBar.style.width = `${pacePct}%`;

  // 4. Steadiness
  let steadyScore = 0;
  let steadyDisplay = '—';
  if (speechActive) {
    if (vocal.steadiness_pct !== undefined && vocal.steadiness_pct > 0) {
      steadyScore = vocal.steadiness_pct;
      steadyDisplay = vocal.steadiness_raw !== undefined ? vocal.steadiness_raw.toFixed(2) : (steadyScore / 100).toFixed(2);
    } else if (vocal.jitter_local !== undefined || vocal.jitter_local_pct !== undefined) {
      const jitter = vocal.jitter_local_pct ?? ((vocal.jitter_local ?? 0.05) * 100);
      const shimmer = vocal.shimmer_local_pct ?? ((vocal.shimmer_local ?? 0.05) * 100);
      steadyScore = Math.max(10, Math.min(100, Math.round(100 - (jitter * 4 + shimmer * 3))));
      steadyDisplay = (steadyScore / 100).toFixed(2);
    } else if (isSim) {
      steadyScore = DEMO_DIAGNOSTICS.vocal.steadiness_pct;
      steadyDisplay = DEMO_DIAGNOSTICS.vocal.steadiness_raw.toFixed(2);
    }
  }

  if (steadyEl) {
    steadyEl.textContent = steadyDisplay;
    steadyEl.title = "Voice steadiness: acoustic stability index based on local jitter and shimmer perturbation (0.00 - 1.00)";
  }
  if (steadyBar) steadyBar.style.width = `${steadyScore}%`;

  if (voiceAct !== null || pitchScore > 0 || isSim) {
    lastVoiceSnapshotAt = Date.now();
  }

  // Live badge
  const liveBadge = document.getElementById('voiceLiveTag');
  if (liveBadge) {
    const isLive = Boolean(isSim || (lastVoiceSnapshotAt > 0 && Date.now() - lastVoiceSnapshotAt < 2000));
    liveBadge.className = isLive ? 'diag-badge live' : 'diag-badge idle';
    liveBadge.innerHTML = `<span class="badge-dot"></span> ${isLive ? 'LIVE' : 'IDLE'}`;
  }

  // Mic & VAD status pills
  const micPill = $('micPill');
  const vadPill = $('vadPill');
  if (micPill) {
    const isLive = Boolean(mediaStream && mediaStream.getAudioTracks().some(t => t.readyState === 'live' && t.enabled && !t.muted));
    micPill.innerHTML = `<span class="pill-dot"></span> ${isLive ? 'Mic (on)' : 'Mic (muted)'}`;
    micPill.className = isLive ? 'indicator-pill on' : 'indicator-pill off';
  }
  if (vadPill) {
    const vadActive = Boolean(myvad);
    vadPill.innerHTML = `<span class="pill-dot"></span> ${vadActive ? (speechActive ? 'VAD (active)' : 'VAD') : 'VAD (off)'}`;
    vadPill.className = vadActive ? 'indicator-pill vad' : 'indicator-pill off';
  }
}

function updateFaceRailStatus() {
  const voice = document.getElementById('voiceFusionState');
  const face = document.getElementById('faceFusionState');
  const reason = document.getElementById('reasonFusionState');
  const videoReady = Boolean(mediaStream && mediaStream.getVideoTracks().some(track => track.readyState === 'live'));
  const audioReady = Boolean(mediaStream && mediaStream.getAudioTracks().some(track => track.readyState === 'live' && track.enabled));

  if (voice) voice.textContent = audioReady ? (myvad ? 'READY' : 'STARTING') : 'PAUSED';
  if (reason) reason.textContent = state === 'processing' ? 'RUNNING' : (wsOpen() ? 'READY' : 'OFFLINE');
  if (face) face.textContent = demoModeActive ? 'DEMO' : (cameraEnabled && videoReady ? 'ACTIVE' : 'IDLE');

  if (demoModeActive) {
    setFaceRailStatus('demo', 'Simulated sample · demo mode');
  } else if (!cameraEnabled || !videoReady) {
    if (lastFaceSnapshotAt) clearFaceMetrics();
    setFaceRailStatus('paused', 'Camera paused');
  } else if (!wsOpen()) {
    setFaceRailStatus('waiting', 'Waiting for local service');
  } else if (!lastFaceSnapshotAt) {
    setFaceRailStatus('waiting', 'Waiting for camera frames');
  } else {
    const age = Math.max(0, Math.floor((Date.now() - lastFaceSnapshotAt) / 1000));
    if (age > 20) {
      clearFaceMetrics();
      setFaceRailStatus('waiting', 'Waiting for a fresh frame');
    }
    else if (lastFaceDetectionState === 'no-face') setFaceRailStatus('no-face', 'Face not detected · adjust position');
    else setFaceRailStatus('active', `Local face features · ${age}s ago`);
  }
}

function updateDiagnostics() {
  updateFaceRailStatus();
  if (!diagMic) return;
  // Mic
  if (!mediaStream || !mediaStream.getAudioTracks().length) {
    diagMic.className = 'diag-val error'; diagMic.textContent = '⚫ No device';
    if (micPill) { micPill.textContent = '• Mic (off)'; micPill.className = 'pipeline-pill muted'; }
    if (micBtn) micBtn.classList.add('muted');
  } else {
    const track = mediaStream.getAudioTracks()[0];
    const label = track.label ? ` (${track.label.split(' ')[0]})` : '';
    if (track.readyState === 'ended') {
      diagMic.className = 'diag-val error'; diagMic.textContent = `🔴 Disconnected${label}`;
      if (micPill) { micPill.textContent = '• Mic (ended)'; micPill.className = 'pipeline-pill muted'; }
      if (micBtn) micBtn.classList.add('muted');
    } else if (track.muted || !track.enabled) {
      diagMic.className = 'diag-val warning'; diagMic.textContent = `🔴 Muted${label}`;
      if (micPill) { micPill.textContent = '• Mic (muted)'; micPill.className = 'pipeline-pill muted'; }
      if (micBtn) micBtn.classList.add('muted');
    } else {
      diagMic.className = 'diag-val ok'; diagMic.textContent = `🟢 Live${label}`;
      if (micPill) { micPill.textContent = '• Mic (on)'; micPill.className = 'pipeline-pill live'; }
      if (micBtn) micBtn.classList.remove('muted');
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
  if (shouldOpen) {
    if (wellnessPanel && !wellnessPanel.hidden) toggleWellness(false);
    updateDiagnostics();
  }
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

function toggleWellness(forceOpen) {
  if (!wellnessBtn || !wellnessPanel) return;
  const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : wellnessPanel.hidden;
  wellnessPanel.hidden = !shouldOpen;
  wellnessBtn.setAttribute('aria-expanded', String(shouldOpen));
  if (shouldOpen && diagPanel && !diagPanel.hidden) {
    toggleDiagnostics(false);
  }
}

function bindWellnessControls() {
  if (wellnessControlsBound) return;
  if (wellnessBtn && wellnessPanel) {
    wellnessBtn.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleWellness();
    });
    if (wellnessClose) {
      wellnessClose.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleWellness(false);
      });
    }
  }
  if (wellnessSensitivity) {
    wellnessSensitivity.addEventListener('change', (e) => {
      const val = e.target.value;
      const policyLabel = document.getElementById('wellnessPolicyLabel');
      if (policyLabel) {
        if (val === 'conservative') policyLabel.textContent = 'Conservative (4 cycles, 450s cooldown)';
        else if (val === 'sensitive') policyLabel.textContent = 'Sensitive (2 cycles, 180s cooldown)';
        else policyLabel.textContent = 'Balanced (3 cycles, 300s cooldown)';
      }
      wsSend({ type: 'set_wellness_sensitivity', sensitivity: val });
      showToast(`Wellness sensitivity set to ${val}`, 'success', 3000);
    });
  }
  if (wellnessMuteToggle) {
    wellnessMuteToggle.addEventListener('change', (e) => {
      wellnessMuted = e.target.checked;
      const badge = document.getElementById('interventionMutedBadge');
      if (badge) badge.hidden = !wellnessMuted;
      wsSend({ type: 'set_wellness_mute', muted: wellnessMuted });
      showToast(wellnessMuted ? 'Wellness alerts muted' : 'Wellness alerts active', wellnessMuted ? 'warning' : 'success', 3000);
    });
  }
  const researchOptInToggle = $('researchOptInToggle');
  if (researchOptInToggle) {
    researchOptInToggle.addEventListener('change', (e) => {
      const enabled = e.target.checked;
      wsSend({ type: 'set_research_opt_in', enabled });
      showToast(
        enabled
          ? 'Research Mode enabled: search queries may contact external frontier API'
          : 'Research Mode disabled: 100% on-device operation',
        enabled ? 'warning' : 'success',
        4000
      );
    });
  }
  wellnessControlsBound = true;
}

// ── Waveform & Sparkline Visualizers ──
let analyser, micSource;
const BAR_COUNT = 40;
const BAR_GAP = 3;
let waveformRAF;
let ambientPhase = 0;
let sparklinePhase = 0;

function initSparkline() {
  if (!voiceSparklineCanvas || !voiceSparklineCtx) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = voiceSparklineCanvas.getBoundingClientRect();
  const w = rect.width || 140;
  const h = rect.height || 48;
  voiceSparklineCanvas.width = w * dpr;
  voiceSparklineCanvas.height = h * dpr;
  voiceSparklineCtx.setTransform(1, 0, 0, 1, 0, 0);
  voiceSparklineCtx.scale(dpr, dpr);
}

function drawSparkline() {
  if (!voiceSparklineCanvas || !voiceSparklineCtx) return;
  const rect = voiceSparklineCanvas.getBoundingClientRect();
  const w = rect.width || 140;
  const h = rect.height || 48;
  if (w <= 0 || h <= 0) return;

  voiceSparklineCtx.clearRect(0, 0, w, h);

  const grad = voiceSparklineCtx.createLinearGradient(0, 0, w, 0);
  grad.addColorStop(0, '#38bdf8');
  grad.addColorStop(0.5, '#818cf8');
  grad.addColorStop(1, '#c084fc');

  voiceSparklineCtx.beginPath();
  voiceSparklineCtx.strokeStyle = grad;
  voiceSparklineCtx.lineWidth = 2.0;
  voiceSparklineCtx.lineCap = 'round';
  voiceSparklineCtx.lineJoin = 'round';
  voiceSparklineCtx.shadowColor = 'rgba(129, 140, 248, 0.6)';
  voiceSparklineCtx.shadowBlur = 6;

  const midY = h / 2;

  if (demoModeActive) {
    sparklinePhase += 0.045;
    const points = 24;
    const step = w / (points - 1);
    for (let i = 0; i < points; i++) {
      const x = i * step;
      const s1 = Math.sin(sparklinePhase + i * 0.38);
      const s2 = Math.sin(sparklinePhase * 1.6 + i * 0.75) * 0.55;
      const wave = (s1 + s2) * (h * 0.32);
      const taper = Math.sin((i / (points - 1)) * Math.PI);
      const y = midY + wave * taper;
      if (i === 0) voiceSparklineCtx.moveTo(x, y);
      else voiceSparklineCtx.lineTo(x, y);
    }
  } else if (analyser && state !== 'muted' && (state === 'listening' || state === 'speaking')) {
    const binCount = analyser.frequencyBinCount;
    const data = new Uint8Array(binCount);
    analyser.getByteFrequencyData(data);

    let maxVal = 0;
    for (let i = 0; i < 48; i++) {
      if (data[i] > maxVal) maxVal = data[i];
    }

    if (maxVal < 6) {
      // Flat baseline when muted or idle / no acoustic activity
      voiceSparklineCtx.moveTo(0, midY);
      voiceSparklineCtx.lineTo(w, midY);
    } else {
      const points = 24;
      const step = w / (points - 1);
      for (let i = 0; i < points; i++) {
        const x = i * step;
        const binIndex = Math.floor((i / points) * (binCount * 0.5));
        const normVal = (data[binIndex] || 0) / 255.0;
        const taper = Math.sin((i / (points - 1)) * Math.PI);
        const wave = normVal * (h * 0.45) * taper;
        const y = midY - wave;
        if (i === 0) voiceSparklineCtx.moveTo(x, y);
        else voiceSparklineCtx.lineTo(x, y);
      }
    }
  } else {
    // Flat baseline when muted, idle, or uninitialized
    voiceSparklineCtx.moveTo(0, midY);
    voiceSparklineCtx.lineTo(w, midY);
  }
  voiceSparklineCtx.stroke();
  voiceSparklineCtx.shadowBlur = 0;
}

function initWaveformCanvas() {
  if (!waveformCanvas || !waveformCtx) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = waveformCanvas.getBoundingClientRect();
  waveformCanvas.width = rect.width * dpr;
  waveformCanvas.height = rect.height * dpr;
  waveformCtx.setTransform(1, 0, 0, 1, 0, 0);
  waveformCtx.scale(dpr, dpr);
}

function drawWaveform() {
  if (!waveformCanvas || !waveformCtx) return;
  const { width: w, height: h } = waveformCanvas.getBoundingClientRect();
  waveformCtx.clearRect(0, 0, w, h);

  const barWidth = (w - (BAR_COUNT - 1) * BAR_GAP) / BAR_COUNT;
  waveformCtx.fillStyle = (STATE_COLORS[state] || STATE_COLORS.loading)[0];

  let dataArray = null;
  if (analyser && state !== 'muted') {
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
  }

  for (let i = 0; i < BAR_COUNT; i++) {
    let amplitude = 0.01;
    if (demoModeActive) {
      ambientPhase += 0.001;
      const s = Math.sin(ambientPhase * 3 + i * 0.35) * 0.5 + 0.5;
      amplitude = 0.12 + s * 0.65;
    } else if (dataArray && state !== 'muted') {
      const binIndex = Math.floor((i / BAR_COUNT) * dataArray.length * 0.6);
      const raw = dataArray[binIndex] / 255.0;
      amplitude = raw > 0.02 ? raw : 0.01;
    } else {
      amplitude = 0.01;
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
  drawSparkline();
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

let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 8;
const BASE_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 12000;
let reconnectTimer = null;

function connect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
  // Windows IPv6 fallback: resolve 'localhost' to IPv4 loopback '127.0.0.1' to prevent [::1] connection timeouts
  const wsHost = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? `127.0.0.1:${location.port || '8000'}`
    : location.host;

  ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);
  ws.onopen = () => {
    reconnectAttempts = 0;
    setStatus('connected', 'Connected');
    wsSend({ type: 'get_system_status' });
    if (state !== 'loading') setState('listening');
    updateDiagnostics();
    // Dismiss any stale reconnection warning toasts
    if (toastContainer) {
      Array.from(toastContainer.querySelectorAll('.toast-banner')).forEach(t => {
        const txt = t.textContent || '';
        if (txt.includes('Disconnected') || txt.includes('reconnecting') || txt.includes('WebSocket connection error')) {
          t.remove();
        }
      });
    }
  };
  ws.onerror = (err) => {
    updateDiagnostics();
    console.warn('[WS ERROR]', err);
    // Suppress separate toast here — onclose immediately handles user notification
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
      showToast('Connection rejected: Another session is active in another tab. Please close other Parlor tabs and reload.', 'error', 0);
      console.warn('[SINGLE SESSION POLICY] Connection closed (code 4001): another tab is active.');
      return; // Do NOT auto-reconnect in a loop
    }
    if (evt && evt.code === 1011) {
      setStatus('disconnected', 'Server Error');
      setState('muted');
      updateDiagnostics();
      showToast('Server initialization failed: llama-server or model unavailable. Check server console and .env configuration.', 'error', 0);
      showModelUnavailableMessage('The assistant engine (llama-server) or quantized model weights failed to initialize. Please check server configuration.');
      console.warn('[SERVER INIT ERROR] Connection closed (code 1011): server model load failed.');
      return; // Stop retrying on fatal server configuration failure
    }

    reconnectAttempts++;
    if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
      setStatus('disconnected', 'Connection Failed');
      updateDiagnostics();
      showToast('Could not connect to Parlor server after multiple attempts. Please ensure start.ps1 or Launch-Parlor.ps1 is running.', 'error', 0);
      console.error(`[WS RECONNECT] Aborted after ${MAX_RECONNECT_ATTEMPTS} attempts.`);
      return;
    }

    const delay = Math.min(MAX_RECONNECT_DELAY_MS, Math.round(BASE_RECONNECT_DELAY_MS * Math.pow(1.5, reconnectAttempts - 1)));
    setStatus('disconnected', `Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
    updateDiagnostics();
    showToast(`Disconnected from server — reconnecting in ${(delay / 1000).toFixed(0)}s...`, 'warning', delay + 400);
    reconnectTimer = setTimeout(connect, delay);
  };
  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data);
    window.__wsReceivedMessages = window.__wsReceivedMessages || [];
    window.__wsReceivedMessages.push(msg);
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
    if (msg.type === 'system_status') {
      if (modelReadyVal) modelReadyVal.textContent = msg.model_name || 'Gemma 4 E2B (on-device)';
      if (schemaValidVal) schemaValidVal.textContent = msg.schema_version || 'Diagnostics schema v1.0';
      if (baselineActiveVal) {
        baselineActiveVal.textContent = msg.baseline_mode || 'calibrating (0/60 s)';
      }
      const baselineIcon = $('baselineCheckIcon');
      if (baselineIcon) {
        if (msg.baseline_active) {
          baselineIcon.textContent = '✓';
          baselineIcon.className = 'check-icon';
        } else {
          baselineIcon.textContent = '⚪';
          baselineIcon.className = 'check-icon neutral';
        }
      }
      if (privateStateVal) privateStateVal.textContent = 'All processing on this device';
      return;
    }
    if (msg.type === 'wellness_snoozed') {
      startSnoozeCountdown(msg.minutes || 10);
      showToast(`Interventions snoozed for ${msg.minutes || 10} minutes`, 'warning', 4000);
      return;
    }
    if (msg.type === 'wellness_face_metrics') {
      if (!demoModeActive) updateFaceMetrics(msg.face || {});
      return;
    }
    if (msg.type === 'wellness_vocal_metrics') {
      if (!demoModeActive) updateVocalMetrics(msg.vocal || {});
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
    } else if (msg.type === 'research_opt_in_changed') {
      const toggle = $('researchOptInToggle');
      if (toggle) {
        toggle.checked = Boolean(msg.enabled);
        // If the server reports no API key is configured, disable the toggle
        // and update the sublabel so the user knows why it stays off.
        const configured = msg.configured !== false; // absent → assume configured (back-compat)
        toggle.disabled = !configured;
        const row = toggle.closest('.diag-row') || toggle.parentElement;
        const sublabel = row && row.querySelector('.diag-sublabel');
        if (sublabel) {
          sublabel.textContent = configured
            ? 'Sends spoken queries to external API for live web answers (Off by default)'
            : 'No API key configured — research mode unavailable';
        }
      }
    }
  };
}

// ── Streamed assistant message helpers ──
const LOADING_DOTS = '<span class="loading-dots"><span></span><span></span><span></span></span>';
let currentAssistantEl = null;
let currentAssistantBodyEl = null;

function updateConversationCount() {
  if (!msgCountBadge || !messagesDiv) return;
  const count = messagesDiv.querySelectorAll('.msg').length;
  msgCountBadge.textContent = `${count} ${count === 1 ? 'message' : 'messages'}`;
}

function appendAssistantText(text) {
  if (!currentAssistantEl) {
    currentAssistantEl = document.createElement('div');
    currentAssistantEl.className = 'msg assistant';
    currentAssistantEl.innerHTML = '<div class="assistant-avatar" aria-hidden="true"></div><div class="msg-content"><span class="body"></span></div>';
    currentAssistantBodyEl = currentAssistantEl.querySelector('.body');
    messagesDiv.appendChild(currentAssistantEl);
    updateConversationCount();
  }
  currentAssistantBodyEl.textContent += text;
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function setAssistantMeta(text) {
  if (!currentAssistantEl) return;
  const target = currentAssistantEl.querySelector('.msg-content') || currentAssistantEl;
  let meta = target.querySelector('.meta');
  if (!meta) {
    meta = document.createElement('div');
    meta.className = 'meta';
    target.appendChild(meta);
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
  updateConversationCount();
}

// One pending bubble per utterance-group: a continuation after a hold (or a
// flush) belongs to the same bubble the first segment created. The base
// meta ('with camera') is kept in dataset so later info can extend it.
function addUserLoadingBubble(meta = '') {
  if (pendingUserBubble()) return;
  addMessage('user', LOADING_DOTS, meta).dataset.base = meta;
  updateConversationCount();
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
  const body = bubble.querySelector('.body') || bubble;
  body.textContent = transcription || '…';
  setBubbleMeta(bubble, '');
  updateConversationCount();
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
  const placeholder = $('cameraPlaceholder');
  const placeholderTitle = $('placeholderTitle');
  const placeholderSubtext = $('placeholderSubtext');

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: VIDEO_CONSTRAINTS, audio: AUDIO_CONSTRAINTS,
    });
    video.srcObject = mediaStream;
    cameraEnabled = true;
    if (placeholder) placeholder.classList.add('hidden');
  } catch (e) {
    console.warn('Video+audio getUserMedia failed, attempting audio-only fallback:', e.message);
    cameraEnabled = false;
      updateFaceRailStatus();
    if (placeholder) {
      placeholder.classList.remove('hidden');
      if (placeholderTitle) placeholderTitle.textContent = 'Camera Inactive (Voice Mode)';
      if (placeholderSubtext) placeholderSubtext.textContent = 'Continuing in voice-only mode. Click "Camera On" below or allow webcam access in your browser settings to enable stress monitoring.';
    }
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: AUDIO_CONSTRAINTS });
      showToast('Camera unavailable or permission denied — continuing in audio-only mode', 'warning', 6000);
    } catch (audioErr) {
      console.error('Audio-only getUserMedia failed:', audioErr.message);
      setStatus('disconnected', 'Mic Access Denied');
      setState('muted');
      updateDiagnostics();
      if (placeholder) {
        placeholder.classList.remove('hidden');
        if (placeholderTitle) placeholderTitle.textContent = 'Microphone Access Required';
        if (placeholderSubtext) placeholderSubtext.textContent = 'Microphone permission was denied. Please allow microphone access in your browser settings to speak with Parlor.';
      }
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
  const targetWidth = Math.min(640, video.videoWidth);
  const scale = targetWidth / video.videoWidth;
  canvas.width = targetWidth;
  canvas.height = Math.round(video.videoHeight * scale);
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
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
  addUserLoadingBubble('');
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
  if (role === 'assistant') {
    div.innerHTML = `<div class="assistant-avatar" aria-hidden="true"></div><div class="msg-content"><span class="body">${text}</span>${meta ? `<div class="meta">${meta}</div>` : ''}</div>`;
  } else {
    div.innerHTML = `<div class="body">${text}</div>${meta ? `<div class="meta">${meta}</div>` : ''}`;
  }
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  updateConversationCount();
  return div;
}

$('modeStop').addEventListener('click', () => {
  stopPlayback();
  wsSend({ type: 'set_mode', mode: 'conversation' });
  goListening();
});

cameraToggle.addEventListener('click', () => {
  cameraEnabled = !cameraEnabled;
  if (!cameraEnabled && demoModeActive) {
    updateFaceMetrics(DEMO_DIAGNOSTICS.face, true);
  } else if (!cameraEnabled) {
    clearFaceMetrics();
  }
  cameraToggle.classList.toggle('active', cameraEnabled);
  cameraToggle.innerHTML = cameraEnabled
    ? '<span class="ctrl-icon">📷</span><span>Camera On</span>'
    : '<span class="ctrl-icon">🚫</span><span>Camera Off</span>';
  video.style.opacity = cameraEnabled ? 1 : 0.2;
  const placeholder = $('cameraPlaceholder');
  const placeholderTitle = $('placeholderTitle');
  const placeholderSubtext = $('placeholderSubtext');
  if (placeholder) {
    if (!cameraEnabled) {
      placeholder.classList.remove('hidden');
      if (placeholderTitle) placeholderTitle.textContent = 'Camera Off';
      if (placeholderSubtext) placeholderSubtext.textContent = 'Webcam monitoring paused by user. Click "Camera On" to resume.';
    } else if (mediaStream && mediaStream.getVideoTracks().length) {
      placeholder.classList.add('hidden');
    }
  }
  if (videoLiveBadge) {
    if (!cameraEnabled) {
      videoLiveBadge.classList.add('off');
      const text = videoLiveBadge.querySelector('.badge-text');
      if (text) text.textContent = 'Camera Off';
    } else {
      videoLiveBadge.classList.remove('off');
      const text = videoLiveBadge.querySelector('.badge-text');
      if (text) text.textContent = landmarksVisible ? 'Face landmarks · live' : 'Face landmarks · hidden';
    }
  }
  updateFaceRailStatus();
});

function setViewTab(tab) {
  const isDiag = tab === 'diagnostics';
  if (viewDiagnosticsBtn) {
    viewDiagnosticsBtn.classList.toggle('active', isDiag);
    viewDiagnosticsBtn.setAttribute('aria-selected', String(isDiag));
  }
  if (viewWellnessBtn) {
    viewWellnessBtn.classList.toggle('active', !isDiag);
    viewWellnessBtn.setAttribute('aria-selected', String(!isDiag));
  }
  if (diagnosticsRail) diagnosticsRail.hidden = !isDiag;
  if (wellnessRail) wellnessRail.hidden = isDiag;
}

function bindViewSwitcher() {
  if (viewWellnessBtn) {
    viewWellnessBtn.addEventListener('click', () => setViewTab('wellness'));
  }
  if (viewDiagnosticsBtn) {
    viewDiagnosticsBtn.addEventListener('click', () => setViewTab('diagnostics'));
  }
}

function bindQuickControls() {
  if (videoLiveBadge) {
    videoLiveBadge.addEventListener('click', () => {
      landmarksVisible = !landmarksVisible;
      const text = videoLiveBadge.querySelector('.badge-text');
      if (text) text.textContent = landmarksVisible ? 'Face landmarks · live' : 'Face landmarks · hidden';
      videoLiveBadge.classList.toggle('off', !landmarksVisible);
      if (!landmarksVisible) {
        clearLandmarkOverlay();
      } else if (demoModeActive) {
        drawLandmarkOverlay(DEMO_DIAGNOSTICS.face.mesh_points);
      }
    });
  }

  if (micBtn) {
    micBtn.addEventListener('click', () => {
      if (!mediaStream) {
        showToast('Microphone not initialized', 'warning');
        return;
      }
      const tracks = mediaStream.getAudioTracks();
      if (!tracks.length) return;
      const willEnable = !tracks[0].enabled;
      tracks.forEach(t => t.enabled = willEnable);
      micBtn.classList.toggle('muted', !willEnable);
      if (willEnable) {
        setState('listening');
        showToast('Microphone active', 'success', 2000);
      } else {
        setState('muted');
        showToast('Microphone muted', 'warning', 2000);
      }
      updateDiagnostics();
      updateVocalMetrics(demoModeActive ? DEMO_DIAGNOSTICS.vocal : {});
    });
  }

  if (wellnessSensitivityQuick && wellnessSensitivity) {
    wellnessSensitivityQuick.value = wellnessSensitivity.value;
    wellnessSensitivityQuick.addEventListener('change', (e) => {
      wellnessSensitivity.value = e.target.value;
      wellnessSensitivity.dispatchEvent(new Event('change'));
    });
    wellnessSensitivity.addEventListener('change', (e) => {
      wellnessSensitivityQuick.value = e.target.value;
    });
  }

  if (wellnessMuteToggleQuick && wellnessMuteToggle) {
    wellnessMuteToggleQuick.checked = wellnessMuteToggle.checked;
    wellnessMuteToggleQuick.addEventListener('change', (e) => {
      wellnessMuteToggle.checked = e.target.checked;
      wellnessMuteToggle.dispatchEvent(new Event('change'));
    });
    wellnessMuteToggle.addEventListener('change', (e) => {
      wellnessMuteToggleQuick.checked = e.target.checked;
    });
  }

  if (startExerciseQuick) {
    startExerciseQuick.addEventListener('click', () => {
      startBreathingExercise(120);
    });
  }
}

function initStarterConversation() {
  if (!messagesDiv || messagesDiv.children.length > 0) {
    updateConversationCount();
    return;
  }
  addMessage('assistant', "I'm here if you need anything else.");
  addMessage('user', "Can we do a short reset?");
  addMessage('assistant', "Sure. Let's take a two-minute breathing reset.");
  updateConversationCount();
}

let nonLocalRequestCount = 0;

function initPrivacyObserver() {
  if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          try {
            const url = new URL(entry.name);
            const isLocal = url.hostname === 'localhost' ||
                            url.hostname === '127.0.0.1' ||
                            url.hostname === '0.0.0.0' ||
                            url.hostname === '::1' ||
                            url.hostname === window.location.hostname;
            if (!isLocal) {
              nonLocalRequestCount++;
              updatePrivacyBadge();
            }
          } catch (_) {}
        }
      });
      observer.observe({ type: 'resource', buffered: true });
    } catch (_) {}
  }
}

function updatePrivacyBadge() {
  const privateEl = $('privateStateVal');
  if (privateEl) {
    if (nonLocalRequestCount === 0) {
      privateEl.textContent = 'Non-local requests: 0 (100% on-device)';
    } else {
      privateEl.textContent = `External requests: ${nonLocalRequestCount}`;
    }
  }
}

function initFreshnessWatcher() {
  setInterval(() => {
    if (!demoModeActive) {
      // Face freshness check (< 2.0s)
      const faceLiveTag = $('faceLiveTag') || $('diagFaceLiveStatus');
      if (faceLiveTag) {
        const isLive = lastFaceSnapshotAt > 0 && (Date.now() - lastFaceSnapshotAt < 2000);
        faceLiveTag.className = isLive ? 'diag-badge live' : 'diag-badge idle';
        faceLiveTag.innerHTML = `<span class="badge-dot"></span> ${isLive ? 'LIVE' : 'IDLE'}`;
        if (!isLive) {
          clearLandmarkOverlay();
          if (faceEmptyState) faceEmptyState.hidden = false;
          if (faceMiniCanvas) faceMiniCanvas.hidden = true;
        }
      }
      // Voice freshness check (< 2.0s)
      const voiceLiveTag = $('voiceLiveTag');
      if (voiceLiveTag) {
        const isLive = lastVoiceSnapshotAt > 0 && (Date.now() - lastVoiceSnapshotAt < 2000);
        voiceLiveTag.className = isLive ? 'diag-badge live' : 'diag-badge idle';
        voiceLiveTag.innerHTML = `<span class="badge-dot"></span> ${isLive ? 'LIVE' : 'IDLE'}`;
      }
    }
  }, 500);
}

// ── Init ──
async function init() {
  initWaveformCanvas();
  initSparkline();
  initLandmarkCanvas();
  initPrivacyObserver();
  initFreshnessWatcher();

  const handleResize = () => {
    initWaveformCanvas();
    initSparkline();
    initLandmarkCanvas();
  };
  window.addEventListener('resize', handleResize);

  bindViewSwitcher();
  bindQuickControls();
  bindDiagnosticsControls();
  bindWellnessControls();
  bindDemoModeControls();
  initStarterConversation();

  // Initial state: Start clean with uninitialized/idle markers ('—') unless Demo mode is already on
  if (demoModeActive) {
    updateFaceMetrics(DEMO_DIAGNOSTICS.face, true);
    updateVocalMetrics(DEMO_DIAGNOSTICS.vocal, true);
  } else {
    clearFaceMetrics();
    clearVocalMetrics();
  }

  connect(); // Establish WebSocket connection immediately — do not wait for camera permission
  bindDiagnosticsControls();
  await startCamera();

  if (mediaStream && mediaStream.getAudioTracks().length) {
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
      onnxWASMBasePath: "/static/vendor/",
      baseAssetPath: "/static/vendor/",
    });
    myvad.start();
  } catch (e) {
    console.error('VAD init failed:', e);
    showToast('Failed to initialize VAD engine', 'error');
  }
} else {
  updateDiagnostics();
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

let wellnessMuted = false;
let exerciseTimerInterval = null;
let exerciseTimeRemaining = 120;

function playWellnessChime() {
  if (wellnessMuted) return;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880.00, ctx.currentTime + 0.18); // A5
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.45);
  } catch (e) {
    // AudioContext autoplay restrictions or disabled audio
  }
}

let demoModeActive = false;
let demoModeInterval = null;

const DEMO_VECTOR_B07_V10 = {
  window_samples: 5,
  face_detected: true,
  au04_brow_furrow: 0.98,
  au07_lid_tightener: 0.95,
  au15_lip_depressor: 0.65,
  au20_lip_stretcher: 0.60,
  ear: 0.22,
  head_pitch: 0.0,
  head_yaw: 0.0,
  head_roll: 0.0,
  face_confidence: 0.98,
  speech_detected: true,
  rms_energy: 0.08,
  f0_mean_hz: 212.0,
  f0_baseline_hz: 120.0,
  f0_delta_hz: 92.0,
  f0_std_hz: 38.0,
  jitter_local_pct: 5.6,
  shimmer_local_pct: 6.8,
  pause_ratio: 0.35,
  vocal_tension_index: 0.95
};

function bindDemoModeControls() {
  const demoToggle = document.getElementById('demoModeToggle');
  const simBadge = document.getElementById('simulatedInputBadge');
  if (!demoToggle) return;

  const onToggle = () => {
    demoModeActive = Boolean(demoToggle.checked);
    if (simBadge) simBadge.hidden = !demoModeActive;
    if (diagFaceDemoBadge) diagFaceDemoBadge.hidden = !demoModeActive;
    if (diagVoiceDemoBadge) diagVoiceDemoBadge.hidden = !demoModeActive;
    if (diagReasonerDemoBadge) diagReasonerDemoBadge.hidden = !demoModeActive;

    if (demoModeActive) {
      updateFaceMetrics(DEMO_DIAGNOSTICS.face, true);
      updateVocalMetrics(DEMO_DIAGNOSTICS.vocal, true);
    } else {
      clearFaceMetrics();
      updateVocalMetrics({});
      updateFaceRailStatus();
    }

    wsSend({ type: 'set_demo_mode', enabled: demoModeActive });

    if (demoModeActive) {
      console.warn('[DEMO MODE] Activated: injecting SIMULATED INPUT stress vector (B07_V10)');
      showToast('Demo Mode ON: injecting simulated stress biomarkers', 'warning', 4000);
      wsSend({ type: 'test_wellness_cycle', vector: DEMO_VECTOR_B07_V10, is_simulated: true });
      if (demoModeInterval) clearInterval(demoModeInterval);
      demoModeInterval = setInterval(() => {
        if (demoModeActive && wsOpen()) {
          console.log('[DEMO MODE] Injecting periodic simulated stress vector...');
          wsSend({ type: 'test_wellness_cycle', vector: DEMO_VECTOR_B07_V10, is_simulated: true });
        }
      }, 8000);
    } else {
      console.log('[DEMO MODE] Deactivated: returning to live sensor stream');
      showToast('Demo Mode OFF: live sensor monitoring restored', 'success', 3000);
      if (demoModeInterval) {
        clearInterval(demoModeInterval);
        demoModeInterval = null;
      }
    }
  };

  demoToggle.addEventListener('change', onToggle);
  demoToggle.addEventListener('click', onToggle);
}

function showInterventionCard(data) {
  if (!data) return;
  const card = document.getElementById('interventionCard');
  if (!card) return;

  document.getElementById('interventionIcon').textContent = data.icon || '🫁';
  document.getElementById('interventionTitle').textContent = data.title || 'Micro-Intervention';
  document.getElementById('interventionCategory').textContent = data.category || 'Wellness';
  document.getElementById('interventionNote').textContent = data.personalized_note || 'Sustained stress biomarkers detected across observation windows.';

  const mutedBadge = document.getElementById('interventionMutedBadge');
  if (mutedBadge) mutedBadge.hidden = !wellnessMuted;

  const simCardBadge = document.getElementById('interventionSimulatedBadge');
  if (simCardBadge) {
    simCardBadge.hidden = !(demoModeActive || data.is_simulated || data.simulated);
  }

  // Render Driver Chips
  const chipsContainer = document.getElementById('interventionChips');
  if (chipsContainer) {
    chipsContainer.innerHTML = '';
    const drivers = data.slm_drivers || data.primary_drivers || [];
    const driverList = Array.isArray(drivers) ? drivers : [drivers];
    driverList.forEach(driver => {
      const chip = document.createElement('span');
      chip.className = 'driver-chip';
      chip.textContent = driver;
      chipsContainer.appendChild(chip);
    });
  }

  const stepsUl = document.getElementById('interventionSteps');
  stepsUl.innerHTML = '';
  (data.steps || []).forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    stepsUl.appendChild(li);
  });

  const reasoningDiv = document.getElementById('interventionReasoning');
  const driversStr = (data.slm_drivers || data.primary_drivers || []).join(', ');
  reasoningDiv.innerHTML = `
    <div><strong>Model Reasoning:</strong> ${data.slm_reasoning || data.explainable_reasoning || 'Elevated facial tension and acoustic frequency perturbation.'}</div>
    <div style="margin-top:4px;"><strong>Assessment Tier:</strong> ${data.stress_level || 'High (Tier 2)'} (Confidence: ${data.confidence_score || '0.98'})</div>
    <div style="margin-top:4px;"><strong>Biomarkers Detected:</strong> ${driversStr || 'AU04 Brow Furrow=0.98, Pitch Delta=+92.0Hz, Vocal Tension=0.95'}</div>
  `;

  const actionBtn = document.getElementById('interventionAction');
  actionBtn.textContent = 'Start Exercise';

  card.hidden = false;
  playWellnessChime();
}

function hideInterventionCard() {
  const card = document.getElementById('interventionCard');
  if (card) card.hidden = true;
}

function startBreathingExercise(durationSec = 120) {
  hideInterventionCard();
  const exCard = document.getElementById('exerciseCard');
  if (!exCard) return;

  exCard.hidden = false;
  exerciseTimeRemaining = durationSec;

  const timerEl = document.getElementById('exerciseTimer');
  const phaseEl = document.getElementById('breathingPhase');
  const pacerEl = document.getElementById('breathingPacer');
  const cycleEl = document.getElementById('exerciseCycleNum');

  if (exerciseTimerInterval) clearInterval(exerciseTimerInterval);

  function updateVisuals(secRemaining) {
    const mins = Math.floor(secRemaining / 60);
    const secs = secRemaining % 60;
    if (timerEl) timerEl.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    const elapsed = durationSec - secRemaining;
    const cycle = Math.floor(elapsed / 16) + 1;
    if (cycleEl) cycleEl.textContent = Math.min(cycle, 7);

    const phase = Math.floor((elapsed % 16) / 4);
    if (phase === 0) {
      if (phaseEl) phaseEl.textContent = 'Inhale (4s)';
      if (pacerEl) pacerEl.className = 'breathing-circle inhale';
    } else if (phase === 1) {
      if (phaseEl) phaseEl.textContent = 'Hold (4s)';
      if (pacerEl) pacerEl.className = 'breathing-circle hold';
    } else if (phase === 2) {
      if (phaseEl) phaseEl.textContent = 'Exhale (4s)';
      if (pacerEl) pacerEl.className = 'breathing-circle exhale';
    } else {
      if (phaseEl) phaseEl.textContent = 'Hold (4s)';
      if (pacerEl) pacerEl.className = 'breathing-circle hold';
    }
  }

  updateVisuals(exerciseTimeRemaining);

  exerciseTimerInterval = setInterval(() => {
    exerciseTimeRemaining--;
    if (exerciseTimeRemaining <= 0) {
      stopBreathingExercise();
      showToast('2-Minute Box Breathing completed! Well done.', 'success', 4000);
      return;
    }
    updateVisuals(exerciseTimeRemaining);
  }, 1000);
}

function stopBreathingExercise() {
  if (exerciseTimerInterval) {
    clearInterval(exerciseTimerInterval);
    exerciseTimerInterval = null;
  }
  const exCard = document.getElementById('exerciseCard');
  if (exCard) exCard.hidden = true;
}

let snoozeCountdownTimer = null;
let snoozeRemainingSec = 0;

function startSnoozeCountdown(minutes = 10) {
  snoozeRemainingSec = Math.round(minutes * 60);
  if (snoozeCountdownTimer) clearInterval(snoozeCountdownTimer);
  updateSnoozeButtonLabel();
  snoozeCountdownTimer = setInterval(() => {
    snoozeRemainingSec--;
    if (snoozeRemainingSec <= 0) {
      clearInterval(snoozeCountdownTimer);
      snoozeCountdownTimer = null;
      updateSnoozeButtonLabel();
      showToast('Snooze period ended. Alerts active.', 'ok', 3000);
    } else {
      updateSnoozeButtonLabel();
    }
  }, 1000);
}

function updateSnoozeButtonLabel() {
  const snoozeBtn = document.getElementById('interventionSnooze');
  if (!snoozeBtn) return;
  if (snoozeRemainingSec > 0) {
    const mins = Math.floor(snoozeRemainingSec / 60);
    const secs = snoozeRemainingSec % 60;
    const pad = (n) => n.toString().padStart(2, '0');
    snoozeBtn.textContent = `Snoozed (${pad(mins)}:${pad(secs)})`;
    snoozeBtn.classList.add('snoozed');
  } else {
    snoozeBtn.textContent = 'Snooze 10m';
    snoozeBtn.classList.remove('snoozed');
  }
}

function updateBaselineUI(baseline) {
  if (!baseline) return;
  const el = $('baselineActiveVal');
  const icon = $('baselineCheckIcon');
  if (baseline.calibrated) {
    if (el) {
      el.textContent = 'Personal baseline (local)';
      el.className = 'verify-val ok';
    }
    if (icon) {
      icon.textContent = '✓';
      icon.className = 'check-icon';
    }
  } else {
    if (el) {
      el.textContent = baseline.status || 'calibrating (0/60 s)';
      el.className = 'verify-val neutral';
    }
    if (icon) {
      icon.textContent = '⚪';
      icon.className = 'check-icon neutral';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  bindDiagnosticsControls();
  bindWellnessControls();
  bindDemoModeControls();
  setInterval(updateFaceRailStatus, 3000);

  const closeBtn = document.getElementById('interventionClose');
  if (closeBtn) closeBtn.addEventListener('click', hideInterventionCard);

  const actionBtn = document.getElementById('interventionAction');
  if (actionBtn) actionBtn.addEventListener('click', () => {
    startBreathingExercise(120);
  });

  const exClose = document.getElementById('exerciseClose');
  if (exClose) exClose.addEventListener('click', stopBreathingExercise);

  const exFinish = document.getElementById('exerciseFinish');
  if (exFinish) exFinish.addEventListener('click', () => {
    stopBreathingExercise();
    showToast('Exercise completed.', 'success', 3000);
  });

  const snoozeBtn = document.getElementById('interventionSnooze');
  if (snoozeBtn) snoozeBtn.addEventListener('click', () => {
    wsSend({ type: 'snooze_wellness', minutes: 10 });
    startSnoozeCountdown(10);
    showToast('Interventions snoozed for 10 minutes', 'warning', 4000);
    hideInterventionCard();
  });

  // Global Escape key dismisses modals, drawers, and intervention cards
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (typeof toggleDiagnostics === 'function') toggleDiagnostics(false);
      if (typeof toggleWellness === 'function') toggleWellness(false);
      hideInterventionCard();
      stopBreathingExercise();
    }
  });

  // Periodic wellness telemetry sender: stream camera frames every 8s while idle
  setInterval(() => {
    if (wsOpen() && cameraEnabled && !speechActive && state === 'listening') {
      const frame = captureFrame();
      if (frame) {
        wsSend({ type: 'wellness_telemetry', image: frame });
      }
    }
  }, 8000);
});

init();
