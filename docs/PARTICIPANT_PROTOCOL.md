# Ground-Truth EMA Validation Protocol

**Protocol Status:** `REQUIRES HUMAN — PROTOCOL AND COLLECTION HARNESS READY`  
**Ethics & Consent:** Voluntary peer evaluation protocol for on-device real-time multimodal stress detection.  
**Survey Standard:** Ecological Momentary Assessment (EMA) 3-item composite (PSS-10 / WESAD aligned).

---

## 1. Participant Participant Consent & Instructions

> **Participant Consent Line:**  
> *"I understand that audio and facial landmarks are extracted locally in real-time on this device with zero external transmission, and that raw video/audio is immediately discarded. I agree to complete 3-item self-report ratings following observation windows."*

### Hardware & Environment Setup
- **Workstation:** Local PC running `parlor` (`python -m parlor.server` on port 8000).
- **Sensors:** Standard USB/built-in webcam (720p or 1080p) positioned at eye level; built-in or headset microphone.
- **Lighting:** Standard indoor office lighting (~300–500 lux).

---

## 2. Experimental Conditions (Protocol Workflow)

Each participant completes 4 distinct activity windows (5 to 10 minutes each):

| Condition ID | Description | Primary Modalities Active | Expected Target Tier |
|:---|:---|:---|:---|
| **C1: Quiet Focused Work** | Participant reads academic papers or documents quietly without speaking. Camera tracks baseline brow relaxation and blink rate. | Video (Facial AUs) | Tier 0 (Baseline) |
| **C2: Active Conversation** | Participant engages in conversational interaction or describes a topic aloud. Tests vocal prosody and articulation without stress. | Video + Audio | Tier 0 or Tier 1 |
| **C3: Acute Timed Stressor** | Participant performs a high-speed mental arithmetic test or Stroop color-word interference task under a strict 60-second timer. | Video + Audio | Tier 2 (High Tension) |
| **C4: Occluded / Low-Light Fallback** | Camera is intentionally occluded or lighting is dimmed (<50 lux). Tests graceful fallback to acoustic-only confidence estimation. | Audio-only | Tier 1 or Tier 2 |

---

## 3. EMA 3-Item Survey Instrument

Administered immediately following each capture window via `python scripts/ema_collector.py`:

1. **Emotional Tension:**  
   *"How tense, anxious, or stressed did you feel during the last capture window?"*  
   - `[1]` Calm / Relaxed  
   - `[2]` Mildly Aware  
   - `[3]` Moderately Tense  
   - `[4]` Noticeably Stressed  
   - `[5]` Extremely Tense  

2. **Perceived Demand:**  
   *"How overwhelmed did you feel by your current activity?"*  
   - `[1]` Fully in Control  
   - `[2]` Manageable  
   - `[3]` Slightly Strained  
   - `[4]` Struggling to Keep Pace  
   - `[5]` Overwhelmed  

3. **Somatic Symptoms:**  
   *"Did you notice any physical tension (brow furrowing, jaw clenching, rapid breathing)?"*  
   - `[1]` None  
   - `[2]` Slight / Fleeting  
   - `[3]` Mild  
   - `[4]` Distinct Physical Tightness  
   - `[5]` Severe / Persistent  

### Score to Ground-Truth Tier Mapping
$$\text{Composite Score} = Q_1 + Q_2 + Q_3 \quad (\text{Range: } 3 \text{ to } 15)$$

- **Composite 3 – 5:** $\rightarrow$ **Tier 0** (Low Stress / Baseline)
- **Composite 6 – 10:** $\rightarrow$ **Tier 1** (Moderate Stress / Elevated Tension)
- **Composite 11 – 15:** $\rightarrow$ **Tier 2** (High Stress / Burnout Risk)

---

## 4. Execution Commands for Evaluation

To run data collection with human participants:
```powershell
python scripts/ema_collector.py
```

To evaluate the collected results:
```powershell
python scripts/evaluate_ema.py
```

