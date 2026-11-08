"""Parlor — on-device, real-time multimodal AI (voice + vision).

LLM inference runs on llama.cpp (llama-server, spawned as a subprocess —
see llama.py). This server owns the conversation history and re-sends it
every request; llama-server's prefix cache makes that cheap, and it also
enables two speculative tricks (see pipeline.py): the camera frame and the
user's speech (in ~3s chunks) are pushed through cache-priming requests
WHILE the user is still talking, so the final request only pays for the
tail of the utterance.
"""

import asyncio
import itertools
import json
import os
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional, Dict, List

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)  # logs stream even when piped
sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

import base64
import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

try:  # raised by ws.send_text after the client goes away (uvicorn-specific)
    from uvicorn.protocols.utils import ClientDisconnected
except ImportError:  # pragma: no cover
    class ClientDisconnected(OSError):
        pass

DISCONNECT_ERRORS = (WebSocketDisconnect, ClientDisconnected)

from dotenv import load_dotenv
load_dotenv()  # before importing llama — it reads its config at import time

from parlor import actions, db, llama, reasoner, tts
from parlor.modes import MODES
from parlor.pipeline import (estimate_tokens, pad_tail_silence, prime_cache,
                             release_client, run_turn, send_json, text_part,
                             user_content, valid_audio, wav_to_float32)
from parlor.wellness import WellnessService

# Turn completeness is judged by the smart-turn audio classifier before the
# LLM is involved, so the prompt carries no FINISHED/WAIT machinery at all.
# Asking Gemma to judge it instead scores at chance on audio — see
# benchmarks/turnbench.py, which still reproduces those two variants.
SYSTEM_PROMPT = (
    "You are a friendly, conversational AI assistant. The user talks to you "
    "through a microphone and may show you their camera. Your replies are "
    "spoken aloud, so write plain conversational text without formatting. "
    "Never comment on the user's appearance, skin tone, gender, or age unless explicitly asked. "
    "For emotional statements, respond with brief, warm support. "
    "If an audio message is just your own previous reply playing back "
    "(echo), don't answer it — briefly ask what they'd like to talk about."
)

# The model's replies are pure speech: it never emits control markup.
# Actions (timers, mode switches, research) are decided by a separate
# grammar-forced request — see actions.py for the measured rationale.
# The speech prompt only needs the model to KNOW the capabilities exist,
# so confirmations sound natural and never contradict what the decider
# does. This note lives in the system prompt because it changes no
# per-turn behavior — unlike the old in-band tags, nothing here has to
# fight for attention next to the audio.
CAPABILITY_NOTE = (
    " You can set countdown timers, translate everything the user says, "
    "or just listen quietly while they think out loud. When the user "
    "asks for one of these, confirm it in one short natural sentence — a "
    "separate system watches the conversation and actually performs it, "
    "so never say you can't, and never invent its results. "
    "Answer greetings, chat, and general knowledge questions directly and completely yourself from memory. "
    "If the user asks about anything current or changing — today's weather, live prices, "
    "breaking news, or current scores — tell them honestly that you cannot look that up "
    "right now and they should check a live source."
)

# Appended only when a reasoner endpoint is configured (.env REASONER_*):
# the model must not answer current-info questions from stale memory —
# the decider hands them to the background assistant. The closing
# "everything else, answer yourself" is load-bearing: without it, once
# history contains one "I'll find out" the model starts deferring stable
# general-knowledge questions too (both e2e failures of the first
# migration run were "capital of France" answered with a deferral).
RESEARCH_NOTE = (
    " You also have a background research assistant with web access: "
    "when the user explicitly asks to search or look up current info (weather, news, prices), say in "
    "one short sentence that you'll find out; the answer arrives later "
    "and you can share it then. Everything else — greetings, chat, "
    "general knowledge, unchanging facts — answer directly and completely yourself from memory. "
    "Never say you will find out unless explicitly asked to search or look up."
)

# The per-utterance instruction in translate mode. Exit commands are not
# its concern: the action decider judges every utterance BEFORE this
# prompt runs (see the turn loop), so the prompt stays a pure interpreter.
TRANSLATE_PROMPT = (
    "Live translation mode: you are an interpreter, NOT a conversation partner. "
    "Begin your reply with one line: ###TRANSCRIPT: "
    "followed by the exact words the user said in this message's audio, in "
    "their original language. Then, on a new line, write ONLY the English "
    "translation or restatement of those words. Write exactly ONE sentence and STOP. "
    "Never answer questions, provide answers, or offer commentary (for example, if the user says \"Tell me about the weather today\", restate \"Tell me about the weather today\", do not answer it). "
    "If they already spoke English, restate their question or words in clear English without answering it. "
    "If the audio has no clear words, write ###TRANSCRIPT: (no speech) "
    "and nothing else."
)

# The per-utterance instruction in listen mode: a silent scribe. Exit
# detection likewise lives in the decider, keeping this prompt pure.
LISTEN_PROMPT = (
    "Quiet listening mode. The user asked you to just listen while they "
    "talk or think out loud. Begin your reply with one line: "
    "###TRANSCRIPT: followed by the exact words the user said in this "
    "message's audio. Then write NOTHING else — no reply, no commentary, "
    "no questions. If the audio has no clear words, write ###TRANSCRIPT: "
    "(no speech) and nothing else."
)

# Modes whose audio turns replace the standard respond/flush instruction
# wholesale (the mode chooses what a turn IS, not just how it's phrased).
MODE_PROMPTS = {"translate": TRANSLATE_PROMPT, "listen": LISTEN_PROMPT}

# The ring is a server-initiated turn like a delegation delivery: the
# model phrases the announcement, and if it yields nothing speakable the
# fallback IS the announcement. "System note (not user audio)" for the
# same anti-echo reason as DELIVER_PROMPT.
TIMER_PROMPT = (
    'System note (not user audio): the user\'s countdown timer "{label}" '
    "(set for {duration}) just went off. Tell them it's done in one short "
    "spoken sentence. Don't start anything new."
)
TIMER_FALLBACK = "Ding — your {label} timer is done."

# A session can only usefully run a few timers, and a runaway decision
# must not schedule endless rings; > 8h is a misread, not a timer. The
# duration itself arrives as integer seconds from the action decider —
# the model does the word-number math, in any language.
MAX_PENDING_TIMERS = 3
MAX_TIMER_S = 8 * 3600


