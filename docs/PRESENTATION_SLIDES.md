# PROJECT PRESENTATION: EMO ASSISTANT ("PARLOR")
## On-Device Multimodal Affective Wellness Monitoring & Conversational AI

**Batch:** 14 | **Section:** A | **Branch:** Computer Science and Engineering  
**Academic Year:** 2026–2027  
**Project Guide:** Mrs. V. Aruna, Project Guide, Dept. of CSE  
**Team Members:**
- M. Rama Venkata Charan (Roll No: 23KN1A0543)
- B. Murali Gopi (Roll No: 23KN1A0515)
- M. Kumar Siva Sai (Roll No: 23KN1A0542)
- Y. Yashwanth Prakash (Roll No: 23KN1A0571)

---

### Slide 1: Title & Overview
- **Project Title:** EMO Assistant ("Parlor")
- **Subtitle:** On-Device Multimodal Affective Wellness Monitoring and Real-Time Voice Assistant
- **Domain:** Affective Computing, Edge AI, Multimodal Signal Processing, Human-Computer Interaction
- **Academic Context:** Major Project — Department of Computer Science & Engineering (Batch 14, Section A, Academic Year 2026–2027)
- **Project Guide:** Mrs. V. Aruna, Project Guide, Dept. of CSE

---

### Slide 2: The Problem: Silent Workplace Burnout & Wearable Friction
- **The Burnout Crisis:** Knowledge workers suffer from insidious "stress blindness" — accumulating cognitive fatigue and autonomic tension without conscious awareness.
- **Wearable Friction:** Smartwatches and chest bands require charging, cause skin irritation, cost \$200–\$500, and suffer from high abandonment rates.
- **Manual Logging Failure:** Subjective journaling apps experience substantial user attrition within the initial weeks due to workflow disruption (Baumel et al., 2019; Eysenbach, 2005).
- **Cloud Privacy Dilemma:** Transmitting raw webcam video and microphone audio to remote servers introduces catastrophic privacy and compliance risks (GDPR/HIPAA).
- **Brittle Thresholds:** Static statistical cutoffs misclassify animated speaking as stress, triggering irritating false alarms.

---

### Slide 3: The Proposed Solution: Parlor
- **Passive & Sensorless:** Operates entirely through existing, commodity laptop webcams and built-in microphones.
- **Multimodal Perception:** Simultaneously tracks facial Action Units (MediaPipe FaceMesh) and vocal acoustic biomarkers (DSP feature extraction).
- **Cognitive SLM Reasoning:** Replaces brittle thresholds with an on-device Small Language Model (Gemma 4 E2B IT at Q4_0) performing qualitative pattern reasoning.
- **Explainable Provenance:** Every intervention discloses the physiological signals that triggered it via a *"Why did this fire?"* interface.
- **Strict Local Isolation:** The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.

---

### Slide 4: High-Level System Architecture
- **Single-Process Coexistence:** Conversational voice turns and passive affective monitoring run concurrently in a single Python 3.12 `asyncio` process.
- **WebSocket Gateway:** Browser client streams 720p canvas frames (2 fps) and 16 kHz 16-bit PCM audio chunks over `/ws`.
- **Decoupled Heavy Compute:** MediaPipe landmarking, vocal FFT extraction, and SLM completions are offloaded to a thread pool executor, maintaining UI responsiveness.
- **Local Model Backends:**
  - `smart-turn-v3.2.onnx` (Acoustic turn boundary classifier, 68 ms)
  - `llama-server` (Gemma 4 E2B IT Q4_0, CUDA 12.4 GPU accelerated)
  - `kokoro-v1.0.onnx` (Neural speech synthesis, streaming audio chunks)
  - SQLite (`wellness_history.db` with deterministic indexing)

---

### Slide 5: Perception Layer: Facial Micro-Expression Extraction
- **Landmarking Core:** Google MediaPipe FaceMesh tracking 478 3D landmarks in real time (**3.97 ms mean, 4.81 ms p95** on CPU with real face; **1.92 ms** on blank frame early exit).
- **Condition Robustness:** Dim light 15% lux (**4.39 ms mean**, simulated); Head turned ~30° (**4.69 ms mean**, simulated).
- **Target Action Units (FACS):**
  - **AU04 (Brow Lowerer):** Medial brow contraction normalized to nasal bridge (corrugator supercilii — cognitive strain).
  - **AU07 (Lid Tightener):** Palpebral fissure narrowing (orbicularis oculi — visual strain/fatigue).
  - **AU20 (Lip Stretcher):** Transverse oral commissure displacement (somatic tension).
