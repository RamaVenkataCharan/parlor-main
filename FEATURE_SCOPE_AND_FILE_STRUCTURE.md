# Parlor — File Structure & Feature Scope Specification

> **Project:** EMO Assistant ("Parlor") — Fully On-Device Multimodal AI Voice, Vision & Affective Wellness Assistant  
> **Document Purpose:** Complete reference specification of project file organization, component responsibilities, real-time feature capabilities, architectural data flows, and operational scope.

---

## 1. Executive Summary

**Parlor** is a privacy-first, on-device multimodal AI assistant capable of real-time conversational voice interaction, visual understanding via camera stream, hands-free turn-taking, neural text-to-speech synthesis, and passive affective stress/wellness monitoring.

Operating as a unified single process, Parlor coordinates two complementary cognitive architectures:
1. **System 1 (Conversational Interaction Engine):** Low-latency cascade pipeline achieving **Time to First Audio (TTFA measured: $1.411\,\text{s}$ loop off, $1.829\,\text{s}$ loop on)** through acoustic turn-taking classification (`smart-turn-v3.2`), speculative prompt cache prefilling on `llama-server` (Google Gemma 4 E2B Q4_0), and local neural TTS (`kokoro-onnx`).
2. **System 2 (Affective Wellness Monitoring Engine):** Continuous on-device stress analysis extracting facial Action Units via MediaPipe FaceMesh and vocal acoustic biomarkers via Librosa/DSP. It reasons qualitatively over rolling feature windows using the local SLM, records longitudinal trends in an on-device SQLite store, and delivers personalized micro-interventions over WebSocket without relying on brittle fixed numeric thresholds.

---

## 2. Directory & File Structure

