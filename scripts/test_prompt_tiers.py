"""Test updated prompt with explicit tier definitions."""
import json
from parlor import llama
from parlor.fusion import FeatureFusionEngine

TEST_PROMPT = (
    "You are an expert Affective Neuroscience & Stress Monitoring AI. "
    "Analyze the provided multimodal feature vector (vocal acoustic biomarkers and facial Action Units). "
    "Your evaluation must be structured, grounded strictly in the numerical signals provided, and fully explainable.\n\n"
    "Tier Guidelines:\n"
    "- Low (Tier 0): Baseline calm or isolated mild signal without congruent distress (e.g., AU04 < 0.35, F0 delta < +25Hz, tension < 0.45).\n"
    "- Moderate (Tier 1): Noticeable tension in one or both modalities (e.g., AU04 0.35-0.70, F0 delta +25 to +50Hz, tension 0.45-0.70).\n"
    "- High (Tier 2): Severe, acute multimodal strain with congruent high facial tension (AU04 >= 0.70, AU07 >= 0.60) and vocal perturbation (F0 delta >= +50Hz, vocal tension >= 0.70, or jitter >= 3.0%).\n\n"
    "Respond using the following JSON schema:\n"
    "{\n"
    '  "stress_level": "Low (Tier 0)" | "Moderate (Tier 1)" | "High (Tier 2)",\n'
    '  "primary_drivers": ["biomarker 1", "biomarker 2"],\n'
    '  "explainable_reasoning": "Clear 2-3 sentence clinical explanation linking observed signals to physiological tension.",\n'
    '  "confidence_score": 0.0 to 1.0,\n'
    '  "ambiguity_note": "Note any conflicting signals or missing face/audio data, else None"\n'
    "}"
)

fe = FeatureFusionEngine()
# Test V01 (Calm)
fe.clear()
fe.add_frame(
    {'face_detected': True, 'confidence': 0.95, 'au04_brow_furrow': 0.05, 'au07_lid_tightener': 0.02, 'au15_lip_depressor': 0.0, 'au20_lip_stretcher': 0.0, 'ear': 0.30, 'head_pitch': 0.0, 'head_yaw': 0.0, 'head_roll': 0.0},
    {'speech_detected': True, 'rms_energy': 0.08, 'f0_mean_hz': 147.0, 'f0_std_hz': 15.0, 'jitter_local': 0.8, 'shimmer_local': 0.9, 'pause_ratio': 0.35, 'vocal_tension_index': 0.22}
)
res1 = llama.chat_blocking(messages=[{'role': 'system', 'content': TEST_PROMPT}, {'role': 'user', 'content': fe.format_prompt()}], max_tokens=300, temperature=0.1)

# Test V05 (Clear Moderate)
fe.clear()
fe.add_frame(
    {'face_detected': True, 'confidence': 0.95, 'au04_brow_furrow': 0.58, 'au07_lid_tightener': 0.52, 'au15_lip_depressor': 0.25, 'au20_lip_stretcher': 0.35, 'ear': 0.30, 'head_pitch': 0.0, 'head_yaw': 0.0, 'head_roll': 0.0},
    {'speech_detected': True, 'rms_energy': 0.09, 'f0_mean_hz': 183.0, 'f0_std_hz': 26.0, 'jitter_local': 2.4, 'shimmer_local': 2.6, 'pause_ratio': 0.35, 'vocal_tension_index': 0.60}
)
res5 = llama.chat_blocking(messages=[{'role': 'system', 'content': TEST_PROMPT}, {'role': 'user', 'content': fe.format_prompt()}], max_tokens=300, temperature=0.1)

# Test V08 (Acute Strain)
fe.clear()
fe.add_frame(
    {'face_detected': True, 'confidence': 0.95, 'au04_brow_furrow': 0.85, 'au07_lid_tightener': 0.78, 'au15_lip_depressor': 0.42, 'au20_lip_stretcher': 0.51, 'ear': 0.30, 'head_pitch': 0.0, 'head_yaw': 0.0, 'head_roll': 0.0},
    {'speech_detected': True, 'rms_energy': 0.12, 'f0_mean_hz': 210.0, 'f0_std_hz': 34.0, 'jitter_local': 4.1, 'shimmer_local': 4.5, 'pause_ratio': 0.35, 'vocal_tension_index': 0.81}
)
res8 = llama.chat_blocking(messages=[{'role': 'system', 'content': TEST_PROMPT}, {'role': 'user', 'content': fe.format_prompt()}], max_tokens=300, temperature=0.1)

for name, r in [('V01', res1), ('V05', res5), ('V08', res8)]:
    print(name, '->', [line.strip() for line in r.split('\n') if 'stress_level' in line])

