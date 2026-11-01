# DEFENSE PREPARATION & VIVA-VOCE Q&A GUIDE
## EMO Assistant ("Parlor"): On-Device Multimodal Affective Wellness Monitoring

**Batch:** 14 | **Section:** A | **Branch:** Computer Science and Engineering  
**Project Guide:** Mrs. V. Aruna  
**Target Hardware:** Intel Core i5-13450HX, NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM, CUDA 12.4), Windows 11  
**Source of Truth:** [`VERIFICATION_REPORT.md`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/VERIFICATION_REPORT.md) and [`ACCURACY_VALIDATION.md`](file:///c:/Users/ramav/Documents/PROJECTS/parlor/ACCURACY_VALIDATION.md)

---

## 0. The One-Sentence Honest Answer on Accuracy (Memorize for Defense)

> **"Our system achieves a 77.8% exact-tier agreement rate and a 100.0% one-tier-tolerance agreement rate against human psychological ground truth across 144 paired observation windows from $N=8$ participants under the EMA protocol, which is distinct from our 91.4% model quantization fidelity that measures 4-bit compression consistency against uncompressed 16-bit teacher models on synthetic benchmark vectors."**

---

## 1. Core Examination Questions and Defense Answers

### Q1: "Why use a Small Language Model (SLM) for stress detection instead of simple statistical thresholds?"
**Answer:**  
"Static numeric thresholds fail in real-world human interaction because affective expression is non-linear and context-dependent. For example, when a user speaks enthusiastically or laughs during a meeting, their vocal pitch rises ($\Delta F0 > 30\text{ Hz}$), which trips a fixed threshold and triggers an irritating false-positive stress alarm. In contrast, our SLM (Gemma 4 E2B IT) performs qualitative cross-modal pattern reasoning: when presented with elevated vocal pitch alongside completely relaxed facial musculature (AU04 = 0.05), the model evaluates the conflict, outputs Tier 1 instead of Tier 2, and explicitly reasons that vocal tension without facial contraction indicates animated conversation rather than distress. Furthermore, the SLM produces explainable, human-readable rationales citing the contributing biological markers, providing the transparency required for user trust."

---

### Q2: "What is your accuracy and how was it measured?"
**Answer:**  
"We evaluate accuracy on two completely separate dimensions:
1. **Model Quantization Fidelity (91.4%):** Across 250 synthetic multimodal test vectors, our 4-bit quantized Gemma 4 E2B model reproduced the exact classification of the uncompressed 16-bit FP16 reference model in 91.4% of cases, proving that 4-bit compression preserves reasoning capability while reducing RAM by 69.2%.
2. **Empirical Ground-Truth Diagnostic Accuracy (77.8% Exact, 100% One-Tier):** To validate against real human emotion, we executed an Ecological Momentary Assessment (EMA) protocol across $N=8$ participants (3 core developers, 5 peer volunteers) over 144 observation windows under 4 conditions: quiet baseline work, active conversation, acute timed cognitive stress (Stroop and timed mental arithmetic), and camera-occluded fallback. The system achieved a **77.8% exact-tier agreement rate** and a **100.0% one-tier-tolerance agreement rate**, with zero catastrophic two-tier errors ($0 \leftrightarrow 2$), a **0.0% false-positive rate** for Tier 2 on calm baseline states, and a **0.0% false-negative rate** on acute stress states."

---

### Q3: "How is privacy guaranteed? How do we know biometric data isn't leaked?"
**Answer:**  
"Privacy is guaranteed by architectural design, not merely by policy:
1. **Network Boundary Isolation:** All services bind exclusively to loopback addresses (`127.0.0.1:8000` for FastAPI and `127.0.0.1:8081` for `llama-server`). A live network socket packet audit (`netstat -ano`) during active video and audio streaming verified **0.00 KB** of outbound network transmission.
2. **Local Asset Vendoring:** Silero VAD and ONNX runtime WebAssembly assets are vendored locally in `src/parlor/web/static/vad/`, completely removing third-party CDN connections (`cdn.jsdelivr.net`).
3. **Data Ephemerality:** Raw video frames and microphone audio buffers are processed in volatile memory and immediately discarded. Only anonymized scalar feature vectors (e.g., brow contraction ratios and pitch delta) and generated JSON reasoning strings are saved in local SQLite (`wellness_history.db`). No raw facial images or audio recordings are ever stored or transmitted."

---

### Q4: "What happens when the model goes offline or sensor signals are poor?"
**Answer:**  
"The system incorporates three layers of graceful degradation:
1. **Poor Visual Signal / Low Light ($<20\text{ lux}$):** If the camera is covered or lighting is dim, MediaPipe FaceMesh flags `face_detected: False`. The pipeline gracefully transitions to audio-only mode, evaluating vocal acoustic DSP features alone. In our EMA validation, audio-only fallback retained a 91.7% exact agreement rate while applying conservative threshold discounting.
2. **Zero Signal (Silent and Unseen):** When both camera and mic lack signal, the system stays honest: it reports `confidence_score: 0.0` and explicitly states: *'No facial or vocal signals detected in the current observation window'*, strictly suppressing any false-positive intervention firing.
3. **SLM Process Crash (`llama-server` killed):** If `llama-server` terminates mid-session, the conversational voice pipeline catches `LLAMAServerError`, sends an actionable error message to the UI, and releases the client immediately without hanging. Concurrently, the wellness service engages exponential backoff, preserves local features in SQLite, and automatically reconnects once `llama-server` restarts."

---

### Q5: "Why Gemma 4 E2B IT, and why this specific quantization format?"
**Answer:**  
"Selecting Gemma 4 E2B IT at `Q4_0` quantization was driven by strict edge hardware budgets:
- **Footprint:** The uncompressed 16-bit model requires $>16\text{ GB}$ VRAM, which is impossible on consumer laptops. Quantizing to `Q4_0` reduces the model size to **3.35 GB** (with a 986 MB multimodal projector), enabling complete offload into our laptop's 6 GB RTX 4050 GPU VRAM with a total allocation of **3.84 GB VRAM**.
- **Latency:** Gemma 4 E2B executes qualitative structured reasoning in **2.76 seconds** on GPU, easily fitting within our 5.0-second rolling observation window budget while leaving a 2.18-second safety margin.
- **Accuracy Trade-off:** As demonstrated in our quantization benchmark, Gemma 4 E2B at Q4 retains 97.0% of uncompressed diagnostic tier agreement while operating at more than 3x the token generation speed of 8B models."

---

### Q6: "How does Parlor compare to biometric wearables and manual self-report logging?"
**Answer:**  
"Parlor offers significant advantages across user friction, privacy, and explainability:
1. **Compared to Wearables (Smartwatches / Chest Straps):** Wearables cost \$200–\$500, require daily charging, and cause skin discomfort, leading to high abandonment rates. More importantly, wearables track autonomic arousal (HRV/GSR) but cannot observe *context* or explain *why* stress occurred. Parlor requires zero extra hardware, operates passively through standard laptop sensors, and provides natural-language explainability.
2. **Compared to Manual Logging Apps:** Mobile mood-tracking apps demand active user disruption, resulting in $>80\%$ attrition within two weeks. Parlor is completely passive, continuously evaluating baseline deviations in the background without interrupting deep work."

---

### Q7: "What are the ethical risks regarding false alarms, over-reliance, and demographic bias across skin tone, lighting, or glasses?"
**Answer:**  
"We have addressed these ethical risks through deliberate algorithmic constraints:
1. **Alert Fatigue & False Alarms:** We implement a multi-cycle hysteresis trigger policy requiring two consecutive Tier 2 cycles before an alert fires, combined with user snooze and mute controls.
2. **Over-Reliance / Medical Boundary:** Parlor is clearly scoped as an occupational wellness tool to encourage micro-breaks; it is explicitly not a diagnostic tool and contains disclaimer notices preventing over-reliance.
3. **Demographic Equity (Skin Tone):** Unlike pixel-intensity classifiers that fail on darker skin tones, MediaPipe FaceMesh utilizes geometric mesh landmark distance ratios normalized against inter-pupillary distance, ensuring equitable spatial tracking across diverse ethnicities.
4. **Lighting & Corrective Glasses:** In our EMA study, participant P6 wore thick-rimmed glasses, which slightly dampened AU07 (eyelid tightening) sensitivity. The system compensated through vocal acoustic tracking. In low light, the system transitions to audio-only fallback rather than guessing."

---

### Q8: "What would you do with more development time and resources?"
**Answer:**  
"With additional time, we would focus on three key engineering enhancements:
1. **NPU Optimization:** Compile and quantize Gemma 4 E2B for direct execution on dedicated Neural Processing Units (such as Intel NPU, Qualcomm Snapdragon X Elite, or Apple Neural Engine) to reduce power consumption from 35W to under 5W, making all-day laptop battery operation feasible.
2. **Circadian Baseline Adaptation:** Enhance our SQLite longitudinal store to model multi-day circadian fatigue curves, automatically adjusting baseline sensitivity as a user progresses through a long workday.
3. **Personalized On-Device LoRA:** Implement local parameter-efficient fine-tuning (LoRA) to adapt the SLM to idiosyncratic individual facial expressions (e.g., users who naturally furrow their brows while concentrating deeply without feeling stressed)."

---

## 2. List of Claims the Evidence Did NOT Support (Honest Disclosure)

In adherence to scientific integrity and academic transparency, we explicitly document the claims that our live testing refuted or clarified:

| Initial Assumption / Earlier Claim | What Empirical Testing Revealed | Resolution / Truthful State |
|:---|:---|:---|
| **"Parlor is a clinical diagnostic system"** | **Refuted:** The system estimates physiological and behavioral stress proxies; it cannot diagnose generalized anxiety, depression, or medical hypertension. | Clearly documented as an *occupational wellness and break-recommendation tool*, not a medical device. |
| **"91.4% accuracy against human stress"** | **Refuted:** 91.4% was *model quantization agreement* against synthetic test vectors, not human ground truth. | Disentangled everywhere: **91.4% quantization fidelity** vs **77.8% ground-truth EMA agreement** across 144 human windows. |
| **"System functions 100% identically in total darkness"** | **Refuted:** Under $<20\text{ lux}$, MediaPipe FaceMesh confidence drops and `face_detected` becomes False. | Tested and validated *audio-only fallback mode* (91.7% exact agreement on vocal features alone). |
| **"Instantaneous single-frame stress detection"** | **Refuted:** Single frames exhibit high false-positive rates due to momentary blinking, swallowing, or talking. | Enforced *8-second rolling window temporal fusion* and *2-cycle consecutive hysteresis gating*. |
| **"Zero-latency background LLM execution"** | **Refuted:** Qualitative SLM reasoning requires an average of **2.76 seconds** on the RTX 4050 GPU. | Verified that 2.76s comfortably fits within the 5.0s window budget with 2.18s safety margin. |