def duration_phrase(seconds: float) -> str:
    """Exact spoken duration for timer prompts ('3 minutes', '90 seconds')
    — unlike elapsed_phrase, a timer's length is not approximate."""
    if seconds < 120:
        return f"{seconds:g} seconds"
    if seconds < 3600:
        return f"{seconds / 60:g} minutes"
    n = seconds / 3600
    return "1 hour" if n == 1 else f"{n:g} hours"

# A finished background task is delivered by the voice model, not read out
# raw: it ties the answer back to the conversation and keeps one voice.
# "System note (not user audio)" leads both prompts because the model
# occasionally misread the text-only turn as its own reply playing back
# and gave the anti-echo response instead of the answer (observed live).
DELIVER_PROMPT = (
    "System note (not user audio): your background research assistant "
    'just finished the task "{task}" (it took {took}). Its answer:\n'
    "{answer}\n\n"
    "Tell the user now: one short lead-in sentence tying it back to what "
    "they asked, then the answer itself word-for-word. Never drop or "
    "change a name, number, or place — the words above are already "
    "spoken-style. Plain spoken text."
)
DELIVER_FAILED_PROMPT = (
    "System note (not user audio): your background research assistant "
    'could not finish the task "{task}". Briefly tell the user you '
    "couldn't get that answer, and that they're welcome to ask again. "
    "Don't start new research now."
)
DELIVER_FALLBACK = "Sorry — I couldn't get an answer for that one."

# One session can only usefully consume a few pending research tasks, and
# an off-the-rails reply must not queue an HTTP call per imagined tag.
MAX_PENDING_DELEGATIONS = 3

# The transcript line LEADS the reply: transcribing after the response
# turns the transcript into a paraphrase from memory (WER 0.39 vs 0.00 on a
# clean 33-word utterance), and the leading line reaches the client while
# the response still decodes. Costs its decode time (~0.2s short / ~0.7s
# long utterances) before first audio — measured worth it. Grammar-forced
# JSON ({transcript, response}) was also measured: format breaks 1-3/3 on
# degraded audio and 3/3 on chunked — don't go back to structured output.
# The no-speech clause gives the model a sanctioned out for VAD false
# triggers (breath, cough, room noise). Without it the prompt DEMANDS
# words, so on speechless audio the model invents some — measured at
# temp 0.7: a breath came back as "Hi, can you help me with my homework?"
# (answered), "can you translate everything I say from now on?" (mode
# switched!), or an earlier turn's question copied verbatim. "this
# message's audio" (not "their audio message") points the transcription
# at the newest clip among the many in history; measured clean with this
# wording at temp 0 and 0.7 (WER 0.0 on speech, fresh and late).
NO_SPEECH_CLAUSE = (
    " If the audio has no clear words — noise, breathing, silence — write "
    "###TRANSCRIPT: (no speech) instead; never guess words or repeat "
    "earlier ones."
)

RESPOND_PROMPT = (
    "Begin your reply with one line: ###TRANSCRIPT: followed by the exact "
    "words the user said in this message's audio." + NO_SPEECH_CLAUSE +
    " Then, on a new line, respond "
    "to them: 1-4 short sentences, spoken aloud.{camera}"
)

# The clause a camera turn appends to its instruction — a named constant
# so benchmarks measure the production wording, never a retyped copy.
CAMERA_CLAUSE = " Describe the colors, shapes, and objects you see on their camera."

# Spoken when a turn yields no reply at all (models of every size
# occasionally emit only the transcript line) — silence would leave the
# user hanging, and a stored transcript-only reply teaches the model to
# do it again next turn.
FLUSH_FALLBACK = "Take your time — I'm listening."
AUDIO_FALLBACK = "Sorry, I didn't catch that — could you say it again?"

# A "flush" turn: the classifier judged the utterance unfinished, the user
# then stayed silent, so answer what we have — the model decides whether it
# is answerable or needs encouragement to continue. Dedicated prompt: with
# a bolted-on suffix the model would sometimes emit the transcript line and
# stop, leaving the turn silent.
FLUSH_PROMPT = (
    "Begin your reply with one line: ###TRANSCRIPT: followed by the exact "
    "words the user said in this message's audio." + NO_SPEECH_CLAUSE +
    " The user paused mid-thought, "
    "so on a new line: if their words feel unfinished, write one short, warm "
    "sentence encouraging them to continue; otherwise respond to them in 1-4 "
    "short sentences, spoken aloud.{camera}"
)

# A sense of elapsed time. The model can't perceive silence between
# turns, so when a real gap precedes an utterance the turn instruction
# says so — in the per-turn tail (never the system prompt: that's the
# prefix-cache prefix), and only on audio turns (a text turn's
# instruction IS the user's typed words). Coarse buckets on purpose:
# exact numbers read as data the model parrots back awkwardly.
try:
    TIME_NOTE_MIN_S = float(os.environ.get("TIME_NOTE_MIN_S", "120"))
except ValueError:
    print("TIME_NOTE_MIN_S is not a number — using 120s")
    TIME_NOTE_MIN_S = 120.0
TIME_NOTE = " (Time note: {phrase} of quiet passed before this message.)"

# The model has no clock; the start time anchors rough what-time-is-it
# awareness. Formatted ONCE at connect — never re-formatted mid-session.
SESSION_CLOCK = " This conversation started on {clock}."


def elapsed_phrase(seconds: float) -> str:
    """'a few seconds' / 'about 20 seconds' / 'about a minute' /
    'about N minutes' / 'about an hour' / 'about N hours'."""
    if seconds < 10:
        return "a few seconds"
    if seconds < 45:
        return f"about {round(seconds / 10) * 10} seconds"
    if seconds < 90:
        return "about a minute"
    if seconds < 55 * 60:
        return f"about {round(seconds / 60)} minutes"
    if seconds < 90 * 60:
        return "about an hour"
    return f"about {round(seconds / 3600)} hours"


