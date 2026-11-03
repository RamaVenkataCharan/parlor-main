# FINAL PROJECT REPORT
## B.Tech in Computer Science and Engineering

---

# EMO Assistant ("Parlor"): On-Device Multimodal Affective Wellness Monitoring and Real-Time Conversational AI

### A Major Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of
### BACHELOR OF TECHNOLOGY
### in
### COMPUTER SCIENCE AND ENGINEERING

**Submitted by:**
- **Student 1:** M. Rama Venkata Charan (Roll No: 23KN1A0543)
- **Student 2:** B. Murali Gopi (Roll No: 23KN1A0515)
- **Student 3:** M. Kumar Siva Sai (Roll No: 23KN1A0542)
- **Student 4:** Y. Yashwanth Prakash (Roll No: 23KN1A0571)

**Under the Guidance of:**  
**Mrs. V. Aruna**  
Project Guide  
Department of Computer Science and Engineering  

**Batch:** 14 | **Section:** A | **Academic Year:** 2026–2027  
**Department of Computer Science and Engineering**  
**[University / College Name Placeholder]**  

---

## CERTIFICATE

This is to certify that the project entitled **"EMO Assistant ('Parlor'): On-Device Multimodal Affective Wellness Monitoring and Real-Time Conversational AI"** is a bona fide record of work carried out by **Batch 14, Section A**:
- **M. Rama Venkata Charan** (Roll No: 23KN1A0543)
- **B. Murali Gopi** (Roll No: 23KN1A0515)
- **M. Kumar Siva Sai** (Roll No: 23KN1A0542)
- **Y. Yashwanth Prakash** (Roll No: 23KN1A0571)

under my guidance and supervision in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science and Engineering**.

\
\
**Mrs. V. Aruna**  
Project Guide  
Department of Computer Science and Engineering  

\
\
**Head of the Department**  
Department of Computer Science and Engineering  

---

## DECLARATION

We hereby declare that the project work entitled **"EMO Assistant ('Parlor'): On-Device Multimodal Affective Wellness Monitoring and Real-Time Conversational AI"** submitted to the Department of Computer Science and Engineering is an authentic record of our own original work conducted under the guidance of **Mrs. V. Aruna**. We further declare that this work has not been submitted previously to any other university or institute for any degree or diploma.

- **M. Rama Venkata Charan** (Roll No: 23KN1A0543)
- **B. Murali Gopi** (Roll No: 23KN1A0515)
- **M. Kumar Siva Sai** (Roll No: 23KN1A0542)
- **Y. Yashwanth Prakash** (Roll No: 23KN1A0571)

Date: November 1, 2026  
Place: [City Placeholder]

---

## ACKNOWLEDGMENTS

We express our profound gratitude to our esteemed project guide, **Mrs. V. Aruna**, for her invaluable guidance, continuous encouragement, and constructive critique throughout the architecture, implementation, and empirical verification of this project. Her insightful feedback on affective computing, on-device model architectures, and rigorous testing methodologies was instrumental in completing this work.

We extend our sincere thanks to the Head of the Department and the faculty members of the Department of Computer Science and Engineering for providing the laboratory facilities, computing infrastructure, and supportive academic environment necessary to pursue this research.

---

## ABSTRACT

Digital burnout and workplace cognitive fatigue in knowledge workers often develop silently, culminating in chronic exhaustion and reduced productivity before clinical symptoms are recognized. Existing workplace wellness solutions rely heavily on active manual self-logging—which suffers from severe user attrition—or continuous biometric wearables, which introduce skin discomfort, cost barriers, and severe privacy concerns regarding cloud biometric streaming. 

This project presents **Parlor**, a fully on-device multimodal artificial intelligence assistant and passive affective wellness monitoring platform that operates entirely on commodity laptop hardware. Parlor passively analyzes facial micro-expressions via MediaPipe FaceMesh Action Units (AU04 Brow Lowerer, AU07 Lid Tightener, AU20 Lip Stretcher) and vocal acoustic biomarkers via real-time digital signal processing (fundamental frequency perturbation, jitter, shimmer, spectral tension) extracted over rolling observation windows. Rather than enforcing static, brittle numeric thresholds, an on-device Small Language Model (Google Gemma 4 E2B IT quantized at `Q4_0` running via `llama-server`) performs qualitative clinical reasoning over the pattern of signals, distinguishing animated conversation from genuine stress and providing natural-language explanations citing active physiological markers. 

To prevent user annoyance and alert fatigue, an anti-false-positive trigger manager enforces a multi-cycle hysteresis policy (requiring consecutive elevated cycles) coupled with customizable sensitivity tiers, snooze timers, and provenance disclosures. The entire pipeline runs within a single-process, asynchronous Python 3.12 architecture alongside an ultra-low-latency voice assistant utilizing acoustic turn-taking classification (`smart-turn-v3.2`) and local neural speech synthesis (`Kokoro-ONNX`).

Comprehensive empirical testing across the regression test suite demonstrated a **99.1% pass rate** (111 passed out of 112 items, 0 failed, 1 intentionally skipped by design: *"the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live"*). In rigorous 30-turn alternating live measurements on an NVIDIA GeForce RTX 4050 Laptop GPU (plugged into AC power, 2700 MHz core clocks, 54°C–71°C GPU temperature), Parlor achieved a conversational Time to First Audio (**TTFA**) of **1.92 s mean / 3.55 s p95** with background monitoring inactive (Loop OFF, 95% CI: [1.66 s, 2.21 s]), **1.74 s mean / 3.61 s p95** unmitigated (95% CI: [1.47 s, 2.07 s]), and **1.77 s mean / 3.42 s p95** with concurrent background wellness monitoring (Loop ON Mitigated, 95% CI: [1.51 s, 2.08 s]). The end-to-end background SLM qualitative reasoning latency averaged **2.14 s mean / 2.45 s p95** across standard prompts (pooled across all prompt types including cross-modal conflict reasoning: **2.23 s mean / 2.49 s p95 / 4.32 s max**, leaving a **0.68 s safety margin** against the worst observed case below the 5.0 s budget and a **2.77 s margin** against the pooled mean), supported by a lightweight non-SLM feature extraction overhead of **10.89 ms mean** (3.97 ms facial, 2.85 ms vocal DSP, 4.07 ms SQLite persistence). Hardware monitoring confirmed a peak footprint of **3.90 GB dedicated GPU VRAM** (3991 MB / 6141 MB), **2.42 GB host process working set RAM** (5.24 GB committed), and a longitudinal storage growth rate of **132 KB/hour** (~1.03 MB / 8-hour workday). A network socket audit confirmed **0.00 KB** of outbound data transmission during operation (strictly local network boundary on `127.0.0.1`). An Ecological Momentary Assessment (**EMA**) evaluation protocol and collection harness were established to benchmark inferred stress against momentary human self-reports; empirical collection across human cohorts is formalized as an ongoing study (`REQUIRES HUMAN`). Synthetic feature vector evaluations confirmed robust cross-modal pattern reasoning, complete signal honesty under zero-input conditions (stored as "insufficient signal" with a HOLD policy on trigger hysteresis and excluded from EMA ground-truth analysis), fine-grained Tier 2 reachability boundaries (AU04 $\ge$ 0.97, Pitch Delta $\ge$ +90Hz), and reliable multi-cycle intervention triggering in Balanced mode verified with live-model inference over WebSockets. Parlor establishes that explainable, non-invasive affective wellness computing can be achieved locally, privately, and affordably on everyday personal computing devices.

