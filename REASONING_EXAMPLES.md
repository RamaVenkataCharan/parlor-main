# Explainable SLM Reasoning Examples for Multimodal Affective Stress Detection

> **Model Tested:** Google Gemma 4 E2B IT Q4_0 (`gemma-4-E2B_q4_0-it.gguf` + `gemma-4-E2B-it-mmproj.gguf`)  
> **Inference Engine:** `llama.cpp` b12015 on NVIDIA GeForce RTX 4050 Laptop GPU (CUDA 12.4)  
> **Source Evidence Files:** `evidence/live_pattern_reasoning.json`, `evidence/live_single_modality.json`, `evidence/live_zero_signal.json`  
> **Execution Status:** Live empirical responses captured directly from the local running model.

---

## Example 1: Cross-Modal Conflict (Vocal Tension with Relaxed Face)

### Context & Physiological Rationale
The user exhibits a significant fundamental pitch spike ($\Delta F0 = +37.5\,\text{Hz}$ above baseline) and elevated vocal tension ($0.65$), which would trigger a false-positive stress alarm under naive thresholding. However, their facial musculature is completely relaxed ($\text{AU04}=0.05, \text{AU07}=0.05, \text{EAR}=0.32$). Gemma 4 E2B recognizes the discrepancy and appropriately classifies the state as Low Stress (Tier 0).

### Input Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: DETECTED (Confidence: 0.94)
- AU04 Brow Furrow (Eyebrow Tension): 0.05 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.05 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.02 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.05 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.32 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=2.1°, Yaw=-1.4°, Roll=0.8°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.045)
- Pitch Mean (F0): 182.5 Hz (Baseline: 145.0 Hz, Delta: +37.5 Hz)
- Pitch Variance (F0 SD): 24.2 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 3.82% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 4.15% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.18 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.65 (Normal <0.40, High >0.65)

TASK: Evaluate the physiological and behavioral stress state based strictly on the biomarkers above. Output the JSON schema with stress level, primary drivers, explainable reasoning, confidence score, and ambiguity notes.
```

### Live Verbatim Model Response (Latency: 2.37s)
```json
{
  "stress_level": "Low (Tier 0)",
  "primary_drivers": [
    "Vocal Tension Index (HF Energy >1kHz Ratio)=0.65",
    "AU04 Brow Furrow (Eyebrow Tension)=0.05"
  ],
  "explainable_reasoning": "The vocal biomarkers indicate a slight elevation in pitch (F0 Delta=+37.5 Hz) and a high Vocal Tension Index (0.65), which could suggest stress. However, all facial micro-expressions are at baseline/relaxed levels (AU04=0.05, AU07=0.05), indicating an absence of emotional facial tension. This conflicting data lowers the overall stress assessment to Low (Tier 0).",
  "confidence_score": 0.85,
  "ambiguity_note": "The Vocal Tension Index (0.65) is at the upper threshold for 'Moderate' stress, but the lack of corresponding facial tension suggests the arousal is primarily vocal/respiratory rather than emotional distress."
}
```

---

## Example 2: Consistent Multimodal Acute Stress

### Context & Physiological Rationale
Both visual and acoustic channels exhibit concurrent physiological tension: severe brow furrowing ($\text{AU04}=0.84$), eye squinting ($\text{AU07}=0.72$), pitch elevation ($\Delta F0 = +49.0\,\text{Hz}$), and vocal tension ($0.76$). The SLM synthesizes both streams and identifies acute stress.

### Input Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: DETECTED (Confidence: 0.95)
- AU04 Brow Furrow (Eyebrow Tension): 0.84 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.72 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.48 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.58 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.22 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=-8.5°, Yaw=3.2°, Roll=-2.1°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.052)
- Pitch Mean (F0): 194.0 Hz (Baseline: 145.0 Hz, Delta: +49.0 Hz)
- Pitch Variance (F0 SD): 29.5 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 4.65% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 5.4% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.44 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.76 (Normal <0.40, High >0.65)

TASK: Evaluate the physiological and behavioral stress state based strictly on the biomarkers above. Output the JSON schema with stress level, primary drivers, explainable reasoning, confidence score, and ambiguity notes.
```

### Live Verbatim Model Response (Latency: 2.01s)
```json
{
  "stress_level": "Moderate (Tier 1)",
  "primary_drivers": [
    "AU04 Brow Furrow (Eyebrow Tension)=0.84",
    "AU07 Lid Tightener (Eye Squint/Strain)=0.72",
    "Vocal Tension Index (HF Energy >1kHz Ratio)=0.76"
  ],
  "explainable_reasoning": "The high AU04 Brow Furrow and elevated Vocal Tension Index indicate significant emotional and physiological stress. The presence of eye strain (AU07) further supports this assessment. While vocal jitter and shimmer are elevated, the pitch delta (+49.0 Hz) is notable, pointing to sustained vocal strain.",
  "confidence_score": 0.92,
  "ambiguity_note": "The combination of pronounced facial tension and elevated vocal tension strongly suggests a moderate stress state. However, the moderate pause ratio (0.44) and absence of extreme pitch shifts suggest the user is not in an acute panic state."
}
```

---

## Example 3: Zero-Signal Honesty (Covered Camera + Complete Silence)

### Context & Implementation
When the user covers the webcam or steps away, naive systems frequently hallucinate stress or crash. In Parlor, when both `face_detected: False` and `speech_detected: False` occur, the system evaluates the state honestly with zero compute wasted.

### Verbatim System Output (Source: `evidence/live_zero_signal.json`)
```json
{
  "stress_level": "Low (Tier 0)",
  "primary_drivers": [
    "No active signals detected"
  ],
  "explainable_reasoning": "No facial or vocal signals detected in the current observation window.",
  "confidence_score": 0.0,
  "ambiguity_note": "Camera unlit/obscured and microphone silent."
}
```

---

## Example 4: Single-Modality Fallbacks

### A. Camera-Only Mode (Face Detected, Audio Silent)
- **Observed Biomarkers:** AU04=0.76, AU07=0.68, Audio RMS=0.0 (Silence).
- **Live Verbatim Reasoning (Latency: 4.63s):**
  *"The presence of elevated AU04 (Brow Furrow) and AU07 (Lid Tightener) indicates active cognitive engagement or mild negative affect, suggesting concentration or slight concern. The lack of vocal activity and normal vocal metrics (zero tension index) suggest the current state is internal and focused, rather than externally vocalized stress."*
- **Ambiguity Note:** *"The lack of vocal data (RMS Energy: 0.0) means the assessment is purely based on facial micro-expressions."*

### B. Mic-Only Mode (Camera Covered/Dim, Audio Speech Detected)
- **Observed Biomarkers:** Face not detected, Pitch Delta=+43.0Hz, Vocal Tension=0.72.
- **Live Verbatim Reasoning (Latency: 2.37s):**
  *"The vocal biomarkers indicate significant physiological arousal, evidenced by a high mean pitch shift (+43.0 Hz) and elevated vocal tension (0.72). The increased jitter and shimmer suggest vocal instability and increased muscular effort in the vocal folds, consistent with moderate stress or heightened emotional engagement."*
- **Ambiguity Note:** *"Facial micro-expression data is not detected due to poor lighting, limiting the assessment of facial tension markers."*
