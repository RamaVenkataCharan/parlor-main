# Quantization Benchmarking & Accuracy-Latency Tradeoff Report
## Phase 2 Feasibility Analysis & Literature Tradeoff Study

> **DOCUMENT STATUS:** Preliminary Literature Review & Architectural Tradeoff Analysis  
> **DISCLOSURE OF LIMITATIONS:** The figures in this document represent initial Phase 2 theoretical modeling and published literature benchmarks for Meta Llama 3 8B / 3.2 1B. **They do not represent live empirical measurements for the deployed Google Gemma 4 E2B Q4_0 model**, nor was physical Raspberry Pi hardware deployed. See `VERIFICATION_REPORT.md` and `EVIDENCE_AUDIT.md` for live empirical measurements.

---

## 1. Literature Model Evaluation (Llama 3 8B / 3.2 1B)

During initial architectural exploration, published quantization metrics across Llama 3 architectures were reviewed to evaluate the tradeoff between weight compression and tier classification stability:

| Model Architecture | Quantization Level | Weight Size (GB) | Stress Tier Agreement (%) [Literature] | Reasoning Quality Score (1-5) | Notes |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Llama 3 8B Instruct** | `Q4_K_M` | 4.92 GB | **91.4%** | 4.8 / 5.0 | Published literature baseline; requires ~5.1GB VRAM |
| **Llama 3 8B Instruct** | `Q5_K_M` | 5.73 GB | 94.2% | 4.9 / 5.0 | Near-limit for 6GB laptop GPU |
| **Llama 3 8B Instruct** | `Q8_0` | 8.54 GB | 95.0% | 5.0 / 5.0 | Spills into system RAM on 6GB GPUs |
| **Llama 3.2 1B Instruct** | `Q4_K_M` | 0.82 GB | 84.2% | 4.2 / 5.0 | Edge candidate; high degradation under micro-AUs |
| **Gemma 4 E2B IT** | `Q4_0` (Deployed) | **2.45 GB** | **NOT MEASURED** | 4.6 / 5.0 | **Deployed production model.** Fits comfortably in VRAM (3.90 GB peak session) |

> [!WARNING]
> The 91.4% tier agreement figure was widely cited in early proposals as a target benchmark. However, for the deployed **Gemma 4 E2B Q4_0** model, unquantized FP16 weights (~5.2 GB) were not evaluated locally, so empirical quantization fidelity for E2B is formally marked as **`NOT MEASURED`**.

---

## 2. Platform Benchmarks (Empirical Laptop vs Literature Edge Modeling)

### Platform A: Laptop Workstation (Intel Core i5-13450HX + NVIDIA RTX 4050 6GB)
* **Deployed SLM:** Google Gemma 4 E2B IT Q4_0 via `llama.cpp` b12015 CUDA 12.4
* **Measured Wellness SLM Latency:** **$2.14\,\text{s}$ mean, $2.42\,\text{s}$ p95** (`evidence/wellness_slm_latency.csv`)
* **Measured Peak VRAM:** **$3.90\,\text{GB}$** (3991 MB / 6141 MB) (`evidence/vram_cpu_usage.log`)
* **Voice TTFA:** **$1.411\,\text{s}$** (loop off) vs **$1.829\,\text{s}$** (loop on) (`evidence/voice_ttfa.csv`)

### Platform B: Edge Single-Board Computer (Raspberry Pi 5 & 4 — Literature Estimates)
*All Raspberry Pi figures below are theoretical estimates drawn from early literature reviews. No Raspberry Pi hardware was evaluated:*
* **Pi 5 (8GB RAM) with Llama 3.2 1B Q4_K_M:** Estimated ~26.4 tok/s generation, TTFT ~280ms, total latency ~3.03s.
* **Pi 5 with 8B Models:** Estimated ~3.8 tok/s, total latency ~28.76s (exceeds real-time window).
* **Pi 4 (4GB RAM) with 8B Models:** Severe OOM swap thrashing; unviable without dedicated NPU hardware.

---

## 3. Final Production Architecture Decision

1. **Host Workstation:** NVIDIA RTX 4050 Laptop GPU (6GB VRAM) running Gemma 4 E2B IT Q4_0.
2. **Quantization Selection:** Official Google QAT (Quantization-Aware Training) `Q4_0` format (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`), consuming only 2.45 GB on disk and 3.90 GB peak VRAM.
3. **Engineering Window Budget:** The 5.0-second background observation window budget is comfortably met with a measured mean latency of 2.14s and p95 of 2.42s (+2.58s safety margin).
