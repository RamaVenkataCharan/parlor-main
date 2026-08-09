# Explainable SLM Reasoning Examples for Multimodal Affective Stress Detection

> **Phase 2 Deliverable:** Documented input feature vectors and corresponding SLM reasoning outputs proving explainability, citation of grounding biomarkers, and handling of ambiguous signals.

---

## Example 1: Clear Low Stress / Baseline

### Input Feature Vector Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: DETECTED (Confidence: 0.96)
- AU04 Brow Furrow (Eyebrow Tension): 0.08 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.12 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.05 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.10 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.312 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=-1.2°, Yaw=+2.1°, Roll=+0.4°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.042)
- Pitch Mean (F0): 146.8 Hz (Baseline: 145.0 Hz, Delta: +1.8 Hz)
- Pitch Variance (F0 SD): 12.4 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 0.85% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 1.42% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.38 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.285 (Normal <0.40, High >0.65)
```

### SLM Explainable Output
```json
{
  "stress_level": "Low (Tier 0)",
  "primary_drivers": [
    "AU04 Brow Furrow=0.08 (Relaxed facial musculature)",
    "Pitch Delta=+1.8Hz (Baseline pitch stability)",
    "Local Jitter=0.85% & Shimmer=1.42% (Normal acoustic periodicity)",
    "Pause Ratio=0.38 (Natural speech phrasing)"
  ],
  "explainable_reasoning": "The user demonstrates baseline physiological and vocal stability. Facial Action Units indicate relaxed facial musculature with minimal eyebrow furrowing (AU04=0.08) and normal eye aspect ratio (EAR=0.312). Acoustic pitch remains within +1.8 Hz of baseline with normal jitter (0.85%) and shimmer (1.42%), showing no signs of vocal cord tension or stress.",
  "confidence_score": 0.98,
  "ambiguity_note": null
}
```

---

## Example 2: Clear High Stress / Acute Tension

### Input Feature Vector Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: DETECTED (Confidence: 0.94)
- AU04 Brow Furrow (Eyebrow Tension): 0.84 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.68 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.48 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.72 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.185 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=-8.4°, Yaw=+12.1°, Roll=+2.8°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.085)
- Pitch Mean (F0): 188.4 Hz (Baseline: 145.0 Hz, Delta: +43.4 Hz)
- Pitch Variance (F0 SD): 48.2 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 3.92% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 4.85% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.09 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.742 (Normal <0.40, High >0.65)
```

### SLM Explainable Output
```json
{
  "stress_level": "High (Tier 2)",
  "primary_drivers": [
    "AU04 Brow Furrow=0.84 & AU20 Jaw Tension=0.72 (High facial strain)",
    "Pitch Delta=+43.4Hz & F0 SD=48.2Hz (Elevated vocal pitch & micro-tremor)",
    "Local Jitter=3.92% & Shimmer=4.85% (Severe acoustic perturbation)",
    "Pause Ratio=0.09 (Pressured speech with minimal pauses)",
    "Vocal Tension Index=0.742 (High high-frequency energy ratio)"
  ],
  "explainable_reasoning": "The user exhibits acute physiological stress across both facial and vocal modalities. High AU04 brow furrowing (0.84) and AU20 jaw tension (0.72) combine with significant eye strain (EAR=0.185). Vocally, fundamental pitch is elevated +43.4 Hz above baseline with severe pitch variance (48.2 Hz) and high spectral tension (0.742), accompanied by pressured speech (pause ratio 0.09).",
  "confidence_score": 0.96,
  "ambiguity_note": null
}
```

---

## Example 3: Ambiguous / Conflicting Modalities (High Vocal Pitch vs Relaxed Face)

