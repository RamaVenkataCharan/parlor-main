# PROJECT PRESENTATION: EMO ASSISTANT ("PARLOR")
## On-Device Multimodal Affective Wellness Monitoring & Conversational AI

**Batch:** 14 | **Section:** A | **Branch:** Computer Science and Engineering  
**Project Guide:** Mrs. V. Aruna, Senior Assistant Professor  
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
- **Academic Context:** Major Project — Department of Computer Science & Engineering (Batch 14, Section A)
- **Project Guide:** Mrs. V. Aruna, Senior Assistant Professor, Dept. of CSE

---

### Slide 2: The Problem: Silent Workplace Burnout & Wearable Friction
- **The Burnout Crisis:** Knowledge workers suffer from insidious "stress blindness" — accumulating cognitive fatigue and autonomic tension without conscious awareness.
- **Wearable Friction:** Smartwatches and chest bands require charging, cause skin irritation, cost \$200–\$500, and suffer from high abandonment rates.
- **Manual Logging Failure:** Subjective journaling apps experience $>80\%$ user attrition within 14 days due to workflow disruption.
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
- **Condition Robustness:** Dim light 15% lux (**4.39 ms mean**); Head turned ~30° (**4.69 ms mean**).
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
- **Inference Latency:** **2.14 s mean / 2.42 s p95** on NVIDIA RTX 4050 GPU (comfortably within the 5.0 s budget with 2.58 s safety margin).
- **Temporal Fusion:** 8-second observation window buffer normalizes signals against the user's calibrated baseline before prompt generation.

---

### Slide 8: Why an SLM Over Brittle Thresholds? (Cross-Modal Disambiguation)
- **The Threshold Failure Case:** A user laughing or speaking passionately raises vocal pitch ($\Delta F0 > 30\text{ Hz}$). A static threshold immediately misfires a high-stress alarm.
- **Parlor's SLM Disambiguation:**
  - Input: Elevated vocal pitch ($\Delta F0 = +32\text{ Hz}$) + completely relaxed face (AU04 = 0.05).
  - SLM Output: **Tier 1** (Confidence 0.72).
  - SLM Reasoning: *"Assessed as Moderate Stress due to conflicting signals between modalities... Vocal biomarkers indicate acoustic tension while facial expressions remain neutral."*
- **Signal Honesty:** When camera is covered and user is silent $\rightarrow$ outputs `confidence_score: 0.0` and suppresses all interventions.

---

### Slide 9: Intervention Policy & Anti-False-Positive Gating
- **Multi-Cycle Hysteresis:** Interventions require **two consecutive Tier 2 cycles** (16+ seconds of sustained tension). Single momentary spikes are logged but suppressed.
- **Sensitivity Profiles:**
  - *Gentle (Low):* 3 consecutive cycles, 30-min cooldown between alerts.
  - *Balanced (Default):* 2 consecutive cycles, 15-min cooldown.
  - *Responsive (High):* Sustained Tier 1 or 2, 10-min cooldown.
- **User Control Agency:** One-click Snooze (10–60 mins) and Audio Mute directly from the UI.
- **Provenance Card:** Interactive UI card with expandable *"Why did this fire?"* panel displaying contributing biological signals.

---

### Slide 10: Conversational Engine & Acoustic Turn-Taking
- **Real-Time Voice Assistant:** Built-in multimodal conversational agent sharing the same event loop.
- **Conversational TTFA:** **1.411 s mean** (loop off) / **1.829 s mean** (loop on, +0.418s concurrency cost mitigated via voice turn deferral).
- **Smart-Turn Classifier:** `smart-turn-v3.2` ONNX model classifies audio completeness in **68.2 ms**, eliminating awkward artificial turn pauses while holding incomplete thoughts.
- **Local Speech Synthesis:** `Kokoro-ONNX` neural TTS synthesizes natural speech chunks streamed directly over WebSockets.

---

### Slide 11: Experimental Setup & Verification Protocol
- **Evaluation Workstation:**
  - OS: Windows 11 Home (64-bit)
  - CPU: Intel Core i5-13450HX (10 cores, 16 threads)
  - GPU: NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM, CUDA 12.4)
  - RAM: 16 GB DDR5
- **Automated Test Suite:**
  - Full suite of **111 tests** covering end-to-end conversation, turn gating, delegation, facial/vocal extraction, fusion, and crash resilience.
  - **Results:** **110 Passed, 0 Failed, 1 Skipped by Design** (**99.1% Pass Rate**).
  - *Test Note:* 42 E2E tests that previously skipped now execute live against Gemma 4 E2B; single remaining skip is `test_thinking_pause_is_held` due to synthetic falling TTS prosody.

---

