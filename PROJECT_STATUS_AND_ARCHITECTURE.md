# Parlor — System Architecture & Post-Integration Verification Status

> **Project:** EMO Assistant ("Parlor") — Multimodal Affective Voice & Vision Assistant  
> **Architecture Status:** Single-Process Live WebSocket Unified Architecture (Primary Production Path)  
> **Fallback/Dev Mode:** Decoupled Two-Process File Pipeline (`person_a_loop.py` / `person_b_loop.py`)  

---

## 1. Executive Overview

Parlor is a privacy-first, on-device multimodal assistant combining two complementary real-time cognitive loops operating concurrently within a single unified process:

1. **System 1 (Conversational Interaction Loop):** Conversational voice and vision pipeline powered by on-device acoustic turn detection (`smart-turn-v3.2`), quantized local SLM inference (`llama-server` hosting Google Gemma 4 E2B Q4_0), and neural text-to-speech (`kokoro-onnx`). Measured voice TTFA is **$1.411\,\text{s}$ mean** (loop off) and **$1.829\,\text{s}$ mean** (loop on).
2. **System 2 (Affective Wellness Monitoring Loop):** Continuous, passive stress and burnout detection that extracts facial Action Units (`MediaPipe FaceMesh`) and vocal acoustic biomarkers (`librosa`/DSP), aggregates them across rolling temporal windows, and performs explainable qualitative reasoning via local SLM without relying on brittle fixed numeric thresholds. Triggered micro-interventions are pushed directly over WebSocket to the client UI with full provenance disclosure.

