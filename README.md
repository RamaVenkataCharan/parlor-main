# Parlor — Fully On-Device Multimodal AI & Affective Wellness Monitoring

> **Major Project — Department of Computer Science & Engineering**  
> **Class & Batch:** B.Tech CSE, Section A, Batch 14  
> **Project Guide:** Mrs. V. Aruna, Senior Assistant Professor  
> **Student Team:**
> - M. Rama Venkata Charan (Roll No: 23KN1A0543)
> - B. Murali Gopi (Roll No: 23KN1A0515)
> - M. Kumar Siva Sai (Roll No: 23KN1A0542)
> - Y. Yashwanth Prakash (Roll No: 23KN1A0571)  
> **Academic Session:** 2025 – 2026

[![Test Suite](https://img.shields.io/badge/pytest-110%20passed%20%7C%200%20failed-brightgreen.svg)](VERIFICATION_REPORT.md)
[![TTFA](https://img.shields.io/badge/Conversational%20TTFA-1.33s%20mean-blue.svg)](VERIFICATION_REPORT.md)
[![Quantization](https://img.shields.io/badge/Quantization%20Agreement-NOT%20MEASURED-lightgrey.svg)](ACCURACY_VALIDATION.md)
[![Ground Truth](https://img.shields.io/badge/EMA%20Ground%20Truth-REQUIRES%20HUMAN%20STUDY-orange.svg)](ACCURACY_VALIDATION.md)
[![Privacy](https://img.shields.io/badge/Network%20Transmission-0.00%20KB%20(Local%20Only)-success.svg)](VERIFICATION_REPORT.md)

---

## 1. Project Overview

**EMO Assistant ("Parlor")** is a privacy-first, fully on-device multimodal AI system designed to mitigate digital burnout and acute cognitive fatigue in knowledge workers and software developers.

Combining an ultra-low-latency conversational voice interface with continuous, passive affective monitoring, Parlor operates exclusively on consumer-grade laptop hardware (webcam + microphone) without requiring smartwatches, chest straps, or manual journal logging.

### Key Capabilities
- **Sub-Second Voice Conversational Assistant:** Achieves **1.33s mean Time-To-First-Audio (TTFA)** across diverse turns (with short queries reaching **0.83s**) using acoustic endpointing (`smart-turn-v3.2.onnx`), speculative prompt cache pre-filling, and on-device Kokoro TTS (`kokoro-v1.0.onnx`).
- **Passive Multimodal Feature Extraction:** Concurrently extracts MediaPipe FaceMesh facial Action Units (`AU04` brow furrow, `AU07` eyelid tightener, `AU20` lip stretcher: **1.75 ms**) and Librosa acoustic DSP features ($\Delta F0$ pitch shift, jitter %, shimmer %, spectral tension: **2.34 ms**) on standard CPU threads.
- **Pattern-Based Qualitative SLM Reasoning:** Evaluates cross-modal physiological signals using a local Small Language Model (**Google Gemma 4 E2B IT `Q4_0`** via `llama-server`) with structured JSON schema outputs in **2.14 s mean / 2.42 s p95** on GPU, eliminating brittle rigid thresholds.
- **Explainable, Gated Micro-Interventions:** Enforces consecutive elevated observation cycles (Tier 2) and an 80-second cooldown before triggering non-intrusive micro-breaks (Somatic, Cognitive, Environmental) with complete provenance disclosure (*"Why did this fire?"*).
- **Strict Local Isolation & Zero External Transmission:** Transmits **0.00 KB** over external networks. The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.

---

## 2. Empirical Verification & Performance Metrics

All metrics reported below were measured directly on the evaluation hardware: **Windows 11 Home, Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6GB GDDR6 VRAM, CUDA 12.4), 16GB RAM**.

| Metric Dimension | Measured Empirical Result | Target Spec Budget | Verification Source |
| :--- | :---: | :---: | :--- |
| **Conversational Turn TTFA (Loop OFF)** | **`1.33 s`** (0.83 s short turn) | $\le 2.000\text{ s}$ | [`evidence/voice_ttfa.csv`](evidence/voice_ttfa.csv) |
| **Conversational Turn TTFA (Loop ON)** | **`1.88 s`** | $\le 2.500\text{ s}$ | [`evidence/voice_ttfa.csv`](evidence/voice_ttfa.csv) |
| **Acoustic Turn Classification** | **`68.2 ms`** | $\le 100.0\text{ ms}$ | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) |
| **Facial AU Feature Extraction (CPU, p95)** | **`1.91 ms`** (mean: 1.75 ms) | $\le 30.0\text{ ms}$ | [`evidence/facial_extraction.csv`](evidence/facial_extraction.csv) |
| **Vocal Acoustic DSP Extraction (CPU, p95)** | **`2.88 ms`** (mean: 2.34 ms) | $\le 30.0\text{ ms}$ | [`evidence/vocal_extraction.csv`](evidence/vocal_extraction.csv) |
| **SLM Wellness Cycle Latency (GPU, p95)** | **`2.42 s`** (mean: `2.14 s`) | $\le 5.00\text{ s}$ | [`evidence/wellness_slm_latency.csv`](evidence/wellness_slm_latency.csv) |
| **Complete Observation Cycle Latency** | **`2.43 s`** (p95 total) | $\le 5.00\text{ s}$ | [`evidence/wellness_slm_latency.csv`](evidence/wellness_slm_latency.csv) |
| **Outbound Network Transmission** | **`0.00 KB`** (0 remote sockets) | $0.00\text{ KB}$ | [`evidence/netstat_outbound.txt`](evidence/netstat_outbound.txt) |
| **Peak GPU VRAM Utilization** | **`3.90 GB`** (3991 MB / 6141 MB) | $\le 5.50\text{ GB}$ | [`evidence/vram_cpu_usage.log`](evidence/vram_cpu_usage.log) |
| **Automated Test Suite Pass Rate** | **`99.1%`** (110 pass, 0 fail, 1 skip\*) | $\ge 95\%$ | [`evidence/pytest_full.log`](evidence/pytest_full.log) |
| **Model Quantization Agreement** | **`NOT MEASURED`** (No FP16 weights on disk) | N/A | [`EVIDENCE_AUDIT.md`](EVIDENCE_AUDIT.md) |
| **EMA Ground-Truth Human Agreement** | **`NOT COLLECTED / REQUIRES HUMAN STUDY`** | Kit Ready | [`docs/EMA_RECOLLECTION_KIT.md`](docs/EMA_RECOLLECTION_KIT.md) |

*\*Note on Skipped Test:* `test_thinking_pause_is_held` in `tests/test_conversation.py` is skipped by design; synthetic TTS imparts falling pitch prosody evaluated as turn completion, whereas human hesitation must be evaluated live.

### Single-Command Viva Examiner Verification
Examiners can reproduce all 8 empirical metrics immediately with a single command:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/reproduce_numbers.ps1
```

---

## 3. Ground-Truth Agreement vs. Quantization Fidelity

> [!IMPORTANT]
> In academic research and viva defense, it is critical to distinguish between these two distinct metrics:
> 1. **Model Quantization Consistency:** Measures algorithmic compression fidelity between 4-bit integer weights (`Q4_0`) and uncompressed 16-bit floating point weights (`FP16`) across identical prompts. Uncompressed FP16 weights were not stored locally for Gemma 4 E2B, so this is marked **NOT MEASURED**.
> 2. **Ground-Truth Diagnostic Accuracy:** Measures agreement between system-inferred stress tiers and actual human psychological self-report collected via the 3-item Ecological Momentary Assessment (EMA) protocol. Preliminary reports referenced a 144-window synthetic distribution (`run_ema_validation.py`); empirical human data is designated **`NOT COLLECTED / REQUIRES HUMAN STUDY`**. A standardized collection harness and protocol guide are packaged in `docs/EMA_RECOLLECTION_KIT.md` for study execution with $\ge 3$ human participants prior to viva.

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

## 5. Academic Deliverables & Documentation Manifest

| Document / Asset | File Path | Scope & Content |
| :--- | :--- | :--- |
| **Evidence Audit Report** | [`EVIDENCE_AUDIT.md`](EVIDENCE_AUDIT.md) | Exhaustive empirical grounding audit, changed numbers log, and refuted claims. |
| **Comprehensive Final Report** | [`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) | Complete 8-section university major project report with verified figures and diagrams. |
| **Printable Report (HTML/PDF)** | [`docs/FINAL_PROJECT_REPORT.html`](docs/FINAL_PROJECT_REPORT.html) | Self-contained, styled HTML report ready for printing or saving to PDF (`Ctrl+P`). |
| **Presentation Slides** | [`docs/PRESENTATION_SLIDES.md`](docs/PRESENTATION_SLIDES.md) | 15-slide defense deck with empirical citations and diagrams. |
| **Viva Defense Q&A Guide** | [`docs/DEFENSE_QA_GUIDE.md`](docs/DEFENSE_QA_GUIDE.md) | Defense answers, one-sentence honest metric disclosure, and examination guide. |
| **Demo Safeguards & Checklist** | [`docs/DEMO_SAFEGUARDS_AND_CHECKLIST.md`](docs/DEMO_SAFEGUARDS_AND_CHECKLIST.md) | 30-minute pre-flight checklist, video backup plan, and troubleshooting table. |
| **EMA Re-Collection Kit** | [`docs/EMA_RECOLLECTION_KIT.md`](docs/EMA_RECOLLECTION_KIT.md) | Human study protocol, informed consent form, and operator guide for $\ge 3$ participants. |
| **Live Verification Report** | [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) | Source-of-truth empirical timing, resource footprint, and test results. |
| **Accuracy Validation Report** | [`ACCURACY_VALIDATION.md`](ACCURACY_VALIDATION.md) | EMA experimental protocol, synthetic reference matrix, and clinical boundaries. |
| **Reproducibility Harness** | [`scripts/reproduce_numbers.ps1`](scripts/reproduce_numbers.ps1) | Single-command verification runner reproducing the 8-metric table for examiners. |
| **Offline Playback Utility** | [`scripts/offline_demo_playback.py`](scripts/offline_demo_playback.py) | Standalone replay script driving terminal or browser UI from SQLite history. |
| **Packaging Script** | [`scripts/create_submission_zip.py`](scripts/create_submission_zip.py) | Automated packager generating clean ZIP (`dist/parlor_submission_batch14.zip`). |

---

## 6. Submission Package

To generate a clean ZIP archive of the project for submission (excluding bulky model weights, `.venv`, `.pytest_cache`, and secrets):

```powershell
uv run python scripts/create_submission_zip.py
```
**Output Archive:** `dist/parlor_submission_batch14.zip`.

---

## 7. License & Ethical Disclaimer

This software is developed strictly for research, educational, and wellness assistance purposes. **Parlor is not a clinical medical diagnostic tool and does not treat, diagnose, or prevent any psychological or physiological pathology.** All affective assessments are heuristic estimations aimed at encouraging ergonomic computer usage and micro-breaks.
