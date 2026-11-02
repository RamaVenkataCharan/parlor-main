# Parlor Demonstration Safeguards, Rehearsal Checklist & Fallback Guide

> **Project:** EMO Assistant ("Parlor") — Fully On-Device Multimodal AI & Affective Wellness Monitoring  
> **Academic Year:** 2026–2027  
> **Target Audience:** Project Team (Batch 14, Section A), Technical Guide (Mrs. V. Aruna, Project Guide), External Reviewers & Defense Committee  
> **Primary Document Purpose:** Mission-critical operational safeguards to guarantee 100% demonstration reliability during final university project viva-voce and committee examinations.

---

## 1. Pre-Flight Rehearsal Checklist

Execute this checklist sequentially **30 minutes prior** to the live viva-voce presentation.

### 1.1 Physical & Environmental Calibration

| Domain | Specification Requirement | Verification Step | Remediation if Non-Compliant |
| :--- | :--- | :--- | :--- |
| **Room Lighting** | Frontal, diffuse lighting ($\ge 100\text{ lux}$); zero harsh backlighting. | Open Windows Camera app. Confirm face mesh tracking points are sharp without blown-out whites. | Reposition laptop away from window; adjust desk lamp towards face. |
| **Acoustic Noise Floor** | Ambient room noise $< 45\text{ dBA}$; no active AC blowing directly into microphone. | Check Windows Sound Settings $\rightarrow$ Input $\rightarrow$ Test your microphone. Base level should register $\le 2\%$. | Switch from internal laptop mic to dedicated headset or directional lapel microphone. |
| **Eyewear & Occlusions** | Unobscured eye landmarks and brow ridge (AU04/AU07). | Ensure glasses frames do not cast shadows directly over eyebrow vertices. | Slightly tilt glasses down or adjust lighting angle. |

### 1.2 System & Hardware Verification

```powershell
# 1. Check GPU VRAM and active compute processes
nvidia-smi

# Verification criteria:
# - Driver Version: >= 550.00 | CUDA Version: >= 12.4
# - Free VRAM: >= 4.2 GB (out of 6.0 GB on RTX 4050)
# - No other heavy graphics/CUDA processes running (kill games, DaVinci, Blender)
```

```powershell
# 2. Verify Port 8000 (FastAPI/WebSockets) and Port 8081 (llama-server) are free
Get-NetTCPConnection -LocalPort 8000, 8081 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess, State

# If any process is occupying these ports, terminate it safely:
# Stop-Process -Id <OwningProcessId> -Force
```

```powershell
# 3. Verify Python virtual environment and dependencies
cd parlor-main-main
uv run python -c "import cv2, mediapipe, scipy, onnxruntime; print('OpenCV:', cv2.__version__, '| MediaPipe:', mediapipe.__version__, '| ONNX:', onnxruntime.__version__)"
```

### 1.3 Model & Engine Warm-Up Procedure

On-device SLMs incur a cold-start overhead (~1.8s) during the initial KV cache initialization. To ensure the committee witnesses the verified **1.789s TTFA (loop off) / 1.903s (loop on mitigated)** immediately:

1. Launch Parlor via the hardened launch script:
   ```powershell
   .\start.ps1
   ```
2. Open Google Chrome or Microsoft Edge to `http://localhost:8000`.
3. Allow camera and microphone permissions when prompted.
4. Issue a single warm-up phrase: *"Good morning Parlor, system ready."*
5. Confirm Kokoro audio streams instantly and the wellness telemetry ticker begins emitting cycles in the bottom drawer.
6. The system is now warm, resident in GPU VRAM, and primed for live evaluation.

---

## 2. Live Committee Demonstration Script (3-Tier Protocol)

Follow this 5-minute interactive walkthrough to demonstrate each technical milestone in order:

```
                  ┌──────────────────────────────────────────────┐
                  │   STEP 1: Conversational Turn-Taking (1m)   │
                  │   TTFA = 1.79s | Smart-Turn | Kokoro Speech  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │   STEP 2: Multimodal Stress Escalation (2m)  │
                  │   Cognitive Arithmetic -> AU04 + Vocal Jitter│
                  │   Tier 2 Escalation -> Empathic Micro-Break  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │   STEP 3: Cross-Modal Contradiction Test (1m)│
                  │   Lively Vocal Inflection + Relaxed Smile    │
                  │   SLM Reasoner Disallows False Positives     │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │   STEP 4: Resilience & Mid-Session Fault (1m)│
                  │   Kill llama-server -> Amber Banner Appears  │
                  │   Process Restarts -> Reconnect in < 4.2s     │
                  └──────────────────────────────────────────────┘
```