```
+-----------------------------------------------------------------------------------------------+
|                                  BROWSER CLIENT (localhost:8000)                             |
|                                                                                               |
|  [ Webcam Stream ]     [ Microphone PCM ]       [ Audio Synthesizer ]      [ UI Interventions ]
|          |                     |                         ^                          ^         |
+----------|---------------------|-------------------------|--------------------------|---------+
           | (image frames)      | (audio chunks)          | (TTS audio PCM)          | (events)|
           v                     v                         |                          |         |
+-------------------------------------------------------------------------------------|---------+
|                               FASTAPI / UVICORN APPLICATION (server.py)             |         |
|                                                                                     |         |
|  +--------------------------------------------+  +----------------------------------|------+  |
|  |       SYSTEM 1: CONVERSATIONAL VOICE       |  |     SYSTEM 2: WELLNESS MONITOR   |      |  |
|  |                                            |  |                                  |      |  |
|  |   SmartTurn Detector (40-80ms)             |  |   FacialExtractor (AU04, AU07, EAR)|      |  |
|  |              |                             |  |   VocalExtractor (F0, Jitter, HF)  |      |  |
|  |   Speculative Cache Priming                |  |              |                     |      |  |
|  |              |                             |  |   FeatureFusionEngine (Window=5)   |      |  |
|  |   Llama-Server (Gemma 4 E2B Q4 GGUF)       |  |              |                     |      |  |
|  |              |                             |  |   Explainable SLM Reasoning        |      |  |
|  |   Kokoro-ONNX Neural TTS (24kHz)           |  |   (loop.run_in_executor offload)   |      |  |
|  |              |                             |  |              |                     |      |  |
|  |              +-----------------------------+  |   TriggerManager (Sensitivity Mode)|      |  |
|  |                                               |   InterventionGenerator            |      |  |
|  |                                               |              |                     |      |  |
|  |                                               |   SQLite Store (wellness_history)  |      |  |
|  |                                               |   WebSocket Push Dispatch ---------+      |  |
|  +-----------------------------------------------+  +----------------------------------------+  |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Primary Architecture: Single-Process Live Integration

In Phase 5, the two previously separate systems were consolidated into a unified single process inside `src/parlor/server.py`:

- **Lifespan Initialization:** FastAPI's async lifespan launches `WellnessService` alongside `llama-server`, loading neural backends in parallel.
- **WebSocket Multiplexing:** Client camera snapshots and speech chunks stream over `/ws`. Audio and video frames feed the conversational turn detector and simultaneously update `WellnessService` rolling feature extractors.
- **Voice Turn Deferral & Concurrency Protection:** SLM wellness reasoning queries (`_call_slm_reasoning`) run in Python's default thread pool executor via `loop.run_in_executor(None, ...)`. During active conversational turns, background wellness SLM reasoning cycles are deferred (`wellness_service.set_voice_active(True)`) to preserve conversational slot responsiveness and protect slot 0 KV cache tokens.
- **Direct Event Dispatch:** When the anti-false-positive trigger policy requirements are satisfied, `WellnessService` invokes `dispatch_wellness_intervention`, instantly pushing an `intervention_triggered` WebSocket payload to the client UI.
- **Live Diagnostics & Control Messages:** The client UI dynamically communicates with `WellnessService` over WebSocket via:
  - `set_wellness_sensitivity`: Toggles between `conservative` ($N=4$, cooldown 450s), `balanced` ($N=3$, cooldown 300s), and `sensitive` ($N=2$, cooldown 180s).
  - `set_wellness_mute`: Instantly disables or enables pop-up intervention notifications.
  - `snooze_wellness`: Postpones wellness interventions for a user-specified interval (default 10 minutes).
  - `wellness_telemetry`: Periodic lightweight snapshot payload updating diagnostic bars.

---

## 3. Fallback / Development Architecture: Two-Process Pipeline

For standalone testing, debugging, or resource-constrained headless environments, the original decoupled two-process architecture remains operational:

- **Person A Producer (`person_a_loop.py`):** Captures OpenCV video frames and microphone audio, computes facial Action Units and acoustic features, and writes an atomic JSON snapshot to `shared_state/latest_features.json`.
- **Person B Consumer (`person_b_loop.py`):** Watches `shared_state/latest_features.json`, formats structured fusion prompts, queries `llama-server` via `person_b_slm_reasoning.py`, logs reasoning verdicts to the console, and triggers desktop notifications.
- **Atomic File Sync:** `write_features_atomically` in `wellness.py` maintains `shared_state/latest_features.json` continuously even during single-process runs, allowing external observability tools to monitor real-time features without interfering with WebSocket operations.

---

## 4. Hardware Verification & Performance Metrics (Empirically Measured)

All figures measured on **Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 6GB GPU, Windows 11**:

| Metric | Engineering Budget | Workstation Measured (RTX 4050 + i5 CPU) | Edge Tier (Raspberry Pi 5) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Conversational Turn TTFA (Loop OFF)** | — | **$1.411\,\text{s}$** (p50: $1.384\,\text{s}$, N=10) | Untested | Empirical Baseline (`evidence/voice_ttfa.csv`) |
| **Conversational Turn TTFA (Loop ON)** | — | **$1.829\,\text{s}$** (p50: $1.745\,\text{s}$, N=10) | Untested | **+0.418s Latency Cost** (Mitigated) |
| **Facial AU Extraction Latency (Real Face)** | — | **$3.97\,\text{ms}$** (p95: $4.81\,\text{ms}$, N=100) | Literature est: ~38.2 ms | Real face tracking (`evidence/facial_extraction_real.csv`) |
| **Facial AU Extraction (Dim Light / Turned)**| — | **$4.39\,\text{ms}$ / $4.69\,\text{ms}$** | Literature est | Robust under non-ideal angles |
| **Facial AU Extraction (Blank / No Face)** | — | **$1.92\,\text{ms}$** (p95: $2.45\,\text{ms}$, N=100) | Literature est | Early exit without face |
| **Vocal Acoustic DSP Latency** | — | **$2.85\,\text{ms}$** (p95: $3.73\,\text{ms}$, N=100) | Literature est: ~18.6 ms | Fast vectorized CPU DSP (`evidence/vocal_extraction.csv`) |
| **Multimodal Feature Fusion** | — | **$0.02\,\text{ms}$** | Literature est: ~0.05 ms | In-memory deque aggregation |
| **SLM Reasoning Generation (GPU)** | $\le 5.0\,\text{s}$ (window) | **$2.14\,\text{s}$** mean (p95: $2.42\,\text{s}$, N=30) | Literature est: ~4.15 s | **PASS** (+2.58s margin within 5.0s window) |
| **SQLite Persistence Write** | — | **$4.07\,\text{ms}$** (p95: $5.29\,\text{ms}$, N=100) | Literature est | Local synchronous write (`evidence/db_write_latency.csv`) |
| **Peak GPU VRAM Utilization** | — | **$3.90\,\text{GB}$** (3991 MB / 6141 MB) | N/A | Fully resident in 6GB VRAM |
| **Outbound Network Traffic** | **$0.0\,\text{KB}$** | **$0.00\,\text{KB}$ (0 Outbound Sockets)** | $0.00\,\text{KB}$ | **PASS** (`evidence/netstat_outbound.txt`) |

---

## 5. Persistence Store Specification

Longitudinal stress history is stored on-device in SQLite (`shared_state/wellness_history.db`).

### Table Schema: `stress_assessments`
```sql
CREATE TABLE IF NOT EXISTS stress_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    stress_level TEXT NOT NULL,
    numeric_score REAL NOT NULL,
    primary_drivers TEXT,        -- JSON array of specific biomarker deviations
    reasoning TEXT,              -- Clinically grounded plain-language explanation
    confidence REAL,             -- Confidence score [0.0 - 1.0]
    intervention_fired INTEGER,  -- 1 if an intervention card was triggered, 0 otherwise
    intervention_type TEXT,      -- Somatic, Cognitive, or Environmental category
    metadata TEXT                -- JSON object with trigger cycle count, cooldown, etc.
);
```

REST Endpoint `/api/wellness/history` exposes this table to the frontend and export scripts without exposing private raw video frames or audio recordings.