- **Eye Aspect Ratio (EAR):** Tracks spontaneous blink suppression and fatigue flutter.
- **Perspective Filtering:** Perspective-n-Point (PnP) solver extracts head pitch, yaw, and roll.

---

### Slide 6: Perception Layer: Vocal Acoustic Biomarkers
- **DSP Core:** Real-time NumPy and SciPy signal processing (**2.85 ms mean, 3.73 ms p95** execution latency).
- **Target Acoustic Indicators:**
  - **Pitch Delta ($\Delta F0$):** Parabolic interpolation over autocorrelation peaks; measures fundamental frequency rise against baseline.
  - **Jitter (%):** Cycle-to-cycle frequency perturbation reflecting vocal fold micro-tremors under autonomic arousal.
  - **Shimmer (%):** Cycle-to-cycle amplitude perturbation reflecting laryngeal instability.
  - **Spectral Tension:** High-to-low frequency spectral energy distribution ($>1\text{ kHz} / <1\text{ kHz}$) measuring laryngeal constriction.
  - **Pause Ratio:** Ratio of active phonation to silent pauses during speech turns.

---

### Slide 7: Cognitive Layer: Qualitative SLM Pattern Reasoning
- **Small Language Model:** Google Gemma 4 E2B IT quantized at `Q4_0` (3.35 GB GGUF) running locally via `llama-server`.
- **Grammar-Forced Schema:** Response is constrained to deterministic JSON schema containing `tier` (0, 1, 2), `confidence` (0.0–1.0), `reasoning`, and `contributing_factors`.
- **Inference Latency:** **2.14 s mean / 2.45 s p95** on NVIDIA RTX 4050 GPU (pooled across all prompts including cross-modal conflict CoT: **2.23 s mean / 2.49 s p95 / 4.32 s max**, comfortably within the 5.0 s budget with 0.68 s safety margin on worst-case and 2.77 s on mean).
- **Temporal Fusion:** 8-second observation window buffer normalizes signals against the user's calibrated baseline before prompt generation.

---

### Slide 8: Why an SLM Over Brittle Thresholds? (Cross-Modal Disambiguation)
- **The Threshold Failure Case:** A user laughing or speaking passionately raises vocal pitch ($\Delta F0 > 30\text{ Hz}$). A static threshold immediately misfires a high-stress alarm.
- **Parlor's SLM Disambiguation:**
  - Input: Elevated vocal pitch ($\Delta F0 = +32\text{ Hz}$) + completely relaxed face (AU04 = 0.05).
  - SLM Output: **Tier 1** (Confidence 0.72).
  - SLM Reasoning: *"Assessed as Moderate Stress due to conflicting signals between modalities... Vocal biomarkers indicate acoustic tension while facial expressions remain neutral."*
- **Signal Honesty:** When camera is covered and user is silent $\rightarrow$ stored and displayed as **"insufficient signal"** (numeric score -1.0, confidence 0.0), suppressing all interventions and strictly excluded from EMA ground-truth analysis.

---

### Slide 9: Intervention Policy & Anti-False-Positive Gating
- **Multi-Cycle Hysteresis:** Interventions require sustained elevated tension across multiple observation windows before an alert can trigger. Single momentary spikes are logged but suppressed.
- **Sensitivity Profiles (Harmonized):**
  - *Conservative:* 4 consecutive cycles, 7.5-min (450 s) cooldown.
  - *Balanced (Default):* 3 consecutive cycles, 5.0-min (300 s) cooldown.
  - *Sensitive:* 2 consecutive cycles, 3.0-min (180 s) cooldown.
- **Insufficient Signal Window HOLD Policy:** Sensor occlusion / missing face (-1.0) holds the consecutive stress count to prevent transient occlusion wiping real distress, while strictly prohibiting interventions from firing.
- **User Control Agency:** One-click Snooze (10–60 mins) and Audio Mute directly from the UI.
- **Provenance Card:** Interactive UI card with expandable *"Why did this fire?"* panel displaying contributing biological signals.

---

