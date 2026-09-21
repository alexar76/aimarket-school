#!/usr/bin/env python3
"""Capture School portal hero + per-lesson reel stills for the GitHub README gallery.

Serves ecosystem-landing (or SCHOOL_BASE_URL) and writes:
  school/docs/recordings/school-portal-hero.png
  school/docs/screenshots/{lesson-id}.png

Usage (from monorepo root):
  python3 school/scripts/capture_readme_gallery.py
  SCHOOL_BASE_URL=https://edu.modelmarket.dev python3 school/scripts/capture_readme_gallery.py
"""

from __future__ import annotations

import http.server
import os
import socketserver
import threading
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SCHOOL = ROOT / "school"
LANDING = ROOT / "ecosystem-landing"
OUT_HERO = SCHOOL / "docs" / "recordings" / "school-portal-hero.png"
OUT_SHOTS = SCHOOL / "docs" / "screenshots"
MOUNT = "/school"


def _lessons() -> list[dict]:
    data = yaml.safe_load((SCHOOL / "lessons.yaml").read_text(encoding="utf-8"))
    return list(data.get("lessons") or [])


def _serve(directory: Path) -> tuple[socketserver.TCPServer, int]:
    os.chdir(directory)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    httpd.allow_reuse_address = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def main() -> int:
    base = os.environ.get("SCHOOL_BASE_URL", "").rstrip("/")
    httpd = None
    if not base:
        httpd, port = _serve(LANDING)
        base = f"http://127.0.0.1:{port}{MOUNT}"
        time.sleep(0.3)
        print(f"Serving {LANDING} at {base}")

    OUT_HERO.parent.mkdir(parents=True, exist_ok=True)
    OUT_SHOTS.mkdir(parents=True, exist_ok=True)
    lessons = _lessons()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1.5,
        )
        try:
            page.goto(f"{base}/", wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(2500)
            page.locator("header.hero-cosmic").screenshot(path=str(OUT_HERO))
            print(f"OK {OUT_HERO.relative_to(ROOT)}")

            for L in lessons:
                lid = L["id"]
                out = OUT_SHOTS / f"{lid}.png"
                page.goto(f"{base}/{lid}/", wait_until="networkidle", timeout=60_000)
                page.wait_for_timeout(2200)
                reel = page.locator("#reel")
                if reel.count():
                    reel.screenshot(path=str(out))
                else:
                    page.screenshot(path=str(out), full_page=False)
                print(f"OK {out.relative_to(ROOT)}")
        finally:
            page.close()
            browser.close()
            if httpd is not None:
                httpd.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
