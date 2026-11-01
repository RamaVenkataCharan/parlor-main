# Parlor System Evidence Audit & Empirical Grounding Report

**Academic Context:** B.Tech Major Project, Department of Computer Science & Engineering, Section A, Batch 14  
**Project Title:** EMO Assistant ("Parlor") — Fully On-Device Multimodal Wellness & Fatigue Mitigation Assistant  
**Hardware Target:** Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM), 16 GB RAM, Windows 11  
**SLM Target:** Gemma 4 E2B Q4_0 IT (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`) via llama.cpp b12015 CUDA 12.4  
**Audit Date:** 2026-11-01  
**Audit Policy:** Zero simulated, estimated, or carried-over numbers. Every reported figure traces to a raw timestamped file in `evidence/`.

---

## 1. Master Evidence Audit Matrix

| Metric / Parameter | Value in Preliminary Reports | Value Measured on This Machine | Raw Evidence File | Source Command / Harness | Empirical Audit Status |
|:---|:---:|:---:|:---|:---|:---:|
| **Facial AU Extraction (CPU, Mean)** | 14.2 ms | **1.75 ms** | `evidence/facial_extraction.csv` | `uv run python scripts/measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **Facial AU Extraction (CPU, p95)** | Not specified | **1.91 ms** | `evidence/facial_extraction.csv` | `uv run python scripts/measure_extraction.py` (N=100) | **VERIFIED** |
| **Vocal DSP Extraction (CPU, Mean)** | 18.7 ms | **2.34 ms** | `evidence/vocal_extraction.csv` | `uv run python scripts/measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **Vocal DSP Extraction (CPU, p95)** | Not specified | **2.88 ms** | `evidence/vocal_extraction.csv` | `uv run python scripts/measure_extraction.py` (N=100) | **VERIFIED** |
| **Database Write Latency (SQLite)** | 2.57 ms | **2.67 ms (mean) / 3.59 ms (p95)** | `evidence/db_write_latency.csv` | `uv run python scripts/measure_extraction.py` (N=100) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Mean, GPU)** | 2.76 s | **2.14 s** | `evidence/wellness_slm_latency.csv` | `uv run python scripts/measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (p50, GPU)** | Not specified | **2.23 s** | `evidence/wellness_slm_latency.csv` | `uv run python scripts/measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM Wellness Latency (p95, GPU)** | 3.12 s | **2.42 s** | `evidence/wellness_slm_latency.csv` | `uv run python scripts/measure_wellness_slm.py` (N=30) | **CHANGED (VERIFIED)** |
| **SLM Wellness Latency (Max, GPU)** | Not specified | **2.45 s** | `evidence/wellness_slm_latency.csv` | `uv run python scripts/measure_wellness_slm.py` (N=30) | **VERIFIED** |
| **SLM 5.0s Window Margin** | 1.88 s | **2.58 s** | `evidence/wellness_slm_latency.csv` | Margin = 5.0s - p95 Latency | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop OFF, Mean)** | 0.781 s (isolated) | **1.33 s** | `evidence/voice_ttfa.csv` | `uv run python scripts/measure_voice_ttfa.py` (N=10) | **CHANGED (VERIFIED)** |
| **Voice TTFA (Loop ON, Mean)** | Not measured | **1.88 s** | `evidence/voice_ttfa.csv` | `uv run python scripts/measure_voice_ttfa.py` (N=10) | **VERIFIED** |
| **Voice TTFA (Combined Mean)** | 0.781 s | **1.61 s** | `evidence/voice_ttfa.csv` | `uv run python scripts/measure_voice_ttfa.py` (N=20) | **CHANGED (VERIFIED)** |
| **Peak GPU VRAM (Session)** | ~3.8 GB (unverified) | **3.90 GB (3991 MB / 6141 MB)** | `evidence/vram_cpu_usage.log` | `uv run python scripts/measure_hardware_and_network.py` | **CHANGED (VERIFIED)** |
| **Outbound Network Telemetry** | "Air-gapped" | **0 outbound sockets (0.00 KB)** | `evidence/netstat_outbound.txt` | `netstat -ano` audit; loopback 127.0.0.1 only | **VERIFIED** |
| **Test Suite Passed** | 69 passed, 42 skipped | **110 passed, 0 failed, 1 skipped** | `evidence/pytest_full.log` | `uv run pytest tests/ -v` | **CHANGED (VERIFIED)** |
| **Gemma 4 E2B Quantization Agreement**| 91.4% (Q4_K_M vs FP16) | **NOT MEASURED** | Local disk contains only Q4_0 | FP16 unquantized weights not present locally | **NOT MEASURED** |
| **Ground-Truth Human EMA Agreement** | 77.8% exact / 100% 1-tier | **NOT COLLECTED** | `shared_state/ema_validation_trials.json` | Synthetic trial generator (`run_ema_validation.py`) | **NOT COLLECTED / REQUIRES HUMAN** |
| **Live Demonstration Video (.mp4)** | Claimed in submission | **REQUIRES HUMAN** | Script in `DEMO_SCRIPT.md` | Human recording with webcam/mic required | **REQUIRES HUMAN** |

---

## 2. Summary of Numerical Changes (Old vs New)

1. **Facial AU Extraction Latency:**
   - *Old Value:* 14.2 ms
   - *Audited Value:* **1.75 ms mean, 1.91 ms p95**
   - *Reason for Change:* The previous figure was carried over from an unverified benchmark on different hardware. On the Intel Core i5-13450HX CPU using MediaPipe Tasks 0.10.14 C++ backend, extraction is approximately $8\times$ faster than previously assumed.

2. **Vocal Acoustic DSP Latency:**
   - *Old Value:* 18.7 ms
   - *Audited Value:* **2.34 ms mean, 2.88 ms p95**
   - *Reason for Change:* Previous figure was an estimate. On the local CPU with vectorized NumPy and SciPy operations, extracting F0, jitter, shimmer, and spectral flux across a 2-second audio frame requires only 2.34 ms.

3. **SQLite Database Write Latency:**
   - *Old Value:* 2.57 ms
   - *Audited Value:* **2.67 ms mean, 3.59 ms p95**
   - *Reason for Change:* Re-measured directly against the live `wellness_history.db` database schema across 100 consecutive synchronous writes.

4. **SLM Wellness Reasoning Latency:**
   - *Old Value:* 2.76 s mean, 3.12 s p95
   - *Audited Value:* **2.14 s mean, 2.23 s p50, 2.42 s p95, 2.45 s max**
   - *Reason for Change:* Earlier numbers were carried over prior to setting up CUDA 12.4 offloading with llama.cpp b12015. On the NVIDIA RTX 4050 Laptop GPU, full grammar-constrained JSON inference completes comfortably within the 5.0-second background cycle budget with a 2.58-second safety margin.

5. **Voice TTFA (Time to First Audio):**
   - *Old Value:* 0.781 s (isolated audio turn without full pipeline load)
   - *Audited Value:* **1.33 s mean (Wellness loop OFF), 1.88 s mean (Wellness loop ON)**
   - *Reason for Change:* Short queries achieve ~0.83 s TTFA, but across realistic varied conversational queries (10 turns with wellness loop off and 10 turns with wellness loop actively performing multimodal reasoning in the background), the empirical average is 1.33 s and 1.88 s respectively.

6. **Full Test Suite Status:**
   - *Old Value:* 69 passed, 0 failed, 42 skipped
   - *Audited Value:* **110 passed, 0 failed, 1 skipped** (out of 111 tests)
   - *Reason for Change:* Earlier, 42 E2E tests skipped because `llama-server` and model weights were not locally present. After installing llama.cpp b12015, downloading Gemma 4 E2B Q4_0 and mmproj weights, and fixing the `decide_before` listen exit evaluation prompt in `src/parlor/actions.py`, 110 tests pass completely. The single remaining skip is `test_thinking_pause_is_held` in `tests/test_conversation.py`, which is skipped by design because the synthetic TTS fixture has falling prosody that the acoustic classifier correctly identifies as complete speech.

---

## 3. Claims That Did Not Survive the Empirical Audit

### Claim 1: Carried-Over Latency & Resource Figures
- **Previous Statement:** "TTFA 0.781s, SLM latency 2.76s GPU / 4.23s CPU, facial extraction 14.2ms, vocal extraction 18.7ms, DB write 2.57ms."
- **Audit Finding:** These figures were carried over from preliminary development logs on different hardware or software configurations prior to installing the Gemma 4 E2B model.
- **Resolution:** Replaced in all reports, presentations, and defense guides with the empirically measured values listed in Table 1 above.

### Claim 2: Ground-Truth Classification Accuracy (77.8% Exact, 100% One-Tier)
- **Previous Statement:** "System achieved 77.8% exact tier agreement and 100% one-tier tolerance across 144 observation windows against human EMA self-reports."
- **Audit Finding:** Code audit of `scripts/run_ema_validation.py` and `shared_state/ema_validation_trials.json` reveals that the 144 trials were synthetically generated using `random.choices` and `np.random.normal(0.08, 0.05)`. No real human participant consent logs or study session recordings exist on disk.
- **Resolution:** The 77.8% claim is completely expunged from the abstract, conclusion, and results sections. The EMA accuracy is formally marked as **`NOT COLLECTED / REQUIRES HUMAN STUDY`**. A standardized collection harness and protocol guide have been authored (`docs/EMA_RECOLLECTION_KIT.md`) for the team to collect genuine human data prior to viva.

### Claim 3: Model Quantization Agreement (91.4% at Q4_K_M)
- **Previous Statement:** "Gemma 4 Q4_K_M quantization achieved 91.4% agreement with unquantized FP16 weights."
- **Audit Finding:** The local filesystem only contains `gemma-4-E2B_q4_0-it.gguf` (Q4_0, not Q4_K_M). The uncompressed FP16 baseline model weights (~5.2 GB) were never downloaded or benchmarked on this machine.
- **Resolution:** Marked as **`NOT MEASURED`** in all documentation. The distinction between compression fidelity (quantization agreement) and human ground-truth agreement (EMA self-report) is strictly maintained.

### Claim 4: "Air-Gapped" Operation
- **Previous Statement:** "Fully air-gapped system architecture."
- **Audit Finding:** "Air-gapped" technically implies physical network isolation (no network interface card connected). Parlor connects to local loopback sockets (`127.0.0.1:8000` and `127.0.0.1:8081`). Furthermore, initial model weights must be downloaded once during setup, and an optional user-invoked "research mode" allows web lookup.
- **Resolution:** Replaced across all documents with the legally and technically accurate statement:  
  *"The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls."*

### Claim 5: Existing 1080p60 Demonstration Video File
- **Previous Statement:** `dist/demo_backup/Parlor_Live_System_Demonstration_1080p60.mp4` is bundled as a pre-recorded fail-safe demo.
- **Audit Finding:** The directory `dist/demo_backup/` does not contain an MP4 file. Only the markdown script (`DEMO_SCRIPT.md`) and timed cue sheet exist.
- **Resolution:** Marked as **`REQUIRES HUMAN: record the demo`**. The fail-safe protocol and cue sheet remain ready for the team to record the video using OBS Studio.

---

## 4. Comprehensive List of Items Marked "REQUIRES HUMAN"

In accordance with academic ethics and the hard constraint against data fabrication, the following tasks require human action and have NOT been simulated:

1. **`REQUIRES HUMAN: Collect Empirical Human EMA Study`**
   - *Task:* Recruit at least 3 human participants (team members or peers) and run the 20-minute 4-condition protocol in `docs/EMA_RECOLLECTION_KIT.md` using `uv run python scripts/ema_collector.py`.
   - *Outcome:* Populate `shared_state/ema_records.json` with authentic human ratings and run `uv run python scripts/evaluate_ema.py` to obtain genuine accuracy figures.

2. **`REQUIRES HUMAN: Record Live Video Backup`**
   - *Task:* Screen-record a 4-minute demonstration of Parlor running live on `http://127.0.0.1:8000` following `DEMO_SCRIPT.md`.
   - *Outcome:* Save the resulting video file as `dist/demo_backup/Parlor_Live_System_Demonstration_1080p60.mp4`.

3. **`REQUIRES HUMAN: Declaration & Certificate Signatures`**
   - *Task:* Sign the final declaration and certificate pages of the project report.
   - *Personnel:*
     - M. Rama Venkata Charan (23KN1A0543)
     - B. Murali Gopi (23KN1A0515)
     - M. Kumar Siva Sai (23KN1A0542)
     - Y. Yashwanth Prakash (23KN1A0571)
     - Project Guide: Mrs. V. Aruna (Senior Assistant Professor, Dept of CSE)

---

## 5. Verification Harness Execution

Examiners and auditors can reproduce all 8 verified empirical metrics in a single command:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/reproduce_numbers.ps1
```
The script immediately outputs the verified benchmark table matching the numbers in this thesis.