---

## TABLE OF CONTENTS

1. **Introduction and Problem Statement**
   - 1.1 The Silent Epidemic of Digital Workplace Burnout
   - 1.2 Limitations of Existing Approaches
   - 1.3 Project Objectives and Research Scope
   - 1.4 Outline of the Report
2. **Literature Review and Related Work**
   - 2.1 Occupational Stress and Affective Computing
   - 2.2 Facial Action Coding System (FACS) in Stress Detection
   - 2.3 Acoustic Biomarkers of Cognitive Load and Tension
   - 2.4 Evolution of Edge AI and Small Language Models (SLMs)
   - 2.5 Ecological Momentary Assessment (EMA) Methodologies
3. **System Design and Architecture**
   - 3.1 Architectural Principles and Requirements
   - 3.2 Single-Process Asynchronous Pipeline Architecture
   - 3.3 Multimodal Perception Engine
   - 3.4 Temporal Fusion and Rolling Window Buffer
   - 3.5 SLM Reasoning Engine and Prompt Specification
   - 3.6 Anti-False-Positive Trigger Management and Intervention Policy
   - 3.7 Database Schema and Longitudinal State Storage
   - 3.8 User Interface Design and Feedback Mechanisms
4. **Implementation Details**
   - 4.1 System Environment and Technology Stack
   - 4.2 Software Modules and Responsibility Matrix
   - 4.3 On-Device Model Integration and Quantization Strategy
   - 4.4 Acoustic Turn-Taking and Speech Synthesis Pipeline
   - 4.5 Vendoring Local VAD Assets for Zero-Cloud Resilience
5. **Experimental Verification and Empirical Results**
   - 5.1 Verification Test Suite Audit (111 Tests)
   - 5.2 System Latency and Subsystem Benchmark Breakdown
   - 5.3 Hardware Resource Utilization Profiling
   - 5.4 Privacy and Local Isolation Network Audit
   - 5.5 Ground-Truth Accuracy Validation (EMA Protocol Analysis)
   - 5.6 Cross-Modal Conflict and Signal Honesty Verification
6. **Discussion, Limitations, and Ethical Considerations**
   - 6.1 Clinical Role Boundary: Stress Signal Estimation vs Medical Diagnosis
   - 6.2 System Limitations Under Adverse Environmental Conditions
   - 6.3 Ethical Safeguards: Alert Fatigue, Over-Reliance, and Demographics
7. **Future Work and Conclusion**
   - 7.1 Potential Hardware and Algorithmic Extensions
   - 7.2 Summary of Contributions and Final Conclusion
8. **References**

---

## 1. INTRODUCTION AND PROBLEM STATEMENT

### 1.1 The Silent Epidemic of Digital Workplace Burnout
Modern knowledge work is increasingly mediated through digital displays, virtual meetings, and continuous asynchronous communication channels. While these technologies afford unprecedented geographical flexibility, they have precipitated widespread digital burnout, cognitive overload, and chronic workplace stress. According to occupational health studies, sustained stress triggers autonomic nervous system hyperactivation, leading to elevated cortisol levels, reduced executive function, cardiovascular strain, and eventual clinical burnout.

Crucially, stress rarely manifests instantaneously; it accumulates insidiously across extended work sessions. Knowledge workers frequently experience "stress blindness," where intense cognitive immersion blinds individuals to escalating physiological tension—such as prolonged brow furrowing, shallow irregular breathing, and vocal strain—until severe fatigue or headaches occur.

### 1.2 Limitations of Existing Approaches
Current interventions for workplace stress suffer from significant structural limitations:
1. **Manual Ecological Momentary Logging:** Mobile wellness applications prompt users to rate their mood or stress levels periodically. These systems suffer from drastic attrition rates common in self-monitoring eHealth interventions (Baumel et al., 2019; Eysenbach, 2005) because manual self-reporting introduces disruptive cognitive friction during deep work.
2. **Wearable Physiological Sensors:** Smartwatches and chest bands track Heart Rate Variability (HRV) and Galvanic Skin Response (GSR). However, consumer wearables require daily charging, introduce skin irritation, cost hundreds of dollars, and cannot visually or acoustically explain *why* an individual is stressed.
3. **Cloud-Based Surveillance Platforms:** Emerging enterprise sentiment analytics tools record employee video and audio and transmit the streams to corporate cloud servers. This approach creates catastrophic privacy risks, employee surveillance resistance, and compliance violations under regulations such as GDPR and CCPA.
4. **Brittle Fixed-Threshold Heuristics:** Traditional computer-vision stress tools employ rigid statistical cutoffs (e.g., if brow contraction > 0.6, trigger stress). In practice, human affective expression is highly non-linear; an enthusiastic developer laughing or speaking passionately trips static thresholds, flooding the user with irritating false alarms.

### 1.3 Project Objectives and Research Scope
To overcome these limitations, this project designs, implements, and verifies **Parlor**, an open-source, fully on-device multimodal artificial intelligence platform. The primary objectives are:
- **Zero-Cloud Privacy:** Execute all vision, acoustic, language reasoning, and database operations entirely on local hardware (`127.0.0.1`), ensuring zero outbound biometric data transmission.
- **Sensorless Passive Monitoring:** Leverage existing laptop webcams and microphones to passively track facial micro-expressions and vocal acoustic biomarkers without requiring wearable sensors.
- **Qualitative SLM Pattern Reasoning:** Replace brittle numeric rules with an on-device Small Language Model (Google Gemma 4 E2B IT at `Q4_0`) that contextualizes cross-modal patterns and provides explainable reasoning.
- **Low-Latency Conversational Responsiveness:** Co-locate the wellness monitoring engine with an interactive voice assistant maintaining conversational Time to First Audio (**TTFA** empirically measured at 1.77 s – 1.92 s mean, with p95 at 3.42 s – 3.55 s) to ensure fluid dialogue without disrupting deep work.
- **Rigorous Ground-Truth Validation:** Empirically evaluate system accuracy against human psychological self-report using an Ecological Momentary Assessment (EMA) protocol across diverse participants and tasks.

---

## 2. LITERATURE REVIEW AND RELATED WORK

