"""The action decider: what the user asked the assistant to DO, decided by
a separate grammar-forced JSON request instead of in-band control tags.

Why a second request (benchmarks/archbench.py, e4b, 19 spoken cases x 2):
in-band tags scored recall 0.955 with the miss being an ack-without-action
("I will be quiet", no tag) — a spoken promise the server never keeps,
the worst failure a voice assistant has. The decoupled head scored recall
1.0, its only error an unwanted-but-cancellable timer misfire (0.062).
Structurally, the head can never leak into speech (there is nothing to
excise), runs at temperature 0 while speech keeps its sampling
temperature, sees the model's own confirmation as evidence, and does the
duration math itself ("twenty minutes" → 1200) in any language. History
stays pure speech — no stored tag can teach the model a state the server
isn't in.

Cost: the head decodes ~35 JSON tokens over the cached prefix (~2s GPU on
e4b, hidden under TTS playback), every turn. A cheaper 1-token yes/no
pre-gate was measured (archbench B_gated): its recall is a perfect 1.0,
but it answers "yes" on nearly every turn — including "how are you" —
so it adds ~0.9s and then runs the head anyway. Not worth its
complexity; revisit only if per-turn GPU cost shows up in practice.

The head must run on the SAME llama-server as speech: a separate model
would pay full prefill of history + audio every turn — the shared prefix
cache is what makes deciding cheap.
"""

import json
from dataclasses import dataclass

from parlor import llama

# One prompt per session mode: the head must know what "no change" means
# ("conversation" reported while already conversing is state, not an
# action) and, mid-translation/listening, what an exit command sounds
# like. The listen wording carries the clearly-ask-YOU nuance measured in
# the e2e suite: a think-aloud quasi-question ("the thing I wanted to ask
# you about is…") is still thinking, not an exit.
_HEAD_COMMON = (
    "Do not think or reason. Immediately output the JSON action.\n"
    "System note (not user audio): you are the action decider. From the "
    "user's last message (the assistant's reply above may help), report "
    "what the user asked the assistant to DO, as JSON. timer_seconds: "
    "the countdown duration in seconds if they asked for a timer or a "
    "timed reminder, else 0 — asking the assistant to be quiet for some "
    "time is a mode request, never a timer. timer_label: a "
    "two-or-three-word label for it, else empty. {mode_clause} "
    "research_task: if they asked to "
    "search, look up, or research something, or asked about anything "
    "current or changing (weather, news, prices, scores, openings, "
    "\"right now\", \"today\"), the task restated to stand alone, else "
    "empty. A duration or topic merely mentioned in passing is NOT a "
    "request: report an action only when the user asked for it."
)
_MODE_CLAUSES = {
    "conversation": (
        "mode: 'translate' if the user asked to translate what they say (e.g. 'translate everything I say', 'translate from now on', 'translate into English'), "
        "'listen' if they asked the assistant to just listen quietly, be quiet, or stop responding, "
        "otherwise 'none'."),
    "translate": (
        "mode: 'conversation' if the user's words ask to stop translating or go back to normal conversation, "
        "else 'none'."),
    "listen": (
        "mode: 'conversation' if the user indicates they are done thinking out loud, wants to stop listening, "
        "or asks the assistant to speak/respond (e.g. 'I\'m done', 'what do you think', 'stop listening'), "
        "else 'none'."),
}
HEAD_SCHEMA = {
    "type": "object",
    "properties": {
        "timer_seconds": {"type": "integer"},
        "timer_label": {"type": "string"},
        "mode": {"type": "string",
                 "enum": ["none", "translate", "listen", "conversation"]},
        "research_task": {"type": "string"},
    },
    "required": ["timer_seconds", "timer_label", "mode", "research_task"],
}


@dataclass(frozen=True)
class ActionDecision:
    """What the user asked for, typed. None/empty means 'nothing'."""
    timer: tuple[int, str] | None = None   # (seconds, label)
    mode: str | None = None                # target mode, already ≠ current
    research: str | None = None            # self-contained task

    def any(self) -> bool:
        return bool(self.timer or self.mode or self.research)


NONE = ActionDecision()


