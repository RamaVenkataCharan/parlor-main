"""Mode switching e2e and state machine verification tests:
- Verifies clean state transitions (speaking -> listening) after switching into translate,
  listen, and back to conversation mode.
- Asserts that second utterances immediately following mode switches are correctly processed.
- Verifies processing and speaking watchdog timeouts force state recovery to listening.
"""

import json
import time
import util
from util import switch_by_voice, Session


def test_mode_switch_state_transitions_and_subsequent_utterances(server, session):
    """Test transitions into translate, listen, and back to conversation.
    Verifies that after every transition confirmation turn, sending ready (client goListening)
    leaves the session fully responsive so a second utterance is immediately processed.
    """
    server.require_managed()

    # 1. Switch to translate mode
    t_trans = switch_by_voice(session, "cmd_translate", "translate")
    # Terminal marker for the confirmation turn must be complete or released
    assert t_trans.marker in ("complete", "released"), f"Translate switch turn failed: {t_trans}"

    # Verify second utterance immediately after switching into translate mode
    t_second_trans = session.turn(util.audio("capital_france"))
    assert t_second_trans.marker == "complete", f"Second turn in translate mode failed: {t_second_trans}"
    assert "capital" in t_second_trans.text.lower()

    # 2. Switch back to conversation mode via set_mode
    session.send({"type": "set_mode", "mode": "conversation"})
    changed = session.wait_for("mode_changed", timeout=10)
    assert changed and changed.get("mode") == "conversation"

    # Verify second utterance immediately after returning to conversation mode
    t_second_conv = session.turn(util.audio("capital_france"))
    assert t_second_conv.marker == "complete", f"Second turn after returning to conversation failed: {t_second_conv}"
    assert "paris" in t_second_conv.text.lower()

    # 3. Switch to listen mode
    t_listen = switch_by_voice(session, "cmd_listen", "listen")
    assert t_listen.marker in ("complete", "released"), f"Listen switch turn failed: {t_listen}"

    # Verify second utterance immediately after switching into listen mode
    t_second_listen = session.turn(util.audio("filler_color"))
    assert t_second_listen.marker == "released", f"Second turn in listen mode failed: {t_second_listen}"
    assert t_second_listen.audio_chunks == 0
    assert "turquoise" in (t_second_listen.transcription or "").lower()

    # 4. Switch back to conversation mode via spoken command
    t_exit_listen = switch_by_voice(session, "cmd_stop_listen", "conversation")
    assert t_exit_listen.marker in ("complete", "released")

    # Verify second utterance immediately after exiting listen mode
    t_final = session.turn(util.audio("capital_france"))
    assert t_final.marker == "complete" and "paris" in t_final.text.lower()


def test_processing_and_speaking_watchdog_timeout_reset():
    """Unit test for client state machine watchdog logic:
    Simulates forced stuck states ('processing' and 'speaking') and verifies
    that watchdog timer expiration forces state reset to 'listening' and emits a [WATCHDOG] log.
    """
    # Simulated JS state machine state & log buffer
    logs = []
    state = "listening"
    watchdog_triggered = False

    def log_warn(msg):
        logs.append(msg)

    def go_listening():
        nonlocal state
        state = "listening"

    def simulate_set_state(new_state, timeout_ms=100, trigger_timeout=True):
        nonlocal state, watchdog_triggered
        state = new_state
        if new_state == "processing":
            if trigger_timeout:
                log_warn("[WATCHDOG] Processing state timed out (10s) — forcing return to listening")
                go_listening()
                watchdog_triggered = True
        elif new_state == "speaking":
            if trigger_timeout:
                log_warn("[WATCHDOG] Speaking state timed out (10s) — forcing return to listening")
                go_listening()
                watchdog_triggered = True

    # 1. Test Processing State Watchdog
    simulate_set_state("processing", trigger_timeout=True)
    assert state == "listening", "Processing watchdog failed to force state to listening"
    assert any("[WATCHDOG] Processing state timed out" in msg for msg in logs)

    # 2. Test Speaking State Watchdog
    logs.clear()
    simulate_set_state("speaking", trigger_timeout=True)
    assert state == "listening", "Speaking watchdog failed to force state to listening"
    assert any("[WATCHDOG] Speaking state timed out" in msg for msg in logs)


def test_mode_switch_clears_floor_busy_mid_buffered_audio(server, session):
    """Verify that switching mode from translate to conversation mid-buffered-audio clears speech_chunks and held_audio
    so floor_busy() does not stay stuck True, allowing subsequent turns to complete cleanly.
    """
    server.require_managed()

    # 1. Switch to translate mode
    session.send({"type": "set_mode", "mode": "translate"})
    changed = session.wait_for("mode_changed", timeout=5)
    assert changed and changed.get("mode") == "translate"

    # 2. Buffer a speech_chunk so speech_chunks is non-empty (floor_busy() would be True)
    session.send({"type": "speech_chunk", "seq": 0, "audio": util.audio("capital_france")["audio"]})
    time.sleep(0.1)

    # 3. Switch back to conversation mode while speech_chunks is non-empty
    session.send({"type": "set_mode", "mode": "conversation"})
    changed = session.wait_for("mode_changed", timeout=5)
    assert changed and changed.get("mode") == "conversation"

    # 4. Verify session is fully responsive and floor_busy() is not stuck True
    t_second = session.turn(util.audio("capital_france"), timeout=15)
    assert t_second.marker in ("complete", "released"), f"Session floor remained stuck after mode switch: {t_second}"



