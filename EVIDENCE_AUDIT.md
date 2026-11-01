# Parlor System Evidence Audit & Empirical Grounding Report

**Academic Context:** B.Tech Major Project, Department of Computer Science & Engineering, Section A, Batch 14  
**Project Title:** EMO Assistant ("Parlor") — Fully On-Device Multimodal Wellness & Fatigue Mitigation Assistant  
**Hardware Target:** Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM), 16 GB RAM, Windows 11  
**SLM Target:** Google Gemma 4 E2B Q4_0 IT (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`) via llama.cpp b12015 CUDA 12.4  
**Audit Date:** 2026-11-01  
**Audit Policy:** Zero simulated, estimated, or carried-over numbers. Every reported figure traces to a raw timestamped file in `evidence/`.

---

## 1. Master Evidence Audit Matrix

| Metric / Parameter | Value in Preliminary Reports | Value Measured on This Machine | Raw Evidence File | Source Command / Harness | Empirical Audit Status |
|:---|:---:|:---:|:---|:---|:---:|
| **Facial AU Extraction (Real Face, Normal)** | 14.2 ms (carried-over) / 1.75 ms (blank) | **3.97 ms (mean) / 4.81 ms (p95)** | `evidence/facial_extraction_real.csv` | `benchmark_facial_conditions.py` (N=100) | **CHANGED (VERIFIED)** |
| **Facial AU Extraction (Real Face, Dim Light)** | Not specified | **4.39 ms (mean) / 6.84 ms (p95)** | `evidence/facial_extraction_dim.csv` | `benchmark_facial_conditions.py` (N=100) | **VERIFIED** |
| **Facial AU Extraction (Head Turned ~30°)** | Not specified | **4.69 ms (mean) / 6.58 ms (p95)** | `evidence/facial_extraction_turned.csv` | `benchmark_facial_conditions.py` (N=100) | **VERIFIED** |
| **Facial AU Extraction (Blank / No Face)** | 1.75 ms (earlier blank) | **1.92 ms (mean) / 2.45 ms (p95)** | `evidence/facial_extraction_blank.csv` | `benchmark_facial_conditions.py` (N=100) | **VERIFIED** |
| **Vocal DSP Extraction (CPU, Mean)** | 18.7 ms (carried-over) | **2.85 ms (mean) / 3.73 ms (p95)** | `evidence/vocal_extraction.csv` | `measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **Database Write Latency (SQLite)** | 2.57 ms (carried-over) | **4.07 ms (mean) / 5.29 ms (p95)** | `evidence/db_write_latency.csv` | `measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Mean, GPU)** | 2.76 s (carried-over) | **2.14 s (mean)** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (p50, GPU)** | Not specified | **2.23 s (p50)** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM Wellness Latency (p95, GPU)** | 3.12 s (carried-over) | **2.42 s (p95)** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Max, GPU)** | Not specified | **2.45 s (max)** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM 5.0s Window Margin** | 1.88 s | **+2.58 s (5.0s - 2.42s p95)** | `evidence/wellness_slm_latency.csv` | Margin within 5.0s engineering budget | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop OFF, Mean)** | 0.781 s (isolated) | **1.411 s (mean) / 1.384 s (p50)** | `evidence/voice_ttfa.csv` | `measure_voice_ttfa.py` (N=10) | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop ON, Mean)** | Not measured | **1.829 s (mean) / 1.745 s (p50)** | `evidence/voice_ttfa.csv` | `measure_voice_ttfa.py` (N=10, mitigated) | **CHANGED (VERIFIED)** |
| **Voice TTFA Concurrency Cost (Delta)**| Claimed "Zero regression" | **+0.418 s (+0.55s unmitigated)** | `evidence/voice_ttfa.csv` | Mitigated via voice turn deferral | **CHANGED (VERIFIED)** |
| **Cross-Modal Conflict Reasoning** | Claimed in theory | **5/5 trials Low (Tier 0)** | `evidence/live_pattern_reasoning.json` | `collect_live_evidence.py` | **VERIFIED** |
| **Consistent Acute Stress Reasoning** | Claimed in theory | **5/5 trials Moderate (Tier 1)** | `evidence/live_pattern_reasoning.json` | `collect_live_evidence.py` | **VERIFIED** |
| **Zero-Signal Honesty** | Claimed in theory | **Confidence 0.0, Tier 0** | `evidence/live_zero_signal.json` | `collect_live_evidence.py` | **VERIFIED** |
| **llama-server Crash & Recovery** | Claimed in theory | **3.95 s mean recovery time** | `evidence/live_llama_kill_recovery.log` | `collect_live_evidence.py` (3 repeats) | **VERIFIED** |
| **Peak GPU VRAM (Session)** | ~3.8 GB (unverified) | **3.90 GB (3991 MB / 6141 MB)** | `evidence/vram_cpu_usage.log` | `measure_hardware_and_network.py` | **CHANGED (VERIFIED)** |
| **Outbound Network Telemetry** | "Air-gapped" | **0 outbound sockets (0.00 KB)** | `evidence/netstat_outbound.txt` | `netstat -ano` audit; loopback 127.0.0.1 only | **VERIFIED** |
| **Test Suite Passed** | 69 passed, 42 skipped | **110 passed, 0 failed, 1 skipped** | `evidence/pytest_full.log` | `uv run pytest tests/ -v` | **CHANGED (VERIFIED)** |
| **Gemma 4 E2B Quantization Agreement**| 91.4% (Q4_K_M vs FP16) | **NOT MEASURED** | Local disk contains only Q4_0 | FP16 unquantized weights not present locally | **NOT MEASURED** |
| **Ground-Truth Human EMA Agreement** | 77.8% exact / 100% 1-tier | **NOT COLLECTED** | `shared_state/ema_validation_trials.json` | Synthetic trial generator (`run_ema_validation.py`) | **NOT COLLECTED / REQUIRES HUMAN** |
| **Live Demonstration Video (.mp4)** | Claimed in submission | **REQUIRES HUMAN** | Script in `DEMO_SCRIPT.md` | Human recording with webcam/mic required | **REQUIRES HUMAN** |

---

## 2. Detailed Summary of Numerical Changes & Root Causes

1. **Facial AU Extraction Latency (1.75 ms $\rightarrow$ 3.97 ms):**
   - *Audit Finding:* The earlier reported 1.75 ms was measured on blank gray frames (`np.full`) where MediaPipe detected no face and exited early.
   - *Resolution:* Re-benchmarked across 4 standardized conditions with active landmarks:
     - Real Face (Normal Light): **3.97 ms mean, 4.81 ms p95** (`evidence/facial_extraction_real.csv`).
     - Real Face (Dim Light 15% Lux): **4.39 ms mean, 6.84 ms p95** (`evidence/facial_extraction_dim.csv`).
     - Real Face (Head Turned ~30°): **4.69 ms mean, 6.58 ms p95** (`evidence/facial_extraction_turned.csv`).
     - Blank / Empty Frame: **1.92 ms mean, 2.45 ms p95** (`evidence/facial_extraction_blank.csv`).

2. **Voice Latency Regression & Mitigation (0.781s $\rightarrow$ 1.411s / 1.829s):**
   - *Audit Finding:* Profiling revealed that running the background wellness loop concurrently caused a $+0.55\text{s}$ latency regression (1.33s off vs 1.88s on) due to slot 0 contention (`-np 1`) and KV cache eviction when the background wellness prompt overwrote conversational context tokens.
   - *Mitigation Implemented:* Added `set_voice_active(True)` in `src/parlor/server.py` and `src/parlor/wellness.py`: when user speech or an active voice turn is detected, background wellness SLM reasoning cycles are deferred to protect slot 0 KV cache tokens.
   - *Re-Measured Result:* Loop OFF: **1.411s mean**; Loop ON: **1.829s mean** (delta **+0.418s**). All claims of "zero regression" or "0.781s" were permanently removed.

3. **Target Columns Cleaned (Fix 3):**
   - *Audit Finding:* Earlier tables included invented post-hoc target specifications (`< 2.0s`, `< 2.5s`, `< 5.5GB`, `< 30ms`) created after measuring.
   - *Resolution:* Deleted invented targets across all documents. The pre-set **5.0-second wellness window budget** is retained as an "Engineering budget".

4. **Synthetic Confusion Matrix Expunged (Fix 5):**
   - *Audit Finding:* The 77.8% exact / 100% one-tier agreement claim was traced to synthetic randomized data in `scripts/run_ema_validation.py`.
   - *Resolution:* Synthetic figures were removed from all reports, slides, and Q&A guides. Human ground-truth accuracy is formally stated as: **`NOT YET COLLECTED — REQUIRES HUMAN STUDY`**. Evaluation script `scripts/evaluate_ema.py` was updated with refusal checks, bootstrap CIs, quadratic-weighted kappa, and developer vs external cohort breakdowns.

5. **Live Evidence Captured for Key Claims (Fix 6):**
   - *Pattern Reasoning:* 5 repeats of cross-modal conflict (vocal spike + relaxed face) verified that Gemma 4 E2B maintains Low (Tier 0) rating with clinical reasoning; 5 repeats of consistent stress verified Moderate (Tier 1) rating (`evidence/live_pattern_reasoning.json`).
   - *Insufficient Signal:* Covered camera + silence verified zero compute wasted, confidence 0.0 (`evidence/live_zero_signal.json`).
   - *Graceful Recovery:* 3 trials of mid-session `llama-server` termination verified automatic recovery in **3.95s mean** (`evidence/live_llama_kill_recovery.log`).
   - *Single Modality:* Camera-only and mic-only evaluations captured (`evidence/live_single_modality.json`).

---

## 3. The "REQUIRES HUMAN" Action Items

The following items cannot and will not be filled with synthetic data:

1. **EMA Human Participant Study ($N \ge 8$ Participants):**
   - **Harness Ready:** `scripts/ema_collector.py` and `scripts/evaluate_ema.py`.
   - **Protocol Documented:** `docs/EMA_RECOLLECTION_KIT.md`.
   - **Action Required:** Team Batch 14 to recruit 4 developers + 4 external peers, obtain signed consent, execute the 20-minute battery, and run `python scripts/evaluate_ema.py`.
2. **Demonstration Video Recording (`.mp4`):**
   - **Script Ready:** `DEMO_SCRIPT.md` and `docs/DEMO_SAFEGUARDS_AND_CHECKLIST.md`.
   - **Action Required:** Team Batch 14 to record the 5-7 minute demonstration using OBS Studio.
3. **Formal Institutional Declarations & Certificates:**
   - **Placeholders Provided:** `docs/FINAL_PROJECT_REPORT.md`.
   - **Action Required:** Physical signatures from student team members and project guide Mrs. V. Aruna.