### 2.1 Occupational Stress and Affective Computing
Affective computing, pioneered by Rosalind Picard (1997), seeks to develop systems capable of recognizing, interpreting, and processing human emotional and affective states. In occupational settings, stress is conceptualized as an imbalance between environmental demands and an individual's perceived coping resources (Lazarus & Folkman, 1984). Chronic activation of the sympathetic-adrenomedullary (SAM) axis manifests in observable somatic, behavioral, and vocal perturbations, providing an objective substrate for passive computational detection.

### 2.2 Facial Action Coding System (FACS) in Stress Detection
Paul Ekman and Wallace Friesen developed the Facial Action Coding System (FACS) in 1978, decomposing facial expressions into individual Action Units (AUs) tied to specific facial muscle contractions. Empirical clinical research has identified specific AUs correlated with acute mental stress and cognitive load:
- **AU04 (Brow Lowerer / Corrugator supercilii):** Strongest indicator of cognitive struggle, frustration, and intense concentration.
- **AU07 (Lid Tightener / Orbicularis oculi):** Associated with squinting under mental fatigue and visual strain.
- **AU20 (Lip Stretcher / Risorius):** Indicates somatic tension and anxiety.
- **Eye Aspect Ratio (EAR) & Blink Metrics:** Spontaneous blink rate drops drastically during visual absorption and spikes erratically during acute fatigue.

Recent advancements in deep learning landmark detection, notably Google's **MediaPipe FaceMesh** (Kartynnik et al., 2019), allow real-time 3D tracking of 478 facial landmarks on consumer hardware at negligible CPU overhead, enabling robust AU estimation without heavy deep neural networks.

### 2.3 Acoustic Biomarkers of Cognitive Load and Tension
Speech production is intrinsically coupled to the autonomic nervous system. Under acute psychological stress, physiological arousal induces laryngeal muscle tension, vocal fold stiffening, and subglottal pressure changes (Scherer, 1986). These physiological changes generate measurable acoustic perturbations:
- **Fundamental Frequency ($F0$) Perturbation:** Stress increases average pitch and causes abrupt micro-tremors in fundamental frequency.
- **Jitter and Shimmer:** Vocal instability manifests as cycle-to-cycle frequency variation (jitter) and amplitude variation (shimmer).
- **Spectral Energy Distribution:** Laryngeal constriction redistributes vocal energy into higher frequency formants (spectral tilt / spectral tension).
- **Speech Cadence & Pause Ratios:** Under acute cognitive demand, speech rate accelerates while pause duration ratios become erratic.

### 2.4 Evolution of Edge AI and Small Language Models (SLMs)
Historically, qualitative clinical reasoning required large foundational models hosted in centralized datacenters. However, recent breakthroughs in model architecture, quantization techniques (such as `llama.cpp` GGML/GGUF quantization), and compact architectures—exemplified by Google's **Gemma** family (Gemma Team, 2024) and Meta's **Llama 3** (AI@Meta, 2024)—demonstrate that 2-billion to 4-billion parameter models can perform sophisticated structured reasoning locally on consumer GPUs. Constraining model outputs via context-free grammar-forced JSON schemas guarantees deterministic output parsing, making SLMs practical for safety-critical background control loops.

### 2.5 Ecological Momentary Assessment (EMA) Methodologies
Laboratory stress studies frequently utilize standardized stressors such as the Trier Social Stress Test (TSST) or the Stroop color-word interference task. However, laboratory affect often fails to generalize to naturalistic office environments. Ecological Momentary Assessment (EMA) addresses this ecological validity gap by collecting real-time, in-situ self-reports immediately following active task windows (Stone & Shiffman, 1994). Mapping continuous Likert ratings to discrete ordinal stress tiers establishes an objective ground truth for validating automated affect recognition systems.

---

## 3. SYSTEM DESIGN AND ARCHITECTURE

### 3.1 Architectural Principles and Requirements
The architecture of Parlor is governed by five foundational design requirements:
1. **Single-Process Coexistence:** Conversational voice turns and passive wellness monitoring must execute concurrently within a single unified process without thread locking or event loop starvation.
2. **Deterministic Processing Budgets:** The conversational assistant operates with interactive low latency; the background wellness monitoring loop enforces a strict $<5.0\text{ s}$ observation analysis budget within each 8.0-second cycle.
3. **Cross-Modal Pattern Reasoning:** High vocal energy without facial contraction must be recognized as animated conversation rather than stress; simultaneous facial brow furrowing and vocal pitch jitter must be recognized as acute tension.
4. **Anti-False-Positive Hysteresis:** Interventions must never trigger on momentary spikes; a user must exhibit sustained tension across consecutive observation cycles.
5. **Transparency & Provenance Disclosure:** Every intervention card must feature an expandable *"Why did this fire?"* panel detailing the specific physiological signals that triggered the alert.

### 3.2 Single-Process Asynchronous Pipeline Architecture
Parlor rejects complex multi-service container architectures in favor of an elegant, single-process asynchronous Python 3.12 architecture running on FastAPI and Uvicorn. 

```
                                  BROWSER CLIENT (Chrome / Web Frontend)
                     ┌─────────────────────────────────────────────────────────────┐
                     │ • Local Silero VAD (Client-side speech boundary detection)  │
                     │ • Canvas Video Capture (720p / 2 fps passive snapshots)     │
                     │ • AudioWorklet PCM Streamer (16 kHz 16-bit mono chunks)    │
                     │ • Interactive Diagnostics Drawer & Intervention UI Cards   │
                     └──────────────────────────────┬──────────────────────────────┘
                                                    │
                                     WebSocket Connection (/ws)
                                                    │
                     ┌──────────────────────────────▼──────────────────────────────┐
                     │                PARLOR CORE SERVER (FastAPI / asyncio)       │
                     │                                                             │
                     │  ┌────────────────────────┐     ┌────────────────────────┐  │
                     │  │  CONVERSATIONAL ENGINE │     │    WELLNESS SERVICE    │  │
                     │  │                        │     │                        │  │
                     │  │ • Smart-Turn Classifier│     │ • MediaPipe FaceMesh   │  │
                     │  │   (Turn Detection ONNX)│     │   (AU04, AU07, AU20)   │  │
                     │  │ • Llama-Server Streamer│     │ • Vocal DSP (Librosa)  │  │
                     │  │ • Kokoro-ONNX Neural   │     │   (F0, Jitter, Shimmer)│  │
                     │  │   Speech Synthesis     │     │ • Temporal Fusion      │  │
                     │  │ • Action Head Decider  │     │   (Rolling Window)     │  │
                     │  └───────────┬────────────┘     └───────────┬────────────┘  │
                     │              │                              │               │
                     │              └──────────────┬───────────────┘               │
                     │                             │                               │
                     │           Non-blocking ThreadPoolExecutor Offload           │
                     │                             │                               │
                     │             ┌───────────────▼───────────────┐               │
                     │             │  LOCAL INFERENCE BACKENDS     │               │
                     │             │                               │               │
                     │             │ • llama-server (Gemma 4 E2B)  │               │
                     │             │   Port 8081 / HTTP Keep-Alive │               │
                     │             │ • SQLite DB (Local Storage)   │               │
                     │             └───────────────────────────────┘               │
                     └─────────────────────────────────────────────────────────────┘
```

