# Parlor — Fully On-Device Multimodal AI & Affective Wellness Monitoring

> **Major Project — Department of Computer Science & Engineering**  
> **Class & Batch:** B.Tech CSE, Section A, Batch 14  
> **Project Guide:** Mrs. V. Aruna  
> **Student Team:** Rama Venkata Charan & Team  
> **Academic Session:** 2025 – 2026

[![Test Suite](https://img.shields.io/badge/pytest-110%20passed%20%7C%200%20failed-brightgreen.svg)](VERIFICATION_REPORT.md)
[![TTFA](https://img.shields.io/badge/Conversational%20TTFA-0.781s-blue.svg)](VERIFICATION_REPORT.md)
[![Quantization](https://img.shields.io/badge/Quantization%20Agreement-91.4%25-informational.svg)](ACCURACY_VALIDATION.md)
[![Ground Truth](https://img.shields.io/badge/EMA%20Ground%20Truth-77.8%25%20exact%20%7C%20100%25%20one--tier-success.svg)](ACCURACY_VALIDATION.md)
[![Privacy](https://img.shields.io/badge/Network%20Transmission-0.00%20KB%20(Air--Gapped)-success.svg)](VERIFICATION_REPORT.md)

---

## 1. Project Overview

**EMO Assistant ("Parlor")** is a privacy-first, fully on-device multimodal AI system designed to mitigate digital burnout and acute cognitive fatigue in knowledge workers and software developers.

Combining a sub-second conversational voice interface with continuous, passive affective monitoring, Parlor operates exclusively on consumer-grade laptop hardware (webcam + microphone) without requiring smartwatches, chest straps, or manual journal logging.

### Key Capabilities
- **Sub-Second Voice Conversational Assistant:** Achieves **0.781s Time-To-First-Audio (TTFA)** using acoustic endpointing (`smart-turn-v3.2.onnx`), speculative prompt cache pre-filling, and on-device Kokoro TTS (`kokoro-v1.0.onnx`).
- **Passive Multimodal Feature Extraction:** Concurrently extracts MediaPipe FaceMesh facial Action Units (`AU04` brow furrow, `AU07` eyelid tightener, `AU20` lip stretcher) and Librosa acoustic DSP features ($\Delta F0$ pitch shift, jitter %, shimmer %, spectral tension) with only **21ms non-SLM compute overhead**.
- **Pattern-Based Qualitative SLM Reasoning:** Evaluates cross-modal physiological signals using a local Small Language Model (**Google Gemma 4 E2B IT `Q4_0`** via `llama-server`) with structured JSON schema outputs, eliminating brittle rigid thresholds.
- **Explainable, Gated Micro-Interventions:** Enforces consecutive elevated observation cycles (Tier 2) and an 80-second cooldown before triggering non-intrusive micro-breaks (Somatic, Cognitive, Environmental) with complete provenance disclosure (*"Why did this fire?"*).
- **100% On-Device Privacy & Zero Network Calls:** Transmits **0.00 KB** over external networks. All Silero VAD assets and model weights are vendored locally; longitudinal stress trends are persisted strictly in local SQLite (`shared_state/wellness_history.db`).

---

## 2. Empirical Verification & Performance Metrics

All metrics reported below were measured directly on the evaluation hardware: **Windows 11 Home, Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6GB GDDR6 VRAM, CUDA 12.4), 16GB RAM**.

| Metric Dimension | Measured Empirical Result | Target Spec Budget | Verification Source |
| :--- | :---: | :---: | :--- |
| **Conversational Turn TTFA** | **`0.781 s`** | $\le 1.000\text{ s}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Acoustic Turn Classification** | **`68.2 ms`** | $\le 100.0\text{ ms}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Facial AU Feature Extraction** | **`14.2 ms`** | $\le 35.0\text{ ms}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Vocal Acoustic DSP Extraction** | **`18.7 ms`** | $\le 30.0\text{ ms}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **SLM Wellness Cycle Latency (GPU)** | **`2.76 s`** mean (p95: `3.12 s`) | $\le 4.50\text{ s}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Total Observation Cycle Latency** | **`2.82 s`** | $\le 5.00\text{ s}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Outbound Network Transmission** | **`0.00 KB`** | $0.00\text{ KB}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Peak GPU VRAM Utilization** | **`3.84 GB`** | $\le 6.00\text{ GB}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Automated Test Suite Pass Rate** | **`99.1%`** (110 pass, 0 fail, 1 skip\*) | $100\%$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Model Quantization Agreement** | **`91.4%`** ($N=250$, Q4_0 vs FP16) | $\ge 85.0\%$ | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) |
| **EMA Ground-Truth Exact Agreement** | **`77.8%`** ($N=144$ windows, 8 subjects)| $\ge 70.0\%$ | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) |
| **EMA One-Tier-Tolerance Agreement** | **`100.0%`** (Zero 2-tier errors) | $\ge 95.0\%$ | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) |
| **False Positive Rate (FPR)** | **`0.0%`** (0 / 40 calm windows) | $\le 5.0\%$ | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) |

*\*Note on Skipped Test:* `test_thinking_pause_is_held` in `tests/test_conversation.py` is skipped by design; synthetic TTS imparts falling pitch prosody evaluated as turn completion, whereas human hesitation must be evaluated live.

---

## 3. Ground-Truth Agreement vs. Quantization Fidelity

> [!IMPORTANT]
> In academic research and viva defense, it is critical to distinguish between these two distinct metrics:
> 1. **Model Quantization Consistency (`91.4%`):** Measures algorithmic compression fidelity between 4-bit integer weights (`Q4_0`) and uncompressed 16-bit floating point weights (`FP16`) across 250 controlled biomarker vectors.
> 2. **Ground-Truth Diagnostic Accuracy (`77.8%` exact, `100.0%` one-tier):** Measures agreement between system-inferred stress tiers and actual human psychological self-report collected via the 3-item Ecological Momentary Assessment (EMA) protocol across 144 live 45-minute trials ($N=8$ participants).

---

## 4. Quick Start: Clean Clone Reproduction Guide

Follow these verified steps to run the complete system on Windows 10/11:

### 4.1 Prerequisites
- **Python:** 3.10 – 3.12 (Python 3.12 64-bit recommended).
- **Package Manager:** Astral [`uv`](https://github.com/astral-sh/uv).
- **Inference Engine:** `llama.cpp` (`llama-server.exe`, build $\ge$ b9503, b12015 recommended with CUDA 12.4).
- **Hardware:** Webcam, microphone, and NVIDIA GPU with $\ge 4.5\text{ GB}$ free VRAM (or CPU fallback).

### 4.2 Installation Steps

```powershell
# 1. Clone repository
git clone https://github.com/your-username/parlor.git
cd parlor

# 2. Install dependencies via uv
uv sync

# 3. Verify core C++ and ML bindings
uv run python -c "import cv2, mediapipe, scipy, onnxruntime; print('Environment operational!')"

# 4. Copy environment configuration
Copy-Item .env.example .env
```

### 4.3 Model Weights Placement

Place the downloaded GGUF and ONNX models into the `models/` directory (or verify paths in `.env`):
- `models/gemma-4-E2B_q4_0-it.gguf` (3.35 GB)
- `models/gemma-4-E2B-it-mmproj.gguf` (986 MB)
- `models/kokoro-v1.0.onnx` (326 MB)
- `models/voices-v1.0.bin` (27 MB)
- `models/smart-turn-v3.2.onnx` (1.8 MB)

### 4.4 Running Automated Verification & Tests

```powershell
# Run the complete test suite (110 passed, 0 failed, 1 skipped)
uv run pytest tests/ -v

# Run with test coverage
uv run pytest tests/ --cov=src/parlor

# Run static analysis and linting
uv run ruff check .
```

### 4.5 Launching the Live System

Execute the hardened startup script:
```powershell
.\start.ps1
```
The script safely frees ports 8000 and 8081, launches `llama-server.exe` with GPU offload (`-ngl 99`), and spawns the FastAPI application.

Open your browser to:
```
http://localhost:8000
```
Allow camera and microphone access when prompted.

---

## 5. Offline Fallback & Committee Demonstration Utility

For live academic defense presentations where GPU hardware, webcam, or microphone access may be constrained:

```powershell
# 1. Display statistical summary of 1,717 stored cycles:
uv run python scripts/offline_demo_playback.py --summary

# 2. Stream historical assessments chronologically in the terminal:
uv run python scripts/offline_demo_playback.py --replay --limit 15 --delay 1.0

# 3. Broadcast real stored telemetry to the web UI without GPU/camera:
uv run python scripts/offline_demo_playback.py --serve --port 8000
```

---

## 6. Academic Deliverables & Documentation Manifest

| Document / Asset | File Path | Scope & Content |
| :--- | :--- | :--- |
| **Comprehensive Final Report** | [`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) | Complete 8-section university major project report with architecture diagrams and references. |
| **Printable Report (HTML/PDF)** | [`docs/FINAL_PROJECT_REPORT.html`](docs/FINAL_PROJECT_REPORT.html) | Self-contained, styled HTML report ready for printing or saving to PDF (`Ctrl+P`). |
| **Presentation Slides** | [`docs/PRESENTATION_SLIDES.md`](docs/PRESENTATION_SLIDES.md) | 15-slide defense deck with empirical citations and diagrams. |
| **Viva Defense Q&A Guide** | [`docs/DEFENSE_QA_GUIDE.md`](docs/DEFENSE_QA_GUIDE.md) | Exhaustive defense answers, one-sentence honest metric disclosure, and refuted claims. |
| **Demo Safeguards & Checklist** | [`docs/DEMO_SAFEGUARDS_AND_CHECKLIST.md`](docs/DEMO_SAFEGUARDS_AND_CHECKLIST.md) | 30-minute pre-flight checklist, video backup plan, and troubleshooting table. |
| **Live Verification Report** | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) | Source-of-truth empirical timing, resource footprint, and test results. |
| **Accuracy Validation Report** | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) | EMA experimental protocol, participant breakdown ($N=8$), and 3x3 confusion matrix. |
| **Participant Protocol** | [`docs/PARTICIPANT_PROTOCOL.md`](docs/PARTICIPANT_PROTOCOL.md) | Informed consent form, ethical guidelines, and 3-item EMA instrument. |
| **Offline Playback Utility** | [`scripts/offline_demo_playback.py`](scripts/offline_demo_playback.py) | Standalone replay script driving terminal or browser UI from SQLite history. |
| **Packaging Script** | [`scripts/create_submission_zip.py`](scripts/create_submission_zip.py) | Automated packager generating clean ZIP (`dist/parlor_submission_batch14.zip`). |

---

## 7. Submission Package

To generate a clean ZIP archive of the project for submission (excluding bulky model weights, `.venv`, `.pytest_cache`, and secrets):

```powershell
uv run python scripts/create_submission_zip.py
```
**Output Archive:** `dist/parlor_submission_batch14.zip` (139 files, ~6.15 MB compressed).

---

## 8. License & Ethical Disclaimer

This software is developed strictly for research, educational, and wellness assistance purposes. **Parlor is not a clinical medical diagnostic tool and does not treat, diagnose, or prevent any psychological or physiological pathology.** All affective assessments are heuristic estimations aimed at encouraging ergonomic computer usage and micro-breaks.
