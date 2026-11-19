# Parlor Human Study Runbook & Operational Protocol
**Document Version:** 1.0.0 (Study Protocol & Tooling Freeze)  
**Study Harness:** `Parlor Study Mode (Guided Runner)`  
**Protocol Status:** `REQUIRES HUMAN — PROTOCOL AND COLLECTION HARNESS READY`  
**Ethics Mandate:** Zero raw media retention (frames, audio, landmark meshes); local-only processing.

---

## 1. Overview & Protocol Purpose

This runbook specifies the standard operating procedures (SOP) for running human calibration and Ecological Momentary Assessment (EMA) validation sessions with Parlor.

### Core Objectives
1. **Calibration Cohort ($N \ge 3$):** Capture baseline facial Action Unit (AU) and vocal prosody distributions across 4 conditions to establish individualized baseline thresholds and evaluate trigger rules.
2. **Validation Cohort ($N \ge 5$):** Capture paired observation windows and ground-truth 3-item EMA ratings under blinded conditions to compute Cohen's kappa ($\kappa_w$), majority baseline, and safety rates.

---

## 2. Workstation & Environmental Setup

### 2.1 Lighting & Illuminance
- **Target Lux:** 300 to 500 lux of diffused, indirect ambient lighting across the participant's face.
- **Orientation:** Light source positioned in front of or slightly above the participant (avoid backlighting from windows or harsh overhead shadows).
- **Camera Exposure:** Verify that the camera feed is not underexposed or blown out. Skin tones and facial contours should remain distinct without blooming.