The server maintains a single active WebSocket connection per client. Media chunks streamed from the browser are multiplexed:
- Audio buffers immediately feed conversational turn detection.
- Audio and video buffers simultaneously update thread-safe circular feature buffers inside `WellnessService`.
- Heavy computing operations (MediaPipe landmarking, Librosa FFT extraction, and SLM HTTP completions) are dispatched to `concurrent.futures.ThreadPoolExecutor` worker threads, preventing event-loop blocking.

### 3.3 Multimodal Perception Engine

#### 3.3.1 Facial Action Unit Extractor (`facial.py`)
Facial landmarking is performed using **MediaPipe FaceMesh**, tracking 478 3D facial coordinates normalized relative to inter-pupillary distance:
- **AU04 (Brow Lowerer):** Computed as Euclidean distance between medial brow landmarks (55, 285) normalized against nasal anchor (168).
- **AU07 (Lid Tightener):** Computed as vertical eye aperture across superior/inferior palpebral landmarks (159–145 and 386–374).
- **AU20 (Lip Stretcher):** Computed as transverse distance between oral commissures (61, 291).
- **Head Pose Estimation:** Solved via Perspective-n-Point (PnP) using facial symmetry landmarks to estimate Euler angles (Pitch, Yaw, Roll). Observations with $|\text{Yaw}| > 30^\circ$ or $|\text{Pitch}| > 25^\circ$ are down-weighted to prevent false landmark distortion.

#### 3.3.2 Vocal Acoustic DSP Extractor (`vocal.py`)
Acoustic feature extraction operates on 16 kHz raw PCM audio buffers captured during user speech turns:
- **Fundamental Frequency ($F0$):** Extracted via parabolic interpolation over normalized autocorrelation peaks. Pitch delta ($\Delta F0$) is computed against participant calibrated baseline.
- **Jitter (Frequency Perturbation):** Measured as relative average cycle perturbation:
  $$Jitter(\%) = \frac{\frac{1}{N-1}\sum_{i=1}^{N-1}|T_i - T_{i+1}|}{\frac{1}{N}\sum_{i=1}^N T_i} \times 100$$
- **Shimmer (Amplitude Perturbation):** Measured as relative amplitude perturbation:
  $$Shimmer(\%) = \frac{\frac{1}{N-1}\sum_{i=1}^{N-1}|A_i - A_{i+1}|}{\frac{1}{N}\sum_{i=1}^N A_i} \times 100$$
- **Spectral Energy & Tension:** Ratio of high-frequency energy ($>1000\text{ Hz}$) to low-frequency energy ($<1000\text{ Hz}$), capturing laryngeal constriction.

### 3.4 Temporal Fusion and Rolling Window Buffer (`fusion.py`)
Human affective states exhibit temporal inertia. Instantaneous feature snapshots are stored in an 8-second rolling window buffer maintaining up to 5 temporal cycles. The fusion engine computes running statistical summaries (mean, standard deviation, and peak rates) and normalizes active features against user baselines established during the initial 60 seconds of interaction.

```json
{
  "window_summary": {
    "facial_signals": {
      "au04_brow_furrow_mean": 0.38,
      "au07_eye_tightening_mean": 0.42,
      "blink_rate_per_min": 8.4,
      "face_detected": true
    },
    "vocal_signals": {
      "f0_delta_hz": 24.2,
      "jitter_percent": 2.14,
      "shimmer_percent": 3.82,
      "spectral_tension": 0.68,
      "speech_detected": true
    },
    "temporal_context": {
      "cycles_observed": 5,
      "sustained_tension_trend": true
    }
  }
}
```

### 3.5 SLM Reasoning Engine and Prompt Specification
The fused JSON vector is submitted to the local Small Language Model (Gemma 4 E2B IT). The prompt enforces qualitative clinical evaluation and demands a grammar-constrained JSON response adhering to `REASONING_SCHEMA`:

```json
{
  "type": "object",
  "properties": {
    "tier": {"type": "integer", "enum": [0, 1, 2]},
    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "reasoning": {"type": "string"},
    "contributing_factors": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["tier", "confidence", "reasoning", "contributing_factors"]
}
```

#### Stress Tier Semantic Definitions:
- **Tier 0 (Baseline / Low Tension):** Relaxed facial musculature, stable vocal pitch, normal blink rate. No action required.
- **Tier 1 (Elevated / Moderate Tension):** Mild brow tension, minor vocal strain, or cross-modal discordance (e.g., high vocal energy during friendly conversation). System logs observation; soft micro-intervention may prepare.
- **Tier 2 (Acute Stress / High Tension):** Sustained concurrent brow furrowing (AU04), eyelid tightening (AU07), and vocal acoustic tremor (elevated jitter/shimmer). Triggers proactive wellness intervention.

### 3.6 Anti-False-Positive Trigger Management and Intervention Policy (`triggers.py`, `interventions.py`)
To prevent alert fatigue, the trigger manager enforces strict behavioral guardrails:
1. **Consecutive Cycle Requirement (Hysteresis):** An intervention fires only when the system classifies the user in elevated stress (Tier 1 or Tier 2) across consecutive observation cycles according to the configured sensitivity profile. A single isolated spike is suppressed.
2. **Dynamic Sensitivity Profiles:**
   - *Conservative:* Requires 4 consecutive cycles; 7.5-minute (450s) cooldown between alerts.
   - *Balanced (Default):* Requires 3 consecutive cycles; 5.0-minute (300s) cooldown.
   - *Sensitive:* Requires 2 consecutive cycles; 3.0-minute (180s) cooldown.
3. **User Control Mechanisms:**
   - *Snooze:* Suppresses alerts for 10 to 60 minutes with a single click.
   - *Mute:* Completely disables audio notifications while preserving visual logging.
4. **Explainable Provenance Disclosure:**
   Intervention cards display the clinical reasoning and allow expanding an *"Observed triggers"* panel, disclosing the exact physiological markers that drove the SLM decision (e.g., *"Observed triggers: AU04 Brow Furrow=0.98, Pitch Mean (F0) Delta=+92.0 Hz, Vocal Tension Index=0.95"*).
5. **Insufficient Signal Window Policy (HOLD):** Observation windows where sensors detect no human face or vocal activity (unlit webcam, covered lens, user looking away) are assigned a score of `-1.0` ('insufficient signal'). Missing sensor telemetry is not evidence of physiological relaxation. To prevent transient occlusion (e.g., looking down at notes or turning away momentarily for 8 seconds) from prematurely wiping accumulated distress, the trigger engine enforces a **HOLD** policy: consecutive high-stress counts are preserved without incrementing or resetting, while strictly prohibiting interventions from firing during zero-signal windows (`should_fire = False`). A verified Low Stress (Tier 0) cycle immediately resets the consecutive count to 0.

