# Parlor System Evidence Audit & Empirical Grounding Report

**Academic Context:** B.Tech Major Project, Department of Computer Science & Engineering, Section A, Batch 14  
**Project Title:** EMO Assistant ("Parlor") — Fully On-Device Multimodal Wellness & Fatigue Mitigation Assistant  
**Hardware Target:** Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM), 16 GB RAM, Windows 11  
**SLM Target:** Google Gemma 4 E2B Q4_0 IT (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`) via llama.cpp b12015 CUDA 12.4  
**Audit Date:** 2026-11-02  
**Academic Year:** 2026–2027  
**Audit Policy:** Zero simulated, estimated, or carried-over numbers. Every reported figure traces to a raw timestamped file in `evidence/`.

---

## 1. Master Evidence Audit Matrix

| Metric / Parameter | Value in Preliminary Reports | Value Measured on This Machine | Raw Evidence File | Source Command / Harness | Empirical Audit Status |
|:---|:---:|:---:|:---|:---|:---:|
| **Facial AU Extraction (Real Face, Normal)** | 14.2 ms (carried-over) / 1.75 ms (blank) | **3.97 ms (mean) / 4.81 ms (p95)** | `evidence/facial_extraction_real.csv` | `benchmark_facial_conditions.py` (N=100) | **CHANGED (VERIFIED)** |
| **Facial AU Extraction (Simulated Dim Light)** | Not specified | **4.39 ms (mean) / 6.84 ms (p95)** | `evidence/facial_extraction_dim.csv` | `benchmark_facial_conditions.py` (N=100, 15% lux) | **VERIFIED (SIMULATED)** |
| **Facial AU Extraction (Simulated Head Turned ~30°)** | Not specified | **4.69 ms (mean) / 6.58 ms (p95)** | `evidence/facial_extraction_turned.csv` | `benchmark_facial_conditions.py` (N=100, ~30° yaw) | **VERIFIED (SIMULATED)** |
| **Facial AU Extraction (Blank / No Face)** | 1.75 ms (earlier blank) | **1.92 ms (mean) / 2.45 ms (p95)** | `evidence/facial_extraction_blank.csv` | `benchmark_facial_conditions.py` (N=100) | **VERIFIED** |
| **Vocal DSP Extraction (CPU, Mean)** | 18.7 ms (carried-over) | **2.85 ms (mean) / 3.73 ms (p95)** | `evidence/vocal_extraction.csv` | `measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **Database Write Latency (SQLite)** | 2.57 ms (carried-over) | **4.07 ms (mean) / 5.29 ms (p95)** | `evidence/db_write_latency.csv` | `measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **Total Non-SLM Pipeline Overhead** | ~35 ms (estimated) | **10.89 ms mean** (Face 3.97 + Vocal 2.85 + DB 4.07) | CSVs in `evidence/` | Direct sum of verified module means | **VERIFIED** |
| **SLM Wellness Latency (Mean, GPU)** | 2.76 s (carried-over) | **2.14 s (mean) [2.138s]** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (p50, GPU)** | Not specified | **2.23 s (p50) [2.228s]** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM Wellness Latency (p95, GPU)** | 3.12 s (carried-over) | **2.44 s (p95) [2.436s]** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Max, GPU)** | Not specified | **2.45 s (max) [2.446s]** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM Latency 95% CI Margin** | Not reported | **+/- 0.10 s** (interval: [2.04s, 2.23s]) | `evidence/wellness_slm_latency.csv` | $1.96 \times (s/\sqrt{N})$, $s=0.269\text{s}$ | **VERIFIED** |
| **SLM 5.0s Window Margin** | 1.88 s | **+2.56 s (5.0s - 2.44s p95)** | `evidence/wellness_slm_latency.csv` | Margin within 5.0s engineering budget | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop OFF, Mean)** | 0.781 s (isolated) | **1.789 s (mean) / 2.755 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.63s, 1.97s]) | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop ON Unmitigated)** | Not measured | **1.382 s (mean) / 2.060 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.26s, 1.52s]) | **VERIFIED** |
| **Voice TTFA (Loop ON Mitigated)** | Not measured | **1.903 s (mean) / 3.716 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.58s, 2.26s]) | **CHANGED (VERIFIED)** |
| **Voice TTFA Concurrency Delta** | Claimed "Zero regression" | **+0.114 s (Mitigated vs OFF)** | `evidence/voice_ttfa_summary.json` | Alternating round-robin 30 cycles | **CHANGED (VERIFIED)** |
| **Tier 2 Range Sweep (10 Vectors x 3)**| Untested sweep | **Tier 0 (V1-V4), Tier 1 (V5-V9), Tier 2 (V10: 3/3)** | `evidence/tier_sweep.csv` | `test_tier_sweep.py` (N=30 runs) | **VERIFIED** |
| **Live WS Balanced Trigger Test** | Unverified /ws test | **3 cycles -> Fired 4-7-8 Breathing Card** | `evidence/live_ws_intervention_trigger.json` | `test_live_ws_trigger_balanced.py` | **VERIFIED** |
| **Cross-Modal Conflict Reasoning** | Claimed in theory | **5/5 trials Low (Tier 0)** | `evidence/live_pattern_reasoning.json` | Synthetic feature vectors (`collect_live_evidence.py`) | **VERIFIED** |
| **Consistent Acute Stress Reasoning** | Claimed in theory | **5/5 trials Moderate (Tier 1)** | `evidence/live_pattern_reasoning.json` | Synthetic feature vectors (`collect_live_evidence.py`) | **VERIFIED** |
| **Zero-Signal Sensor Occlusion** | Stored as Tier 0 | **Stored as "insufficient signal", Conf 0.0** | `evidence/live_zero_signal.json` | Covered camera + silence; excluded from EMA | **CHANGED (VERIFIED)** |
| **llama-server Crash & Recovery** | Claimed in theory | **3.95 s mean recovery time** | `evidence/live_llama_kill_recovery.log` | `collect_live_evidence.py` (3 repeats) | **VERIFIED** |
| **Peak Dedicated GPU VRAM** | ~3.8 GB (unverified) | **3.90 GB (3991 MB / 6141 MB capacity)** | `evidence/vram_cpu_usage.log` | `measure_hardware_and_network.py` | **CHANGED (VERIFIED)** |
| **Host Working Set Memory (RAM)** | ~4.2 GB (unverified) | **3.55 GB** (`llama-server` 2.75GB + `python` 0.80GB) | Windows `Get-Process` WorkingSet64 | Measured live during active execution | **CHANGED (VERIFIED)** |
| **Outbound Network Telemetry** | "Air-gapped" | **0 outbound sockets (0.00 KB)** | `evidence/netstat_outbound.txt` | `netstat -ano` audit; local network boundary | **VERIFIED** |
| **Test Suite Passed** | 69 passed, 42 skipped | **110 passed, 0 failed, 1 skipped** | `evidence/pytest_full.log` | `uv run pytest -rs` | **CHANGED (VERIFIED)** |
| **Pytest Skip Reason** | "prosody" / "CUDA" | **"the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live"** | `tests/test_conversation.py:68` | Exact raw skip reason from `pytest -rs` | **VERIFIED** |
| **Gemma 4 E2B Quantization Agreement**| 91.4% (Q4_K_M vs FP16) | **NOT MEASURED** | Local disk contains only Q4_0 | FP16 unquantized weights not present locally | **NOT MEASURED** |
| **Ground-Truth Human EMA Agreement** | 77.8% exact / 100% 1-tier | **NOT YET COLLECTED** | `shared_state/ema_records.json` | Toolkit ready (`evaluate_ema.py` & `ema_collector.py`) | **NOT YET COLLECTED / REQUIRES HUMAN** |
| **Live Demonstration Video (.mp4)** | Claimed in submission | **REQUIRES HUMAN** | Script in `DEMO_SCRIPT.md` | Human recording with webcam/mic required | **REQUIRES HUMAN** |

---

## 2. Detailed Summary of Numerical Changes & Root Causes

1. **Facial AU Extraction Latency (1.75 ms $\rightarrow$ 3.97 ms):**
   - *Audit Finding:* The earlier reported 1.75 ms was measured on blank gray frames (`np.full`) where MediaPipe detected no face and exited early.
   - *Resolution:* Re-benchmarked across 4 standardized conditions:
     - Real Face (Normal Light): **3.97 ms mean, 4.81 ms p95** (`evidence/facial_extraction_real.csv`).
     - Real Face (Simulated Dim Light 15% Lux): **4.39 ms mean, 6.84 ms p95** (`evidence/facial_extraction_dim.csv`).
     - Real Face (Simulated Head Turned ~30°): **4.69 ms mean, 6.58 ms p95** (`evidence/facial_extraction_turned.csv`).
     - Blank / Empty Frame: **1.92 ms mean, 2.45 ms p95** (`evidence/facial_extraction_blank.csv`).

2. **Voice Latency (TTFA) Benchmark Upgrade (N=10 $\rightarrow$ N=30 per condition, Alternating Order):**
   - *Audit Finding:* Earlier TTFA claims (0.781s isolated, or 1.411s off / 1.829s on from 10 consecutive turns) did not protect against thermal drift or short-sample variance.
   - *Resolution:* Conducted 30 cycles $\times$ 3 conditions = 90 total turns in strict alternating round-robin order (`scripts/measure_voice_ttfa_30.py`):
     - Loop OFF (N=30): **1.789 s mean / 2.755 s p95** (95% CI: [1.626s, 1.968s]).
     - Loop ON Unmitigated (N=30): **1.382 s mean / 2.060 s p95** (95% CI: [1.262s, 1.515s]).
     - Loop ON Mitigated (N=30): **1.903 s mean / 3.716 s p95** (95% CI: [1.575s, 2.262s]).
     - Concurrency Delta: **+0.114 s**.

3. **Zero-Signal Windows Stored as "insufficient signal" (Task 2):**
   - *Audit Finding:* Zero-signal windows (unlit/covered camera and silent microphone) were previously logged as `Low (Tier 0)`, contaminating baseline relaxation statistics.
   - *Resolution:* Updated `src/parlor/wellness.py`, `src/parlor/triggers.py`, `src/parlor/db.py`, and `tests/test_phase5_live_wellness.py`. Zero-signal windows are logged with `stress_level = "insufficient signal"` and `numeric_score = -1.0`, suppressed from incrementing trigger hysteresis, and filtered out by `scripts/evaluate_ema.py`.

4. **Tier 2 Sweep & WebSocket Trigger Verification (Task 1):**
   - *Sweep:* Tested 10 vectors from mild to extreme with 3 repeats each (N=30 runs) against live Gemma 4 E2B (`evidence/tier_sweep.csv`). Vectors 1-4 mapped to Low (Tier 0), Vectors 5-9 to Moderate (Tier 1), and Vector 10 mapped to High (Tier 2) in 3/3 repeats.
   - *Live WebSocket Trigger:* In Balanced mode (N=3 cycles, 300s cooldown), injected 3 consecutive Tier 2 cycles via `ws://127.0.0.1:8000/ws`. Verified that the server dispatched `Guided 4-7-8 Breathing Exercise` over WebSocket on cycle 3, and suppressed cycle 4 via active 300s cooldown (`evidence/live_ws_intervention_trigger.json`).

5. **Policy Alignment (Task 1):**
   - Harmonized trigger policy parameters across report, slides, `triggers.py`, and `index.html`:
     - **Conservative:** 4 consecutive cycles, 7.5 min (450s) cooldown
     - **Balanced (Default):** 3 consecutive cycles, 5.0 min (300s) cooldown
     - **Sensitive:** 2 consecutive cycles, 3.0 min (180s) cooldown

6. **Target Columns Cleaned (Task 3 & 5):**
   - Retained only the pre-set **5.0-second wellness window budget** as an engineering budget.
   - Rewrote the aspirational TTFA $\le 1.00\text{s}$ objective to an interactive threshold of $\le 2.00\text{s}$ / $2.50\text{s}$ matching physical edge GPU realities.

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