### 2.2 Physical Positioning
- **Eye-Level Alignment:** The webcam must be mounted directly at eye level (tilt within $\pm 5^\circ$).
- **Distance:** Position the participant 50 to 70 cm (approximately arm's length) from the camera.
- **Head Centering:** Ensure the participant's head is horizontally and vertically centered in the camera viewport.

### 2.3 Audio & Acoustics
- **Acoustic Environment:** Enclosed quiet room with ambient sound level $< 45\text{ dBA}$ (no conversational background chatter, loud air conditioners, or computer fan whine).
- **Microphone Placement:** Position built-in laptop mic or external condenser microphone 30 to 45 cm from mouth, angled towards speech source. Avoid breathing directly into mic capsules.

---

## 3. Experimenter Script & Checklist

### 3.1 Welcoming the Participant
> *"Hello! Thank you for volunteering to participate in our evaluation session for Parlor, an on-device emotional wellness assistant. Today's session takes approximately 15 minutes. Before we start, I will explain what we record, how your privacy is protected, and review the consent agreement."*

### 3.2 Explaining Privacy & Data Handling
> *"Parlor operates entirely on this computer. All facial expressions and speech features are extracted in real time into numeric numbers—such as brow movement ratios and voice pitch variations. Raw video frames, camera snapshots, audio recordings, and 3D face mesh coordinates are immediately discarded and are NEVER stored to disk or transmitted across any network. You can inspect the data at any time or request immediate deletion."*

### 3.3 Confirming Voluntary Participation & Rights
> *"Your participation is entirely voluntary. You can take a break or stop at any time without needing to provide a reason. If you choose to withdraw, clicking 'Withdraw' permanently purges all your recorded numbers from the computer."*

---

## 4. Consent & Registration Procedure

1. **Launch Parlor:**
   ```powershell
   python -m parlor.server
   ```
   Open `http://localhost:8000` in Google Chrome or Microsoft Edge.
2. **Enable Study Mode in Settings:**
   - Click the gear/settings icon in the top header (`#diagBtn`).
   - In the **Study & Validation Protocol** section, toggle **Study Mode** to `ON`.
   - Verify the persistent header badge appears: `🧪 Study mode: recording numeric features locally`.
3. **Launch Study Runner:**
   - Click **Launch Study Runner** (`#btnLaunchStudy`).
4. **Step 1: Consent & Setup:**
   - Ask the participant to read the on-screen consent text from `docs/PARTICIPANT_PROTOCOL.md`.
   - **Adult Confirmation (18+):** Check the box `I confirm that I am 18 years of age or older`.
   - **Informed Consent Check:** Check the box `I understand that audio and facial landmarks are extracted locally in real-time...`.
   - **Participant Code:** Confirm or assign the auto-generated code (e.g. `P01`, `P02`).
   - **Participant Role:** Select `External Participant` (or `Team Member` for internal testing).
   - **Study Group:** Select `Calibration Cohort` or `Validation Cohort`.
     > [!IMPORTANT]
     > **Strict Group Separation:** A participant cannot belong to both groups. If a participant was previously assigned to `Calibration`, they cannot be enrolled in `Validation`. The system enforces this at the API level.
   - Click **Proceed to Sensor Quality Check** (`#btnProceedToQuality`).

---

## 5. Pre-Session Sensor Quality Check (~1 Minute)

Before starting the timed protocol, execute the 5-point sensor check:
1. **Camera Active & Visible:** Verify video stream preview is clear and centered.
2. **Face Detected $\ge 95\%$:** Check that `#qaCheckFace` shows green pass.
3. **Action Unit (AU) Movement:**
   - Prompt the participant to relax muscles: *Neutral face*.
   - Prompt: *Knit eyebrows together firmly* $\rightarrow$ observe `AU04 Brow` increase on meter.
   - Prompt: *Squint lower eyelids* $\rightarrow$ observe `AU07 Lid` increase on meter.
   - Prompt: *Smile and stretch lips horizontally* $\rightarrow$ observe `AU20 Lip Stretch` increase on meter.
4. **Lighting Check:** Verify `#qaCheckLight` shows pass (no extreme underexposure or contrast blowout).
5. **Acoustic & Speech Check:**
   - Prompt: *Say 'One, two, three, four' in your normal speaking voice.*
   - Observe `Mic Energy` and verify `#qaCheckSpeech` passes.
6. Once all checks pass, click **Start 12-Minute Guided Protocol** (`#btnStartProtocol`).

---

## 6. Step-by-Step 12-Minute Guided Protocol

During the entire protocol, **blinding is automatically active**: affective state pills, real-time stress classifications, trend graphs, and intervention recommendations are hidden from the participant to prevent confirmation bias.

### Step 1: Baseline Rest (3 Minutes)
- **Instructions to Participant:** *"Please sit quietly, breathe naturally, and look towards the screen. No speaking or active tasks are required during this period."*
- **System Activity:** Captures baseline unaroused facial relaxation and vocal silence.
- **Post-Step Survey:** When the countdown reaches `00:00`, the 3-item EMA survey pops up on screen:
  1. *Emotional tension* (1 = Not at all, 5 = Extremely)
  2. *Perceived demand* (1 = Not at all, 5 = Overwhelmed)
  3. *Physical tension* (1 = None, 5 = Severe)
  Participant selects ratings and clicks **Save Rating & Proceed**.

### Step 2: Neutral Conversational Speech (3 Minutes)
- **Instructions to Participant:** *"Please speak aloud at a normal conversational volume on any of the low-stress topics shown on screen:"*
  - Describe your daily routine from waking up to arriving at work/study.
  - Summarize the plot of a favorite book, movie, or documentary.
  - Explain the step-by-step recipe for preparing a meal you like.
- **System Activity:** Measures baseline conversational prosody, pitch variability ($\Delta F_0$), jitter, shimmer, and articulation rate.
- **Post-Step Survey:** Administer and submit the 3-item EMA survey.

### Step 3: Timed Mental Stressor Task (3 Minutes)
- **Instructions to Participant:** *"You will now solve speed mental arithmetic problems shown on screen. Type your answer into the box and press Enter or Submit as quickly and accurately as possible. The system tracks your score and flags errors."*
- **System Activity:** Introduces cognitive demand and time urgency. Captures corrugator activation (AU04 brow furrowing), eyelid narrowing (AU07), and head posture shifts.
- **Post-Step Survey:** Administer and submit the 3-item EMA survey.

### Step 4: Physiological Recovery (3 Minutes)
- **Instructions to Participant:** *"The test is complete. Please sit comfortably with eyes open, relax your shoulders, and allow your breathing and physiology to settle."*
- **System Activity:** Measures post-stressor physiological return-to-baseline latency.
- **Post-Step Survey:** Administer and submit the 4th and final 3-item EMA survey.

---

## 7. Session Completion, QA Summary & Data Operations

1. **Review Session QA Summary:**
   - Confirm Participant Code, Group, Role, and Total Duration (~12–15 min).
   - Verify that all 4 steps recorded $\ge 90\%$ face detection and valid vocal metrics.
   - Confirm Signal Quality reads `100% Valid (No Dropouts)`.
2. **Export Anonymized CSV:**
   - Click **Download Anonymized CSV** (`#btnSummaryExportCsv`).
   - Files are also stored locally in `study_data/observation_windows.jsonl` and `study_data/ema_responses.jsonl`.
3. **Participant Withdrawal (If Requested):**
   - If the participant requests withdrawal at any point, click **Withdraw Participant & Erase Data** (`#btnSummaryWithdraw`).
   - The system permanently deletes all windows, survey responses, and registry entries for that code, and outputs a confirmation toast.

---

## 8. Cohort Scheduling: Running 8 Sessions in a 3-Hour Window

To collect an 8-participant study cohort efficiently without experimenter or workstation fatigue:

| Time Slot | Session | Participant Code | Group Assignment | Notes |
|:---|:---:|:---:|:---:|:---|
| **09:00 – 09:20** | Session 1 | `P01` | Calibration | Initial setup check; verify lighting |
| **09:20 – 09:40** | Session 2 | `P02` | Calibration | Team / developer baseline |
| **09:40 – 10:00** | Session 3 | `P03` | Calibration | External participant baseline |
| **10:00 – 10:15** | *Break* | — | — | **15-Minute Environment Reset & Calibration Check** |
| **10:15 – 10:35** | Session 4 | `P04` | Validation | External participant validation |
| **10:35 – 10:55** | Session 5 | `P05` | Validation | External participant validation |
| **10:55 – 11:15** | Session 6 | `P06` | Validation | Team member validation |
| **11:15 – 11:25** | *Break* | — | — | **10-Minute Buffer** |
| **11:25 – 11:45** | Session 7 | `P07` | Validation | External participant validation |
| **11:45 – 12:05** | Session 8 | `P08` | Validation | External participant validation |

---

## 9. Handling Exceptions & Troubleshooting

- **Camera Disconnection or Stream Stalled:**
  - Instruct participant to pause. Click "Camera Off" then "Camera On" in the bottom control bar to reacquire the media stream.
  - If USB device resets, reload page (`Ctrl+R`); the registry keeps existing participants.
- **Participant Experiencing Acute Distress:**
  - If a participant shows genuine discomfort during the arithmetic stressor, stop the session immediately.
  - Offer water and a quiet break. Remind them their data can be erased with one click.
- **Low Face Detection Warning ($< 90\%$):**
  - Check distance (ensure 50–70 cm).
  - Check hair occluding eyes/brows or reflective glare on spectacles.
  - Increase ambient light lamp level.

---

## 10. Automated Analysis Execution

Once sessions are complete, run the automated analysis scripts:

### 10.1 Calibration Analysis
```powershell
python scripts/analyze_calibration.py
```
- Reads `study_data/observation_windows.jsonl` filtered to `group == 'calibration'`.
- Computes feature distributions per step (median, IQR, 5th, 95th percentiles).
- Computes Cohen's d effect sizes (Rest vs Stressor) with 95% bootstrap CIs.
- Simulates candidate trigger rules (Tier $\ge 1$ vs Tier 2, z-score thresholds).
- Outputs `docs/CALIBRATION_REPORT.md` and face-free scalar plots in `evidence/calibration_plots/`.

### 10.2 EMA Validation Accuracy Analysis
```powershell
python scripts/evaluate_ema.py
```
- Reads `study_data/ema_responses.jsonl` paired with `observation_windows.jsonl`.
- Strictly excludes calibration participants.
- Performs consent and ID integrity audit (refuses execution if unverified).
- Outputs:
  - Exact-tier agreement % with 95% bootstrap CI.
  - One-tier-tolerance agreement % with 95% bootstrap CI.
  - Quadratic-weighted Cohen's Kappa ($\kappa_w$).
  - Full $3 \times 3$ confusion matrix.
  - Per-participant agreement breakdown.
  - Safety rates (Tier 2 False Positive Rate and False Negative Rate) with and without developer participants.

---

## 11. Project Guide Ethics & Data Protection Statement

> **Note for Academic & Project Guides:**  
> Parlor implements an **On-Device Affective Computing Architecture** engineered to comply with strict research ethics guidelines (aligned with GDPR Art. 9 biometric data processing standards and IEEE P7000 ethics standards):
> 1. **Zero Media Storage Mandate:** No camera frames, video clips, microphone audio buffers, or 3D coordinate face meshes are EVER written to disk, cached, or transmitted externally.
> 2. **Ephemeral Feature Extraction:** Video frames and audio frames exist purely in volatile memory during feature extraction (~120 ms) and are immediately overwritten.
> 3. **Non-Diagnostic Framing:** Parlor labels all inferences as *observable behavioral cues* rather than medical, psychiatric, or definitive affective diagnoses.
> 4. **Consent-First Architecture:** Sessions cannot begin without explicit 18+ adult verification and informed consent checkboxes. Immediate participant withdrawal erases all numeric records instantly.

## 12. Academic References & Bibliography

1. **WESAD Multimodal Dataset:**  
   Schmidt, P., Reiss, A., Duerichen, R., Marberger, C., & Van Laerhoven, K. (2018). *Introducing WESAD, a Multimodal Dataset for Wearable Stress and Affect Detection*. Proceedings of the 20th ACM International Conference on Multimodal Interaction (ICMI '18), 400–408.
2. **Trier Social Stress Test (TSST):**  
   Kirschbaum, C., Pirke, K. M., & Hellhammer, D. H. (1993). *The 'Trier Social Stress Test' – A Tool for Investigating Psychobiological Stress Responses in a Laboratory Setting*. Neuropsychobiology, 28(1-2), 76–81.
3. **Facial Action Coding System (FACS):**  
   Ekman, P., & Friesen, W. V. (1978). *Facial Action Coding System: A Technique for the Measurement of Facial Movement*. Consulting Psychologists Press.
4. **Vocal Acoustic Perturbation (Jitter/Shimmer):**  
   Farrús, M., Codina, J., & Hernando, J. (2007). *Jitter and shimmer measurements for speaker recognition*. In INTERSPEECH (pp. 778-781).
