# Phase 1 Feature Extraction Pipeline Benchmarking & Latency Impact Report

> **DOCUMENT STATUS:** Phase 1 Benchmarking & Pipeline Integration Report  
> **DISCLOSURE OF HARDWARE:** Live physical benchmarking was conducted exclusively on the Laptop Workstation (**Intel Core i5-13450HX CPU, NVIDIA GeForce RTX 4050 6GB GPU**). Raspberry Pi 5 and 4 figures are literature estimates from early architectural exploration; no physical Raspberry Pi hardware was evaluated in the physical lab.

---

## 1. Feature Extraction Resource Cost Breakdown (Empirically Measured)

### A. Facial Micro-Expression Extraction (`src/parlor/facial.py`)
- **Input:** 640x480 RGB image frame
- **Model:** MediaPipe Tasks FaceLandmarker (478 3D facial landmarks) + OpenCV solvePnP head pose estimator
- **Extracted Biomarkers:** AU04 Brow Furrow, AU07 Lid Tightener, AU15 Lip Depressor, AU20 Lip Stretcher, EAR, Head Pitch/Yaw/Roll
- **Live Empirical Latency on Host Workstation (Intel Core i5-13450HX CPU, N=100 runs each):**
  - **Real Face (Normal Light):** **$3.97\,\text{ms}$ mean, $3.85\,\text{ms}$ p50, $4.81\,\text{ms}$ p95, $5.96\,\text{ms}$ max** (`evidence/facial_extraction_real.csv`)
  - **Real Face (Dim Light 15% Lux):** **$4.39\,\text{ms}$ mean, $3.95\,\text{ms}$ p50, $6.84\,\text{ms}$ p95, $8.81\,\text{ms}$ max** (`evidence/facial_extraction_dim.csv`)
  - **Real Face (Head Turned ~30°):** **$4.69\,\text{ms}$ mean, $4.44\,\text{ms}$ p50, $6.58\,\text{ms}$ p95, $7.22\,\text{ms}$ max** (`evidence/facial_extraction_turned.csv`)
  - **Blank / No Face Frame:** **$1.92\,\text{ms}$ mean, $1.84\,\text{ms}$ p50, $2.45\,\text{ms}$ p95, $3.82\,\text{ms}$ max** (`evidence/facial_extraction_blank.csv`)
- **Memory Footprint:** ~42 MB RAM; CPU utilization < 2.0% of one core.

---

### B. Vocal Biomarker Extraction (`src/parlor/vocal.py`)
- **Input:** 2.0-second audio window @ 16kHz 16-bit PCM (32,000 samples)
- **Signal Processing:** Vectorized NumPy / SciPy Short-Time Energy VAD, autocorrelation pitch (F0), local jitter, local shimmer, FFT high-frequency spectral tension index (>1kHz).
- **Live Empirical Latency on Host Workstation (Intel Core i5-13450HX CPU, N=100 runs):**
  - **Mean Latency:** **$2.85\,\text{ms}$**
  - **Median (p50):** **$2.76\,\text{ms}$**
  - **95th Percentile (p95):** **$3.73\,\text{ms}$**
  - **Maximum Latency:** **$4.42\,\text{ms}$** (`evidence/vocal_extraction.csv`)
- **Memory Footprint:** ~12 MB RAM; CPU utilization < 0.5% of one core.

---

## 2. Combined Feature Extraction Overhead & Engineering Budget Impact

```text
========================================================================================
Host Workstation Feature Extraction Performance (Intel i5-13450HX CPU):
  - Facial AU Extraction (Real Face):     3.97 ms (mean)
  - Vocal Biomarker DSP (2.0s Audio):     2.85 ms (mean)
  - Combined Extraction Stage:            ~6.82 ms (mean)
  - SQLite Assessment Write:              4.07 ms (mean)
  - Combined Memory Overhead:             ~54 MB RAM
========================================================================================
```

### Cumulative End-to-End Latency vs Engineering Budget

| Platform | Model Target | Feature Extraction | SLM Qualitative Reasoning | Total E2E Cycle Latency | Engineering Window Budget | Margin |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Host Workstation (RTX 4050 GPU + i5 CPU)** | **Gemma 4 E2B Q4_0 (Deployed)** | **$6.82\,\text{ms}$** | **$2.14\,\text{s}$** mean ($2.42\,\text{s}$ p95) | **$2.15\,\text{s}$** mean ($2.43\,\text{s}$ p95) | **$\le 5.00\,\text{s}$** | **$+2.57\,\text{s}$ PASS** |
| **Edge Pi 5 (8GB)** | Llama 3.2 1B (Literature Est) | 56.8 ms | 2.17 s | ~3.03 s | $\le 5.00\,\text{s}$ | $+1.97\,\text{s}$ (Est) |

### Benchmark Conclusion:
Feature extraction adds **less than 7 ms** of processing time on the host CPU. The entire observation and reasoning pipeline executes well within the 5.0-second engineering budget, leaving ample headroom (+2.57s) for background operations.