```
parlor-main/
│
├── .env                                # Environment variable overrides (API keys, ports, model paths)
├── .env.example                        # Template for environment configuration
├── .gitignore                          # Git exclusions (.venv, cached models, temporary files)
├── CHANGELOG.md                        # Historical log of version updates and release notes
├── DEMO_SCRIPT.md                      # 5-10 minute presentation & defense walkthrough script
├── FEATURE_SCOPE_AND_FILE_STRUCTURE.md  # Complete project feature scope & directory specification
├── FYP_RESULTS_SUMMARY.md              # One-page results & benchmark summary for FYP defense
├── LICENSE                             # Software license (MIT)
├── PROJECT_DEVELOPMENT_REPORT.md       # Comprehensive status report & milestone breakdown
├── PROJECT_STATUS_AND_ARCHITECTURE.md  # System status, unified architecture & benchmark overview
├── QUANTIZATION_BENCHMARK.md           # Quantization tradeoffs & tier agreement benchmarks
├── REASONING_EXAMPLES.md               # Catalogue of grounded multimodal SLM reasoning outputs
├── README.md                           # Primary documentation, setup guide & quick start
├── pyproject.toml                      # Python project configuration, dependencies, and entrypoints
├── start.ps1                           # PowerShell launcher script for Windows environment
├── stop.ps1                            # PowerShell script to stop server and clean up processes
├── person_a_loop.py                    # Fallback/dev producer: webcam/mic capture & feature export
├── person_b_loop.py                    # Fallback/dev consumer: feature reader & SLM reasoner loop
├── person_b_slm_reasoning.py           # Fallback/dev standalone SLM reasoning HTTP caller
├── uv.lock                             # Lockfile maintaining strict package dependency trees
│
├── shared_state/                       # On-device persistent data store & IPC
│   ├── latest_features.json            # Atomic rolling feature vector snapshot (fallback/inspection)
│   └── wellness_history.db             # On-device SQLite longitudinal stress assessment database
│
├── docs/                               # Documentation suite
│   ├── configuration.md                # Detailed reference for configuration flags & env variables
│   ├── INTERVENTION_LOGIC.md           # Clinical taxonomy of micro-interventions and trigger rules
│   └── DATASET_AND_GROUND_TRUTH.md     # Ground-truth evaluation protocols & survey instruments
│
├── src/                                # Core application source code
│   └── parlor/                         # Main Python package
│       ├── __init__.py                 # Package initialization marker
│       ├── actions.py                  # Action grammar rules, tool definitions (timers, search, modes)
│       ├── db.py                       # Local SQLite persistence store for wellness history
│       ├── facial.py                   # MediaPipe FaceMesh AU extractor (AU04, AU07, AU15, AU20, EAR)
│       ├── fusion.py                   # Multimodal temporal feature fusion & prompt constructor
│       ├── interventions.py            # Micro-intervention generator (Somatic, Cognitive, Environmental)
│       ├── llama.py                    # Process controller & HTTP client for llama-server
│       ├── modes.py                    # System operating modes (Conversation, Translation, Listen)
│       ├── pipeline.py                 # Main pipeline orchestrator connecting turns, LLM, TTS, & actions
│       ├── reasoner.py                 # Asynchronous background web research engine (isolated)
│       ├── server.py                   # FastAPI server, unified WebSocket gateway, static asset routing
│       ├── triggers.py                 # Anti-false-positive trigger manager (sensitivity, cooldown)
│       ├── tts.py                      # Neural text-to-speech synthesis engine (Kokoro-ONNX)
│       ├── turn_detector.py            # Acoustic end-of-turn classifier (smart-turn-v3.2 ONNX)
│       ├── vocal.py                    # Vocal acoustic biomarker extractor (F0, Jitter, Shimmer, Tension)
│       ├── wellness.py                 # Unified wellness service coordinator & background reasoning task
│       └── web/                        # Frontend single-page application
│           ├── index.html              # Main HTML layout, intervention card, wellness settings
│           └── static/
│               ├── app.js              # Web Audio API recorder, WebSocket client, wellness telemetry
│               └── style.css           # Dark theme styling, intervention cards, diagnostics drawer
│
├── tests/                              # Comprehensive Pytest test suite (22+ modules)
│   ├── conftest.py                     # Test fixtures, mock environments, and server hooks
│   ├── test_conversation.py            # End-to-end conversation flow verification
│   ├── test_delegation.py              # Delegation mode and background research testing
│   ├── test_elapsed.py                 # Timing precision and time-awareness tests
│   ├── test_extraction_pipelines.py    # Unit tests for facial Action Units and vocal DSP extractors
│   ├── test_fusion.py                  # Unit tests for temporal fusion and prompt formatting
│   ├── test_history.py                 # Multi-turn conversation state & history retention tests
│   ├── test_listen.py                  # Passive listening (scribe) mode testing
│   ├── test_llama_startup.py           # Subprocess lifecycle and readiness checks for llama-server
│   ├── test_mic_mute.py                # Hardware mic mute detection & amber indicator tests
│   ├── test_mode_switch.py             # State machine transition tests between operating modes
│   ├── test_phase2_resilience.py       # SLM offline degradation, malformed JSON recovery, and backoff
│   ├── test_phase3_interventions.py    # Trigger policies, sensitivity thresholds, cooldowns, snooze
│   ├── test_phase5_live_wellness.py    # Live WebSocket unification, controls, and SQLite store tests
│   ├── test_robustness.py              # Network dropouts, malformed data, and fault tolerance tests
│   ├── test_stream_parser.py           # Streaming token parser and action tag extraction tests
│   ├── test_timer.py                   # Countdown timer creation, ring, and cancellation tests
│   ├── test_transcription_stability.py # Audio stream integrity & transcription alignment tests
│   ├── test_translation.py            # Consecutive live translation mode testing
│   ├── test_ui_diagnostics.py          # Browser automation tests for diagnostic drawer clicks
│   ├── test_ui_mic_mute.py             # Browser automation tests for mic mute warning banner
│   ├── test_z_failure.py               # Edge case failure modes and graceful error recovery
│   └── util.py                         # Helper functions and mock streaming data generators
│
└── benchmarks/                         # Performance evaluation and latency measurement suite
    ├── archbench.py                    # End-to-end architecture latency & token throughput benchmark
    ├── bench.py                        # Master benchmark runner for regression testing
    ├── benchmark_tts.py                # TTS audio synthesis latency and RTF (Real-Time Factor) probe
    ├── camerabench.py                  # Camera frame prefilling overhead & cache priming benchmark
    ├── compare.py                      # Benchmark comparison script across multiple runs
    ├── fixtures.py                     # Benchmark dataset fixtures and audio input samples
    ├── legacy_tags.py                  # Comparative benchmark for in-band vs grammar-forced actions
    ├── tagbench.py                     # Action tag classification latency & accuracy benchmark
    ├── timerprobe.py                   # Timer precision & background execution probe
    └── turnbench.py                    # Smart-Turn classifier latency & decision boundary evaluation
```

---

## 3. Comprehensive File Catalog & Module Breakdown

### 3.1 Core Conversational Modules (`src/parlor/`)

