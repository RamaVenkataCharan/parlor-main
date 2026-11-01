"""Destructive last test: llama-server dies mid-session.

Runs last (file name order) because it kills the suite server's llama.cpp
child; every turn after that can only fail gracefully.
"""

import subprocess
import sys
import pytest

from util import audio


def test_llama_death_fails_gracefully(server, session):
    server.require_managed()
    if sys.platform == "win32":
        cmd = f"Get-CimInstance Win32_Process | Where-Object {{ $_.Name -like '*llama-server*' }} | Select-Object -ExpandProperty ProcessId"
        out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                             capture_output=True, text=True).stdout.split()
        assert out, "could not find the spawned llama-server"
        for pid in out:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    else:
        out = subprocess.run(["pgrep", "-P", str(server.proc.pid), "llama-server"],
                             capture_output=True, text=True).stdout.split()
        assert out, "could not find the spawned llama-server"
        subprocess.run(["kill", "-9", out[0]])

    t = session.turn(audio("capital_france"), timeout=30)
    assert t.marker == "released", "client left hanging after llama-server died"
    # The server itself must survive to release the next attempt too.
    t = session.turn(audio("capital_france"), timeout=30)
    assert t.marker == "released"
