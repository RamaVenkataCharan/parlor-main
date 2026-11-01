# Phase 0 Technical Feasibility & Model Benchmarking Report

> **DOCUMENT STATUS:** Phase 0 Historical Feasibility Study & Literature Modeling  
> **DISCLOSURE OF TESTED HARDWARE:** Live physical benchmarking in this project was conducted exclusively on the Laptop Workstation (**Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU, 16GB RAM**). All Raspberry Pi 5 & Pi 4 figures represent early theoretical modeling and published literature estimates; no Raspberry Pi hardware was deployed in the physical lab.

---

## 1. Hardware Specifications & Evaluation Context

### Platform A: Host Laptop / Workstation (Physical Benchmark Platform)
- **CPU:** Intel Core i5-13450HX (10 Cores / 16 Threads, up to 4.6 GHz)
- **GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (6 GB GDDR6 VRAM, CUDA 12.4)
- **System Memory:** 16 GB DDR5 RAM
- **OS / Environment:** Windows 11 64-bit, `llama.cpp` (b12015) with CUDA acceleration

### Platform B: Edge Single-Board Computer (Literature Modeling Estimates Only)
- **Raspberry Pi 5:** Broadcom BCM2712 Quad-core ARM Cortex-A76 @ 2.4 GHz, 8 GB LPDDR4X (Literature specifications)
- **Raspberry Pi 4:** Broadcom BCM2711 Quad-core ARM Cortex-A72 @ 1.5 GHz, 4 GB LPDDR4 (Literature specifications)

---

## 2. Realistic Multimodal Benchmark Prompt

Benchmarks utilized a representative input prompt simulating a fused facial and vocal feature vector:

```text
[SYSTEM: Multimodal Affective Wellness Monitor]
TIMESTAMP: 2026-08-07T23:00:00Z
WINDOW_DURATION: 10.0s

ACOUSTIC_VOCAL_FEATURES:
- Mean Pitch (F0): 182.4 Hz (Baseline: 145.0 Hz, Delta: +37.4 Hz, Elevated)
- Pitch Variance (F0_SD): 42.1 Hz (Elevated micro-tremor)
- Shimmer (Amplitude Perturbation): 3.82% (Mild instability)
- Jitter (Frequency Perturbation): 1.15% (Normal)
- Speech Rate: 198 words/min (Fast/Pressured)
- Pauses: 2 (Avg duration: 0.18s, Abnormally brief)
- Intensity / Energy: 68.2 dB (High)
- Vocal Tension Index: 0.74 (Elevated)

FACIAL_VISUAL_FEATURES (Action Units):
- AU04 (Brow Lowerer): 0.82 (High - Furrowed brow)
- AU07 (Lid Tightener): 0.65 (Moderate - Eye strain/squinting)
- AU15 (Lip Corner Depressor): 0.45 (Mild)
- AU20 (Lip Stretcher): 0.58 (Moderate)
- Gaze Direction: Off-screen center left, gaze fixation duration: 1.2s
- Head Pose: Pitch -8.4 deg, Yaw +12.1 deg
- Blink Rate: 34 blinks/min (Elevated stress indicator)

COMPOSITE AFFECT SUMMARY:
- Valence: -0.68 (Negative)
- Arousal: +0.81 (High Activation / Acute Stress)

TASK: Analyze the fused feature vector above. Determine if an affective wellness intervention is required. If yes, generate a calm, empathetic 2-sentence micro-intervention.
```

---

## 3. Preliminary Historical Benchmarks (Llama 3 8B Q4_K_M)

*Early Phase 0 exploration evaluated Meta Llama 3 8B Instruct before selecting Google Gemma 4 E2B IT as the final deployed production model:*

| Platform | Acceleration | Peak RAM / VRAM | Model Load Time | Time to 1st Token (TTFT) | Generation Speed | Total SLM Stage Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Laptop (Workstation)** | RTX 4050 GPU (CUDA) | **5.10 GB VRAM** | 1.85 s | **85 ms** | **52.4 tok/s** | **1.99 s** | **PASS** |
| **Laptop (Workstation)** | Intel i5-13450HX (CPU) | **5.42 GB RAM** | 2.40 s | **620 ms** | **14.8 tok/s** | **7.37 s** | **PASS** |
| **Raspberry Pi 5 (8GB)** | Cortex-A76 (Literature Est) | 5.65 GB RAM | 8.20 s | 2,450 ms | 3.8 tok/s | 28.76 s | **FAIL (Too Slow)** |
| **Raspberry Pi 4 (4GB)** | Cortex-A72 (Literature Est) | > 4.00 GB | N/A | N/A | < 0.8 tok/s | > 120 s | **FAIL (OOM)** |

---

## 4. Edge Model Tradeoff Analysis (Literature Estimates)

| Model | Quantization | Model Size | Target Hardware | Est Peak RAM | Est TTFT | Est Gen Speed | Est SLM Stage (50 tok) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Llama 3.2 1B Instruct** | `Q4_K_M` | 0.82 GB | Pi 5 (Literature) | 1.15 GB | 280 ms | 26.4 tok/s | 2.17 s |
| **Llama 3.2 1B Instruct** | `Q4_K_M` | 0.82 GB | Pi 4 (Literature) | 1.18 GB | 640 ms | 11.2 tok/s | 5.10 s |
| **Gemma 2B IT** | `Q4_K_M` | 1.63 GB | Pi 5 (Literature) | 2.10 GB | 620 ms | 12.1 tok/s | 4.75 s |
| **Gemma 4 E2B IT (Deployed)**| `Q4_0` | **2.45 GB** | **RTX 4050 Laptop** | **3.90 GB VRAM** | **< 100 ms** | **~42 tok/s** | **2.14 s (Measured)** |

---

## 5. Engineering Budget & Real-Time Definition

Unlike conversational speech turns requiring sub-second turn-taking, the **Affective Wellness Monitor** operates across continuous temporal observation windows (5–10 seconds).

* **Engineering Budget:** $\le 5.0\,\text{seconds}$ end-to-end per observation window.
* **Workstation Measured Performance:** **$2.14\,\text{s}$ mean, $2.42\,\text{s}$ p95**, providing an empirical **safety margin of $+2.58\,\text{s}$**.
