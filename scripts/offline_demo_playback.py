"""Offline Playback & Fallback Demonstration Utility for Parlor.

This script enables deterministic, offline demonstration of the Parlor affective
wellness monitoring system by replaying genuine historical sessions stored in
`shared_state/wellness_history.db`.

Usage:
    # 1. View statistical summary of stored assessments:
    python scripts/offline_demo_playback.py --summary

    # 2. Replay chronological assessments in the terminal:
    python scripts/offline_demo_playback.py --replay --limit 15 --delay 1.0

    # 3. Launch an offline mock WebSocket server to drive the web UI:
    python scripts/offline_demo_playback.py --serve --port 8000
"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
import time
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_state", "wellness_history.db")


def load_assessments(db_path: str, limit: Optional[int] = None, order: str = "ASC") -> List[Dict[str, Any]]:
    """Loads historical assessments from SQLite."""
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at: {db_path}", file=sys.stderr)
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"SELECT * FROM stress_assessments ORDER BY id {order}"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    assessments = []
    for row in rows:
        drivers = []
        if row["primary_drivers"]:
            try:
                drivers = json.loads(row["primary_drivers"])
            except Exception:
                drivers = [row["primary_drivers"]]

        meta = {}
        if row["metadata"]:
            try:
                meta = json.loads(row["metadata"])
            except Exception:
                pass

        assessments.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "stress_level": row["stress_level"],
            "numeric_score": row["numeric_score"],
            "primary_drivers": drivers,
            "reasoning": row["reasoning"],
            "confidence": row["confidence"],
            "intervention_fired": bool(row["intervention_fired"]),
            "intervention_type": row["intervention_type"],
            "metadata": meta,
        })
    return assessments


def print_summary(db_path: str) -> None:
    """Prints comprehensive statistics of historical assessments."""
    assessments = load_assessments(db_path)
    total = len(assessments)
    if total == 0:
        print("[SUMMARY] No records found.")
        return

    tier0 = sum(1 for a in assessments if a["numeric_score"] == 0.0)
    tier1 = sum(1 for a in assessments if a["numeric_score"] == 1.0)
    tier2 = sum(1 for a in assessments if a["numeric_score"] == 2.0)
    interventions = sum(1 for a in assessments if a["intervention_fired"])
    confidences = [a["confidence"] for a in assessments if a["confidence"] is not None]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    print("=" * 70)
    print("      PARLOR AFFECTIVE WELLNESS HISTORY — DATABASE SUMMARY")
    print("=" * 70)
    print(f" Database Path           : {db_path}")
    print(f" Total Logged Cycles     : {total:,}")
    print(f" Low Stress (Tier 0)     : {tier0:,} ({tier0 / total * 100:.1f}%)")
    print(f" Moderate Stress (Tier 1): {tier1:,} ({tier1 / total * 100:.1f}%)")
    print(f" High Stress (Tier 2)    : {tier2:,} ({tier2 / total * 100:.1f}%)")
    print(f" Interventions Triggered : {interventions:,} ({interventions / total * 100:.1f}%)")
    print(f" Mean SLM Confidence     : {avg_conf:.1%}")
    print("=" * 70)

    # Driver breakdown
    driver_counts: Dict[str, int] = {}
    for a in assessments:
        for d in a["primary_drivers"]:
            key = d.split("=")[0].strip() if "=" in d else d[:25]
            driver_counts[key] = driver_counts.get(key, 0) + 1

    print("\nTop Contributing Biomarker Drivers:")
    sorted_drivers = sorted(driver_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    for name, cnt in sorted_drivers:
        print(f"  • {name:<32} : {cnt:,} occurrences")
    print("=" * 70)


def replay_cli(db_path: str, limit: int = 20, delay_sec: float = 1.0) -> None:
    """Streams historical assessments to the terminal."""
    assessments = load_assessments(db_path, limit=limit, order="DESC")
    # Reverse to play chronologically
    assessments.reverse()

    if not assessments:
        print("[REPLAY] No assessments available to replay.")
        return

    print("=" * 75)
    print(f" STARTING CHRONOLOGICAL REPLAY ({len(assessments)} cycles, {delay_sec}s interval)")
    print(" Press Ctrl+C at any time to pause or abort.")
    print("=" * 75)

    tier_map = {
        0.0: "[TIER 0 - LOW]",
        1.0: "[TIER 1 - MODERATE]",
        2.0: "[TIER 2 - HIGH]"
    }

    try:
        for idx, item in enumerate(assessments, 1):
            tier_badge = tier_map.get(item["numeric_score"], f"[TIER {item['numeric_score']}]")

            print(f"\n[{idx}/{len(assessments)}] Cycle ID: #{item['id']} | Status: {tier_badge}")
            print(f" Confidence : {item['confidence']:.1%} | Score: {item['numeric_score']}")
            if item["primary_drivers"]:
                print(f" Biomarkers : {', '.join(item['primary_drivers'])}")
            if item["reasoning"]:
                print(f" Reasoning  : \"{item['reasoning'][:120]}...\"")
            if item["intervention_fired"]:
                print(f" [!] INTERVENTION TRIGGERED: Category='{item['intervention_type']}'")

            if idx < len(assessments):
                time.sleep(delay_sec)
    except KeyboardInterrupt:
        print("\n[REPLAY] Paused by user.")


def serve_mock_websocket(db_path: str, port: int = 8000) -> None:
    """Launches a mock FastAPI + WebSocket server that pushes recorded assessments."""
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
    except ImportError:
        print("[ERROR] uvicorn and fastapi are required for mock server mode.", file=sys.stderr)
        return

    assessments = load_assessments(db_path, limit=100, order="DESC")
    assessments.reverse()
    if not assessments:
        print("[ERROR] No assessments in DB to broadcast.", file=sys.stderr)
        return

    app = FastAPI(title="Parlor Offline Fallback Demo Server")

    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "parlor", "web", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def get_index():
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "Parlor Offline Fallback Server Active"}

    @app.get("/health")
    async def get_health():
        return {
            "status": "offline_playback",
            "db_path": db_path,
            "total_cycles": len(assessments),
            "llama_server": "simulated_offline"
        }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        print(f"[WS] Client connected from {websocket.client}")
        try:
            curr_idx = 0
            while True:
                item = assessments[curr_idx % len(assessments)]
                curr_idx += 1

                payload = {
                    "type": "wellness_update",
                    "timestamp": time.time(),
                    "stress_tier": item["numeric_score"],
                    "stress_label": item["stress_level"],
                    "confidence": item["confidence"],
                    "drivers": item["primary_drivers"],
                    "reasoning": item["reasoning"],
                    "intervention": {
                        "fired": item["intervention_fired"],
                        "category": item["intervention_type"]
                    } if item["intervention_fired"] else None,
                    "offline_mock": True
                }
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(4.0)
        except Exception as e:
            print(f"[WS] Client disconnected ({e})")

    print("=" * 70)
    print(f" PARLOR OFFLINE DEMO SERVER RUNNING AT: http://127.0.0.1:{port}")
    print(" Simulating real-time WebSocket telemetry from historical DB records.")
    print(" Open browser to http://127.0.0.1:8000 to observe live dashboard UI.")
    print("=" * 70)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="Parlor Offline Demo & Playback Utility")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Path to wellness_history.db")
    parser.add_argument("--summary", action="store_true", help="Display summary statistics of stored history")
    parser.add_argument("--replay", action="store_true", help="Replay stored cycles in the CLI")
    parser.add_argument("--limit", type=int, default=20, help="Number of cycles to replay")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between replayed cycles")
    parser.add_argument("--serve", action="store_true", help="Launch mock web/WebSocket server on port 8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for mock server")

    args = parser.parse_args()

    if args.summary:
        print_summary(args.db)
    elif args.replay:
        replay_cli(args.db, limit=args.limit, delay_sec=args.delay)
    elif args.serve:
        serve_mock_websocket(args.db, port=args.port)
    else:
        # Default behavior: show summary and prompt
        print_summary(args.db)
        print("\nRun with `--replay` to inspect cycle telemetry or `--serve` for live UI playback.")


if __name__ == "__main__":
    main()