def decide_after(messages: list, current_mode: str) -> ActionDecision:
    """Judge a finished conversation turn (blocking — run in an executor)."""
    last_user = ""
    assistant_reply = ""
    for m in reversed(messages):
        if not assistant_reply and m.get("role") == "assistant":
            assistant_reply = str(m.get("content", ""))
        elif not last_user and m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                parts = [p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"]
                last_user = " ".join(parts).strip()
            else:
                last_user = str(c or "")
        if last_user and assistant_reply:
            break

    if "###TRANSCRIPT:" in assistant_reply:
        parts = assistant_reply.split("###TRANSCRIPT:", 1)[1]
        if "\n" in parts:
            t, r = parts.split("\n", 1)
            if t.strip() and "(no speech)" not in t.lower():
                last_user = t.strip()
            assistant_reply = r.strip()
        else:
            if parts.strip() and "(no speech)" not in parts.lower():
                last_user = parts.strip()
            assistant_reply = ""

    clause = _MODE_CLAUSES[current_mode]
    head_prompt = (
        "System note (not user audio): you are the action decider. Given the conversation turn below, "
        "report what action the user asked the assistant to DO, as JSON.\n\n"
        f"User: {last_user}\n"
        f"Assistant: {assistant_reply}\n\n"
        f"{clause} "
        "timer_seconds: countdown in seconds if asked for a timer, else 0. "
        "timer_label: a two-or-three-word label, else empty string. "
        "research_task: if the user explicitly asked to search the web, look up, or research current or changing info (like today's weather, stock prices, news, scores), the task restated. Stable general knowledge and unchanging facts (such as 'what is the capital of France', greetings, chat) are NOT research: for those, research_task MUST be empty string."
    )
    return _decide(lambda _: [{"role": "user", "content": head_prompt}], current_mode)


def decide_before(history: list, content: list, current_mode: str) -> ActionDecision:
    """Judge an utterance BEFORE any reply exists (blocking). Used in
    translate/listen, where what the reply IS depends on the decision
    (content to render, or a command to the assistant)."""
    if current_mode == "listen":
        prompt = (
            "Do not think or reason. Immediately output the JSON action.\n"
            "System note (not user audio): you are the action decider in 'listen' mode.\n"
            "1. If the user indicates they are done thinking, finished talking, asks what you think, asks for feedback, or tells you to stop listening "
            "(e.g. 'I'm done thinking out loud. What do you think about all of that?', 'What do you think?', 'Stop listening', 'I\\'m done'), you MUST output mode: 'conversation'.\n"
            "2. Otherwise, if the user is just monologuing, telling a story, or speaking casually without addressing you (e.g. talking about pets, sourdough, colors, recipes), output mode: 'none'.\n"
            "timer_seconds: 0. timer_label: \"\". research_task: \"\"."
        )
        def build_listen(p: str) -> list:
            text = {"type": "text", "text": p}
            return history + [{"role": "user", "content": content + [text]}]
        try:
            raw = llama.chat_blocking(build_listen(prompt), max_tokens=512,
                                      temperature=0.0, json_schema=HEAD_SCHEMA)
            print(f"[decide_before listen raw output]: {raw}")
            cleaned = raw[raw.find("{"):raw.rfind("}") + 1] if "{" in raw and "}" in raw else raw
            head = json.loads(cleaned)
            mode = "conversation" if head.get("mode") == "conversation" else None
            return ActionDecision(mode=mode)
        except Exception as e:
            print(f"decide_before listen failed: {e}")
            return NONE

    def build(prompt: str) -> list:
        text = {"type": "text", "text": prompt}
        return history + [{"role": "user", "content": content + [text]}]
    return _decide(build, current_mode)


def _decide(build, current_mode: str) -> ActionDecision:
    """One grammar-forced head call. Failures return NONE: a lost
    decision is a no-op turn, never an exception in the turn loop."""
    try:
        head_prompt = _HEAD_COMMON.format(mode_clause=_MODE_CLAUSES[current_mode])
        # max_tokens must clear the JSON skeleton (~30 tokens) PLUS a long
        # restated research task — truncated JSON fails json.loads and
        # silently drops an action the reply already promised (review
        # finding). The grammar bounds the shape, so the cap is generous.
        raw = llama.chat_blocking(build(head_prompt), max_tokens=512,
                                  temperature=0.0, json_schema=HEAD_SCHEMA)
        print(f"[_decide raw output] current_mode={current_mode}: {raw}")
        cleaned = raw[raw.find("{"):raw.rfind("}") + 1] if "{" in raw and "}" in raw else raw
        head = json.loads(cleaned)
    except Exception as e:
        print(f"Action decider failed: {e}")
        return NONE
    timer = None
    seconds = head.get("timer_seconds") or 0
    if isinstance(seconds, int) and seconds > 0:
        timer = (seconds, str(head.get("timer_label", "")).strip())
    target = head.get("mode")
    # Mid-translate/listen the only sanctioned transition is OUT — the
    # clauses ask only about exits, so any other target is a misread
    # (a phantom listen→translate jump would answer aloud mid-listen).
    allowed = (("translate", "listen", "conversation")
               if current_mode == "conversation" else ("conversation",))
    mode = target if target in allowed and target != current_mode else None
    research = str(head.get("research_task", "")).strip() or None
    decision = ActionDecision(timer=timer, mode=mode, research=research)
    if decision.any():
        print(f"Action decision: {decision}")
    return decision
