# Dataset & Ground-Truth Strategy for Multimodal Stress Detection
## Phase 1 Deliverable: Protocol Design & Validation Framework

> **DOCUMENT STATUS:** Standardized Evaluation Protocol & Ground-Truth Methodology  
> **DISCLOSURE OF EXTERNAL DATASETS:** The external datasets (DAIC-WOZ, WESAD, RECOLA, RAVDESS) listed in Section 1 represent a comprehensive **literature review and planned validation protocols**. They were not downloaded or evaluated on this machine due to sensor domain shift (e.g. chest ECG sensors vs webcams) and data privacy licensing constraints. Ground-truth evaluation in Parlor is designed around an on-device **Ecological Momentary Assessment (EMA)** protocol.

---

## 1. Candidate Dataset Evaluation Matrix (Literature Review)

| Dataset | Modalities Included | Label Type & Range | Size / Duration | License & Access Terms | Status in Project |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DAIC-WOZ** *(Distress Analysis Interview Corpus)* | Audio (WAV 16kHz), Video (OpenFace AU features), Transcripts | Clinical PHQ-8 score (0–24) & Binary Distress | 189 sessions (~50 hours) | Restricted Academic DUA (USC ICT License Agreement) | Planned Future Protocol |
| **WESAD** *(Wearable Stress & Affect Detection)* | Physiological (ECG, EDA, EMG, Temp, ACC) + Self-report | Binary (Stress vs Non-stress) & Ordinal PANAS / STAI-6 | 15 subjects (36 hours) | Open Academic (PhysioNet / TU Darmstadt) | Literature Baseline |
| **RECOLA** *(Remote Collaborative Interactions)* | Audio, Video, ECG, EDA | Continuous per-frame Arousal (-1..+1) & Valence (-1..+1) | 46 participants (9.5 hours) | Restricted Academic DUA (AVEC Challenge) | Literature Baseline |
| **RAVDESS / CREMA-D** *(Emotional Speech & Video)* | Audio (WAV 48kHz), HD Video (MP4) | Categorical Affect (Neutral, Calm, Fear, Anger, Sadness, Disgust) | 7,356 clips (24.5 hours) | Open CC-BY 4.0 | Literature Acoustic Baseline |

---

## 2. On-Device Ground-Truth Strategy: Ecological Momentary Assessment (EMA)

Because laboratory datasets utilize studio microphones, chest straps, and scripted emotional portrayals, they suffer from substantial domain shift when applied to everyday desktop computer work. Parlor implements a **standardized, on-device EMA protocol** administered directly through the assistant:

- **Sensor Matching:** Evaluated directly with the user's laptop webcam and microphone.
- **Ecological Validity:** Captures real cognitive strain during natural computer tasks (coding, reading, timed arithmetic) rather than artificial lab stressors.
- **Privacy Preservation:** All ratings and paired assessments are stored locally in SQLite (`shared_state/wellness_history.db`) and JSON (`shared_state/ema_records.json`). No media or ratings leave the machine.

---

## 3. Standardized 3-Item EMA Survey Instrument

Administered immediately following a 5-minute capture window:

```text
Item 1: Emotional Tension
"How tense, anxious, or stressed did you feel during the last capture window?"
[1] Completely Calm / Relaxed
[2] Mildly Aware / At Ease
[3] Moderately Tense
[4] Noticeably Stressed
[5] Extremely Tense / Agitated

Item 2: Perceived Demand
"How overwhelmed did you feel by your current activity?"
[1] Fully in Control
[2] Manageable
[3] Slightly Strained
[4] Struggling to Keep Pace
[5] Overwhelmed / Frustrated

Item 3: Somatic Physical Tension
"Did you notice physical tension (brow furrowing, jaw clenching, rapid breathing)?"
[1] None
[2] Slight / Fleeting
[3] Mild Physical Tension
[4] Distinct Muscle Tightness
[5] Severe / Persistent Strain
```

### Composite EMA Score Mapping (Range: 3 to 15)
$$\text{Composite EMA Score} = Q_1 + Q_2 + Q_3$$

- **Score 3 – 5:** $\rightarrow$ **Tier 0: Low Stress / Baseline** (No intervention required)
- **Score 6 – 10:** $\rightarrow$ **Tier 1: Moderate Stress / Elevated Tension** (Soft subtle breathing micro-break)
- **Score 11 – 15:** $\rightarrow$ **Tier 2: High Stress / Burnout Risk** (Active spoken wellness intervention)

---

## 4. Current Status of Human Empirical Accuracy

> [!IMPORTANT]
> **Human Ground-Truth Accuracy Status:** **`NOT YET COLLECTED — REQUIRES HUMAN STUDY`**  
> Earlier reported agreement rates (77.8% exact / 100% one-tier) were produced by a synthetic simulation test harness (`scripts/run_ema_validation.py`) and have been expunged. The real data collection protocol and automated evaluation script are complete (`scripts/ema_collector.py`, `scripts/evaluate_ema.py`, `docs/EMA_RECOLLECTION_KIT.md`) and ready for student data collection prior to viva.
