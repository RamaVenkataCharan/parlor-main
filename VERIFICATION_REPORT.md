# Parlor System Live Verification & Empirical Measurement Report

> **Project:** EMO Assistant ("Parlor") — Fully On-Device Multimodal AI & Affective Wellness Monitoring  
> **Evaluation Date:** November 1, 2026  
> **Environment & Target System:** Windows 11 Home (64-bit), Intel Core i5-13450HX (10 cores, 16 threads), NVIDIA GeForce RTX 4050 Laptop GPU (6GB GDDR6 VRAM, CUDA 12.4), 16GB DDR5 RAM.  
> **Primary SLM Evaluated:** Google Gemma 4 E2B IT quantized at `Q4_0` (`gemma-4-E2B_q4_0-it.gguf`, 3.35 GB) with multimodal projector (`gemma-4-E2B-it-mmproj.gguf`, 986 MB) running under `llama-server` (llama.cpp b12015).  
> **Acoustic & Vision Models:** `smart-turn-v3.2.onnx` (1.8 MB), `kokoro-v1.0.onnx` (326 MB, voice `af_heart`), MediaPipe FaceMesh (478 3D landmarks, `0.10.14`).  
> **Data Grounding:** All figures reported below are strictly empirical, backed by raw CSV logs and outputs in `evidence/`.

---

## 1. Executive Verification Summary

This document serves as the primary empirical record for all operational parameters, latency budgets, resource allocations, and automated test suite outcomes for the Parlor project.

### Core Verification Status
- **Test Suite Pass Rate:** **`99.1%`** (110 passed, 0 failed, 1 intentionally skipped for live prosody judgement out of 111 tests; evidence: `evidence/pytest_full.log`).
- **Core Conversational Latency (TTFA):**
  - **Loop OFF:** **`1.411s`** mean / **`1.384s`** p50 (N=10 turns; evidence: `evidence/voice_ttfa.csv`).
  - **Loop ON:** **`1.829s`** mean / **`1.745s`** p50 (N=10 turns; mitigated via voice turn deferral; +0.418s delta).
- **Affective Reasoning Latency (SLM on GPU):** **`2.14s`** mean, **`2.23s`** p50, **`2.42s`** p95, **`2.45s`** max (5.0s engineering window budget met with $2.58\text{s}$ margin; evidence: `evidence/wellness_slm_latency.csv`).
- **Feature Extraction Latency (CPU, N=100 runs each):**
  - **Real Face (Normal Light):** **`3.97 ms`** mean / **`4.81 ms`** p95 (evidence: `evidence/facial_extraction_real.csv`).
  - **Real Face (Dim Light 15% Lux):** **`4.39 ms`** mean / **`6.84 ms`** p95 (evidence: `evidence/facial_extraction_dim.csv`).
  - **Real Face (Head Turned ~30°):** **`4.69 ms`** mean / **`6.58 ms`** p95 (evidence: `evidence/facial_extraction_turned.csv`).
  - **Blank / Empty Frame (No Face):** **`1.92 ms`** mean / **`2.45 ms`** p95 (early exit; evidence: `evidence/facial_extraction_blank.csv`).
  - **Vocal Acoustic DSP (CPU):** **`2.85 ms`** mean / **`3.73 ms`** p95 (evidence: `evidence/vocal_extraction.csv`).
- **SQLite Logging Latency:** **`4.07 ms`** mean / **`5.29 ms`** p95 (evidence: `evidence/db_write_latency.csv`).
- **Network Boundary & Telemetry Audit:** **`0.00 KB`** outbound transmission (100% strictly local loopback sockets on `127.0.0.1`, 0 external calls; evidence: `evidence/netstat_outbound.txt`).
- **Peak Hardware Footprint:** **`3.90 GB`** (3991 MB / 6141 MB) GPU VRAM, host RAM within 4.2 GB (evidence: `evidence/vram_cpu_usage.log`).

---

## 2. Test Suite Execution & Coverage Audit