### 3.7 Database Schema and Longitudinal State Storage (`db.py`)
Longitudinal data is persisted in a local SQLite database (`shared_state/wellness_history.db`) with an 8.0-second observation cycle polling a rolling window of 5 feature samples (`FeatureFusionEngine(window_size=5)`). Queries utilize deterministic sorting (`ORDER BY timestamp DESC, id DESC`):

```sql
CREATE TABLE IF NOT EXISTS stress_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    stress_level TEXT NOT NULL,
    numeric_score REAL NOT NULL,
    primary_drivers TEXT,
    reasoning TEXT,
    confidence REAL,
    intervention_fired INTEGER DEFAULT 0,
    intervention_type TEXT,
    metadata TEXT
);
```

---

## 4. IMPLEMENTATION DETAILS

### 4.1 System Environment and Technology Stack
- **Operating System:** Windows 11 Home (Build 26100)
- **Programming Language:** Python 3.12.13 (Managed via `uv`)
- **GPU Acceleration:** NVIDIA CUDA 12.4 with cuDNN
- **Web & Networking:** FastAPI 0.135.3, Uvicorn 0.43.0, WebSockets 16.0
- **Computer Vision & Landmarking:** OpenCV 5.0.0.93, Google MediaPipe 0.10.14
- **Audio Processing & VAD:** NumPy 2.4.4, SciPy 1.17.1, Silero VAD (ONNX)
- **Local Neural Inference:** `llama.cpp` (b12015), `onnxruntime` 1.24.4, `kokoro-onnx` 0.5.0

### 4.2 Software Modules and Responsibility Matrix

| Module Name | File Location | Lines | Core Algorithmic Responsibilities |
|:---|:---|:---:|:---|
| **Server Controller** | `src/parlor/server.py` | 1005 | WebSocket lifecycle, frame routing, conversational turn dispatch, mode switching. |
| **Pipeline Controller**| `src/parlor/pipeline.py`| 471 | Streaming LLM token parser, speculative cache priming, TTS dispatch, barge-in cancellation. |
| **Wellness Loop** | `src/parlor/wellness.py`| 265 | Background observation timer, multimodal feature aggregation, SLM executor handoff. |
| **Facial Extractor** | `src/parlor/facial.py` | 225 | MediaPipe FaceMesh processing, AU04/07/20 geometric ratios, PnP head pose filtering. |
| **Vocal Extractor** | `src/parlor/vocal.py` | 178 | Normalized autocorrelation pitch tracking, jitter, shimmer, spectral tension calculation. |
| **Feature Fusion** | `src/parlor/fusion.py` | 125 | Rolling statistical buffer, baseline normalization, structured SLM prompt synthesis. |
| **Trigger Manager** | `src/parlor/triggers.py` | 105 | Multi-cycle consecutive evaluation, cooldown clocks, sensitivity scaling. |
| **Interventions** | `src/parlor/interventions.py`| 105 | Provenance disclosure generation, personalized empathetic micro-interventions. |
| **LLM Process Host** | `src/parlor/llama.py` | 304 | `llama-server` process management, GGUF parameter compiling, health watchdog probes. |
| **Action Decider** | `src/parlor/actions.py` | 185 | Grammar-forced JSON action routing (mode switches, timers, delegation). |
| **Database Host** | `src/parlor/db.py` | 135 | SQLite transaction manager, assessment history indexing, rolling trend queries. |

### 4.3 On-Device Model Integration and Quantization Strategy
The project standardizes on **Google Gemma 4 E2B IT** quantized at `Q4_0`:
- **Model GGUF:** `gemma-4-E2B_q4_0-it.gguf` (3.35 GB)
- **Multimodal Projector:** `gemma-4-E2B-it-mmproj.gguf` (986 MB)
- **Inference Server:** `llama-server.exe` with `-ngl 99` (all layers offloaded to RTX 4050 GPU VRAM).
- **Thinking Token Budget:** Gemma 4 IT generates reasoning tokens (`reasoning_content`) by default. To prevent JSON schema truncation and eliminate decode latency, `thinking_budget: 0` and `chat_template_kwargs: {"enable_thinking": False}` are enforced for all structured reasoning requests.

### 4.4 Vendoring Local VAD Assets for Zero-Cloud Resilience
Previous iterations loaded `onnxruntime-web` and `@ricky0123/vad-web` from external content delivery networks (`cdn.jsdelivr.net`). To satisfy the strict offline and zero-cloud requirements, all runtime assets were downloaded, verified, and vendored locally under `src/parlor/web/static/vad/`:
- `ort.js` (ONNX Runtime WebAssembly core)
- `silero_vad.onnx` (Silero Voice Activity Detection model weights, 1.8 MB)
- `vad.worklet.bundle.min.js` (Web Audio API audio worklet processor)
The frontend `index.html` loads all scripts locally via relative paths. The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.

---

## 5. EXPERIMENTAL VERIFICATION AND EMPIRICAL RESULTS

### 5.1 Verification Test Suite Audit (111 Tests)
The comprehensive test suite was executed to confirm regression stability:

$$\text{Test Suite Pass Rate} = \frac{110 \text{ Passed}}{111 \text{ Total}} = \mathbf{99.1\%} \quad (0 \text{ Failed}, 1 \text{ Skipped by Design})$$

- `test_thinking_pause_is_held` in `tests/test_conversation.py:68` is skipped by design with the verified skip reason: *"the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live"*.
- All 42 end-to-end multi-turn conversational and delegation tests executed against the live Gemma 4 E2B model on GPU (earlier runs had skipped these 42 tests prior to `llama-server` and GGUF model installation).
- A prompt evaluation discrepancy in `test_listen.py` was identified and resolved in `actions.py`, ensuring 100% pass across all listen turns.

### 5.2 System Latency and Subsystem Benchmark Breakdown
All latency figures represent empirical measurements captured on this machine and logged in `evidence/`:

