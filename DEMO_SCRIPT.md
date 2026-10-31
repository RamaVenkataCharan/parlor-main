# EMO Assistant ("Parlor") — FYP Demonstration & Defense Script

> **Duration:** 5–10 Minutes  
> **Target Audience:** FYP Defense Committee, Evaluators, Technical Audience  
> **Key Value Proposition:** On-device, privacy-preserving multimodal affective AI that reasons qualitatively over physiological and vocal biomarker patterns rather than rigid numeric thresholds.

---

## Preparation Checklist Before Demo

1. **Hardware:**
   - Laptop with working webcam and microphone.
   - External speaker / headphones for voice interaction.
2. **Environment & Terminal Setup:**
   - Terminal 1: Application Server (`uv run uvicorn parlor.server:app --port 8000`)
   - Browser: Google Chrome / Microsoft Edge opened at `http://localhost:8000`
3. **Clean State:**
   - Verify `shared_state/wellness_history.db` is initialized.

---

## 5–10 Minute Presentation Walkthrough

### Phase 1: Clean Startup & Architecture Overview (1.5 Minutes)

- **Action:** Open Terminal 1 and start the unified server:
  ```powershell
  uv run uvicorn parlor.server:app --port 8000
  ```
- **Speaking Points:**
  > *"Parlor is a fully on-device multimodal assistant. Notice that we launch a single unified server process. The lifespan manager starts the conversational voice pipeline alongside our background Affective Wellness Monitoring service. All computation—audio DSP, MediaPipe computer vision, local SLM reasoning, and SQLite persistence—happens 100% on-device with zero cloud dependencies or outbound telemetry."*
- **Visuals:** Point out the startup log showing `[WELLNESS] Starting background monitoring loop (cycle=8.0s)...` and healthy `llama-server` connection.

---

### Phase 2: Conversational Voice Interaction & Sub-Second TTFA (1.5 Minutes)

- **Action:** Open `http://localhost:8000`, grant Camera & Microphone permissions, and click the microphone icon.
- **Utterance:** *"Hey Parlor, what is the capital of France and what is it famous for?"*
- **Expected Behavior:**
  - The turn indicator shows listening $\rightarrow$ thinking.
  - Sub-second **Time to First Audio (TTFA ~0.78s)**: Parlor speaks back naturally using Kokoro-ONNX neural speech.
  - The live transcript prints on the screen without latency.
- **Speaking Points:**
  > *"Notice how responsive the conversational loop is. While the user is speaking, Parlor speculatively pre-fills prompt caches. Even with our affective monitoring running in the background, our Time to First Audio remains around 0.8 seconds—well below the human conversational threshold of one second."*

---

### Phase 3: Telemetry & Live Diagnostics Panel (1.5 Minutes)

- **Action:** Click the **Diagnostics** drawer button in the UI header.
- **Expected Behavior:**
  - Diagnostics drawer slides out showing live biomarker gauges:
    - Facial Action Units: AU04 (Brow Furrow), AU07 (Squint), AU20 (Jaw Tension), EAR (Eye Aspect Ratio).
    - Vocal Acoustic Metrics: Pitch Delta (Hz), Jitter (%), Shimmer (%), Vocal Tension Index.
  - Telemetry updates every ~8 seconds with smooth visual feedback.
- **Speaking Points:**
  > *"Here in the diagnostics drawer, we expose the exact raw physiological signals extracted passively from the laptop webcam and microphone. No wearable sensors or manual self-reporting surveys are required."*

---

### Phase 4: Inducing Stress & Non-Threshold Pattern Reasoning (2 Minutes)

- **Action:**
  - Furrow eyebrows noticeably toward the webcam (simulating cognitive strain).
  - Speak with elevated pitch or pressured tempo: *"I have three overlapping deadlines and my code won't compile!"*
  - Wait for consecutive cycles ($N=3$ in Balanced mode).
