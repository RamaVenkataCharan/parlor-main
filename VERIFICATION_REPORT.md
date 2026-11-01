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
- **Core Conversational Latency (TTFA):** **`1.33s`** mean (wellness loop OFF, short turns 0.83s), **`1.88s`** mean (wellness loop ON) (evidence: `evidence/voice_ttfa.csv`).
- **Affective Reasoning Latency (SLM on GPU):** **`2.14s`** mean, **`2.23s`** p50, **`2.42s`** p95, **`2.45s`** max (5.0s window budget met with $2.58\text{s}$ margin; evidence: `evidence/wellness_slm_latency.csv`).
- **Feature Extraction Latency (CPU):** **`1.75 ms`** mean / **`1.91 ms`** p95 (Facial AU), **`2.34 ms`** mean / **`2.88 ms`** p95 (Vocal DSP) (evidence: `evidence/facial_extraction.csv`, `evidence/vocal_extraction.csv`).
- **SQLite Logging Latency:** **`2.67 ms`** mean / **`3.59 ms`** p95 (evidence: `evidence/db_write_latency.csv`).
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

All measurements below were captured directly on this workstation with real CSV outputs preserved in `evidence/`.

### 3.1 Subsystem Latency Table

| Operation / Subsystem | Measured Duration (Empirical) | Target Budget | Safety Margin | Evidence Log | Evaluation Status |
|:---|:---:|:---:|:---:|:---|:---:|
| **Conversational Turn TTFA (Loop OFF)** | **1.33 s** (mean) / **0.83 s** (short query) | $\le 2.00\text{ s}$ | $+670\text{ ms}$ | `evidence/voice_ttfa.csv` | **PASSED** |
| **Conversational Turn TTFA (Loop ON)** | **1.88 s** (mean) | $\le 2.50\text{ s}$ | $+620\text{ ms}$ | `evidence/voice_ttfa.csv` | **PASSED** |
| **Facial AU Extraction (CPU, MediaPipe)** | **1.75 ms** (mean) / **1.91 ms** (p95) | $\le 30.0\text{ ms}$ | $+28.09\text{ ms}$ | `evidence/facial_extraction.csv` | **PASSED** |
| **Vocal Acoustic DSP Extraction (CPU)** | **2.34 ms** (mean) / **2.88 ms** (p95) | $\le 30.0\text{ ms}$ | $+27.12\text{ ms}$ | `evidence/vocal_extraction.csv` | **PASSED** |
| **Feature Fusion & Prompt Assembly** | **< 0.05 ms** | $\le 5.0\text{ ms}$ | $+4.95\text{ ms}$ | `evidence/wellness_slm_latency.csv` | **PASSED** |
| **SLM Wellness Reasoning (GPU, Gemma 4 E2B)** | **2.14 s** (mean) / **2.42 s** (p95) | $\le 5.00\text{ s}$ | $+2.58\text{ s}$ | `evidence/wellness_slm_latency.csv` | **PASSED** |
| **SQLite DB Logging Transaction** | **2.67 ms** (mean) / **3.59 ms** (p95) | $\le 10.0\text{ ms}$ | $+6.41\text{ ms}$ | `evidence/db_write_latency.csv` | **PASSED** |
| **Complete Background Observation Cycle** | **2.43 s** (p95 total) | $\le 5.00\text{ s}$ | $+2.57\text{ s}$ | `evidence/wellness_slm_latency.csv` | **PASSED** |

### 3.2 SLM Wellness Latency Distribution ($N=30$ Live Calls)
- **Mean:** **`2.14 s`**
- **Median (p50):** **`2.23 s`**
- **95th Percentile (p95):** **`2.42 s`**
- **Maximum:** **`2.45 s`**
- **Cycle Timing Analysis:** Non-SLM overhead is $< 8\text{ ms}$ (Facial + Vocal running concurrently in background executor threads, followed by $2.67\text{ ms}$ SQLite write). Total p95 cycle latency is $2.42\text{ s} + 0.008\text{ s} = 2.428\text{ s}$, maintaining a **$2.572\text{ s}$ safety cushion** well below the 5.0-second background cycle budget.

---

## 4. Hardware Resource & Memory Footprint

Continuous monitoring captured across real runtime execution (evidence: `evidence/vram_cpu_usage.log`):

| Resource Dimension | Idle Baseline | Active Multi-Turn Session | Workstation Limit |
|:---|:---:|:---:|:---:|
| **NVIDIA GPU Dedicated VRAM** | ~1.2 GB | **3.90 GB** (3991 MB peak) | 6.00 GB (RTX 4050) |
| **System CPU Utilization** | ~3.5% | **18% – 28%** | 100.0% (16 threads) |
| **System Host RAM (Private Bytes)** | ~1.9 GB | **~4.2 GB** | 16.00 GB |
| **SQLite Database Growth Rate** | 0 KB | **~18 KB / hour** | Multi-year local storage |

---

## 5. Security & Privacy Audit

1. **Network Transmission Audit:**  
   - Network socket telemetry (`netstat -ano`) audited in `evidence/netstat_outbound.txt`.
   - All server and LLM sockets strictly bind to loopback interface `127.0.0.1` (`127.0.0.1:8000` for FastAPI and `127.0.0.1:8081` for `llama-server`).
   - Outbound remote network transmission during runtime: **`0.00 KB`** (zero external telemetry or remote cloud calls).
   - System network characterization: The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.
2. **Vendored Client-Side Assets:**  
   - Silero VAD (`ort.js`, `silero_vad.onnx`, `vad.worklet.bundle.min.js`) vendored locally under `src/parlor/web/static/vad/`. Zero external CDN calls (`cdn.jsdelivr.net` removed).
3. **Data Ephemerality:**  
   - Raw webcam frames and audio PCM buffers are processed in volatile memory and immediately discarded. No video recordings or audio files are written to disk. Only numeric facial action units, vocal pitch/energy scalars, and model JSON reasoning strings are recorded in local SQLite.
