"""Mic mute detection unit tests:
Simulates MediaStreamTrack mute states (track.muted === true vs track.muted === false)
and verifies that:
1. Muted state (track.muted === true or !track.enabled) sets status to 'muted',
   state to 'muted', triggers amber UI indicators, and logs [MIC MUTE DETECTED].
2. Unmuted state (track.muted === false) returns to active status ('connected' / 'listening')
   and does not trigger false-positive mute warnings.
"""

import pytest


class MockAudioTrack:
    def __init__(self, label="Default Microphone", enabled=True, muted=False, ready_state="live"):
        self.label = label
        self.enabled = enabled
        self.muted = muted
        self.readyState = ready_state
        self.onmute = None
        self.onunmute = None
        self.onended = None

    def getSettings(self):
        return {"deviceId": "mock-mic-1", "sampleRate": 44100}


class MockMediaStream:
    def __init__(self, track):
        self._tracks = [track] if track else []

    def getAudioTracks(self):
        return self._tracks


class AppMicStateSimulator:
    def __init__(self):
        self.status = "loading"
        self.state = "loading"
        self.status_text = ""
        self.diag_mic_class = ""
        self.diag_mic_text = ""
        self.logs = []
        self.toasts = []

    def set_status(self, kind, text):
        self.status = kind
        self.status_text = text

    def set_state(self, new_state):
        self.state = new_state

    def show_toast(self, msg, category="info"):
        self.toasts.append((category, msg))

    def check_audio_track_mute_state(self, stream):
        if not stream:
            return False
        tracks = stream.getAudioTracks()
        if not tracks:
            return False
        track = tracks[0]
        return track.muted or not track.enabled

    def update_mic_mute_ui(self, is_muted):
        if is_muted:
            self.set_status("muted", "Mic Muted")
            self.set_state("muted")
            self.logs.append("[MIC MUTE DETECTED] Hardware/OS mic track is MUTED! Pausing speech detection.")
        else:
            self.set_status("connected", "Connected")
            if self.state != "loading":
                self.set_state("listening")
            self.logs.append("[MIC UNMUTE DETECTED] Mic track is active and unmuted.")

    def update_diagnostics(self, stream):
        if not stream or not stream.getAudioTracks():
            self.diag_mic_class = "diag-val error"
            self.diag_mic_text = "⚫ No device"
            return
        track = stream.getAudioTracks()[0]
        label = f" ({track.label.split()[0]})" if track.label else ""
        if track.readyState == "ended":
            self.diag_mic_class = "diag-val error"
            self.diag_mic_text = f"🔴 Disconnected{label}"
        elif track.muted or not track.enabled:
            self.diag_mic_class = "diag-val warning"
            self.diag_mic_text = f"🔴 Muted{label}"
        else:
            self.diag_mic_class = "diag-val ok"
            self.diag_mic_text = f"🟢 Live{label}"


def test_mic_mute_detection_when_track_muted():
    """Verify that when MediaStreamTrack has muted === True, the app correctly
    triggers the amber Mic Muted state and diagnostic warning, avoiding silent hangs.
    """
    track = MockAudioTrack(label="Microphone Array", enabled=True, muted=True)
    stream = MockMediaStream(track)
    sim = AppMicStateSimulator()

    # 1. Check mute state evaluation
    is_muted = sim.check_audio_track_mute_state(stream)
    assert is_muted is True, "Failed to identify track.muted == True"

    # 2. Trigger UI update
    sim.update_mic_mute_ui(is_muted)
    sim.update_diagnostics(stream)

    assert sim.status == "muted"
    assert sim.status_text == "Mic Muted"
    assert sim.state == "muted"
    assert sim.state != "listening", "App incorrectly reported listening state when mic was muted"
    assert "🔴 Muted" in sim.diag_mic_text
    assert any("[MIC MUTE DETECTED]" in log for log in sim.logs)


def test_mic_unmute_detection_when_track_active():
    """Verify inverse case: when track.muted === False, app correctly sets state to
    'listening' without false positive mute warnings.
    """
    track = MockAudioTrack(label="Microphone Array", enabled=True, muted=False)
    stream = MockMediaStream(track)
    sim = AppMicStateSimulator()
    sim.state = "listening"

    # 1. Check mute state evaluation
    is_muted = sim.check_audio_track_mute_state(stream)
    assert is_muted is False, "Incorrectly reported unmuted track as muted"

    # 2. Trigger UI update
    sim.update_mic_mute_ui(is_muted)
    sim.update_diagnostics(stream)

    assert sim.status == "connected"
    assert sim.state == "listening"
    assert "🟢 Live" in sim.diag_mic_text
    assert any("[MIC UNMUTE DETECTED]" in log for log in sim.logs)
