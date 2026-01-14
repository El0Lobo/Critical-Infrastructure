"""
Utility helpers to start/stop a Cloudflare quick tunnel from the CMS.

This is a development convenience. We spawn ``cloudflared tunnel --url ...`` in the
background, capture the generated trycloudflare.com URL, and keep the process alive
until stopped. Only one tunnel is supported at a time.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
import time
from typing import Optional

_process: Optional[subprocess.Popen[str]] = None
_drain_thread: Optional[threading.Thread] = None
_current_url: Optional[str] = None
_lock = threading.Lock()

URL_RE = re.compile(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)")


def _drain_output(pipe):
    """Keep reading stdout so cloudflared does not block."""
    try:
        for _ in pipe:
            pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def current_url() -> Optional[str]:
    with _lock:
        return _current_url


def is_running() -> bool:
    with _lock:
        return _process is not None and _process.poll() is None


def stop_tunnel() -> bool:
    """Terminate the running tunnel (if any)."""
    global _process, _current_url
    with _lock:
        proc = _process
        _process = None
        _current_url = None

    if not proc:
        return False

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return True


def start_tunnel(target_url: str, timeout: int = 20) -> str:
    """
    Start a quick tunnel that exposes ``target_url`` and return the public URL.
    Raises RuntimeError if cloudflared is missing or fails to start.
    """
    global _process, _drain_thread, _current_url

    if shutil.which("cloudflared") is None:
        raise RuntimeError("cloudflared CLI not found. Install it first.")

    stop_tunnel()

    cmd = ["cloudflared", "tunnel", "--no-autoupdate", "--url", target_url]
    proc = subprocess.Popen(  # noqa: S603 - intentional dev utility
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    discovered_url = None
    captured_lines = []
    start_time = time.time()

    assert proc.stdout is not None  # for type checkers
    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue
        captured_lines.append(line)
        match = URL_RE.search(line)
        if match:
            discovered_url = match.group(1)
            break

    if not discovered_url:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise RuntimeError(
            "Cloudflare tunnel failed to start. Output:\n" + "".join(captured_lines).strip()
        )

    # Keep draining stdout in the background so the process stays happy.
    _drain_thread = threading.Thread(target=_drain_output, args=(proc.stdout,), daemon=True)
    _drain_thread.start()

    with _lock:
        _process = proc
        _current_url = discovered_url

    return discovered_url

