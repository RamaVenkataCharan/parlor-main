"""Local Micro-Intervention Generator.

Generates personalized interventions across four core categories:
1. Guided Breathing Exercises (4-7-8 Box Breathing)
2. Short Movement & Rest Breaks
3. Sensory Mindfulness Grounding (5-4-3-2-1 Method)
4. Motivational & Cognitive Reset Prompts
5. Long-term Burnout Risk Warnings

Combines evidence-based wellness templates with SLM-detected biomarkers for explainable, personalized delivery.
"""

import random
from typing import Dict, Any, List


TEMPLATES = {
    "guided_breathing": {
        "title": "Guided 4-7-8 Breathing Exercise",
        "category": "Guided Breathing",
        "icon": "🫁",
        "action_label": "Start 1-Min Breathing",
        "steps": [
            "Inhale deeply through your nose for 4 seconds.",
            "Hold your breath gently for 7 seconds.",
            "Exhale slowly and completely through your mouth for 8 seconds.",
            "Repeat this cycle 4 times to relax your nervous system."
        ]
    },
    "short_break": {
        "title": "5-Minute Movement & Eye Rest",
        "category": "Short Break",
        "icon": "☕",
        "action_label": "Take a 5-Min Break",
        "steps": [
            "Step away from your screen and look at an object 20 feet away.",
            "Stretch your neck, shoulders, and back to release physical tension.",
            "Drink a glass of water and take 5 slow, deep breaths."
        ]
    },
    "mindfulness": {
        "title": "5-4-3-2-1 Sensory Grounding",
        "category": "Mindfulness",
        "icon": "🌿",
        "action_label": "Begin Grounding Check-in",
        "steps": [
            "Acknowledge 5 things you can see around you.",
            "Acknowledge 4 things you can physically touch.",
            "Acknowledge 3 things you can hear right now.",
            "Acknowledge 2 things you can smell.",
            "Acknowledge 1 thing you can taste."
        ]
    },
    "motivational": {
        "title": "Cognitive Reframing & Encouragement",
        "category": "Motivational Prompt",
        "icon": "💡",
        "action_label": "Read Encouragement",
        "steps": [
            "You are making steady progress. Pause for a moment to acknowledge your effort.",
            "Break your current task into one small, manageable next step.",
            "Remember that taking a short rest improves focus and problem-solving quality."
        ]
    },
    "burnout_warning": {
        "title": "Early Burnout Precautionary Notice",
        "category": "Burnout Warning",
        "icon": "⚠️",
        "action_label": "Schedule Extended Rest",
        "steps": [
            "High physiological strain has been sustained across multiple consecutive work blocks.",
            "Step away from all work tasks for at least 15 to 20 minutes.",
            "Engage in physical movement, fresh air, or non-screen relaxation before resuming."
        ]
    }
}


class InterventionGenerator:
    """Generates personalized micro-interventions grounded in SLM explanations."""

    def __init__(self):
        self.categories = ["guided_breathing", "short_break", "mindfulness", "motivational"]

    def generate(self, category: str, slm_output: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a personalized intervention package.
        
        Args:
            category: "guided_breathing", "short_break", "mindfulness", "motivational", "burnout_warning", or "auto"
            slm_output: Dict containing SLM stress reasoning from Phase 2.
            
        Returns:
            Dict containing intervention title, icon, steps, SLM drivers, explanation, and action metadata.
        """
        if category == "auto" or category not in TEMPLATES:
            # Pick based on primary driver characteristics if available
            drivers = slm_output.get("primary_drivers", [])
            drivers_str = " ".join(drivers).lower()
            if "brow" in drivers_str or "jaw" in drivers_str or "tension" in drivers_str:
                category = "guided_breathing"
            elif "pitch" in drivers_str or "speech" in drivers_str or "jitter" in drivers_str:
                category = "short_break"
            else:
                category = random.choice(self.categories)

        tpl = TEMPLATES[category]

        # Extract SLM explanation & drivers for full transparency
        reasoning = slm_output.get("explainable_reasoning", "Elevated physiological tension detected across observation windows.")
        drivers = slm_output.get("primary_drivers", ["Sustained vocal/facial stress signals"])

        # Construct personalized message
        drivers_text = ", ".join(drivers) if isinstance(drivers, list) else str(drivers)
        personalized_note = f"Observed triggers: {drivers_text}."

        return {
            "title": tpl["title"],
            "category": tpl["category"],
            "icon": tpl["icon"],
            "action_label": tpl["action_label"],
            "steps": tpl["steps"],
            "personalized_note": personalized_note,
            "slm_reasoning": reasoning,
            "slm_drivers": drivers,
            "stress_level": slm_output.get("stress_level", "Moderate (Tier 1)"),
            "confidence_score": slm_output.get("confidence_score", 0.90),
            "ambiguity_note": slm_output.get("ambiguity_note", None)
        }
