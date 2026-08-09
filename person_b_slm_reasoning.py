"""
Person B — Phase 4: Local SLM Stress-Reasoning caller.
Formulates prompt from feature vectors and calls llama-server.
"""

import json
import os
import requests

# Default to llama-server port 8081
LLAMA_SERVER_URL = os.environ.get("LLAMA_SERVER_URL", "http://localhost:8081/v1/chat/completions")


def call_slm(vector, history=None):
    """Calls local SLM to analyze the multimodal features and output stress assessment.

    Returns:
        dict: Containing 'stress_level', 'reasoning', and 'intervention' keys.
    """
    if history is None:
        history = []

    prompt = f"""
[MULTIMODAL AFFECTIVE FEATURE VECTOR]
Timestamp: {vector.get('timestamp')}

--- FACIAL MICRO-EXPRESSIONS ---
- Face Detected: {vector.get('face', {}).get('face_detected', False)}
- AU04 Brow Furrow: {vector.get('face', {}).get('au04_brow_furrow', 0.0)} (0.0=Relaxed, >0.5=Elevated)
- AU07 Lid Tightener: {vector.get('face', {}).get('au07_lid_tightener', 0.0)} (0.0=Relaxed, >0.5=Squinting)
- AU15 Lip Depressor: {vector.get('face', {}).get('au15_lip_depressor', 0.0)} (0.0=Neutral, >0.4=Depressed)
- AU20 Lip Stretcher: {vector.get('face', {}).get('au20_lip_stretcher', 0.0)} (0.0=Neutral, >0.5=Stretched)
- Eye Aspect Ratio (EAR): {vector.get('face', {}).get('ear', 0.3)} (Normal: 0.28-0.35, <0.20=Eye Strain)

--- VOCAL ACOUSTIC BIOMARKERS ---
- Voice Detected: {vector.get('audio', {}).get('voice_detected', False)}
- Pitch Variance: {vector.get('audio', {}).get('pitch_variance', 0.0)} Hz^2 (Baseline: 0.0 - 2.0. High stress: >10.0)
- Local Jitter (Energy Jitter): {vector.get('audio', {}).get('jitter', 0.0)}% (Baseline: 0.01% - 0.05%. High stress: >0.20%)
- Speech Rate Proxy (Onset Rate): {vector.get('audio', {}).get('pause_ratio', 0.0)} events/sec (Baseline: 2.0 - 8.0. High stress: >10.0)

--- HISTORICAL ASSESSMENTS (Oldest to Newest) ---
{json.dumps(history, indent=2)}

TASK:
Analyze the facial micro-expressions and vocal acoustic biomarkers above. Evaluate the user's stress state and output a JSON object.
Follow these strict instructions:
1. Focus ONLY on the provided active biomarkers: pitch_variance, jitter (energy jitter), and speech_rate_proxy (onset rate). Ignore placeholders or absent metrics.
2. Compare the current biomarkers dynamically against the baseline references above. Values within baseline ranges MUST be classified as Low/neutral.
3. Classify stress_level into one of: "Low (Tier 0)", "Moderate (Tier 1)", "High (Tier 2)".
4. Provide a reasoning sentence that explicitly cites the values of the active biomarkers (e.g., pitch_variance, jitter) causing the verdict.
5. Suggest a micro-intervention in "intervention": one of "Guided Breathing", "Short Break", "Eronomic Stretch", or "none".

Return ONLY the JSON.
"""

    response = requests.post(
        LLAMA_SERVER_URL,
        json={
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional physiological stress detection model. You must analyze the feature vectors and return ONLY a valid JSON object matching the requested schema."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        },
        timeout=60
    )
    response.raise_for_status()
    
    # OpenAI/llama-server format response is choices[0].message.content
    choices = response.json().get("choices", [])
    if choices:
        raw_response = choices[0].get("message", {}).get("content", "{}").strip()
    else:
        raw_response = "{}"
    
    # Strip potential markdown code blocks
    if raw_response.startswith("```json"):
        raw_response = raw_response[7:]
    elif raw_response.startswith("```"):
        raw_response = raw_response[3:]
    if raw_response.endswith("```"):
        raw_response = raw_response[:-3]
    
    try:
        result = json.loads(raw_response.strip())
        if "stress_assessment" in result:
            result = result["stress_assessment"]
    except Exception as e:
        print(f"[warning] JSON parsing failed: {e}. Falling back to default values! Raw response was: {raw_response}")
        result = {}

    # Ensure all required keys exist
    return {
        "stress_level": result.get("stress_level", "Low (Tier 0)"),
        "reasoning": result.get("reasoning", "No significant stress biomarkers observed."),
        "intervention": result.get("intervention", "none")
    }