# Rotate history before the llama context fills. Rough token estimates are
# fine here — the guard just needs to fire before generation degrades.
# Scaled to the context size: a fixed 2000 against the suite's small
# LLAMA_CTX left a near-zero threshold, rotating on every turn — history
# never accumulated, so the e2e suite silently stopped exercising
# multi-turn context at all.
CONTEXT_HEADROOM = max(512, min(2000, llama.CTX // 8))


def rotate_history(history: list) -> list:
    """Drop the oldest quarter of messages, keeping the system prompt. The
    kept slice must start on a user message: dropping a user turn while
    keeping its reply would leave an orphaned assistant message about
    words that no longer exist. A history with at most one exchange
    returns unchanged (nothing droppable — and slicing a bare [system]
    would duplicate the system prompt)."""
    if len(history) <= 3:
        return history
    keep = 1 + max(2, 3 * (len(history) - 1) // 4)
    while keep > 3 and history[-(keep - 1)].get("role") != "user":
        keep -= 1
    return [history[0]] + history[-(keep - 1):]

tts_backend = None
detector = None  # smart-turn end-of-turn classifier

# Reasoner calls block for up to REASONER_TIMEOUT — keep them off the
# default executor, which serves the latency-critical path (llama
# streaming, TTS, the turn classifier, cache priming).
REASONER_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="reasoner")


STARTUP_ERROR: str | None = None
ACTIVE_SESSION_WS: WebSocket | None = None
wellness_service: WellnessService | None = None


async def dispatch_wellness_intervention(intervention_pkg: dict) -> None:
    """Pushes a triggered micro-intervention over the active client WebSocket."""
    global ACTIVE_SESSION_WS
    if ACTIVE_SESSION_WS is not None:
        try:
            await send_json(ACTIVE_SESSION_WS, {
                "type": "intervention_triggered",
                "intervention": intervention_pkg
            })
            print(f"[WELLNESS WS] Dispatched intervention '{intervention_pkg.get('title')}' to active client.")
        except Exception as e:
            print(f"[WELLNESS WS ERROR] Failed pushing intervention: {e}")


def load_models():
    global tts_backend, detector, STARTUP_ERROR
    try:
        llama.start()
        from parlor.turn_detector import TurnDetector
        detector = TurnDetector()
        tts_backend = tts.load()
    except Exception as e:
        STARTUP_ERROR = str(e)
        print(f"[STARTUP ERROR] Model initialization failed: {e}")


@asynccontextmanager
async def lifespan(app):
    global STARTUP_ERROR, wellness_service
    try:
        await asyncio.get_event_loop().run_in_executor(None, load_models)
    except Exception as e:
        STARTUP_ERROR = str(e)
        print(f"[STARTUP ERROR] Lifespan task failed: {e}")

    # Start Phase 5 Wellness Monitoring loop on the active event loop
    try:
        wellness_service = WellnessService(
            cycle_interval_sec=8.0,
            on_intervention=dispatch_wellness_intervention
        )
        wellness_service.start()
    except Exception as e:
        print(f"[WELLNESS START ERROR] Could not initialize WellnessService: {e}")

    yield

    if wellness_service:
        wellness_service.stop()
    llama.stop()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web" / "static"), name="static")


@app.get("/")
async def root():
    html = (Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html.replace("{{model}}", llama.model_label()))


@app.get("/api/wellness/history")
async def get_wellness_history(limit: int = 50):
    """Retrieve recent affective stress assessments from local SQLite database."""
    return db.get_recent_history(limit=limit)


@app.get("/api/wellness/baseline")
async def get_wellness_baseline():
    """Retrieve personal baseline calibration status."""
    if wellness_service:
        return wellness_service.get_baseline_status()
    return {"status": "not used", "calibrated": False, "elapsed_sec": 0, "target_sec": 60}


def is_valid_frame(image_data: Any) -> bool:
    """Validate that an image frame is non-empty, valid dimensions, and non-uniform."""
    if not image_data:
        return False
    try:
        if isinstance(image_data, np.ndarray):
            img = image_data
        elif isinstance(image_data, str):
            raw_bytes = base64.b64decode(image_data)
            if len(raw_bytes) < 120:
                return False
            nparr = np.frombuffer(raw_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_data, bytes):
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return False

        if img is None:
            return False
        h, w = img.shape[:2]
        if w < 64 or h < 64:
            return False
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, stddev = cv2.meanStdDev(gray)
        if float(stddev[0][0]) < 5.0:
            # Solid color, blank frame, or placeholder screen
            return False
        return True
    except Exception as e:
        print(f"[FRAME SANITY] Frame validation error: {e}")
        return False


def turn_instruction(msg: dict, has_image: bool, has_audio: bool) -> str:
    if has_audio:
        camera = CAMERA_CLAUSE if has_image else ""
        prompt = FLUSH_PROMPT if msg.get("type") == "flush" else RESPOND_PROMPT
        return prompt.format(camera=camera)
    if has_image:
        text = msg.get("text", "").strip()
        if text:
            visual_kws = ("what do you see", "look at this", "what am i holding", "what is this", "see this", "what can you see", "describe what you see", "describe the scene", "on my camera")
            if any(kw in text.lower() for kw in visual_kws):
                return f"{text} Describe what you see on the camera."
            return text
        return "The user is showing you their camera. Describe what you see."
    return msg.get("text", "Hello!")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global ACTIVE_SESSION_WS
    await ws.accept()

    if STARTUP_ERROR:
        print(f"[WS CONNECTION REJECTED] Startup error: {STARTUP_ERROR}")
        await send_json(ws, {
            "type": "error",
            "message": f"Server startup failed: {STARTUP_ERROR}. Please check server configuration or model paths."
        })
        await ws.close(code=1011)
        return

    if ACTIVE_SESSION_WS is not None:
        print("[WS CONNECTION REJECTED] Single-session policy: another session is active.")
        await send_json(ws, {
            "type": "error",
            "message": "Another session is already active in another tab or window. Parlor supports one active session at a time."
        })
        await ws.close(code=4001, reason="Session active in another tab")
        return

    ACTIVE_SESSION_WS = ws
    try:
        await _run_session(ws)
    finally:
        if ACTIVE_SESSION_WS is ws:
            ACTIVE_SESSION_WS = None


async def _run_session(ws: WebSocket):
    # Research Mode is OFF by default to preserve strict local privacy.
    # An explicit user opt-in is required before any query text is sent to an external API.
    research_opted_in = False
    delegation = False
    clock = time.strftime("%A at %I:%M %p").replace(" 0", " ")
    system = (SYSTEM_PROMPT + SESSION_CLOCK.format(clock=clock)
              + CAPABILITY_NOTE)
    history: list = [{"role": "system", "content": system}]
    mode = MODES["conversation"]

    interrupted = asyncio.Event()
    active = {"stream": None}
    msg_queue = asyncio.Queue()

    async def receiver():
        try:
            while True:
                raw = await ws.receive_text()
                msg = json.loads(raw)
                if msg.get("type") == "interrupt":
                    interrupted.set()
                    stream = active.get("stream")
                    if stream:
                        stream.cancel()  # actually aborts generation
                    print("Client interrupted")
                else:
                    await msg_queue.put(msg)
        except DISCONNECT_ERRORS:
            pass
        finally:
            # Always unblock the main loop, even on unexpected errors.
            await msg_queue.put(None)

    recv_task = asyncio.create_task(receiver())

    frame_image: str | None = None   # camera frame held for the current utterance
    speech_chunks: list[str] = []    # streamed-in speech, already cache-primed
    held_audio: list[str] = []       # incomplete-turn segments awaiting continuation

    def remember(user_msg: dict, raw_text: str, no_speech: bool) -> None:
        """Store a finished turn verbatim (same bytes → full prefix-cache
        hit on the next request). Two kinds of turn are never stored,
        because a degenerate message poisons every later request: one the
        model produced nothing for, and a no_speech turn (the transcript
        line was a no-speech annotation or an instruction echo — no user
        words stand behind it; one stored echo loop came back as invented
        or copied user words on every turn after it). Voice turns must
        keep their raw audio: an experiment storing the transcript as
        user text instead made the model copy the PREVIOUS turn's text as
        the new turn's transcript, deterministically at temp 0 —
        user-role text reads as 'what the user said' more strongly than
        the current audio does."""
        if not raw_text.strip() or no_speech:
            return
        history.append(user_msg)
        history.append({"role": "assistant", "content": raw_text})

    delegation_ids = itertools.count(1)
    delegation_tasks: set[asyncio.Task] = set()
    ready_events: list[dict] = []  # rang/finished while the floor was busy
    timer_ids = itertools.count(1)
    pending_timers: dict[int, asyncio.Task] = {}  # id → sleeping ring task
    playing_since = {"t": 0.0}  # last spoken reply is (probably) still playing
    # When the line was last live — an exchange ending, or the user's
    # speech streaming in (so a long monologue doesn't read as a long
    # silence). The gap since it is the "quiet" the time note reports.
    last_activity = {"t": time.time()}
    prompt_tokens = {"last": 0}  # real context size, from llama-server usage

    def floor_busy() -> bool:
        """The floor is held by the user (audio held for a continuation, a
        mid-utterance chunk stream, a just-fired barge-in) or by our own
        voice: a spoken reply counts as playing until the client's 'ready'
        says playback ended — a delivery starting mid-playback would cut
        the reply off mid-sentence. The 30s staleness escape means a lost
        'ready' can only delay a result, never strand it."""
        playing = playing_since["t"] and time.time() - playing_since["t"] < 30
        return bool(held_audio or speech_chunks or interrupted.is_set() or playing)

    def drain_ready() -> None:
        """Requeue one finished background event whenever the floor frees
        up — called at every point that releases it, because msg_queue
        only wakes for client traffic and a result must not wait for one.
        Timers ring in every mode (they are user-requested alarms) while
        research results wait out translation/listening — an English
        answer must not barge into an interpreting or quiet-listening
        session — so this scans instead of popping the head: a parked
        answer must not block a timer ringing behind it."""
        if floor_busy():
            return
        for i, item in enumerate(ready_events):
            if item["type"] == "timer_done" or mode.allows_delegation:
                msg_queue.put_nowait(ready_events.pop(i))
                return

    async def switch_mode(name: str) -> bool:
        """Enter a mode by name (model tag or UI escape hatch). Unknown and
        already-current names are no-ops, so callers can pass raw values.
        Returns whether a switch happened."""
        nonlocal mode, frame_image, speech_chunks, held_audio
        name = name.strip().lower()
        if name == mode.name:
            return True  # already there — the tag "fired" in every sense
        if name not in MODES:
            # The model confirmed something out loud and then emitted junk —
            # make that diagnosable instead of a silent nothing.
            print(f"Ignoring unknown mode {name!r}")
            return False
        mode = MODES[name]
        # Start the new mode clean: a switch through the UI escape hatch can
        # fire with audio held under the OLD mode's gating, and translate
        # mode never resolves holds — stale held state would keep
        # floor_busy() true and block deliveries for the whole session.
        frame_image = None
        speech_chunks = []
        held_audio = []
        print(f"Mode → {mode.name}")
        await send_json(ws, {"type": "mode_changed", "mode": mode.name})
        drain_ready()  # leaving translation frees deferred deliveries
        return True

    async def run_delegation(task_id: int, task: str) -> None:
        """Background reasoner call; its outcome re-enters the main loop
        through msg_queue so delivery is serialized with real turns."""
        t0 = time.time()
        try:
            answer = await asyncio.get_event_loop().run_in_executor(
                REASONER_POOL, reasoner.ask, task)
            # Clamp a verbose answer: it is interpolated into the delivery
            # prompt and stored in history under a small LLAMA_CTX.
            if len(answer) > 1500:
                answer = answer[:1500].rsplit(". ", 1)[0] + "."
            outcome = {"ok": True, "answer": answer}
        except Exception as e:
            print(f"Delegation #{task_id} failed: {e}")
            outcome = {"ok": False, "answer": ""}
        await msg_queue.put({"type": "delegation_done", "id": task_id,
                             "task": task, "took_s": round(time.time() - t0, 1),
                             **outcome})

    async def spawn_delegation(task: str) -> None:
        """Hand one research task to the background reasoner. Guards stay
        from the tag era: a fragment task gives the reasoner nothing to
        work with, and a runaway decision must not queue an HTTP call per
        imagined task."""
        if not delegation or not mode.allows_delegation:
            return
        task_words = [w for w in re.split(r"[\s_]+", task) if w]
        if len(task_words) < 3:
            print(f"Delegation skipped (fragment): {task!r}")
            return
        if len(delegation_tasks) >= MAX_PENDING_DELEGATIONS:
            print(f"Delegation skipped (cap {MAX_PENDING_DELEGATIONS}): {task!r}")
            return
        task_id = next(delegation_ids)
        print(f"Delegation #{task_id}: {task!r}")
        await send_json(ws, {"type": "delegation_started",
                             "id": task_id, "task": task})
        t = asyncio.create_task(run_delegation(task_id, task))
        delegation_tasks.add(t)
        t.add_done_callback(delegation_tasks.discard)

    async def proactive_turn(prompt: str, fallback: str) -> None:
        """A server-initiated turn — a delegation delivery or a timer ring:
        the model phrases it, TTS speaks it, and history keeps it like any
        real turn. expect_transcript=True although there is no audio: the
        model often opens one with an imitated ###TRANSCRIPT: line, and the
        transcript parser consumes it and streams the real reply; with
        False the ##-markup cut would swallow the whole thing (observed
        live). Nothing server-initiated ever acts: the action decider only
        judges real user turns."""
        user_msg = {"role": "user", "content": [text_part(prompt)]}
        raw_text, pt, _, spoke = await run_turn(
            ws, history + [user_msg], interrupted, active, tts_backend,
            expect_transcript=True, tts_voice=mode.tts_voice,
            proactive=True, fallback=fallback)
        if pt:
            prompt_tokens["last"] = pt
        if spoke:
            playing_since["t"] = time.time()  # this reply is now playing
        remember(user_msg, raw_text, no_speech=False)
        last_activity["t"] = time.time()
        drain_ready()         # more background events may already be waiting

    async def deliver_delegation(done: dict) -> None:
        """A finished research task, spoken by the voice model. Failures are
        delivered too — a delegation must never end in silence, which is
        also why the fallback is the reasoner's own answer: if the model's
        relay yields nothing speakable (##-markup relapse, transcript-only
        reply), TTS speaks the answer directly."""
        interrupted.clear()
        await send_json(ws, {"type": "delegation_resolved",
                             "id": done["id"], "ok": done["ok"]})
        prompt = (DELIVER_PROMPT if done["ok"] else DELIVER_FAILED_PROMPT).format(
            task=done["task"], answer=done["answer"],
            took=elapsed_phrase(done.get("took_s", 0.0)))
        await proactive_turn(
            prompt, done["answer"] if done["ok"] else DELIVER_FALLBACK)

    async def run_timer(timer_id: int, label: str, seconds: float) -> None:
        """Sleep out the countdown, then re-enter the main loop through
        msg_queue so the ring is serialized with real turns. Cancellation
        during the sleep enqueues nothing."""
        await asyncio.sleep(seconds)
        await msg_queue.put({"type": "timer_done", "id": timer_id,
                             "label": label, "seconds": seconds})

    async def spawn_timer(seconds: int, label: str) -> None:
        """Schedule one countdown from the action decision."""
        if seconds > MAX_TIMER_S:
            print(f"Timer skipped (over {MAX_TIMER_S // 3600}h cap): {seconds}s")
            return
        if len(pending_timers) >= MAX_PENDING_TIMERS:
            print(f"Timer skipped (cap {MAX_PENDING_TIMERS}): {label!r}")
            return
        timer_id = next(timer_ids)
        label = label or "timer"
        print(f"Timer #{timer_id}: {seconds}s {label!r}")
        pending_timers[timer_id] = asyncio.create_task(
            run_timer(timer_id, label, seconds))
        await send_json(ws, {"type": "timer_started", "id": timer_id,
                             "label": label, "seconds": seconds})

    async def apply_decision(decision) -> None:
        """Fire what the decider found. Timers/research fire when the
        turn is conversational at EITHER end of a mode transition: a
        plain conversation turn, or a listen/translate exit whose same
        breath asks for more ("okay, I'm done — set a twenty-minute
        timer": the exit turn confirms it aloud, so dropping it would be
        a spoken promise with no action — review finding). A mention
        mid-translate/listen without an exit stays content. Ordering
        keeps spawn_delegation's allows_delegation gate live: entries
        spawn before the switch, exits switch first."""
        if mode.name == "conversation":
            if decision.timer:
                await spawn_timer(*decision.timer)
            if decision.research:
                await spawn_delegation(decision.research)
            if decision.mode:
                await switch_mode(decision.mode)
            return
        if decision.mode:
            await switch_mode(decision.mode)
        if mode.name == "conversation":  # exited just now
            if decision.timer:
                await spawn_timer(*decision.timer)
            if decision.research:
                await spawn_delegation(decision.research)

    async def deliver_timer(done: dict) -> None:
        """The ring. Its label and duration ride the event, not the pending
        entry, so popping it is only about not ringing twice."""
        if pending_timers.pop(done["id"], None) is None:
            return  # cancelled after it fired
        interrupted.clear()
        await send_json(ws, {"type": "timer_resolved", "id": done["id"]})
        prompt = TIMER_PROMPT.format(label=done["label"],
                                     duration=duration_phrase(done["seconds"]))
        await proactive_turn(prompt, TIMER_FALLBACK.format(label=done["label"]))

    async def prime(audio_b64s: list[str]) -> None:
        """Warm the cache for the turn as it stands so far — reads the live
        history and held camera frame, so it must stay in this scope."""
        await prime_cache(history + [
            {"role": "user", "content": user_content(frame_image, audio_b64s)}])

    try:
        while True:
            msg = await msg_queue.get()
            if msg is None:
                break

            mtype = msg.get("type") or "audio_turn"
            if mtype != "speech_chunk":
                print(f"[STAGE 2] [WS RECV] type={mtype!r}, mode={mode.name!r}, msg_keys={list(msg.keys())}")

            # Rotate history before the llama context fills: keep the system
            # prompt and the most recent exchanges. The REAL count from the
            # last request wins over the estimate — when the estimate
            # undershoots (camera turns), llama-server silently truncates
            # the oldest turns first, which reads as the model "forgetting".
            # Double headroom because the incoming turn isn't counted yet;
            # drop a quarter (not half) so a rotation is barely noticeable.
            est = estimate_tokens(history)
            used = max(est, prompt_tokens["last"])
            if used > llama.CTX - 2 * CONTEXT_HEADROOM:
                rotated = rotate_history(history)
                if len(rotated) < len(history):
                    print(f"Context near limit (est {est}, real {prompt_tokens['last']}) "
                          f"— dropping {len(history) - len(rotated)} oldest messages")
                    history = rotated
                    prompt_tokens["last"] = 0  # stale after a rotation

            if msg.get("type") == "ready":
                # The client returned to idle listening: playback finished,
                # or a false barge-in never became an utterance. A sticky
                # interrupted flag must not strand queued deliveries — and
                # the client cleared its own frame-discard flag before
                # sending this, so delivering now is safe.
                if playing_since["t"] > 0.0:
                    last_activity["t"] = time.time()
                playing_since["t"] = 0.0
                interrupted.clear()
                drain_ready()
                continue

            if msg.get("type") == "set_mode":
                # The UI escape hatch (mode chip's stop button): a switch
                # that must work even when the model mistranslates the
                # spoken exit command.
                await switch_mode(str(msg.get("mode", "")))
                continue

            if msg.get("type") == "delegation_done":
                if not mode.allows_delegation:
                    # Parked until the user exits translation/listening —
                    # tell the client so its chip stops implying work in
                    # progress.
                    await send_json(ws, {"type": "delegation_parked",
                                         "id": msg["id"]})
                    ready_events.append(msg)
                    continue
                if floor_busy():
                    ready_events.append(msg)  # deliver at the next idle moment
                    continue
                try:
                    await deliver_delegation(msg)
                except DISCONNECT_ERRORS:
                    raise
                except Exception:
                    traceback.print_exc()  # keep the session alive
                    if not msg.get("redelivered"):
                        msg["redelivered"] = True  # one more try at idle
                        ready_events.append(msg)
                    await release_client(ws)
                continue

            if msg.get("type") == "timer_done":
                if msg["id"] not in pending_timers:
                    continue  # cancelled after it fired
                if floor_busy():
                    ready_events.append(msg)  # ring at the next idle moment
                    continue
                try:
                    await deliver_timer(msg)
                except DISCONNECT_ERRORS:
                    raise
                except Exception:
                    traceback.print_exc()  # keep the session alive
                    pending_timers.pop(msg["id"], None)  # no re-ring
                    await release_client(ws)
                continue

            if msg.get("type") == "cancel_timer":
                # The chip's ✕ — like set_mode, a UI action that must work
                # regardless of what the model believes.
                task = pending_timers.pop(msg.get("id"), None)
                if task:
                    task.cancel()
                    ready_events[:] = [e for e in ready_events
                                       if not (e["type"] == "timer_done"
                                               and e["id"] == msg["id"])]
                    print(f"Timer #{msg['id']} cancelled")
                    await send_json(ws, {"type": "timer_resolved",
                                         "id": msg["id"], "cancelled": True})
                continue

            if msg.get("type") == "get_system_status":
                is_llama_up = llama.is_healthy(timeout=0.8)
                model_name = llama.model_label()
                build_info = "offline"
                if is_llama_up:
                    try:
                        conn = llama._connect(timeout=0.8)
                        conn.request("GET", "/props")
                        resp = conn.getresponse()
                        if resp.status == 200:
                            props = json.loads(resp.read().decode())
                            build_num = props.get("build_number") or props.get("version")
                            build_info = f"b{build_num}" if build_num else "online"
                        else:
                            build_info = "online"
                        conn.close()
                    except Exception:
                        build_info = "online"
                else:
                    build_info = "offline"

                baseline_data = wellness_service.get_baseline_status() if wellness_service else {"status": "not used", "calibrated": False}
                await send_json(ws, {
                    "type": "system_status",
                    "model_ready": is_llama_up,
                    "model_name": f"{model_name} ({build_info})",
                    "schema_valid": True,
                    "schema_version": "Diagnostics schema v1.0",
                    "baseline_active": baseline_data.get("calibrated", False),
                    "baseline_mode": baseline_data.get("status", "calibrating (0/60 s)"),
                    "private_on_device": True,
                    "research_opt_in": bool(research_opted_in),
                    "research_configured": reasoner.enabled()
                })
                continue

            if msg.get("type") == "set_wellness_sensitivity":
                sens = str(msg.get("sensitivity", "balanced"))
                if wellness_service:
                    wellness_service.set_sensitivity(sens)
                await send_json(ws, {"type": "wellness_sensitivity_changed", "sensitivity": sens})
                continue

            if msg.get("type") == "set_wellness_mute":
                muted = bool(msg.get("muted", False))
                if wellness_service:
                    wellness_service.set_muted(muted)
                await send_json(ws, {"type": "wellness_mute_changed", "muted": muted})
                continue

            if msg.get("type") == "snooze_wellness":
                mins = float(msg.get("minutes", 10.0))
                if wellness_service:
                    wellness_service.snooze(mins)
                await send_json(ws, {"type": "wellness_snoozed", "minutes": mins})
                continue

            if msg.get("type") == "set_concurrency_mitigation":
                mitigated = bool(msg.get("enabled", True))
                if wellness_service:
                    wellness_service.concurrency_mitigation_enabled = mitigated
                await send_json(ws, {"type": "concurrency_mitigation_changed", "enabled": mitigated})
                continue

            if msg.get("type") == "set_research_opt_in":
                opt_in = bool(msg.get("enabled", False))
                is_configured = reasoner.enabled()
                research_opted_in = opt_in and is_configured
                delegation = research_opted_in
                clock = time.strftime("%A at %I:%M %p").replace(" 0", " ")
                system = (SYSTEM_PROMPT + SESSION_CLOCK.format(clock=clock)
                          + CAPABILITY_NOTE + (RESEARCH_NOTE if delegation else ""))
                if history and history[0].get("role") == "system":
                    history[0]["content"] = system
                print(f"[RESEARCH MODE] User opt-in {'ENABLED' if delegation else 'DISABLED'} "
                      f"(configured={is_configured})")
                await send_json(ws, {"type": "research_opt_in_changed",
                                     "enabled": delegation,
                                     "configured": is_configured})
                continue

            if msg.get("type") == "set_demo_mode":
                demo_enabled = bool(msg.get("enabled", False))
                if wellness_service:
                    wellness_service.demo_mode = demo_enabled
                print(f"[DEMO MODE] Simulated stress injection {'ENABLED' if demo_enabled else 'DISABLED'}")
                await send_json(ws, {"type": "demo_mode_changed", "enabled": demo_enabled})
                continue

            if msg.get("type") == "test_wellness_cycle":
                is_sim = bool(msg.get("is_simulated", False) or (wellness_service and getattr(wellness_service, "demo_mode", False)))
                if is_sim:
                    print("[STAGE 2] [SIMULATED INPUT] Processing demo-mode stress vector (is_simulated=True).")
                else:
                    print("[TEST CYCLE] Received test_wellness_cycle request")
                vector = msg.get("vector")
                prompt_used = None
                if vector and wellness_service:
                    prompt_used = wellness_service.fusion_engine.format_prompt(vector)
                    print("[TEST CYCLE] Invoking live SLM reasoning...")
                    slm_input = await wellness_service._call_slm_reasoning(prompt_used)
                    print(f"[TEST CYCLE] SLM result: {slm_input.get('stress_level')}")
                else:
                    slm_input = msg.get("slm_output", {
                        "stress_level": "High (Tier 2)",
                        "primary_drivers": ["AU04 Brow Furrow=0.92", "Pitch Delta=+65Hz"],
                        "explainable_reasoning": "Sustained high facial strain and severe acoustic frequency perturbation.",
                        "confidence_score": 0.95,
                        "ambiguity_note": None
                    })
                if wellness_service:
                    should_fire, category, meta = wellness_service.trigger_manager.evaluate(slm_input)
                    if is_sim:
                        meta["simulated"] = True
                    intervention_pkg = None
                    if should_fire:
                        intervention_pkg = wellness_service.intervention_generator.generate(category, slm_input)
                        if is_sim:
                            intervention_pkg["is_simulated"] = True
                        await dispatch_wellness_intervention(intervention_pkg)
                    resp = {
                        "type": "test_wellness_cycle_result",
                        "consecutive_count": wellness_service.trigger_manager.consecutive_high_stress_count,
                        "should_fire": should_fire,
                        "intervention_fired": intervention_pkg is not None,
                        "metadata": meta,
                        "slm_output": slm_input,
                        "prompt": prompt_used,
                        "is_simulated": is_sim
                    }
                    print("[TEST CYCLE] Sending response back to client...")
                    await send_json(ws, resp)
                    print("[TEST CYCLE] Response successfully sent!")
                continue

            if msg.get("type") == "wellness_telemetry":
                if msg.get("image") and wellness_service:
                    wellness_service.feed_frame(msg["image"])
                    face_snap = wellness_service.get_face_snapshot()
                    if face_snap:
                        await send_json(ws, {"type": "wellness_face_metrics", "face": face_snap})
                if msg.get("audio") and valid_audio(msg.get("audio")) and wellness_service:
                    try:
                        wellness_service.feed_audio(wav_to_float32(msg["audio"]))
                        vocal_snap = wellness_service.get_vocal_snapshot()
                        if vocal_snap:
                            await send_json(ws, {"type": "wellness_vocal_metrics", "vocal": vocal_snap})
                    except Exception:
                        pass
                continue

            if msg.get("type") == "frame":
                if msg.get("image") and is_valid_frame(msg["image"]):
                    if wellness_service:
                        wellness_service.feed_frame(msg["image"])
                        face_snap = wellness_service.get_face_snapshot()
                        if face_snap:
                            await send_json(ws, {"type": "wellness_face_metrics", "face": face_snap})
                    if mode.wants_camera:
                        frame_image = msg["image"]
                        speech_chunks = []
                        await prime(held_audio)
                else:
                    frame_image = None
                continue

            if msg.get("type") == "speech_chunk":
                if msg.get("seq") == 0:
                    speech_chunks = []
                if valid_audio(msg.get("audio")):
                    speech_chunks.append(msg["audio"])
                    last_activity["t"] = time.time()
                    if wellness_service:
                        wellness_service.set_voice_active(True)
                        try:
                            wellness_service.feed_audio(wav_to_float32(msg["audio"]))
                            vocal_snap = wellness_service.get_vocal_snapshot()
                            if vocal_snap:
                                await send_json(ws, {"type": "wellness_vocal_metrics", "vocal": vocal_snap})
                        except Exception:
                            pass
                    await prime(held_audio + speech_chunks)
                continue

            interrupted.clear()
            audio_b64s = held_audio + (speech_chunks if msg.get("chunked") else [])
            speech_chunks = []
            if valid_audio(msg.get("audio")):
                audio_b64s.append(msg["audio"])
                if wellness_service:
                    try:
                        wellness_service.feed_audio(wav_to_float32(msg["audio"]))
                    except Exception:
                        pass

            candidate_image = msg.get("image") or frame_image
            if candidate_image and is_valid_frame(candidate_image) and mode.wants_camera:
                image = candidate_image
                if wellness_service:
                    wellness_service.feed_frame(image)
            else:
                image = None
                frame_image = None

            has_audio = bool(audio_b64s)
            if not has_audio and msg.get("text") and image:
                visual_kws = ("what do you see", "look at this", "what am i holding", "what is this", "see this", "what can you see", "describe what you see", "describe the scene", "on my camera")
                if not any(kw in msg["text"].lower() for kw in visual_kws):
                    image = None
            is_flush = msg.get("type") == "flush"
            print(f"[STAGE 2] [AUDIO VALIDATION] audio_b64s_count={len(audio_b64s)}, valid_raw_audio={valid_audio(msg.get('audio'))}, has_audio={has_audio}")

            if not has_audio and not image and not msg.get("text"):
                print(f"[STAGE 2] [NO MEDIA REJECTED] Releasing client (empty/short audio)")
                await release_client(ws)
                drain_ready()  # the floor is provably free here
                continue

            # From here on any failure (malformed WAV included — valid_audio
            # only checks length) must release the client, not kill the
            # session loop.
            p_complete = None  # smart-turn probability, surfaced in the UI
            print(f"[SERVER TURN START] mode={mode.name!r}, has_audio={has_audio}, uses_smart_turn={mode.uses_smart_turn}")
            if wellness_service:
                wellness_service.set_voice_active(True)
            try:
                # The audio classifier judges completeness before the LLM is
                # involved at all. Incomplete → hold the segments (they stay
                # in the next turn's content AND warm in the cache) and wait.
                # A flush turn skips the check: the client waited out the
                # hold and now wants an answer to whatever we have. Translate
                # mode skips it entirely — an interpreter renders on a short
                # silence, it does not wait out thinking pauses.
                if has_audio and not is_flush and mode.uses_smart_turn:
                    pcm = np.concatenate([wav_to_float32(b) for b in audio_b64s])
                    print(f"[STAGE 3] [TURN DETECTOR START] pcm_samples={len(pcm)} ({len(pcm)/16000:.2f}s)")
                    t0 = time.time()
                    complete, prob = await asyncio.get_event_loop().run_in_executor(
                        None, detector.predict, pcm)
                    decision_s = round(time.time() - t0, 3)
                    p_complete = round(prob, 2)
                    if not complete and not interrupted.is_set():
                        print(f"[STAGE 3] [TURN INCOMPLETE] p(complete)={p_complete:.2f} <= 0.50 -> holding audio & returning turn_incomplete to client")
                        held_audio = audio_b64s
                        await send_json(ws, {
                            "type": "turn_incomplete",
                            "decision_s": decision_s, "p_complete": p_complete,
                        })
                        await prime(held_audio)
                        continue
                    else:
                        print(f"[STAGE 3] [TURN COMPLETE] p(complete)={p_complete:.2f} > 0.50 -> proceeding to LLM")

                print(f"[STAGE 4] [PIPELINE HANDOFF] Preparing user_msg & instruction for LLM turn")

                # Padding the final segment diverges it from its primed bytes
                # on flush turns (≤3s re-prefilled) — the honest-transcript
                # win beats that; the continuation path keeps its cache hits.
                if audio_b64s:
                    audio_b64s[-1] = pad_tail_silence(audio_b64s[-1])
                content = user_content(image, audio_b64s)
                frame_image = None
                held_audio = []

                # When the decision runs is a latency choice. Conversation
                # and translate turns speak FIRST and decide after, hidden
                # under TTS playback — an interpreter must start rendering
                # immediately, so a translated exit command gets rendered
                # once and THEN the switch lands (the vanishing chip is
                # the confirmation). Listen turns decide BEFORE: they play
                # nothing (the ~2s only delays the on-screen transcript),
                # and an exit ("what do you think?") must be ANSWERED, not
                # silently transcribed — the decision picks the prompt.
                # Either way a decision FIRES only after the turn, gated
                # on no_speech/interrupt like always.
                decision = actions.NONE
                pre_decided = mode.name == "listen" and has_audio
                if pre_decided:
                    decision = await asyncio.get_event_loop().run_in_executor(
                        None, actions.decide_before, history, content, mode.name)
                if pre_decided and decision.mode:
                    # Addressed to the assistant (an exit command): answer
                    # it as a normal conversation turn, not as content.
                    instruction = RESPOND_PROMPT.format(camera="")
                elif mode.name in MODE_PROMPTS and has_audio:
                    instruction = MODE_PROMPTS[mode.name]
                else:
                    instruction = turn_instruction(msg, bool(image), has_audio)
                # Elapsed quiet, and whether a silent turn gets a spoken
                # line, are per-mode policy — see modes.py for the whys.
                gap = time.time() - last_activity["t"]
                if has_audio and mode.wants_time_note and gap >= TIME_NOTE_MIN_S:
                    phrase = elapsed_phrase(gap)
                    instruction += TIME_NOTE.format(phrase=phrase)
                    print(f"Time note: {phrase}")
                if has_audio and decision.mode:
                    fallback = AUDIO_FALLBACK  # an exit turn must speak
                elif has_audio and not mode.speaks_fallback:
                    fallback = None       # a listen turn is MEANT to end silent
                elif is_flush:
                    fallback = FLUSH_FALLBACK
                elif has_audio:
                    fallback = AUDIO_FALLBACK
                else:
                    fallback = None       # no transcript line to stop short at
                user_msg = {"role": "user", "content": content + [text_part(instruction)]}
                try:
                    raw_text, pt, no_speech, spoke = await run_turn(
                        ws, history + [user_msg], interrupted, active,
                        tts_backend, expect_transcript=has_audio,
                        p_complete=p_complete,
                        tts_voice=mode.tts_voice,
                        fallback=fallback,
                        suppress_speech=(mode.name == "listen" and not bool(decision.mode)))
                except llama.LLAMAServerError as err:
                    print(f"[LLM SERVER ERROR] {err}")
                    await send_json(ws, {
                        "type": "error",
                        "message": f"Assistant engine error: {err}. Please check server logs."
                    })
                    await release_client(ws)
                    playing_since["t"] = 0.0
                    held_audio = []
                    speech_chunks = []
                    continue
                if pt:
                    prompt_tokens["last"] = pt
                if spoke:
                    playing_since["t"] = time.time()  # reply now playing client-side
                if (not pre_decided or not decision.mode) and not no_speech and not interrupted.is_set() \
                        and (has_audio or msg.get("text")):
                    decision = await asyncio.get_event_loop().run_in_executor(
                        None, actions.decide_after,
                        history + [user_msg,
                                   {"role": "assistant", "content": raw_text}],
                        mode.name)
                if no_speech or interrupted.is_set():
                    # No user words stand behind this turn (a breath once
                    # "asked" to translate everything — measured live), or
                    # the user cut it off: nothing may act.
                    decision = actions.NONE
                await apply_decision(decision)
                remember(user_msg, raw_text, no_speech)
                last_activity["t"] = time.time()
                print(f"[SERVER TURN END] mode={mode.name!r}, spoke={spoke}, no_speech={no_speech}")
            except DISCONNECT_ERRORS:
                raise
            except Exception:
                traceback.print_exc()  # keep the session alive
                await release_client(ws)
            finally:
                if wellness_service:
                    wellness_service.set_voice_active(False)

            # A result that finished while the floor was busy delivers now.
            drain_ready()
    except DISCONNECT_ERRORS:
        print("Client disconnected")
    finally:
        recv_task.cancel()
        for t in delegation_tasks:
            t.cancel()
        for t in pending_timers.values():
            t.cancel()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    # localhost, not 0.0.0.0: browsers treat http://localhost as a secure
    # context but not http://0.0.0.0, and without one getUserMedia (mic,
    # camera) doesn't exist.
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