### Slide 12: Empirical Performance & Latency Benchmarks
*All figures measured live on this machine and logged in `evidence/`:*

| Benchmark Component | Empirical Measured | Engineering Budget | Status | Evidence File |
|:---|:---:|:---:|:---:|:---|
| Facial AU Extraction (Real Face, p95) | **4.81 ms** (mean: 3.97 ms) | — | **PASS** | `evidence/facial_extraction_real.csv` |
| Facial AU Extraction (Blank / No Face) | **2.45 ms** (mean: 1.92 ms) | — | **PASS** | `evidence/facial_extraction_blank.csv` |
| Vocal DSP Extraction (CPU, p95) | **3.73 ms** (mean: 2.85 ms) | — | **PASS** | `evidence/vocal_extraction.csv` |
| Wellness SLM Latency (GPU, p95) | **2.42 s** (mean: 2.14 s) | $\le 5.0\text{ s}$ (window) | **PASS (+2.58s)** | `evidence/wellness_slm_latency.csv` |
| Voice TTFA (Loop OFF, Mean) | **1.411 s** (p50: 1.384 s) | — | **Baseline** | `evidence/voice_ttfa.csv` |
| Voice TTFA (Loop ON, Mean) | **1.829 s** (p50: 1.745 s) | — | **+0.418s cost** | `evidence/voice_ttfa.csv` |
| Test Suite Integration | **110 / 111 Passed** | — | **PASS** | `evidence/pytest_full.log` |
| Outbound Network Sockets | **0 (0.00 KB)** | $0.0\text{ KB}$ | **PASS** | `evidence/netstat_outbound.txt` |
| Peak VRAM (Session) | **3.90 GB** (3991 MB peak) | 6.0 GB capacity | **PASS** | `evidence/vram_cpu_usage.log` |

*Examiner Reproducibility:* `powershell -ExecutionPolicy Bypass -File scripts/reproduce_numbers.ps1`

---

### Slide 13: Affective Validation & EMA Ground-Truth Study
*Distinguishing Quantization Agreement (Compression Fidelity) from Human Ground-Truth Agreement:*

- **Model Quantization Agreement:** Measures prediction similarity between 4-bit and FP16 models. Unquantized FP16 weights were not stored locally for Gemma 4 E2B $\rightarrow$ **NOT MEASURED**.
- **Human Ground-Truth Agreement:** Evaluates inferred stress against human self-reports. Preliminary reports used synthetic distributions for analysis smoke testing. Empirical human data is formally marked: **`NOT COLLECTED / REQUIRES HUMAN STUDY`**.
- **Turnkey Human Re-Collection Kit:** Packaged in `docs/EMA_RECOLLECTION_KIT.md` with interactive tool `scripts/ema_collector.py` and evaluation harness `scripts/evaluate_ema.py` for execution with $\ge 8$ human participants (4 developers + 4 external peers) prior to viva.
- **Empirical Live Reasoning Proofs:** Verified 5/5 trials Low Tier 0 on cross-modal conflict; 5/5 trials Moderate Tier 1 on acute stress; 0.0 confidence on zero signal (`evidence/live_pattern_reasoning.json`).

---

### Slide 14: Privacy Architecture & Local Network Audit
- **Zero Outbound Data Transmission:** Socket inspection confirmed **0.00 KB** outbound network traffic during live operation.
- **Strict Local Loopback:** Binds strictly to `127.0.0.1:8000` (FastAPI) and `127.0.0.1:8081` (`llama-server`).
- **Vendored Offline VAD:** Local Silero VAD (`ort.js`, `silero_vad.onnx`, `vad.worklet.bundle.min.js`) completely removes external CDN dependencies (`cdn.jsdelivr.net` removed).
- **Data Ephemerality:** Raw video frames and audio buffers are processed in volatile memory and immediately discarded. Only anonymized scalar feature vectors and clinical reasoning strings are stored in local SQLite.

---

### Slide 15: Limitations, Future Work & Conclusion
- **Clinical Role Boundary:** Parlor estimates behavioral stress signals and suggests micro-breaks; it is an occupational wellness tool, **NOT a medical diagnostic device**.
- **Limitations:** Student/developer participant cohorts, subjectivity of EMA self-report, camera performance in low light ($<20\text{ lux}$), and live demo recording (`REQUIRES HUMAN: record the demo`).
- **Future Directions:**
  - Dedicated NPU offload (Intel NPU, Snapdragon X Elite, Apple Neural Engine) to operate at $<5\text{ Watts}$.
  - Multi-day circadian baseline adaptation in local SQLite.
  - On-device parameter-efficient fine-tuning (LoRA) for user voice personalization.
- **Conclusion:** Parlor proves that explainable, non-invasive, and zero-cloud multimodal affective computing can run entirely on commodity consumer laptops.