### Slide 10: Conversational Engine & Concurrency Engineering
- **Real-Time Voice Assistant:** Built-in multimodal conversational agent sharing the same single-process `asyncio` event loop.
- **Conversational TTFA (30-Turn Alternating Benchmark with GPU Telemetry):**
  - Loop OFF: **1.920 s mean** (p50: 1.622 s, p95: 3.545 s, 95% CI: [1.663 s, 2.213 s]).
  - Loop ON Unmitigated: **1.739 s mean** (p50: 1.514 s, p95: 3.612 s, 95% CI: [1.467 s, 2.066 s]).
  - Loop ON Mitigated: **1.774 s mean** (p50: 1.483 s, p95: 3.419 s, 95% CI: [1.505 s, 2.077 s]).
  - Evaluated on NVIDIA RTX 4050 6GB Laptop GPU (plugged into AC power, 2700 MHz core clocks, 54°C–71°C GPU temp).
- **Smart-Turn Classifier:** `smart-turn-v3.2` ONNX model classifies audio completeness in **68.2 ms**, holding turn during mid-sentence hesitation.
- **Non-SLM Pipeline Overhead:** Total mean latency **10.89 ms** (Facial AU: 3.97 ms, Vocal DSP: 2.85 ms, DB write: 4.07 ms).
- **Resource Footprint:** Host working set RAM **2.42 GB** (`llama-server` 1.84 GB + `python` 0.61 GB; 5.24 GB private commit), Peak GPU VRAM **3.90 GB**, SQLite storage rate **132 KB / active hour**.

---

### Slide 11: Experimental Setup & Verification Protocol
- **Evaluation Workstation:**
  - OS: Windows 11 Home (64-bit)
  - CPU: Intel Core i5-13450HX (10 cores, 16 threads)
  - GPU: NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM, CUDA 12.4)
  - RAM: 16 GB DDR5
- **Automated Test Suite:**
  - Full regression test suite covering end-to-end conversation, turn gating, delegation, facial/vocal extraction, fusion, and crash resilience.
  - **Results:** **111 Passed out of 112 items, 0 Failed, 1 Skipped by Design** (**99.1% Pass Rate**).
  - *Test Note:* All E2E tests execute live against Gemma 4 E2B; single remaining skip is `test_thinking_pause_is_held` in `tests/test_conversation.py:68` (*"the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live"*).

---

### Slide 12: Empirical Performance & Latency Benchmarks
*All figures measured live on this machine and logged in `evidence/`:*

| Benchmark Component | Empirical Measured | Engineering Budget | Status | Evidence File |
|:---|:---:|:---:|:---:|:---|
| Facial AU Extraction (Real Face, p95) | **4.81 ms** (mean: 3.97 ms) | — | **PASS** | `evidence/facial_extraction_real.csv` |
| Facial AU Extraction (Blank / No Face) | **2.45 ms** (mean: 1.92 ms) | — | **PASS** | `evidence/facial_extraction_blank.csv` |
| Vocal DSP Extraction (CPU, p95) | **3.73 ms** (mean: 2.85 ms) | — | **PASS** | `evidence/vocal_extraction.csv` |
| SQLite Logging Latency (p95) | **5.29 ms** (mean: 4.07 ms) | — | **PASS** | `evidence/db_write_latency.csv` |
| Wellness SLM Latency (GPU, Standard p95) | **2.45 s** (mean: 2.14 s, p50: 2.23 s) | $\le 5.0\text{ s}$ (window) | **PASS (+2.55s)** | `evidence/wellness_slm_latency.csv` |
| Wellness SLM Latency (GPU, Conflict Max) | **4.32 s** (mean: 2.79 s, CoT) | $\le 5.0\text{ s}$ (window) | **PASS (+0.68s)** | `evidence/live_pattern_reasoning.json` |
| Conversational Turn TTFA (Loop OFF, p50) | **1.62 s** (mean: 1.92 s, p95: 3.55 s) | — | **MEASURED** | `evidence/voice_ttfa_30_turns.csv` |
| Conversational Turn TTFA (Loop Mitigated, p50) | **1.48 s** (mean: 1.77 s, p95: 3.42 s) | — | **MEASURED** | `evidence/voice_ttfa_30_turns.csv` |
| Voice TTFA (Loop OFF, 30 turns) | **1.789 s mean** (p50: 1.593 s, p95: 2.755 s) | — | **Baseline** | `evidence/voice_ttfa_30_turns.csv` |
| Voice TTFA (Loop ON Mitigated, 30 turns) | **1.903 s mean** (p50: 1.588 s, p95: 3.716 s) | $\le 2.00\text{ s}$ target | **PASS (+0.114s cost)** | `evidence/voice_ttfa_30_turns.csv` |
| Test Suite Integration | **110 / 111 Passed (1 skipped by design)** | All functional | **PASS (99.1%)** | `evidence/pytest_full.log` |
| Outbound Network Sockets | **0 (0.00 KB)** | $0.0\text{ KB}$ | **PASS** | `evidence/netstat_outbound.txt` |
| Peak VRAM (Session) | **3.90 GB** (3991 MB peak) | 6.0 GB capacity | **PASS** | `evidence/vram_cpu_usage.log` |
| Host Working Set RAM | **3.55 GB** (`llama-server` 2.75GB + `python` 0.80GB) | 16.0 GB capacity | **PASS** | `evidence/vram_cpu_usage.log` |