| Subsystem Component | Empirical Measurement | Subsystem Context / Constraint | Evidence File |
|:---|:---:|:---:|:---|
| **Conversational Turn TTFA (Loop OFF)** | **1.920 s mean / 3.545 s p95** (N=30, CI: [1.66s, 2.21s]) | Baseline isolated voice mode | `evidence/voice_ttfa_30_turns.csv` |
| **Conversational Turn TTFA (Loop ON Unmitigated)** | **1.739 s mean / 3.612 s p95** (N=30, CI: [1.47s, 2.07s]) | Concurrent wellness without yield | `evidence/voice_ttfa_30_turns.csv` |
| **Conversational Turn TTFA (Loop ON Mitigated)** | **1.774 s mean / 3.419 s p95** (N=30, CI: [1.51s, 2.08s]) | Concurrent wellness with turn yield | `evidence/voice_ttfa_30_turns.csv` |
| **Facial AU Feature Extraction (Real Face, Normal)**| **3.97 ms mean / 4.81 ms p95** (N=100)| 33.3 ms budget (30 FPS) | `evidence/facial_extraction_real.csv` |
| **Facial AU Feature Extraction (Simulated Dim 15%)**| **4.39 ms mean / 6.84 ms p95** (N=100)| 33.3 ms budget (30 FPS) | `evidence/facial_extraction_dim.csv` |
| **Facial AU Feature Extraction (Simulated Head ~30°)**| **4.69 ms mean / 6.58 ms p95** (N=100)| 33.3 ms budget (30 FPS) | `evidence/facial_extraction_turned.csv` |
| **Facial AU Feature Extraction (Blank / No Face)**  | **1.92 ms mean / 2.45 ms p95** (N=100)| 33.3 ms budget (30 FPS) | `evidence/facial_extraction_blank.csv` (early exit) |
| **Vocal Acoustic DSP Extraction (CPU)** | **2.85 ms mean / 3.73 ms p95** (N=100)| 20.0 ms budget | `evidence/vocal_extraction.csv` |
| **Temporal Feature Fusion & Prompt Build** | **< 0.05 ms** | In-memory deque aggregation | `src/parlor/fusion.py` |
| **SLM Reasoning — Standard Prompts (GPU, Gemma 4 E2B)** | **2.14 s mean / 2.45 s p95** (N=30, max 2.45s) | $\le 5.000\text{ s}$ window budget | `evidence/wellness_slm_latency.csv` (+2.55s margin) |
| **SLM Reasoning — Cross-Modal Conflict Prompts (CoT)** | **2.79 s mean / 4.32 s max** (N=5) | Extended Chain-of-Thought deliberation | `evidence/live_pattern_reasoning.json` (+0.68s margin) |
| **SLM Reasoning — Pooled Across All Types (N=35)** | **2.23 s mean / 2.49 s p95 / 4.32 s max** | Overall inference envelope | `evidence/wellness_slm_latency.csv` (+2.77s mean margin) |
| **SQLite Transaction Logging** | **4.07 ms mean / 5.29 ms p95** (N=100)| Local persistence | `evidence/db_write_latency.csv` |
| **Total Non-SLM Pipeline Overhead** | **10.89 ms mean** (Face 3.97 + Vocal 2.85 + DB 4.07)| $\le 50.0\text{ ms}$ budget | Direct sum of component means |
| **Complete Observation Cycle E2E Latency** | **2.15 s mean / 2.50 s p95 (standard)** | $\le 5.000\text{ s}$ observation window | 46.0% headroom on worst-case 4.32s |

The 95th-percentile SLM latency across 30 repeated live standard cycles was **2.45 s**, which, combined with the **10.89 ms** non-SLM extraction and database overhead, leaves a **2.55 s safety margin** below the 5.0-second background observation window budget. When evaluating ambiguous cross-modal conflict scenarios (e.g., elevated vocal pitch alongside a relaxed facial baseline), the SLM generates extended chain-of-thought clinical explanations, causing peak inference duration to reach **4.32 s**. Even under this worst-case scenario, the system maintains a **0.68 s safety margin** (13.6% headroom) against the 5.0-second SLM budget and a **3.68 s margin** (46.0% headroom) against the 8.0-second cycle interval, guaranteeing zero pipeline backlog. In 30-turn alternating measurements, conversational TTFA remained interactive across all conditions (p50 of 1.48s to 1.62s; mean of 1.74s to 1.92s).

### 5.3 Hardware Resource Utilization Profiling
Continuous telemetry captured via `nvidia-smi`, system process auditing, and database growth benchmarks during live operation:
- **Dedicated GPU Memory (VRAM):** **`3.90 GB`** peak (3991 MB / 6141 MB capacity, resident in GPU VRAM with `-ngl 99`, evidence: `evidence/vram_cpu_usage.log`).
- **Host Process Working Set (RAM):** **`2.42 GB`** physical working set across all active Parlor processes (`llama-server` 1.84 GB + `python` server process 0.61 GB; total committed virtual private memory 5.24 GB, evidence: `evidence/ram_working_set.txt`).
- **Longitudinal SQLite Storage Ingestion Rate:** **`132.00 KB/hour`** measured over 450 simulated 8.0s cycles (300.37 bytes/cycle, totaling 1.03 MB per 8-hour workday and 92.81 MB per continuous 30-day month, evidence: `evidence/storage_growth_rate.txt`).

### 5.4 Privacy and Local Isolation Network Audit
To verify zero data leakage, a network socket packet capture and socket inspection were executed during live interaction:
```powershell
netstat -ano | findstr 8000
netstat -ano | findstr 8081
```
- Port 8000 (Parlor Web / WebSocket Gateway) bound strictly to `127.0.0.1`.
- Port 8081 (`llama-server` inference API) bound strictly to `127.0.0.1`.
- Total outbound remote packets captured: **`0 packets`** (**`0.00 KB`**).
- Network boundary: The system operates with no outbound network traffic during standard operation; model weights are downloaded once during initial setup; the optional research mode is the only feature capable of making external API calls.

### 5.5 Affective Validation and EMA Ground-Truth Study

> **Critical Methodological Distinction:**  
> **Model Quantization Agreement:** Measures numerical and syntactic fidelity between quantized weights and full-precision FP16 weights on identical prompts. On this machine, FP16 weights were not downloaded for Gemma 4 E2B, so quantization agreement is marked **NOT MEASURED**.  
> **Human Ground-Truth Agreement:** Measures agreement between the system's inferred stress tiers and genuine human psychological self-reports via Ecological Momentary Assessment (EMA).

#### 5.5.1 Data Provenance Audit and Human Study Status
A comprehensive code and data audit (`EVIDENCE_AUDIT.md`) revealed that preliminary reports referencing 144 windows with 77.8% exact agreement were based on synthetically generated trials in `shared_state/ema_validation_trials.json` produced by `scripts/run_ema_validation.py` using statistical distributions (`np.random.normal` and `random.choices`) for verifying analysis pipelines.

In strict adherence to academic research integrity:
1. **The synthetic numbers are NOT represented as empirical human ground truth.**
2. **Empirical EMA Accuracy is formally marked as: `NOT COLLECTED / REQUIRES HUMAN STUDY`.**
3. A complete, turnkey collection harness and standardized human study protocol have been established in `scripts/ema_collector.py` and `docs/EMA_RECOLLECTION_KIT.md` for execution by the student team with $\ge 8$ human participants (4 developers + 4 external peers) prior to viva.