### Step 1: Sub-Second Conversational Assistance (60 Seconds)
- **Action:** Speak naturally: *"Parlor, can you explain what an Action Unit is in affective computing?"*
- **Observation:** Notice the assistant responds within **1.79s–1.90s TTFA** (conversational turn latency). Point out the audio streaming visualizer and zero-latency barge-in interruptibility by speaking mid-sentence.
- **Key Talking Point:** *"All acoustic turn-detection and speech synthesis run locally on-device. Zero audio packets leave this machine."*

### Step 2: Multimodal Stress Escalation & Empathic Micro-Break (120 Seconds)
- **Action:** Engage in a live cognitive arithmetic challenge (e.g. subtracting 7s backward from 1000 rapidly: *"1000, 993, 986, 979..."*) while furrowing the brow (AU04) and clenching facial muscles.
- **Observation:** Within 3 consecutive observation windows in default Balanced mode (or 2 in Sensitive mode), the telemetry widget transitions from **Tier 0 (Green)** $\rightarrow$ **Tier 1 (Yellow)** $\rightarrow$ **Tier 2 (Red)**. The assistant triggers a gentle, non-intrusive micro-break prompt: *"I noticed your brow tension and vocal strain rising over the last few minutes. Would you like to pause for 60 seconds?"*
- **Key Talking Point:** *"The intervention engine requires consecutive elevated cycles to prevent jarring, erratic notifications. Provenance disclosure explains exactly why the intervention fired."*

### Step 3: Cross-Modal Contradiction / Honest Disconfirmation (60 Seconds)
- **Action:** Speak with loud, excited, and dynamic vocal pitch inflection while maintaining an open, relaxed posture and a genuine smile (AU12).
- **Observation:** The system classifies the state as **Tier 0 or Tier 1 (Lively Engagement)**, explicitly suppressing a stress alert.
- **Key Talking Point:** *"A purely audio-based heuristic or single-threshold system would false-alarm on high vocal pitch. Gemma 4 E2B reconciles the acoustic perturbation with the smiling facial geometry to prevent false positives."*

### Step 4: Graceful Degradation & Fault Injection (60 Seconds)
- **Action:** Open a terminal and terminate `llama-server.exe`:
  ```powershell
  Stop-Process -Name "llama-server" -Force
  ```
- **Observation:** Point to the browser UI. The screen does not freeze, crash, or go blank; an amber notification bar appears: *"SLM inference engine temporarily unavailable. Retrying connection..."* Re-run `.\start.ps1`, and the UI seamlessly reconnects within **4.1 seconds** without page refresh.

---

## 3. Recorded Backup Video Demonstration Plan

If a catastrophic hardware failure occurs during the committee review (e.g. laptop HDMI output disconnects, camera hardware bus fails, or auditorium noise exceeds 85 dB), switch immediately to the **Pre-Recorded High-Definition Verification Reel** (`REQUIRES HUMAN: record the demo`).

### 3.1 Video Specifications & Recording Status
- **Status:** `REQUIRES HUMAN: Record 1080p60 screen demo following script prior to viva`
- **Target File Name:** `Parlor_Live_System_Demonstration_1080p60.mp4`
- **Target Location:** `dist/demo_backup/` and pre-loaded onto a USB 3.0 Flash Drive.
- **Resolution & Encoding:** 1920x1080 @ 60 FPS, H.264 video, 320 kbps AAC audio.
- **Scripted Duration:** 4 minutes 45 seconds (Full cue sheet prepared below and in `DEMO_SCRIPT.md`).

### 3.2 Video Segment Timecode Guide

| Timestamp | Scenario Title | On-Screen Visuals | Voiceover Commentary Track |
| :---: | :--- | :--- | :--- |
| **0:00 – 1:15** | Conversational Voice Interaction | Live side-by-side terminal logs and Chrome UI showing 1.79s mean TTFA and Kokoro TTS waveform. | "Demonstrating fully local multimodal inference. Notice the Smart-Turn V3.2 acoustic endpointing firing at 68ms." |
| **1:15 – 2:30** | Cognitive Stress Escalation | Live Stroop test execution; MediaPipe AU04 brow furrow heatmap overlays; transition from Tier 0 to Tier 2. | "Observing real-time facial AU extraction running at 3.97ms on real face. The rolling temporal fusion buffer registers multi-cycle elevation." |
| **2:30 – 3:35** | Cross-Modal Conflict Reasoning | Animated pitch jitter spike accompanied by facial smile; Gemma 4 SLM JSON reasoning displayed. | "Demonstrating SLM cross-modal reconciliation (2.14s reasoning). High vocal energy is disambiguated from psychological distress." |
| **3:35 – 4:45** | Fault Injection & Offline Fallback | Terminal process kill; UI warning banner; camera covered showing zero-signal honest reporting. | "Injecting mid-session fault. Parlor reports honest null signals when camera is covered, rather than fabricating stress scores." |