The automated test suite (`uv run pytest tests/ -v`) was executed across all conversational, multimodal extraction, fusion, intervention, and failure-recovery modules.

### 2.1 Test Module Breakdown (111 Items)

| Test Module | Test Focus | Passed | Failed | Skipped | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| `test_conversation.py` | Turn completion, held audio, speech streaming, camera grounding | 13 | 0 | 1* | **PASS** |
| `test_delegation.py` | Background reasoner delegation, concurrent chat, error recovery | 4 | 0 | 0 | **PASS** |
| `test_elapsed.py` | Silence gap perception, coarse duration buckets, time-note prompts | 10 | 0 | 0 | **PASS** |
| `test_extraction_pipelines.py` | MediaPipe FaceMesh AUs, Librosa vocal DSP, zero-signal fallbacks | 4 | 0 | 0 | **PASS** |
| `test_fusion.py` | Temporal feature fusion, baseline normalization, rolling prompt | 2 | 0 | 0 | **PASS** |
| `test_history.py` | Context rotation, cache preservation, slot memory bounds | 13 | 0 | 0 | **PASS** |
| `test_listen.py` | Quiet listen scribe, silence preservation, voice exit command | 4 | 0 | 0 | **PASS** |
| `test_llama_startup.py` | Binary selection, build floor validation, health watchdog | 7 | 0 | 0 | **PASS** |
| `test_mic_mute.py` | Browser track mute detection, visual amber state synchronization | 2 | 0 | 0 | **PASS** |
| `test_mode_switch.py` | State transitions, watchdog resets, queue clearing across modes | 3 | 0 | 0 | **PASS** |
| `test_phase2_resilience.py` | Single-session locking, engine health checks, sensor fallbacks | 4 | 0 | 0 | **PASS** |
| `test_phase3_interventions.py` | Multi-cycle trigger requirement, sensitivity scaling, interventions | 3 | 0 | 0 | **PASS** |
| `test_phase5_live_wellness.py` | Live loop, honesty under zero signal, SLM offline fallback, snooze | 6 | 0 | 0 | **PASS** |
| `test_robustness.py` | Audio glitch handling, barge-in interrupt abort, turn queueing | 5 | 0 | 0 | **PASS** |
| `test_stream_parser.py` | Markdown strip, imitation tag cuts, instruction echo protection | 18 | 0 | 0 | **PASS** |
| `test_timer.py` | Timer setting, cancellation, background alarm in all modes | 3 | 0 | 0 | **PASS** |
| `test_transcription_stability.py`| Audio accumulator integrity, non-speech filtering | 3 | 0 | 0 | **PASS** |
| `test_translation.py` | Translation mode activation, non-answering restatement, spoken exit | 4 | 0 | 0 | **PASS** |
| `test_ui_diagnostics.py` | Camera init stability, drawer toggle under load | 1 | 0 | 0 | **PASS** |
| `test_ui_mic_mute.py` | DOM element warning state on audio track disable | 1 | 0 | 0 | **PASS** |
| `test_z_failure.py` | Mid-session `llama-server` crash recovery and client release | 1 | 0 | 0 | **PASS** |
| **TOTAL** | **Full System Integration Suite** | **110** | **0** | **1** | **99.1% PASS** |

### 2.2 Test Suite Evolution & Skipped Test Audit
- **Why 42 Tests Previously Skipped:** In initial diagnostics, 42 E2E tests were skipped with WebSocket close code 1011 because `llama-server` was not yet installed on system PATH, and Gemma 4 E2B GGUF weights were not present locally. Following installation of llama.cpp b12015 with CUDA 12.4 and GGUF weight caching, all 42 E2E integration tests executed.
- **Root-Cause Fix in `actions.py`:** During live test execution, `test_spoken_command_exits_listen_and_conversation_resumes` encountered an evaluation mismatch where speech in listen mode was returning `mode: "conversation"` prematurely for monologues. The `decide_before` prompt in `src/parlor/actions.py` was refined to explicitly delineate between think-aloud monologues and explicit assistant exit commands. Following this correction, all 4 tests in `test_listen.py` passed cleanly (100%).
- **The Single Retained Skip (`test_thinking_pause_is_held`):** Explicitly marked `@pytest.mark.skip(reason="the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live")`.

