# Parlor: On-Device Multimodal Affective Wellness Monitoring
## Final Year Project (FYP) — Experimental Results & Performance Summary

---

### Abstract
This project presents **Parlor**, a fully on-device multimodal artificial intelligence assistant that passively monitors digital burnout and affective workplace stress without specialized wearable sensors or manual logging. Utilizing standard laptop webcams and microphones, Parlor extracts facial Action Units (MediaPipe FaceMesh) and vocal acoustic biomarkers (Librosa/NumPy DSP), combining them across rolling temporal observation windows. Rather than enforcing static numeric thresholds, an on-device Small Language Model (Google Gemma 4 E2B IT Q4_0 via `llama.cpp` b12015) performs qualitative clinical reasoning over the pattern of signals, deciding both the stress tier and an explainable rationale citing active biomarkers. Triggered micro-interventions are pushed directly via WebSocket into an intuitive user interface with granular sensitivity, snooze, and mute controls.

---

### 1. Key Performance & Latency Benchmarks (Empirically Measured)

All metrics were evaluated on the host workstation (**Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 6GB VRAM, 16GB RAM, Windows 11**) running **Gemma 4 E2B IT Q4_0** on `llama.cpp` b12015 with CUDA 12.4:

| Metric / Stage | Engineering Budget | Workstation Measured (RTX 4050 GPU + i5 CPU) | Edge Tier (Raspberry Pi 5) | Empirical Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Conversational Turn TTFA (Loop OFF)** | — | **$1.411\,\text{s}$** (p50: $1.384\,\text{s}$, N=10) | Untested | Empirical Baseline (`evidence/voice_ttfa.csv`) |
| **Conversational Turn TTFA (Loop ON)** | — | **$1.829\,\text{s}$** (p50: $1.745\,\text{s}$, N=10) | Untested | **+0.418s Latency Cost** (Mitigated via Voice Deferral) |
| **Facial AU Extraction (Real Face, Normal Light)** | — | **$3.97\,\text{ms}$** (p95: $4.81\,\text{ms}$, N=100) | Literature est: ~26.8 ms | Real Face active tracking (`evidence/facial_extraction_real.csv`) |
| **Facial AU Extraction (Real Face, Dim Light 15%)**| — | **$4.39\,\text{ms}$** (p95: $6.84\,\text{ms}$, N=100) | Literature est | Robust face detection under low light |
| **Facial AU Extraction (Head Turned ~30°)** | — | **$4.69\,\text{ms}$** (p95: $6.58\,\text{ms}$, N=100) | Literature est | Pose-invariant tracking (`evidence/facial_extraction_turned.csv`) |
| **Facial AU Extraction (Blank / No Face)** | — | **$1.92\,\text{ms}$** (p95: $2.45\,\text{ms}$, N=100) | Literature est | Early exit when no face detected |
| **Vocal Acoustic DSP (F0, Jitter, Shimmer, Tension)**| — | **$2.85\,\text{ms}$** (p95: $3.73\,\text{ms}$, N=100) | Literature est: ~24.1 ms | Fast vectorized CPU DSP (`evidence/vocal_extraction.csv`) |
| **SQLite Longitudinal Store Logging** | — | **$4.07\,\text{ms}$** (p95: $5.29\,\text{ms}$, N=100) | Literature est | Local synchronous write (`evidence/db_write_latency.csv`) |
| **SLM Wellness Qualitative Reasoning (GPU)** | $\le 5.00\,\text{s}$ (window) | **$2.14\,\text{s}$** mean (p95: $2.42\,\text{s}$, N=30) | Literature est: ~4.15 s | **PASS** (+2.58s margin within 5.0s window) |
| **Peak GPU VRAM Consumption** | — | **$3.90\,\text{GB}$** (3991 MB / 6141 MB) | N/A (Shared RAM) | Fully resident within 6GB VRAM (`evidence/vram_cpu_usage.log`) |
| **Outbound Data Transmission (Privacy Audit)** | **$0.0\,\text{KB}$** | **$0.00\,\text{KB}$** (0 outbound sockets) | $0.00\,\text{KB}$ | **PASS** (100% on-device isolation, `evidence/netstat_outbound.txt`) |
| **Automated Test Suite Pass Rate** | — | **125 / 127 Passed** (1 skipped by design, 1 flaky live-model test; 126 in isolation) | N/A | **PASS** (`evidence/pytest_full.log`) |