- **Expected Behavior:**
  - The **Micro-Intervention Card** animates into view with an audible gentle cue.
  - Card displays a categorized micro-intervention (e.g., *Box Breathing (4-4-4-4)* or *Jaw Relaxation & Neck Release*).
  - Click **"Why did this fire?"** to expand the explainable reasoning disclosure:
    - Highlights cited biomarkers: `AU04 Brow Furrow=0.78`, `AU20 Jaw Tension=0.68`, `Pitch Delta=+38.2 Hz`.
    - Plain-language explanation: *"Assessed as High Stress (Tier 2). Elevated eyebrow furrowing and jaw clamping coincided with pressured vocal cadence and heightened pitch variability."*
- **Speaking Points:**
  > *"Notice that Parlor did not just trigger on a single spike. Our system reasons qualitatively over the pattern across time. In our benchmarks, if a user has elevated pitch from excitement while their face is completely relaxed, the SLM lowers its confidence score to Tier 1 rather than firing an inappropriate burnout alert. Furthermore, every intervention is fully explainable—the user can see exactly which biomarkers influenced the decision."*

---

### Phase 5: Sensitivity Modes, Snooze & Alert Controls (1.5 Minutes)

- **Action:** Click the **🌿 Wellness** button in the header to open the controls modal:
  1. Switch Sensitivity from **Balanced** to **Conservative** (shows $N=4$ cycles required, 10m cooldown).
  2. Toggle **Mute Alerts** (shows icon shift to muted bell; console shows `[WELLNESS] Wellness alerts MUTED`).
  3. Click **"Snooze 10m"** on the intervention card.
- **Expected Behavior:**
  - Card dismisses cleanly.
  - Server logs confirm: `[WELLNESS] Interventions snoozed for 10.0 minutes`.
- **Speaking Points:**
  > *"To ensure high user acceptance in real workplace environments, Parlor provides granular user controls. Users can adjust sensitivity depending on their daily work context, snooze alerts with a single click, or mute pop-ups entirely while longitudinal logging continues quietly in the background."*

---

### Phase 6: Graceful Degradation & Resilience (1.5 Minutes)

- **Action:**
  1. In a separate terminal, simulate SLM unavailability by pausing or stopping `llama-server` (or disconnect test port):
  2. Continue speaking to Parlor.
  3. Cover the webcam with a hand or mute the microphone.
- **Expected Behavior:**
  - The conversational pipeline remains stable and does not crash.
  - The wellness service does not emit false stress tiers; server logs: `[WELLNESS] Local SLM reasoning unavailable — backing off`.
  - When the camera is covered, the system detects insufficient signal and logs: *"No facial or vocal signals detected in the current observation window"* with `confidence: 0.0`.
  - Upon unpausing, the wellness loop recovers automatically without restarting the server.
- **Speaking Points:**
  > *"A critical defense requirement is graceful degradation. If the local language model is momentarily overloaded or offline, Parlor never hangs or crashes the voice assistant. It backs off exponentially and recovers automatically. Crucially, when signals are absent—such as when the camera is covered—it honestly reports insufficient signal rather than guessing."*

---

## Defense Q&A Preparation Cheat Sheet

| Question | Core Defense Answer |
| :--- | :--- |
| **"Why not just use fixed thresholds (e.g. if AU04 > 0.5)?"** | Fixed thresholds fail on natural human diversity and cause false-positive fatigue. A singer or expressive speaker triggers pitch thresholds without being stressed; an individual concentrating deeply furrows brows without vocal strain. The SLM evaluates the *confluence* of modalities and cross-modal discrepancies. |
| **"How is privacy guaranteed?"** | MediaPipe and Librosa process raw audio/video frames in volatile memory on the local machine. Only lightweight numerical vectors pass into the fusion engine. No video frames, audio recordings, or embeddings are ever transmitted externally or written to persistent disk. |
| **"Why Gemma / Llama 8B instead of a cloud model?"** | Zero latency penalty from internet hops, 100% offline privacy, zero operational API costs, and immunity to network outages. |
| **"What is the CPU/GPU footprint?"** | The entire feature extraction and fusion pipeline takes only **~21.5 ms** of CPU time per 8-second cycle (<0.3% CPU utilization). GPU execution for SLM reasoning takes **~2.8s**, comfortably within the 5.0s observation budget. |
