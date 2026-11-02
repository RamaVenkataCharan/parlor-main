"""Full Trigger Test: Verifies that in Balanced mode (N=3 cycles, 300s cooldown),
an intervention card actually fires through the live /ws connection.
"""
import asyncio
import json
import time
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_FILE = ROOT / "evidence" / "live_ws_intervention_trigger.json"


async def main():
    uri = "ws://127.0.0.1:8000/ws"
    print("=" * 75)
    print(" LIVE WEBSOCKET BALANCED MODE INTERVENTION TRIGGER TEST")
    print(f" Connecting to: {uri}")
    print("=" * 75)

    log_data = {
        "timestamp": time.time(),
        "mode": "balanced",
        "consecutive_required": 3,
        "cooldown_sec": 300.0,
        "cycles": []
    }

    async with websockets.connect(uri) as ws:
        # Step 1: Set sensitivity to balanced
        print("\n[STEP 1] Setting sensitivity mode to 'balanced'...")
        await ws.send(json.dumps({"type": "set_wellness_sensitivity", "sensitivity": "balanced"}))
        resp = json.loads(await ws.recv())
        assert resp["type"] == "wellness_sensitivity_changed" and resp["sensitivity"] == "balanced"
        print("  -> Confirmed: sensitivity mode is 'balanced' (N=3, cooldown=300s)")

        slm_test_high = {
            "stress_level": "High (Tier 2)",
            "primary_drivers": ["AU04 Brow Furrow=0.95", "Vocal Tension=0.88", "Pitch Delta=+68Hz"],
            "explainable_reasoning": "Severe sustained brow furrow and high vocal acoustic tension indicating acute stress.",
            "confidence_score": 0.95,
            "ambiguity_note": None
        }

        # Step 2: Cycle 1 (Consecutive = 1)
        print("\n[STEP 2] Injecting Cycle 1 (Tier 2)...")
        await ws.send(json.dumps({"type": "test_wellness_cycle", "slm_output": slm_test_high}))
        r1 = json.loads(await ws.recv())
        print(f"  Cycle 1 result: consecutive_count={r1['consecutive_count']}, should_fire={r1['should_fire']}")
        assert r1["consecutive_count"] == 1
        assert r1["should_fire"] is False
        log_data["cycles"].append({"cycle": 1, "response": r1, "intervention_received": False})

        # Step 3: Cycle 2 (Consecutive = 2)
        print("\n[STEP 3] Injecting Cycle 2 (Tier 2)...")
        await ws.send(json.dumps({"type": "test_wellness_cycle", "slm_output": slm_test_high}))
        r2 = json.loads(await ws.recv())
        print(f"  Cycle 2 result: consecutive_count={r2['consecutive_count']}, should_fire={r2['should_fire']}")
        assert r2["consecutive_count"] == 2
        assert r2["should_fire"] is False
        log_data["cycles"].append({"cycle": 2, "response": r2, "intervention_received": False})

        # Step 4: Cycle 3 (Consecutive = 3 -> SHOULD FIRE!)
        print("\n[STEP 4] Injecting Cycle 3 (Tier 2) -> Hysteresis threshold reached...")
        await ws.send(json.dumps({"type": "test_wellness_cycle", "slm_output": slm_test_high}))

        # Expect messages: test_wellness_cycle_result and intervention_triggered
        recvs = []
        for _ in range(2):
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                msg = json.loads(msg_raw)
                recvs.append(msg)
            except asyncio.TimeoutError:
                break

        cycle_res = next((m for m in recvs if m["type"] == "test_wellness_cycle_result"), None)
        interv_msg = next((m for m in recvs if m["type"] == "intervention_triggered"), None)

        print(f"  Cycle 3 result: should_fire={cycle_res['should_fire']}, intervention_fired={cycle_res['intervention_fired']}")
        assert cycle_res is not None
        assert cycle_res["should_fire"] is True
        assert interv_msg is not None

        pkg = interv_msg.get("intervention", {})
        print(f"  *** INTERVENTION RECEIVED OVER /ws ***")
        print(f"  Title: {pkg.get('title')}")
        print(f"  Icon: {ascii(pkg.get('icon'))}")
        print(f"  Category: {pkg.get('category')}")
        print(f"  Action: {pkg.get('action_label')}")
        print(f"  Personalized Note: {pkg.get('personalized_note')}")
        print(f"  Steps Count: {len(pkg.get('steps', []))}")

        # Assert full schema compliance
        assert "icon" in pkg
        assert "title" in pkg
        assert "category" in pkg
        assert "personalized_note" in pkg
        assert "steps" in pkg and len(pkg["steps"]) > 0
        assert "slm_reasoning" in pkg
        assert "action_label" in pkg

        log_data["cycles"].append({
            "cycle": 3,
            "response": cycle_res,
            "intervention_received": True,
            "intervention_pkg": pkg
        })

        # Step 5: Cycle 4 (Cooldown check)
        print("\n[STEP 5] Injecting Cycle 4 (Tier 2 immediately after) -> Verifying 300s cooldown suppression...")
        await ws.send(json.dumps({"type": "test_wellness_cycle", "slm_output": slm_test_high}))
        r4 = json.loads(await ws.recv())
        print(f"  Cycle 4 result: should_fire={r4['should_fire']}, reason={r4['metadata'].get('reason')}")
        assert r4["should_fire"] is False
        assert "cooldown_active" in r4["metadata"].get("reason", "")
        log_data["cycles"].append({"cycle": 4, "response": r4, "intervention_received": False})

    EVIDENCE_FILE.write_text(json.dumps(log_data, indent=2), encoding="utf-8")
    print("\n" + "=" * 75)
    print(" [SUCCESS] Full trigger test passed! Intervention card verified over live /ws.")
    print(f" Saved raw evidence: {EVIDENCE_FILE}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