| File / Component | Primary Responsibility | Key Functions & Dependencies |
| :--- | :--- | :--- |
| [`server.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/server.py) | **Unified Gateway**: Hosts FastAPI lifespan, `/ws` WebSocket connection, static asset routing, and dispatches turn-taking & wellness interventions. | FastAPI, Uvicorn, WebSockets, asyncio. |
| [`pipeline.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/pipeline.py) | **Central Orchestrator**: Coordinates turn detection, prompt cache priming, LLM request streaming, sentence parsing, action execution, and TTS generation. | Asyncio pipelines, cache management. |
| [`turn_detector.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/turn_detector.py) | **Smart Turn Classifier**: Evaluates whether user finished their thought using `smart-turn-v3.2` ONNX model (~70ms execution). | ONNX Runtime, NumPy, audio windowing. |
| [`llama.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/llama.py) | **LLM Subprocess Wrapper**: Spawns and manages `llama-server` hosting Gemma 4 GGUF models. Handles HTTP completions, prefix caching, and health checks. | Subprocess management, requests/httpx. |
| [`tts.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/tts.py) | **Speech Synthesizer**: Converts text sentences into 24 kHz raw PCM audio using `kokoro-onnx` neural model running on local CPU/GPU. | Kokoro ONNX, SoundFile, base64 encoding. |
| [`actions.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/actions.py) | **Grammar-Forced Action Engine**: Parses and executes structured JSON tool calls (timers, web search, mode switches) out-of-band to prevent speech corruption. | Regex, GBNF/JSON grammar specifications. |
| [`reasoner.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/reasoner.py) | **Background Web Research**: Offloads complex research tasks to external frontier models (e.g. OpenRouter) asynchronously. Strictly isolated from the wellness pipeline. | Async HTTP client, web search integration. |
| [`modes.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/modes.py) | **Operating Mode Handler**: Manages system state shifts between Conversation, Live Translation, Passive Listening, and Delegation modes. | Enum definitions, state transition logic. |

### 3.2 Affective Wellness Modules (`src/parlor/`)

| File / Component | Primary Responsibility | Key Functions & Dependencies |
| :--- | :--- | :--- |
| [`wellness.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/wellness.py) | **Wellness Service Controller**: Runs 8-second observation loop, aggregates multimodal features, delegates reasoning to SLM via non-blocking executor, and triggers alerts. | Asyncio, executor offload, background task. |
| [`db.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/db.py) | **Local Persistence Store**: SQLite interface maintaining `stress_assessments` table in `shared_state/wellness_history.db` with query endpoints. | SQLite3, thread-safe connections. |
| [`facial.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/facial.py) | **Facial Feature Extractor**: Computes eyebrow furrowing (AU04), eye squinting (AU07), mouth corner drop (AU15), jaw tension (AU20), and eye aspect ratio (EAR). | MediaPipe FaceMesh, OpenCV, NumPy. |
| [`vocal.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/vocal.py) | **Vocal Biomarker Extractor**: Computes fundamental frequency (F0 delta/SD), jitter, shimmer, pause ratio, and high-frequency spectral tension. | Librosa, NumPy, SciPy DSP. |
| [`fusion.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/fusion.py) | **Feature Fusion Engine**: Maintains rolling temporal window (5 cycles), normalizes signals against baseline, and constructs explainable SLM prompts. | Statistical rolling buffers, JSON prompt schema. |
| [`triggers.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/triggers.py) | **Trigger Manager**: Anti-false-positive gating enforcing consecutive cycle thresholds ($N=2, 3, 4$), cooldown timers ($180s - 600s$), and snooze periods. | State machine, sensitivity policies. |
| [`interventions.py`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/src/parlor/interventions.py) | **Intervention Generator**: Generates clinically grounded micro-interventions (Somatic, Cognitive, Environmental) personalized with real biomarker citations. | Clinical intervention taxonomy. |

---

## 4. Operational Modes & Fallback Paths

### 4.1 Production Path: Single-Process Live WebSocket
- The primary runtime command `uvicorn parlor.server:app --port 8000` launches both the conversational assistant and the background wellness monitoring service in a single event loop.
- Client video frames and audio chunks flow across WebSocket `/ws`, updating both pipelines without disk I/O bottlenecks.

### 4.2 Fallback Path: Two-Process Pipeline
- In headless deployments or distributed configurations, `person_a_loop.py` writes to `shared_state/latest_features.json` while `person_b_loop.py` consumes the file independently.
- `wellness.py` also writes atomically to `shared_state/latest_features.json` so CLI utilities can inspect live features during production execution.
