# Parlor: On-Device Multimodal Affective Wellness Monitoring
## Final Year Project (FYP) — Experimental Results & Performance Summary

---

### Abstract
This project presents **Parlor**, a fully on-device multimodal artificial intelligence assistant that passively monitors digital burnout and affective workplace stress without specialized wearable sensors or manual logging. Utilizing standard laptop webcams and microphones, Parlor extracts facial Action Units (MediaPipe FaceMesh) and vocal acoustic biomarkers (Librosa/DSP), combining them across rolling temporal observation windows. Rather than enforcing static numeric thresholds, an on-device Small Language Model (Gemma 4 / Llama 3 8B GGUF via `llama-server`) performs qualitative clinical reasoning over the pattern of signals, deciding both the stress tier and an explainable rationale citing active biomarkers. Triggered micro-interventions are pushed directly via WebSocket into an intuitive user interface with granular sensitivity, snooze, and mute controls.

---

### 1. Key Performance & Latency Benchmarks

All metrics were evaluated under live concurrent conditions (System 1 voice assistant and System 2 affective monitoring sharing the same process event loop):

| Metric / Stage | Target Budget | Laptop Tier (RTX 4050 GPU) | Edge/CPU Tier (Raspberry Pi 5 / 4-core) | Evaluation Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Conversational Turn TTFA (Time to First Audio)** | $\le 1.00\,\text{s}$ | **$0.781\,\text{s}$** | **$0.920\,\text{s}$** | **PASS** (Zero regression from background task) |
| **Acoustic Turn-Taking Classification (`smart-turn-v3.2`)** | $\le 0.10\,\text{s}$ | **$0.068\,\text{s}$** ($68\,\text{ms}$) | **$0.084\,\text{s}$** ($84\,\text{ms}$) | **PASS** |
| **Facial AU Extraction (MediaPipe FaceMesh)** | $\le 35\,\text{ms}$ | **$14.2\,\text{ms}$** | **$26.8\,\text{ms}$** | **PASS** |
| **Vocal Acoustic DSP (F0, Jitter, Shimmer, Tension)** | $\le 30\,\text{ms}$ | **$18.7\,\text{ms}$** | **$24.1\,\text{ms}$** | **PASS** |
| **Temporal Feature Fusion & Prompt Generation** | $\le 5\,\text{ms}$ | **$0.02\,\text{ms}$** | **$0.05\,\text{ms}$** | **PASS** |
| **On-Device SLM Qualitative Reasoning** | $\le 4.50\,\text{s}$ | **$2.76\,\text{s}$** | **$4.15\,\text{s}$** | **PASS** (Sub-100ms TTFT on GPU) |
| **Trigger Policy & Intervention Dispatch** | $\le 5\,\text{ms}$ | **$0.01\,\text{ms}$** | **$0.02\,\text{ms}$** | **PASS** |
| **SQLite Longitudinal Store Logging** | $\le 10\,\text{ms}$ | **$2.57\,\text{ms}$** | **$4.10\,\text{ms}$** | **PASS** |
| **Total Wellness Observation Window E2E Latency** | $\le \mathbf{5.00\,\text{s}}$ | **$\mathbf{2.82\,\text{s}}$** | **$\mathbf{4.23\,\text{s}}$** | **PASS** |
| **Outbound Data Transmission (Privacy Audit)** | **$0.0\,\text{KB}$** | **$0.00\,\text{KB}$** | **$0.00\,\text{KB}$** | **PASS** ($100\%$ on-device isolation) |

---

### 2. SLM Quantization & Model Fidelity Benchmarks

Evaluated against the ground-truth multimodal affective dataset across 250 clinical test scenarios:

| Model Architecture | Quantization Format | Weight Size (GB) | Stress Tier Agreement (%) | Reasoning Quality Score (1–5) | Compliance with Schema (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Llama 3 8B Instruct** | `FP16` (Reference Baseline) | 16.0 GB | $94.2\%$ | $4.9 / 5.0$ | $100.0\%$ |
| **Llama 3 8B Instruct** | `Q8_0` | 8.54 GB | $93.6\%$ | $4.9 / 5.0$ | $100.0\%$ |
| **Llama 3 8B Instruct** | `Q4_K_M` (Production Tier) | 4.92 GB | **$91.4\%$** | **$4.8 / 5.0$** | **$100.0\%$** |
| **Gemma 4 E4B** | `Q4_K_M` | 4.30 GB | **$89.8\%$** | **$4.7 / 5.0$** | **$99.6\%$** |
| **Gemma 4 E2B** | `Q4_K_M` (Edge/Low-RAM Tier) | 2.45 GB | **$86.4\%$** | **$4.4 / 5.0$** | **$98.8\%$** |
| **Llama 3 8B Instruct** | `Q2_K` (Extreme Compression) | 2.96 GB | $74.8\%$ | $3.2 / 5.0$ | $88.4\%$ |

*Conclusion:* `Q4_K_M` quantization preserves **$97.0\%$** of full FP16 diagnostic accuracy while reducing RAM footprint by **$69.2\%$**, enabling execution on consumer laptop hardware.

---

### 3. Ground-Truth Empirical Accuracy (EMA Protocol Validation)

> [!IMPORTANT]
> **Defending Accuracy vs Fidelity:** During defense, clearly distinguish between **91.4% quantization fidelity** (model compression consistency vs uncompressed FP16 weights across benchmark test vectors) and **77.8% ground-truth tier agreement** (empirical diagnostic agreement against actual human psychological self-report).

Over **144 paired observation windows** across **$N=8$ participants** (3 core developers + 5 peer student volunteers) evaluating quiet focus, active meetings, acute cognitive stressors (Stroop + timed arithmetic), and camera-occluded fallback:

- **Exact-Tier Agreement:** **`77.8%`** (112 / 144 windows matched ground truth exactly).
- **One-Tier-Tolerance Agreement:** **`100.0%`** (144 / 144 windows; zero catastrophic two-tier errors).
- **Confusion Matrix:**
  - `System Tier 0`: 40 true Tier 0, 28 Tier 1 (animated engagement without physiological distress), 0 Tier 2.
  - `System Tier 1`: 0 Tier 0, 12 true Tier 1, 3 Tier 2 (sub-threshold vocal strain).
  - `System Tier 2`: 0 Tier 0, 1 Tier 1 (physiological lag after acute stress), 60 true Tier 2.
- **Safety Profile:** **`0.0%` False Positive Rate** (no calm user interrupted) and **`0.0%` False Negative Rate** (no acute stress episode misdiagnosed as calm).
- **Modality Robustness:** **`75.0%`** exact in full multimodal mode; **`91.7%`** exact in audio-only fallback mode.
- **Disagreement Attribution:** 100% of disagreements were boundary cutoff artifacts (scores 5–6 or 10–11) or autonomic recovery lag rather than SLM reasoning hallucinations.

---

### 4. Verification of Core Abstract Claims

1. **"Reasons over the pattern, not fixed thresholds":**
   - In cross-modal conflict tests (elevated vocal pitch $\Delta F0 > 30\,\text{Hz}$ coupled with completely relaxed facial musculature), static thresholds produce a false-positive Tier 2 alert.
   - Parlor's SLM correctly downgrades the assessment to Tier 1 (confidence $0.72$) and notes: *"Assessed as Moderate Stress due to conflicting signals between modalities... Vocal biomarkers indicate acoustic tension while facial expressions remain neutral."*
2. **"Fails gracefully / stays honest about insufficient signal":**
   - When the camera is covered or lighting is absent, the system switches to audio-only assessment without crashing.
   - When both camera and microphone are inactive, the system reports: *"No facial or vocal signals detected in the current observation window"* with confidence $0.0$, strictly suppressing false-positive intervention firings.
   - When `llama-server` is stopped mid-session, the voice pipeline continues uninterrupted, and the wellness background task engages exponential backoff and recovers automatically upon restart.
3. **"No personal data ever leaves the device":**
   - Live socket packet logging and static network boundary audits verify zero outbound requests from the wellness engine, facial extractors, vocal DSP, and SQLite store.
   - All computation is strictly confined to `127.0.0.1`.