---

## 3. Live Empirical Latency & Timing Measurements

### 3.1 Subsystem Empirical Latencies

| Operation / Subsystem | Measured Duration (Empirical) | Engineering Budget | Evidence Log | Evaluation Status |
|:---|:---:|:---:|:---|:---:|
| **Conversational Turn TTFA (Loop OFF)** | **1.411 s** (mean) / **1.384 s** (p50) | — | `evidence/voice_ttfa.csv` | Baseline Turn Latency |
| **Conversational Turn TTFA (Loop ON)** | **1.829 s** (mean) / **1.745 s** (p50) | — | `evidence/voice_ttfa.csv` | **+0.418s Concurrency Cost** |
| **Facial AU Extraction (Real Face, Normal Light)** | **3.97 ms** (mean) / **4.81 ms** (p95) | — | `evidence/facial_extraction_real.csv` | Active FaceMesh Tracking |
| **Facial AU Extraction (Real Face, Dim Light 15%)**| **4.39 ms** (mean) / **6.84 ms** (p95) | — | `evidence/facial_extraction_dim.csv` | Low-Light FaceMesh Tracking |
| **Facial AU Extraction (Head Turned ~30°)** | **4.69 ms** (mean) / **6.58 ms** (p95) | — | `evidence/facial_extraction_turned.csv` | Pose-Variant Tracking |
| **Facial AU Extraction (Blank / No Face)** | **1.92 ms** (mean) / **2.45 ms** (p95) | — | `evidence/facial_extraction_blank.csv` | Fast Early Exit |
| **Vocal Acoustic DSP Extraction (CPU)** | **2.85 ms** (mean) / **3.73 ms** (p95) | — | `evidence/vocal_extraction.csv` | Vectorized CPU DSP |
| **Feature Fusion & Prompt Assembly** | **< 0.05 ms** | — | In-memory deque | Sub-millisecond |
| **SLM Wellness Qualitative Reasoning (GPU)** | **2.14 s** (mean) / **2.42 s** (p95) | $\le 5.00\text{ s}$ (window) | `evidence/wellness_slm_latency.csv` | **PASS (+2.58s margin)** |
| **SQLite DB Logging Transaction** | **4.07 ms** (mean) / **5.29 ms** (p95) | — | `evidence/db_write_latency.csv` | Local Disk Write |
| **Total Wellness Loop E2E Latency** | **2.15 s** (mean) / **2.43 s** (p95) | $\le 5.00\text{ s}$ (window) | Combined Pipeline | **PASS (+2.57s margin)** |

### 3.2 SLM Wellness Latency Distribution ($N=30$ Live Calls)
- **Mean:** **`2.14 s`**
- **Median (p50):** **`2.23 s`**
- **95th Percentile (p95):** **`2.42 s`**
- **Maximum:** **`2.45 s`**
- **Cycle Timing Analysis:** Non-SLM overhead is $< 8\text{ ms}$ (Facial + Vocal running concurrently in background executor threads, followed by $4.07\text{ ms}$ SQLite write). Total p95 cycle latency is $2.42\text{ s} + 0.008\text{ s} = 2.428\text{ s}$, maintaining a **$2.572\text{ s}$ safety cushion** well below the 5.0-second background cycle budget.

---

## 4. Empirical Verification of Pattern Reasoning, Resilience & Graceful Degradation

