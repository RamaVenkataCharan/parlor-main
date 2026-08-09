# Intervention Trigger Logic & Cooldown Policy

> **Phase 3 Deliverable:** Trigger threshold rules, anti-false-positive pattern tracking, cooldown management, acute stress vs burnout differentiation, and user control policies.

---

## 1. Anti-False-Positive Strategy & Pattern Thresholds

A wellness monitoring system that fires on false positives (e.g. a momentary sneeze, cough, laugh, or single facial expression misread) quickly annoys users. To guarantee conservative, high-precision delivery, interventions are gated by **two strict pattern requirements**:

```
[SLM Detection Cycle (Every 10s)]
              │
              ├── (1) Consecutive High-Stress Requirement (N = 3 Cycles)
              │     └─ An intervention fires ONLY if 3 consecutive 10s cycles evaluate to
              │        Tier 1 (Moderate Stress) or Tier 2 (High Stress).
              │     └─ A single baseline/relaxed cycle immediately resets the counter to 0.
              │
              └── (2) Exponential Moving Average (EMA) Stress Tracking (α = 0.3)
                    └─ EMA Score = (0.3 * Current_Tier) + (0.7 * Previous_EMA)
                    └─ Fires if EMA Score >= 1.4, providing smoothed trend tracking.
```

---

## 2. Cooldown & Anti-Nagging Policy

* **Default Cooldown Period:** **5 Minutes (300 Seconds)**
* **Mechanics:** Once an intervention fires, the `TriggerManager` arms a mandatory 300-second cooldown timer. During this window:
  - Detection cycles continue silently in the background.
  - No new UI toasts or audio alerts are presented to the user.
  - Prevents nagging or spamming during a sustained stressful task.

---

## 3. Acute Stress vs. Early Burnout Differentiation

The system distinguishes between single-session acute tension and long-term burnout risk across two distinct timescales:

| Intervention Tier | Trigger Condition | Target Timescale | Intervention Type Delivered | User Action Options |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Acute Stress** | $N=3$ consecutive cycles of Tier 1/2 stress (or EMA $\ge 1.4$) | Single Session (30s – 5 mins) | Light micro-interventions: Guided Breathing, Short Movement Break, Mindfulness Grounding, Motivational Prompt | *Start Breathing*, *Dismiss*, *Snooze 10m* |
| **Tier 2: Early Burnout Risk** | $\ge 15$ cumulative high-stress cycles across a 15-minute window | Multi-Window / Long-term | High-priority Burnout Warning: Work pause recommendation, 15-minute screen rest, ergonomic reset | *Schedule Extended Rest*, *Dismiss*, *Pause Monitoring* |

---

## 4. Intervention Personalization & Explainability

Interventions are **template-grounded** for safety and speed, but **SLM-personalized** by embedding the exact reasoning and biomarker drivers from Phase 2:
- **No Black-Box Alerts:** Every intervention card includes a **"Why did this fire?"** dropdown that discloses the exact SLM explanation (e.g. *"Observed triggers: AU04 Brow Furrow=0.84, Vocal Pitch Delta=+43.4Hz"*).
- **Clinical Safety:** Pre-designed templates guarantee that wellness instructions (such as box breathing or sensory grounding) remain clinically sound and free from SLM hallucination.

---

## 5. User Control & Safety Valve Settings

To empower users and act as a practical safety valve against false positives:
- **Sensitivity Modes:**
  - **Conservative:** Requires $N=4$ consecutive cycles; 450s cooldown.
  - **Balanced (Default):** Requires $N=3$ consecutive cycles; 300s cooldown.
  - **Sensitive:** Requires $N=2$ consecutive cycles; 180s cooldown.
- **Snooze & Mute:**
  - **Snooze 10m:** Temporarily pauses interventions for 10 minutes.
  - **Mute Interventions:** Disables UI notifications entirely while continuing background data logging.
