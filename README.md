# Parlor — On-Device Stress-Aware Voice & Vision Multimodal Assistant

> **EMO Assistant ("Parlor")** is a privacy-first, on-device AI assistant that combines a sub-second conversational voice and vision interface with continuous, passive affective wellness and digital burnout monitoring — using hardware you already have (laptop webcam + microphone), with no wearables or manual logging required.

---

## 🌟 Key Features

- **Sub-Second Conversational Turn-Taking (TTFA ~0.78s):** Speculatively pre-fills prompt caches while the user speaks using `smart-turn-v3.2` acoustic turn classification.
- **Multimodal Affective Wellness Monitoring:** Passively extracts facial micro-expression Action Units (`AU04`, `AU07`, `AU15`, `AU20`, `EAR` via MediaPipe FaceMesh) and vocal acoustic biomarkers (Pitch Delta, Jitter, Shimmer, Vocal Tension Index via Librosa/DSP).
- **Pattern-Based Qualitative SLM Reasoning:** Local Small Language Model (Gemma 4 / Llama 3 8B GGUF via `llama-server`) reasons qualitatively over biomarker patterns rather than brittle fixed numeric thresholds.
- **Explainable Micro-Interventions:** Delivers personalized micro-interventions (Somatic, Cognitive, Environmental) with full transparency ("Why did this fire?" reasoning disclosure).
- **User Agency & Control:** In-app sensitivity modes (*Conservative*, *Balanced*, *Sensitive*), one-click 10-minute snooze, and instant alert mute toggle.
- **100% On-Device Privacy:** Zero audio, video, or biomarker data ever leaves your machine. Longitudinal trends are persisted locally in SQLite (`shared_state/wellness_history.db`).

---

## 💻 Hardware & System Requirements

- **Operating System:** Windows 10/11, macOS (Apple Silicon), or Linux (x86_64 / ARM64).
- **Python:** Python 3.10 – 3.12 (Python 3.12 recommended).
- **Memory (RAM):**
  - **8 GB RAM:** Gemma 4 E2B (`Q4_K_M`)
  - **16 GB RAM:** Gemma 4 E4B / Llama 3 8B (`Q4_K_M`, recommended)
- **Acceleration:** NVIDIA GPU (CUDA), Apple Silicon (Metal), or CPU.

---

## 🚀 Quick Start & Clean Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/parlor.git
cd parlor
```

### 2. Environment Setup (Using `uv` — Recommended)
Install [uv](https://github.com/astral-sh/uv) (fast Python package manager) if not already installed:
```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create a virtual environment and install all dependencies:
```bash
uv sync
```

*(Alternatively, using standard `pip`: `python -m venv .venv; source .venv/bin/activate; pip install -e .`)*

### 3. Download Model Weights
1. **`llama-server` (llama.cpp):**
   - Download the prebuilt release for your platform from [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) and place `llama-server` on your system `PATH`.
2. **Quantized Model GGUF:**
   - Download **Gemma 4 E4B Q4_K_M** or **Llama 3 8B Instruct Q4_K_M** GGUF into the project root or configure via `.env`:
   ```bash
   MODEL=e4b
   ```

### 4. Launch Parlor (Single Command)
Run the unified application server:
```bash
uv run uvicorn parlor.server:app --port 8000
```
*(On Windows, you can also run `./start.ps1`)*

Open your browser and navigate to:
```
http://localhost:8000
```
Grant Camera and Microphone permissions when prompted.

---

## 🧪 Running Tests

Execute the automated test suite:
```bash
# Run all unit and integration tests
uv run pytest tests/

# Run Phase 5 live wellness integration tests
uv run pytest tests/test_phase5_live_wellness.py -v
```

---

## 🏛️ System Architecture

```
                                  BROWSER CLIENT (localhost:8000)
    [ Webcam Stream ]     [ Microphone PCM ]       [ Audio Synthesizer ]      [ UI Interventions ]
            |                     |                         ^                          ^
            | (frames)            | (audio chunks)          | (TTS audio PCM)          | (events)
            v                     v                         |                          |
+--------------------------------------------------------------------------------------|---------+
|                               FASTAPI APPLICATION (server.py)                        |         |
|                                                                                      |         |
|  +---------------------------------------------+  +----------------------------------|------+  |
|  |       SYSTEM 1: CONVERSATIONAL VOICE        |  |     SYSTEM 2: WELLNESS MONITOR   |      |  |
|  |                                             |  |                                  |      |  |
|  |   SmartTurn Classifier (~70ms)              |  |   FacialExtractor (MediaPipe AU) |      |  |
|  |   Speculative Cache Priming                 |  |   VocalExtractor (Librosa DSP)   |      |  |
|  |   Llama-Server (Gemma 4 Q4 GGUF)            |  |   FeatureFusionEngine (Window=5) |      |  |
|  |   Kokoro-ONNX Neural TTS (24kHz)            |  |   SLM Qualitative Reasoning      |      |  |
|  |                                             |  |   TriggerManager (Sensitivity)   |      |  |
|  |                                             |  |   InterventionGenerator          |      |  |
|  |                                             |  |   SQLite Store (wellness_history)|      |  |
|  |                                             |  |   WebSocket Push Dispatch -------+      |  |
|  +---------------------------------------------+  +-----------------------------------------+  |
+------------------------------------------------------------------------------------------------+
```

---

## 📚 Key Project Documents

- [FYP_RESULTS_SUMMARY.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/FYP_RESULTS_SUMMARY.md) — 1-page benchmark results and abstract verification summary.
- [DEMO_SCRIPT.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/DEMO_SCRIPT.md) — 5–10 minute demonstration sequence for presentation and defense.
- [PROJECT_STATUS_AND_ARCHITECTURE.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/PROJECT_STATUS_AND_ARCHITECTURE.md) — Detailed technical architecture breakdown.
- [FEATURE_SCOPE_AND_FILE_STRUCTURE.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/FEATURE_SCOPE_AND_FILE_STRUCTURE.md) — Complete repository file catalog.
- [QUANTIZATION_BENCHMARK.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/QUANTIZATION_BENCHMARK.md) — Model quantization trade-off study.
- [REASONING_EXAMPLES.md](file:///c:/Users/ramav/Documents/PROJECTS/parlor/parlor-main-main/REASONING_EXAMPLES.md) — Explainable SLM input/output reasoning traces.