---

## 4. Offline Fallback Demonstration Script (`wellness_history.db`)

If neither the live hardware nor video playback is preferred by the examiner, Parlor includes a deterministic **Offline Playback & Fallback Utility** (`scripts/offline_demo_playback.py`).

This utility replays the **1,717 genuine historical assessment cycles** logged in `shared_state/wellness_history.db`.

### 4.1 Mode A: Terminal Telemetry Stream (Zero Dependencies)
Run directly from PowerShell:
```powershell
uv run python scripts/offline_demo_playback.py --replay --limit 15 --delay 1.0
```
**Expected Examiner Output:**
```
===========================================================================
 STARTING CHRONOLOGICAL REPLAY (15 cycles, 1.0s interval)
===========================================================================

[1/15] Cycle ID: #1703 | Status: [TIER 0 - LOW]
 Confidence : 91.0% | Score: 0.0
 Biomarkers : No active signals detected
 Reasoning  : "All biometric indicators remain within normal relaxed baseline parameters."

[2/15] Cycle ID: #1704 | Status: [TIER 1 - MODERATE]
 Confidence : 85.0% | Score: 1.0
 Biomarkers : Pitch Mean (F0) Delta=+61.5 Hz, Local Jitter 7.43%
 Reasoning  : "Acoustic perturbation indicates moderate vocal tension; facial musculature stable."

[3/15] Cycle ID: #1705 | Status: [TIER 2 - HIGH]
 Confidence : 88.0% | Score: 2.0
 Biomarkers : AU04 Brow Furrow=1.82, Pitch Delta=+74.1 Hz, Shimmer=16.2%
 Reasoning  : "Concurrent facial brow furrow and acoustic jitter indicate high cognitive strain."
 [!] INTERVENTION TRIGGERED: Category='Tactile Micro-Break'
```

### 4.2 Mode B: Live Mock WebSocket Web UI Broadcast
Demonstrates the full graphical web interface without requiring a GPU or camera:
```powershell
uv run python scripts/offline_demo_playback.py --serve --port 8000
```
1. Open `http://localhost:8000`.
2. The browser automatically establishes a WebSocket connection.
3. The offline server emits chronological telemetry cycles every 4.0 seconds.
4. The dashboard gauges, stress timeline, and intervention modals update in real time, demonstrating full frontend functionality to the committee.

---

## 5. Defense Troubleshooting Quick-Reference

| Symptom | Root Cause | Immediate Viva Remedy |
| :--- | :--- | :--- |
| **WebSocket closes with Code 1006 / 1011** | `llama-server` not yet initialized or port blocked. | Run `Get-Process llama-server`. If absent, launch via `.\start.ps1`. |
| **Camera displays black square in UI** | Another application (Teams, Zoom, Camera app) has an exclusive DirectShow lock on webcam. | Close background communication tools: `Get-Process Teams, Zoom | Stop-Process`. Refresh browser. |
| **Microphone does not pick up audio** | Browser permissions revoked or wrong default input in Windows. | Click padlock icon in Chrome address bar $\rightarrow$ Ensure Microphone is set to "Allow". |
| **Response latency feels sluggish (>3s TTFA)** | Model loaded on CPU instead of NVIDIA CUDA GPU due to driver misconfiguration. | Check `start.ps1` output. Confirm `-ngl 99` flag is passed and `llama.cpp` reports `BLAS = 1 / CUDA`. |
| **Intervention modal does not pop up** | Interventions require consecutive Tier 2 cycles (3 in Balanced, 2 in Sensitive, 4 in Conservative) and respect the configured cooldown (300s Balanced, 180s Sensitive, 450s Conservative). | Check database metadata; if cooldown is active, click "Trigger Test Intervention" in UI debug drawer or adjust sensitivity. |

---

*Verified and Prepared by Batch 14, Section A, CSE:*
*- M. Rama Venkata Charan (23KN1A0543)*
*- B. Murali Gopi (23KN1A0515)*
*- M. Kumar Siva Sai (23KN1A0542)*
*- Y. Yashwanth Prakash (23KN1A0571)*
*Under the Guidance of Mrs. V. Aruna, Project Guide, Dept. of CSE.*