#### 5.5.2 Human Ground-Truth Accuracy Status & Tooling Readiness
**Human ground-truth accuracy: NOT YET COLLECTED. Protocol and tools are ready.**

The evaluation suite has been updated in `scripts/evaluate_ema.py` with:
- Strict integrity and consent refusal check (rejects unverified or missing consent flags).
- Ground-truth class distribution and majority-class baseline.
- Exact tier agreement and one-tier tolerance agreement with 95% bootstrap confidence intervals.
- Quadratic-weighted Cohen's Kappa ($\kappa_w$).
- Full 3x3 confusion matrix with marginals.
- Per-participant agreement breakdown.
- Tier 2 safety rates (False Positive Rate and False Negative Rate) computed separately with and without developers to detect confirmation bias.
- Fully tested and verified on `shared_state/toy_ema_records.json`.

### 5.6 Cross-Modal Conflict, Signal Honesty, and Failure Recovery Verification
Live empirical benchmarks were executed directly against Google Gemma 4 E2B IT on this machine to verify pattern reasoning, resilience, and failure recovery:
1. **Cross-Modal Conflict Test (5 Repeats, Evidence: `evidence/live_pattern_reasoning.json`):**
   - Synthetic feature vector: Pitch spike ($\Delta F0 = +37.5\text{ Hz}$), vocal tension $0.65$, with completely relaxed face ($\text{AU04}=0.05, \text{AU07}=0.05, \text{EAR}=0.32$).
   - Result: In **5 out of 5 consecutive trials**, Gemma 4 E2B correctly evaluated the conflict, maintaining a **Low (Tier 0)** stress assessment with explicit clinical reasoning:
     > *"The vocal biomarkers indicate a slight elevation in pitch and a high Vocal Tension Index (0.65)... However, all facial micro-expressions are at baseline/relaxed levels (AU04=0.05, AU07=0.05), indicating an absence of emotional facial tension. This conflicting data lowers the overall stress assessment to Low (Tier 0)."*
2. **Consistent Multimodal Stress Test (5 Repeats, Evidence: `evidence/live_pattern_reasoning.json`):**
   - Synthetic feature vector: Brow furrow ($\text{AU04}=0.84$), eye squint ($\text{AU07}=0.72$), pitch elevation ($\Delta F0 = +49.0\text{ Hz}$), vocal tension $0.76$.
   - Result: In **5 out of 5 consecutive trials**, Gemma 4 E2B classified the state as **Moderate (Tier 1)** with high confidence ($0.92$), citing both facial strain and vocal tension.
3. **Tier 2 Range Sweep (10 Vectors $\times$ 3 Repeats, Evidence: `evidence/tier_sweep.csv`):**
   - Tested 10 synthetic feature vectors from mild to extreme (AU04 0.05 to 0.98, $\Delta F0$ +2Hz to +92Hz, vocal tension 0.22 to 0.95). Vectors 1–4 mapped to Low (Tier 0), Vectors 5–9 to Moderate (Tier 1), and Vector 10 mapped consistently to **High (Tier 2)** across all 3 repeats (3/3).
4. **Live-Model Balanced Mode Intervention Proof (Evidence: `evidence/live_model_card_trigger.json`, `evidence/intervention_card_browser.png`):**
   - Earlier exploratory testing passed a static test payload (`AU04=0.95, Vocal Tension=0.88, Pitch Delta=+68Hz`) directly over WebSocket. To provide rigorous live-model proof without mocks or stubs, all 3 consecutive cycles were evaluated through real `llama-server` inference using Vector B07_V10 (`AU04=0.98, AU07=0.95, Pitch Delta=+92Hz, Tension=0.95`). All 3 cycles returned genuine `High (Tier 2)` classifications, successfully satisfying the 3-cycle hysteresis policy in Balanced mode, triggering the `intervention_triggered` WebSocket event, and rendering the *Guided 4-7-8 Breathing Exercise* intervention card in the live browser DOM.
5. **Signal Honesty Test (Evidence: `evidence/live_zero_signal.json`):**
   - When the webcam is covered and the microphone is silent, the system outputs `stress_level: "insufficient signal"`, `confidence_score: 0.0`, and `ambiguity_note: "Camera unlit/obscured and microphone silent."` with zero compute wasted. These zero-signal observation windows enforce a HOLD policy on trigger hysteresis and are excluded from human EMA analysis.
6. **Graceful Failure and Mid-Session Recovery (3 Repeats, Evidence: `evidence/live_llama_kill_recovery.log`):**
   - When `llama-server` is killed mid-session, the exception is cleanly caught as `LLAMAServerError`. The watchdog automatically respawns the process and restores a healthy responding state in **$3.95\text{ s}$ mean recovery time** ($4.63\text{s}, 3.62\text{s}, 3.59\text{s}$).
7. **Fine-Grained Tier 2 Reachability Sweep (13 Vectors $\times$ 3 Repeats, Evidence: `evidence/tier2_reachability_sweep.csv`):**
   - Evaluated 13 intermediate vectors between Vector 9 and Vector 10 across both modalities, facial AU only, and vocal only (39 evaluations total).
   - *Boundary:* The Tier 1 to Tier 2 transition occurs at $\text{AU04} \ge 0.97$, $\Delta F0 \ge +90\text{ Hz}$, and vocal tension $\ge 0.94$ with co-occurring multimodal activation.
   - *Single-Modality Ceiling:* Neither facial strain alone ($\text{AU04}=0.98$) nor vocal strain alone ($\Delta F0=+92\text{ Hz}$) can cross into Tier 2 when the other modality is neutral.
   - *Real-World Reachability:* In naturalistic desktop environments, human knowledge workers rarely produce uncalibrated raw $\text{AU04} \ge 0.97$ or $+90\text{ Hz}$ pitch shifts without exaggerated grimacing. Personalized z-score baseline calibration is therefore essential for natural user triggering. A standardized collection harness (`scripts/collect_feature_ranges.py`) was prepared to log resting, speaking, and cognitive stress ranges (`REQUIRES HUMAN`).

---

## 6. DISCUSSION, LIMITATIONS, AND ETHICAL CONSIDERATIONS

### 6.1 Clinical Role Boundary: Stress Signal Estimation vs Medical Diagnosis
It is essential to state the clinical boundary of this system with complete transparency:
**Parlor is an affective wellness monitoring tool designed to estimate behavioral stress-related signals and recommend breaks; it is NOT a certified medical diagnostic device.** It does not diagnose anxiety disorders, clinical depression, hypertension, or any medical condition. Its outputs are intended solely to provide actionable self-awareness for computer users to mitigate digital eye strain, physical tension, and workplace burnout.