> [!NOTE]
> Raspberry Pi 5 figures represent published literature estimates from Phase 0 feasibility modeling; no Raspberry Pi hardware was deployed or benchmarked in this project.

---

### 2. SLM Architecture & Empirical Reasoning Behavior

* **Deployed Model:** Google Gemma 4 E2B IT Q4_0 (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`, size: 2.45 GB).
* Earlier reported quantization fidelity (91.4% tier agreement at Q4_K_M) was an initial literature estimate and is marked as **NOT MEASURED** for this specific model configuration.
* **Empirical Pattern Reasoning Verification (N=5 repeats each, live on GPU):**
  1. **Cross-Modal Conflict (Vocal Pitch Spike + Relaxed Face):**
     - Biomarkers: AU04=0.05, AU07=0.05, Pitch Delta=+37.5Hz, Vocal Tension=0.65.
     - SLM Assessment: Consistently evaluated as **Low (Tier 0)** across all 5 trials ($2.35\text{s} - 4.32\text{s}$).
     - Verbatim Reasoning: *"The vocal biomarkers indicate a slight elevation in pitch and a high Vocal Tension Index (0.65)... However, all facial micro-expressions are at baseline/relaxed levels (AU04=0.05, AU07=0.05), indicating an absence of emotional facial tension. This conflicting data lowers the overall stress assessment to Low (Tier 0)."* (`evidence/live_pattern_reasoning.json`).
  2. **Consistent Acute Stress (Brow Furrow + Vocal Strain):**
     - Biomarkers: AU04=0.84, AU07=0.72, Pitch Delta=+49.0Hz, Vocal Tension=0.76.
     - SLM Assessment: Consistently evaluated as **Moderate (Tier 1)** with high confidence (0.92) across all 5 trials ($1.88\text{s} - 4.18\text{s}$).
  3. **Zero-Signal Honesty (Covered Camera + Silence):**
     - Output: `confidence_score: 0.0`, `stress_level: "Low (Tier 0)"`, `ambiguity_note: "Camera unlit/obscured and microphone silent."` with zero compute wasted (`evidence/live_zero_signal.json`).
  4. **Graceful Failure & Recovery:**
     - Killing `llama-server` mid-session triggers immediate caught exception `LLAMAServerError`. Server automatically respawns and restores healthy state in **$3.95\,\text{s}$ mean** across 3 test cycles (`evidence/live_llama_kill_recovery.log`).

---

### 3. Human Ground-Truth Accuracy Status

> [!IMPORTANT]
> **Human Ground-Truth Accuracy Status:** **`NOT YET COLLECTED — REQUIRES HUMAN STUDY`**  
> Earlier reported figures (77.8% exact / 100% one-tier agreement) were generated using a synthetic simulation harness (`scripts/run_ema_validation.py`) and have been **expunged from all submission documents**.

The standardized collection harness (`scripts/ema_collector.py`), audit-grade evaluation tool (`scripts/evaluate_ema.py`), and experimental protocol (`docs/EMA_RECOLLECTION_KIT.md`) are complete and validated using a toy verification dataset (`shared_state/toy_ema_records.json`). The protocol is ready for human data collection ($\ge 8$ participants) prior to viva.

---

### 4. Verification of Core Architectural Claims

1. **"Reasons over the pattern, not fixed thresholds":**
   - Verified live: Gemma 4 E2B correctly identifies cross-modal conflict (vocal spike + neutral face) and avoids false-positive alerts, citing the lack of facial tension.
2. **"Fails gracefully / stays honest about insufficient signal":**
   - Camera covered + silence produces `confidence_score: 0.0` with zero hallucinated stress.
   - Killing `llama-server` mid-session is safely caught without server crash and recovers in ~3.95s.
3. **"No personal data ever leaves the device":**
   - Socket audit confirms 0 outbound network connections. All inference and storage run on `127.0.0.1`.
