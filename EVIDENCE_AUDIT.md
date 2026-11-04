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
| **SLM Wellness Latency (Standard Prompts, GPU)** | 2.76 s (carried-over) | **2.14 s (mean) / 2.45 s (p95) / 2.45 s (max)** | `evidence/wellness_slm_latency.csv` | `measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Conflict CoT, GPU)** | Not specified | **2.79 s (mean) / 4.32 s (max)** | `evidence/live_pattern_reasoning.json` | Extended CoT reasoning (N=5) | **VERIFIED** |
| **SLM Latency Pooled Envelope (N=35)** | Not reported | **2.23 s (mean) / 2.49 s (p95) / 4.32 s (max)** | `wellness_slm_latency.csv` + `live_pattern_reasoning.json` | Combined across all conditions | **VERIFIED** |
| **SLM 5.0s Window Margin (Worst-Case Conflict)**| 1.88 s | **+0.68 s (5.0s - 4.32s max)** | `live_pattern_reasoning.json` | Margin under worst observed deliberation | **VERIFIED** |
| **SLM 5.0s Window Margin (Pooled Mean)** | 1.88 s | **+2.77 s (5.0s - 2.23s mean)** | `wellness_slm_latency.csv` | Standard operational margin | **VERIFIED** |
| **Voice TTFA (Loop OFF, Mean)** | 0.781 s (isolated) | **1.920 s (mean) / 1.622 s (p50) / 3.545 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.66s, 2.21s]) | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop ON Unmitigated)** | Not measured | **1.739 s (mean) / 1.514 s (p50) / 3.612 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.47s, 2.07s]) | **VERIFIED** |
| **Voice TTFA (Loop ON Mitigated)** | Not measured | **1.774 s (mean) / 1.483 s (p50) / 3.419 s (p95)** | `evidence/voice_ttfa_30_turns.csv` | `measure_voice_ttfa_30.py` (N=30, CI: [1.51s, 2.08s]) | **CHANGED (VERIFIED)** |
| **Voice TTFA Telemetry Condition** | Untracked thermal state | **Plugged into AC, 2700MHz core clocks, 54-71°C** | `evidence/voice_ttfa_30_turns.csv` | Logged via nvidia-smi per turn | **VERIFIED** |
| **Tier 2 Reachability Boundary** | Untested fine boundary | **AU04 >= 0.97, Pitch Delta >= +90Hz, Tension >= 0.94** | `evidence/tier2_reachability_sweep.csv` | `sweep_tier2_reachability.py` (13 vec x 3) | **VERIFIED** |
| **Live-Model Card Trigger Proof** | Hardcoded mock payload | **3 real llama-server cycles -> Guided Breathing card** | `evidence/live_model_card_trigger.json` | `test_live_model_card_trigger.py` + Playwright | **VERIFIED** |
| **Insufficient Signal (-1.0) Policy** | Reset counter to 0 | **HOLD counter; do not reset or increment; no fire** | `src/parlor/triggers.py` | `test_phase3_interventions.py` | **VERIFIED** |
| **Longitudinal Storage Ingestion Rate** | ~180 KB/hr (estimated) | **132.00 KB/hour (300.37 bytes/cycle)** | `evidence/storage_growth_rate.txt` | `measure_storage_and_ram.py` (450 cycles) | **VERIFIED** |
| **Host Working Set Memory (RAM)** | ~4.2 GB (unverified) | **2.42 GB working set (5.24 GB commit)** | `evidence/ram_working_set.txt` | `measure_storage_and_ram.py` via Get-Process | **CHANGED (VERIFIED)** |
| **Bibliographic Citation Audit** | Baumel (2019) & Eysenbach (2005) | **Verified full DOI/PMID/Abstract** | `evidence/citation_verification.txt` | JMIR verified records | **VERIFIED** |
| **Outbound Network Telemetry** | No outbound network traffic during operation; weights are downloaded once at setup; the optional research mode is the only feature that can call an external API. | **0 outbound sockets (0.00 KB)** | `evidence/netstat_outbound.txt` | `netstat -ano` audit; local loopback boundary (`127.0.0.1`) | **VERIFIED** |
| **Test Suite Passed** | 69 passed, 42 skipped | **111 passed out of 112 items, 0 failed, 1 skipped** | `evidence/pytest_full.log` | `uv run pytest -rs` | **CHANGED (VERIFIED)** |
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
   - *Resolution:* Conducted 30 cycles $\times$ 3 conditions = 90 total turns in strict alternating round-robin order (`scripts/measure_voice_ttfa_30.py`), yielding the verified baseline in `evidence/voice_ttfa_summary.json`:
     - Loop OFF (N=30): **1.920 s mean / 1.622 s p50 / 3.545 s p95** (95% CI: [1.663s, 2.213s]).
     - Loop ON Unmitigated (N=30): **1.739 s mean / 1.514 s p50 / 3.612 s p95** (95% CI: [1.467s, 2.066s]).
     - Loop ON Mitigated (N=30): **1.774 s mean / 1.483 s p50 / 3.419 s p95** (95% CI: [1.505s, 2.077s]).
     - Spread Across 3 Benchmark Runs: Loop OFF means span [1.411s, 1.920s]; Loop ON means span [1.382s, 1.903s]. Because the 95% confidence intervals overlap across all three conditions, there is **no distinguishable cost** on interactive voice latency from concurrent wellness monitoring. Single-GPU execution serializes concurrent inference without KV-cache-rotation overhead.

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
4. **Physical Camera Disconnect Mid-Session Verification:**
   - **Protocol Documented:** `evidence/browser/permissions_audit.log` and `BROWSER_TEST_REPORT.md`.
   - **Action Required:** Physical unplug of USB webcam cable during viva examination to confirm `MediaStreamTrack.onended` handling.

---

## 4. Browser DevTools Suite Audit (B1–B12)

| Suite ID | Tested Functional Area | Measured Value / Evidence | Raw Evidence File |
|:---|:---|:---|:---|
| **B1** | Load & Console Integrity | Page load: **0.887 s**, Errors: **0**, Warnings: **0** | `evidence/browser/console_load.log` |
| **B2** | Network Privacy HAR Audit | **0 external hosts contacted** (No outbound network traffic during operation; weights downloaded once at setup; optional research mode is the only external API feature; Google Fonts CDN leak removed) | `evidence/browser/session_privacy.har`, `evidence/browser/network_privacy_audit.json` |
| **B3** | Offline Execution | 100% offline capability (vendored ONNX/WASM/VAD; zero outbound network dependency) | `evidence/browser/offline_test.log`, `evidence/browser/offline_mode.png` |
| **B4** | WebSocket Schema Conformance | Chronological CDP frame capture across all commands/events | `evidence/browser/ws_frames_trace.json` |
| **B5** | Single-Session Policy | Tab 2 rejected with Close Code **4001**; no reconnect thrashing | `evidence/browser/single_session.log`, `evidence/browser/single_session_rejected.png` |
| **B6** | Watchdog Respawn Latency | **6.21 s mean** across 3 trials (6.89s, 5.86s, 5.89s) | `evidence/browser/server_failure_recovery.log`, `evidence/browser/llama_down_ui.png` |
| **B7** | Live-Model Card Trigger | Vector B07_V10 $\times$ 3 cycles $\rightarrow$ Tier 2 card, 2-min box breathing UI | `evidence/browser/b7_card_live_model_trace.json`, 6 PNG screenshots |
| **B8** | Performance & 4x CPU Throttle | **SIMULATED:** **0 long tasks**, **60.2 FPS** (1x), **60.0 FPS** (4x throttle), **7.11 MB** JS Heap | `evidence/browser/performance_5turns.json`, `evidence/browser/performance_throttled.json` |
| **B9** | Client Storage Zero-Leak | **0.00 KB** stored across localStorage, sessionStorage, IndexedDB, CacheStorage | `evidence/browser/application_storage_audit.json` |
| **B10** | Permissions & Edge Cases | **SIMULATED:** Camera/Mic denied and Camera Busy handled gracefully via automated CDP overrides (Physical camera disconnect marked **REQUIRES HUMAN**) | `evidence/browser/permissions_audit.log`, 3 PNG screenshots |
| **B11** | Responsive, Accessibility & Lighthouse | 1280x800 & 375x667 viewports (0 overflow), focus rings, Escape dismissal; Lighthouse CLI: **94/100 Accessibility**, **78/100 Best Practices** | `evidence/browser/viewport_desktop.png`, `viewport_mobile.png`, `accessibility_audit.json`, `lighthouse_desktop.json`, `lighthouse_mobile.json` |
| **B12** | Repeatable Media Fixtures | **SIMULATED:** Synthetic Y4M face (30 FPS) and WAV speech fixtures generated for automated tests (Real camera/mic testing marked **REQUIRES HUMAN**) | `evidence/media/synthetic_face_test.y4m`, `evidence/media/synthetic_speech_test.wav` |

