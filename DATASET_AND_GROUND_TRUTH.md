# Dataset & Ground-Truth Strategy for Multimodal Stress Detection

> **Phase 1 Deliverable:** Dataset evaluation, ground-truth labeling protocol, survey instrument specification, and mapping schema for SLM reasoning.

---

## 1. Candidate Dataset Evaluation Matrix

| Dataset | Modalities Included | Label Type & Range | Size / Duration | License & Access Terms | Immediate Availability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DAIC-WOZ** *(Distress Analysis Interview Corpus)* | Audio (WAV 16kHz), Video (OpenFace AU features + MP4), Transcripts | Clinical PHQ-8 score (0–24) & Binary Distress (PHQ-8 >= 10) | 189 sessions (~50 hours) | Restricted Academic DUA (USC ICT License Agreement) | **Requires DUA Application** (1–2 weeks) |
| **WESAD** *(Wearable Stress & Affect Detection)* | Physiological (ECG, EDA, EMG, Temp, ACC) + Self-report | Binary (Stress vs Non-stress) & Ordinal PANAS / STAI-6 | 15 subjects (36 hours) | Open Academic (PhysioNet / TU Darmstadt) | **Immediate Download** |
| **RECOLA** *(Remote Collaborative Interactions)* | Audio, Video, ECG, EDA | Continuous per-frame Arousal (-1..+1) & Valence (-1..+1) | 46 participants (9.5 hours) | Restricted Academic DUA (AVEC Challenge) | **Requires DUA Application** |
| **RAVDESS / CREMA-D** *(Emotional Speech & Video)* | Audio (WAV 48kHz), HD Video (MP4) | Categorical Affect (Neutral, CalmL, Fear, Anger, Sadness, Disgust) + Intensity (Normal/Strong) | 7,356 clips (24.5 hours) | Open CC-BY 4.0 / Open Access | **Immediate Download** |

---

## 2. Dataset Recommendation & Hybrid Strategy

### Primary Benchmark Datasets:
1. **Immediate Open Validation Set:** **RAVDESS / CREMA-D** + **WESAD** (Acoustic & Facial Affect Baselines).
2. **Clinical Validation Set:** **DAIC-WOZ** (Utilized once DUA approval is granted for clinical PHQ-8 grounding).

### Self-Collected Validation & Calibration Protocol:
Because public datasets use external laboratory sensor configurations (e.g. clinical interviews or chest ECG monitors), we supplement the public datasets with a **project-specific self-collected validation set** captured directly through the Parlor web application:
* **Tradeoff Analysis:** Public datasets provide immediate scale but suffer from domain shift (studio microphones, fixed lighting). Self-collected data provides exact sensor matching (webcam + USB mic), calibrating the pipeline against real laptop/webcam artifacts.

---

## 3. Ground-Truth Labeling & Survey Protocol

### Survey Instrument:
We adopt a hybrid of the **PSS-10 (Perceived Stress Scale)** for baseline trait evaluation and a 3-item **Ecological Momentary Assessment (EMA)** for real-time window labeling.

#### Ecological Momentary Assessment (EMA) 3-Item Instrument (Administered Post-Capture Window):
Each item is scored on a **1 to 5 Likert scale**:
1. *"How tense, anxious, or stressed did you feel during the last capture window?"* (1: Calm → 5: Extremely Tense)
2. *"How overwhelmed did you feel by your current activity?"* (1: In Control → 5: Overwhelmed)
3. *"Did you notice any physical tension (brow furrowing, jaw clenching, rapid breathing)?"* (1: None → 5: Severe)

**Composite EMA Score Range:** **3 to 15**

---

## 4. Ground-Truth Mapping to SLM Reasoning Tiers

The continuous Composite EMA Score is mapped directly into a 3-tier ordinal classification schema for SLM reasoning:

```
[EMA Composite Score: 3 - 15]
       │
       ├── Tier 0: Low Stress / Baseline (Score: 3 - 5)
       │     └─ Valence: [-0.20, +1.00] | Arousal: [0.00, +0.40]
       │     └─ Action: No intervention required. System remains silent.
       │
       ├── Tier 1: Moderate Stress / Elevated Tension (Score: 6 - 10)
       │     └─ Valence: [-0.50, -0.21] | Arousal: [+0.41, +0.70]
       │     └─ Action: Soft micro-intervention (Subtle UI pulse, soft breathing prompt).
       │
       └── Tier 2: High Stress / Burnout Risk (Score: 11 - 15)
             └─ Valence: [-1.00, -0.51] | Arousal: [+0.71, +1.00]
             └─ Action: Active wellness intervention (Empathic spoken advice, break recommendation).
```