### Input Feature Vector Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: DETECTED (Confidence: 0.92)
- AU04 Brow Furrow (Eyebrow Tension): 0.12 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.15 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.08 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.14 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.305 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=+1.4°, Yaw=-0.8°, Roll=0.0°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.078)
- Pitch Mean (F0): 178.2 Hz (Baseline: 145.0 Hz, Delta: +33.2 Hz)
- Pitch Variance (F0 SD): 38.5 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 3.15% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 3.65% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.22 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.620 (Normal <0.40, High >0.65)
```

### SLM Explainable Output
```json
{
  "stress_level": "Moderate (Tier 1)",
  "primary_drivers": [
    "Pitch Delta=+33.2Hz & Jitter=3.15% (Acoustic pitch elevation)",
    "AU04 Brow Furrow=0.12 (Relaxed facial features)"
  ],
  "explainable_reasoning": "Assessed as Moderate Stress due to conflicting signals between modalities. Vocal biomarkers show elevated pitch (+33.2 Hz delta), high jitter (3.15%), and vocal tension (0.620), suggesting acoustic stress or excitement. However, facial features remain entirely relaxed (AU04=0.12, EAR=0.305), lowering overall assessment to Tier 1.",
  "confidence_score": 0.72,
  "ambiguity_note": "Conflicting modalities detected: Vocal biomarkers indicate elevated tension while facial expressions remain neutral. May reflect vocal effort, excitement, or background noise interference."
}
```

---

## Example 4: Single Modality Fallback (Missing Video / Camera Disabled)

### Input Feature Vector Prompt
```text
[MULTIMODAL AFFECTIVE FEATURE VECTOR - ROLLING WINDOW (5 SAMPLES)]

--- FACIAL MICRO-EXPRESSIONS (MediaPipe FaceMesh) ---
- Status: NOT DETECTED / POOR LIGHTING (Confidence: 0.0)
- AU04 Brow Furrow (Eyebrow Tension): 0.0 (0.0=Relaxed, >0.5=Elevated Furrow)
- AU07 Lid Tightener (Eye Squint/Strain): 0.0 (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor (Mouth Corner Drop): 0.0 (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher (Jaw Tension): 0.0 (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): 0.3 (Normal: 0.28-0.35, <0.20=Eye Closure/Blink)
- Head Pose: Pitch=0.0°, Yaw=0.0°, Roll=0.0°

--- VOCAL ACOUSTIC BIOMARKERS (16kHz Audio) ---
- Status: DETECTED (RMS Energy: 0.092)
- Pitch Mean (F0): 192.1 Hz (Baseline: 145.0 Hz, Delta: +47.1 Hz)
- Pitch Variance (F0 SD): 52.1 Hz (Micro-tremor indicator)
- Local Jitter (Period Perturbation): 4.12% (Normal <1.5%, High >3.0%)
- Local Shimmer (Amplitude Perturbation): 5.10% (Normal <2.0%, High >3.5%)
- Pause Ratio: 0.05 (0.0=Constant Speech, 1.0=Full Silence)
- Vocal Tension Index (HF Energy >1kHz Ratio): 0.785 (Normal <0.40, High >0.65)
```

### SLM Explainable Output
```json
{
  "stress_level": "High (Tier 2)",
  "primary_drivers": [
    "Pitch Delta=+47.1Hz & F0 SD=52.1Hz (Severe vocal pitch elevation)",
    "Local Jitter=4.12% & Shimmer=5.10% (Severe acoustic perturbation)",
    "Vocal Tension Index=0.785 (Extreme high-frequency tension)"
  ],
  "explainable_reasoning": "Evaluated in audio-only mode due to absent facial video stream. Vocal biomarkers demonstrate severe acute stress: fundamental pitch is elevated +47.1 Hz above baseline, jitter (4.12%) and shimmer (5.10%) are significantly perturbed, and high-frequency vocal tension is extreme (0.785).",
  "confidence_score": 0.85,
  "ambiguity_note": "Facial stream absent (camera disabled or face unlit). Assessment relies exclusively on acoustic biomarkers."
}
```