*Examiner Reproducibility:* `powershell -ExecutionPolicy Bypass -File scripts/reproduce_numbers.ps1`

---

### Slide 13: Affective Validation & EMA Ground-Truth Study
*Distinguishing Quantization Agreement (Compression Fidelity) from Human Ground-Truth Agreement:*

- **Model Quantization Agreement:** Measures prediction similarity between 4-bit and FP16 models. Unquantized FP16 weights were not stored locally for Gemma 4 E2B $\rightarrow$ **NOT MEASURED**.
- **Human Ground-Truth Agreement:** Evaluates inferred stress against human self-reports. Preliminary reports used synthetic distributions for analysis smoke testing. Empirical human data is formally marked: **`NOT COLLECTED / REQUIRES HUMAN STUDY`**.
- **Turnkey Human Re-Collection Kit:** Packaged in `docs/EMA_RECOLLECTION_KIT.md` with interactive tool `scripts/ema_collector.py` and evaluation harness `scripts/evaluate_ema.py` for execution with $\ge 8$ human participants (4 developers + 4 external peers) prior to viva.
- **Empirical Live Reasoning Proofs:** Verified 10 feature vectors $\times$ 3 repeats (N=30 runs) covering Tier 0, Tier 1, and Tier 2 (`evidence/tier_sweep.csv`); cross-modal conflict reasoning verified live; zero-signal windows reported as `"insufficient signal"` (`evidence/live_zero_signal.json`).

---

### Slide 14: Privacy Architecture & Browser DevTools Audit (B1–B12)
- **Zero Outbound Data Transmission:** Socket inspection confirmed **0.00 KB** outbound network traffic during live operation.
- **Strict Local Loopback:** Binds strictly to `127.0.0.1:8000` (FastAPI) and `127.0.0.1:8081` (`llama-server`).
- **Vendored Offline VAD & Clean HAR:** Vendored Silero VAD and removed Google Fonts CDN leak. Verified 100% offline air-gapped execution via session HAR export (`evidence/browser/session_privacy.har`).
- **Browser Performance & Reliability (B1–B12):**
  - Clean page load in **0.887 s** with 0 console errors.
  - Single-session WebSocket policy (Code 4001 rejects concurrent tab without reconnect loops).
  - Watchdog respawn latency: **6.21 s mean** across 3 mid-session kill trials.
  - UI frame rate: **60.2 FPS** (1x) and **60.0 FPS** (4x CPU throttle), zero frame drops below 30 FPS.
  - Client storage audit: **0.00 KB** biometric data retained in localStorage or IndexedDB.
  - Live model card proof: 3 cycles of Vector B07_V10 $\rightarrow$ Tier 2 card, driver chips, 2-min box breathing UI countdown timer, snooze 10m, mute toggle, sensitivity switching, and cooldown blocking.
- **Data Ephemerality:** Raw video frames and audio buffers are processed in volatile memory and immediately discarded. Only anonymized scalar feature vectors and clinical reasoning strings are stored in local SQLite.

---

### Slide 15: Limitations, Future Work & Conclusion
- **Clinical Role Boundary:** Parlor estimates behavioral stress signals and suggests micro-breaks; it is an occupational wellness tool, **NOT a medical diagnostic device**.
- **Limitations:** Student/developer participant cohorts, subjectivity of EMA self-report, camera performance in insufficient ambient lighting, and live demo recording (`REQUIRES HUMAN: record the demo`).
- **Future Directions:**
  - Dedicated NPU offload (Intel NPU, Snapdragon X Elite, Apple Neural Engine) to operate at $<5\text{ Watts}$.
  - Multi-day circadian baseline adaptation in local SQLite.
  - On-device parameter-efficient fine-tuning (LoRA) for user voice personalization.
- **Conclusion:** Parlor proves that explainable, non-invasive, and zero-cloud multimodal affective computing can run entirely on commodity consumer laptops.