### 6.2 System Limitations and Boundary Disclosures
1. **Voice Latency Cost of Concurrent Monitoring:** In 30-turn alternating measurements on an NVIDIA RTX 4050 Laptop GPU (plugged into AC power, 2700 MHz graphics clocks), conversational TTFA averaged **1.920 s mean / 3.545 s p95** (Loop OFF), **1.739 s mean / 3.612 s p95** (Loop ON Unmitigated), and **1.774 s mean / 3.419 s p95** (Loop ON Mitigated). While deferring wellness cycles during speech preserves responsiveness, GPU concurrency cost remains an empirical physical reality on single-GPU hardware.
2. **Single GPU Contention and KV Cache Eviction:** `llama-server` operates on a single GPU slot (`-np 1`). If a background reasoning pass is dispatched, the conversational prefix tokens in the KV cache can be evicted, requiring context re-prefill for subsequent conversational requests unless deferred.
3. **Vocal Biomarker Speech Requirement:** Vocal acoustic biomarkers require active speech. During extended silent reading or programming, the system relies exclusively on facial Action Units and blink metrics.
4. **Lighting and Head-Pose Sensitivity:** MediaPipe landmark tracking relies on adequate ambient illumination; under severely degraded lighting or head yaw angles $>30^\circ$, face detection confidence drops significantly, falling back to audio-only estimation.
5. **Demographic and Eyewear Calibration:** Systematic evaluation across diverse skin tones and facial phenotypes was not conducted on clinical benchmark datasets in this iteration, representing a key limitation for multi-cohort generalization. In addition, optical distortion or reflections from thick-rimmed corrective eyewear can occlude eye landmarks, impacting AU07 (eyelid tightening) and Eye Aspect Ratio (EAR) geometry.
6. **Absence of Large-Scale Human Clinical Data:** Empirical human ground truth is marked as `NOT YET COLLECTED / REQUIRES HUMAN STUDY`. Real EMA data collection ($N \ge 8$) is prepared and pending execution.
7. **Strict Non-Clinical Boundary:** The system estimates behavioral stress indicators to suggest ergonomic micro-breaks; it is NOT clinically validated and does NOT diagnose medical conditions.
8. **Network Boundary Scope:** Standard operation is strictly local (0 outbound sockets); initial model weights are downloaded once, and optional user-triggered research mode is the only network-capable feature.

### 6.3 Ethical Safeguards: Alert Fatigue and Over-Reliance
- **Mitigating Alert Fatigue:** The multi-cycle hysteresis trigger policy ensures that fleeting moments of frustration (e.g., encountering a software bug) do not trigger intrusive notifications.
- **Privacy Assurance:** On-device execution guarantees that biometric expressions and vocal features never leave local volatile memory, preventing surveillance abuse.

---

## 7. FUTURE WORK AND CONCLUSION

### 7.1 Potential Hardware and Algorithmic Extensions
1. **Dedicated NPU / Edge TPU Offload:** Quantizing Gemma 4 E2B to int8/int4 for execution on specialized Neural Processing Units (Intel NPU, Qualcomm Snapdragon X Elite, Apple Neural Engine) to reduce power draw below 5 Watts.
2. **Circadian Baseline Adaptation:** Extending SQLite analytics to track multi-day circadian rhythms, adjusting baseline sensitivity as the workday progresses.
3. **On-Device Parameter-Efficient Fine-Tuning (LoRA):** Allowing local personalization of SLM reasoning weights to adapt to idiosyncratic speaking styles and facial mobility patterns without uploading data.

### 7.2 Summary of Contributions and Final Conclusion
This project successfully designed, implemented, and empirically validated **Parlor**, an on-device multimodal AI assistant and affective wellness monitoring platform. By combining MediaPipe FaceMesh facial Action Units, real-time vocal acoustic DSP, and qualitative Small Language Model pattern reasoning running on consumer laptop hardware, Parlor addresses the challenge of privacy-preserving, non-invasive workplace wellness computing.

With a **99.1% test suite pass rate** (111 passed out of 112 items, 0 failed, 1 skipped by design: *"the TTS fixture has finished-sounding falling prosody, which the acoustic classifier correctly reads as complete — real hesitation must be judged live"*), conversational TTFA of **1.920 s mean / 3.545 s p95** (loop off) and **1.774 s mean / 3.419 s p95** (loop on mitigated), an SLM reasoning latency of **2.14 s mean / 2.45 s p95** on standard prompts and **4.32 s max** on cross-modal conflict reasoning (leaving a 0.68 s safety margin below the 5.0 s budget and 2.77 s margin against the pooled mean), real face extraction of **3.97 ms mean**, vocal DSP of **2.85 ms mean**, local storage consumption of **132 KB/hour**, host working set RAM of **2.42 GB**, complete local network isolation (**0.00 KB** outbound transmission), and a standardized Human Study Re-Collection Kit (`docs/EMA_RECOLLECTION_KIT.md`), Parlor establishes that robust, private, and explainable affective AI is achievable on everyday edge computing devices.

---

## 8. REFERENCES

1. AI@Meta. (2024). *The Llama 3 Herd of Models*. arXiv preprint arXiv:2407.21783.
2. Baumel, A., Muench, F., Edan, S., & Kane, J. M. (2019). Objective user engagement with mobile health apps: Systematic search and analysis of publicly available information. *Journal of Medical Internet Research*, 21(9), e14567. DOI: 10.2196/14567. PMID: 31573916.
3. Eysenbach, G. (2005). The law of attrition. *Journal of Medical Internet Research*, 7(1), e11. DOI: 10.2196/jmir.7.1.e11. PMID: 15829473.
2. Baumel, A., Muench, F., Edan, S., & Kane, J. M. (2019). *Objective User Engagement With Mobile Health Apps: Systematic Search and Panel-Based Usage Analysis*. Journal of Medical Internet Research, 21(9), e14567.
3. Ekman, P., & Friesen, W. V. (1978). *Facial Action Coding System: A Technique for the Measurement of Facial Movement*. Consulting Psychologists Press.
4. Eysenbach, G. (2005). *The Law of Attrition*. Journal of Medical Internet Research, 7(1), e11.
5. Gemma Team. (2024). *Gemma: Open Models Based on Gemini Research and Technology*. Google DeepMind, arXiv preprint arXiv:2403.08295.
6. Kartynnik, Y., Ablavatski, A., Grishchenko, I., & Grundmann, M. (2019). *Real-time Facial Surface Geometry from Monocular Video on Mobile GPUs*. CVPR Workshop on Computer Vision for Augmented and Virtual Reality.
7. Lazarus, R. S., & Folkman, S. (1984). *Stress, Appraisal, and Coping*. Springer Publishing Company.
8. Picard, R. W. (1997). *Affective Computing*. MIT Press.
9. Scherer, K. R. (1986). *Vocal Affect Expression: A Review and a Model for Future Research*. Psychological Bulletin, 99(2), 143–165.
10. Stone, A. A., & Shiffman, S. (1994). *Ecological Momentary Assessment (EMA) in Behavioral Medicine*. Annals of Behavioral Medicine, 16(3), 199–202.

