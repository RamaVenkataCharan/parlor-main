# PROJECT PRESENTATION: EMO ASSISTANT ("PARLOR")
## On-Device Multimodal Affective Wellness Monitoring & Conversational AI

**Batch:** 14 | **Section:** A | **Branch:** Computer Science and Engineering  
**Project Guide:** Mrs. V. Aruna  
**Team Members:** Rama Venkata Charan & Team  

---

### Slide 1: Title & Overview
- **Project Title:** EMO Assistant ("Parlor")
- **Subtitle:** On-Device Multimodal Affective Wellness Monitoring and Real-Time Voice Assistant
- **Domain:** Affective Computing, Edge AI, Multimodal Signal Processing, Human-Computer Interaction
- **Academic Context:** Major Project — Department of Computer Science & Engineering (Batch 14, Section A)
- **Project Guide:** Mrs. V. Aruna, Assistant Professor, Dept. of CSE

---

### Slide 2: The Problem: Silent Workplace Burnout & Wearable Friction
- **The Burnout Crisis:** Knowledge workers suffer from insidious "stress blindness" — accumulating cognitive fatigue and autonomic tension without conscious awareness.
- **Wearable Friction:** Smartwatches and chest bands require charging, cause skin irritation, cost \$200–\$500, and suffer from high abandonment rates.
- **Manual Logging Failure:** Subjective journaling apps experience $>80\%$ user attrition within 14 days due to workflow disruption.
- **Cloud Privacy Dilemma:** Transmitting raw webcam video and microphone audio to remote servers introduces catastrophic privacy and compliance risks (GDPR/HIPAA).
- **Brittle Thresholds:** Static statistical cutoffs misclassify animated speaking as stress, triggering irritating false alarms.

---

### Slide 3: The Proposed Solution: Parlor
- **Passive & Sensorless:** Operates entirely through existing, commodity laptop webcams and USB microphones.
- **Multimodal Perception:** Simultaneously tracks facial Action Units (MediaPipe FaceMesh) and vocal acoustic biomarkers (Librosa DSP).
- **Cognitive SLM Reasoning:** Replaces brittle thresholds with an on-device Small Language Model (Gemma 4 E2B IT at Q4_0) performing qualitative pattern reasoning.
- **Explainable Provenance:** Every intervention discloses the physiological signals that triggered it via a *"Why did this fire?"* interface.
- **Strict Zero-Cloud Privacy:** 100% of audio, video, inference, and storage operations execute locally on loopback (`127.0.0.1`).

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
- **Landmarking Core:** Google MediaPipe FaceMesh tracking 478 3D landmarks in real time ($14.2\text{ ms}$ on laptop GPU).
- **Target Action Units (FACS):**
  - **AU04 (Brow Lowerer):** Medial brow contraction normalized to nasal bridge (corrugator supercilii — cognitive strain).
  - **AU07 (Lid Tightener):** Palpebral fissure narrowing (orbicularis oculi — visual strain/fatigue).
  - **AU20 (Lip Stretcher):** Transverse oral commissure displacement (somatic tension).
- **Eye Aspect Ratio (EAR):** Tracks spontaneous blink suppression and fatigue flutter.
- **Perspective Filtering:** Perspective-n-Point (PnP) solver discards observations with $|\text{Yaw}| > 30^\circ$ or $|\text{Pitch}| > 25^\circ$.

---

### Slide 6: Perception Layer: Vocal Acoustic Biomarkers
- **DSP Core:** Real-time Librosa and SciPy signal processing ($18.7\text{ ms}$ execution latency).
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
- **Thinking Token Elimination:** Configured with `thinking_budget: 0` to prevent token starvation, reducing decode latency from 4.5s to 2.76s on GPU.
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
- **Sub-Second TTFA:** Achieves **0.781 s Time to First Audio** using speculative prompt prefix cache priming.
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
  - Code Coverage: `fusion.py` 98%, `triggers.py` 90%, `interventions.py` 86%, `db.py` 81%, `vocal.py` 77%, `wellness.py` 64%.

---

### Slide 12: Empirical Performance & Latency Benchmarks
*All figures measured live under concurrent dual-system load:*