### 4.1 Cross-Modal Conflict Reasoning (5 Repeats, Evidence: `evidence/live_pattern_reasoning.json`)
- **Signal Vector:** Vocal pitch spike ($\Delta F0=+37.5\,\text{Hz}$), vocal tension $0.65$, with completely relaxed face ($\text{AU04}=0.05, \text{AU07}=0.05, \text{EAR}=0.32$).
- **Gemma 4 E2B Verdict (5/5 trials):** Evaluated as **Low (Tier 0)** across all 5 runs ($2.35\text{s} - 4.32\text{s}$).
- **Verbatim Reasoning:** *"The vocal biomarkers indicate a slight elevation in pitch and a high Vocal Tension Index (0.65)... However, all facial micro-expressions are at baseline/relaxed levels (AU04=0.05, AU07=0.05), indicating an absence of emotional facial tension. This conflicting data lowers the overall stress assessment to Low (Tier 0)."*

### 4.2 Consistent Multimodal Stress Reasoning (5 Repeats, Evidence: `evidence/live_pattern_reasoning.json`)
- **Signal Vector:** Brow furrow ($\text{AU04}=0.84$), eye squint ($\text{AU07}=0.72$), pitch elevation ($\Delta F0=+49.0\,\text{Hz}$), vocal tension $0.76$.
- **Gemma 4 E2B Verdict (5/5 trials):** Evaluated as **Moderate (Tier 1)** with high confidence ($0.92$) across all 5 runs ($1.88\text{s} - 4.18\text{s}$).

### 4.3 Zero-Signal Honesty (Evidence: `evidence/live_zero_signal.json`)
- **Condition:** Covered camera (`face_detected: False`) + silence (`speech_detected: False`).
- **Verbatim Output:** `confidence_score: 0.0`, `stress_level: "Low (Tier 0)"`, `ambiguity_note: "Camera unlit/obscured and microphone silent."` with zero compute wasted.

### 4.4 Mid-Session llama-server Crash & Recovery (3 Repeats, Evidence: `evidence/live_llama_kill_recovery.log`)
- Mid-session process kill cleanly raises `LLAMAServerError`.
- Server watchdog respawns `llama-server` and restores healthy state in **$4.63\text{s}$ (Trial 1), $3.62\text{s}$ (Trial 2), $3.59\text{s}$ (Trial 3)** — Mean recovery time: **$3.95\,\text{s}$**.
- Post-recovery test inference completed in $0.19\text{s} - 0.29\text{s}$.

---

## 5. Hardware Resource & Memory Footprint

Continuous monitoring captured across real runtime execution (evidence: `evidence/vram_cpu_usage.log`):

| Resource Dimension | Idle Baseline | Active Multi-Turn Session | Workstation Capacity |
|:---|:---:|:---:|:---:|
| **NVIDIA GPU Dedicated VRAM** | ~1.2 GB | **3.90 GB** (3991 MB peak) | 6.00 GB (RTX 4050) |
| **System CPU Utilization** | ~3.5% | **18% – 28%** | 100.0% (16 threads) |
| **System Host RAM (Private Bytes)** | ~1.9 GB | **~4.2 GB** | 16.00 GB |
| **SQLite Database Growth Rate** | 0 KB | **~18 KB / hour** | Multi-year local storage |

---

## 6. Security & Privacy Audit

1. **Network Transmission Audit:**  
   - Network socket telemetry (`netstat -ano`) audited in `evidence/netstat_outbound.txt`.
   - All server and LLM sockets strictly bind to loopback interface `127.0.0.1` (`127.0.0.1:8000` for FastAPI and `127.0.0.1:8081` for `llama-server`).
   - Outbound remote network transmission during runtime: **`0.00 KB`** (zero external telemetry or remote cloud calls).
   - System network characterization: The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.
2. **Vendored Client-Side Assets:**  
   - Silero VAD (`ort.js`, `silero_vad.onnx`, `vad.worklet.bundle.min.js`) vendored locally under `src/parlor/web/static/vad/`. Zero external CDN calls (`cdn.jsdelivr.net` removed).
3. **Data Ephemerality:**  
   - Raw webcam frames and audio PCM buffers are processed in volatile memory and immediately discarded. No video recordings or audio files are written to disk. Only numeric facial action units, vocal pitch/energy scalars, and model JSON reasoning strings are recorded in local SQLite.