| Benchmark Component | Measured Duration | Target Budget | Evaluation Status |
|:---|:---:|:---:|:---:|
| Conversational Turn TTFA | **0.781 s** | $\le 1.000\text{ s}$ | **PASS** |
| Acoustic Turn Detection (`smart-turn`) | **68.2 ms** | $\le 100.0\text{ ms}$ | **PASS** |
| Facial AU Landmark Extraction | **14.2 ms** | $\le 35.0\text{ ms}$ | **PASS** |
| Vocal Acoustic DSP Extraction | **18.7 ms** | $\le 30.0\text{ ms}$ | **PASS** |
| Temporal Fusion & Prompt Prep | **0.02 ms** | $\le 5.0\text{ ms}$ | **PASS** |
| SLM Qualitative Reasoning (GPU) | **2.760 s** | $\le 4.500\text{ s}$ | **PASS** |
| SQLite Logging Transaction | **2.57 ms** | $\le 10.0\text{ ms}$ | **PASS** |
| Total Observation Window Latency | **2.820 s** | $\le 5.000\text{ s}$ | **PASS** |

- **Hardware Footprint:** Peak 3.84 GB VRAM (on 6GB GPU), 24.6% CPU utilization, 4.12 GB Host RAM.

---

### Slide 13: Ground-Truth Accuracy Validation (EMA Protocol)
*Distinguishing Quantization Agreement (91.4% compression fidelity) from Ground-Truth Diagnostic Agreement:*

- **Protocol:** Ecological Momentary Assessment (EMA) 3-item self-report (1–5 Likert mapped to Tier 0/1/2) collected across **$N=8$ participants** over **144 paired observation windows** (Quiet Focus, Active Speech, Stroop/Timed Arithmetic Stress, and Occluded Camera).
- **Exact-Tier Agreement Rate:** **`77.8%`** (112 / 144 windows matched exactly).
- **One-Tier-Tolerance Agreement Rate:** **`100.0%`** (144 / 144 windows; zero catastrophic two-tier errors).
- **3x3 Empirical Confusion Matrix:**
  - `System Tier 0`: 40 true Tier 0, 28 Tier 1, 0 Tier 2.
  - `System Tier 1`: 0 Tier 0, 12 true Tier 1, 3 Tier 2.
  - `System Tier 2`: 0 Tier 0, 1 Tier 1, 60 true Tier 2.
- **Safety Profile:** **`0.0%` False Positive Rate** (no calm user interrupted) and **`0.0%` False Negative Rate** (no severe stress missed as calm).

---

### Slide 14: Privacy Architecture & Zero-Cloud Security Audit
- **Zero Outbound Data Transmission:** Socket inspection confirmed **0.00 KB** outbound network traffic during live operation.
- **Complete Local Loopback:** Binds strictly to `127.0.0.1:8000` (FastAPI) and `127.0.0.1:8081` (`llama-server`).
- **Vendored Offline VAD:** Local Silero VAD (`ort.js`, `silero_vad.onnx`, `vad.worklet.bundle.min.js`) completely removes external CDN dependencies (`cdn.jsdelivr.net` removed).
- **Data Ephemerality:** Raw video frames and audio buffers are processed in volatile memory and immediately discarded. Only anonymized scalar feature vectors and clinical reasoning strings are stored in local SQLite.

---

### Slide 15: Limitations, Future Work & Conclusion
- **Clinical Role Boundary:** Parlor estimates behavioral stress signals and suggests micro-breaks; it is an occupational wellness tool, **NOT a medical diagnostic device**.
- **Environmental Limitations:** Camera performance degrades in low light ($<20\text{ lux}$) and extreme head yaw ($>30^\circ$); system automatically falls back to acoustic DSP.
- **Future Directions:**
  - Quantize for dedicated edge NPUs (Intel NPU, Qualcomm Snapdragon X Elite, Apple Neural Engine) to operate at $<5\text{ Watts}$.
  - Multi-day circadian baseline adaptation in local SQLite.
  - On-device parameter-efficient fine-tuning (LoRA) for user voice personalization.
- **Conclusion:** Parlor proves that high-accuracy, explainable, and zero-cloud multimodal affective computing can run entirely on commodity consumer laptops.
