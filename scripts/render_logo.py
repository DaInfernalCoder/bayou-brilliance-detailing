#!/usr/bin/env python3
"""Render the production SVG logo to an exact 1200px square PNG."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: render_logo.py OUTPUT.png")
    destination = Path(sys.argv[1]).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=1)
        page.set_content(
            """<!doctype html><style>
            *{box-sizing:border-box}html,body{margin:0;width:1200px;height:1200px;overflow:hidden;background:#0B302F}
            img{display:block;width:1200px;height:1200px}
            </style><img src="http://127.0.0.1:4176/assets/logo.svg" alt="">"""
        )
        page.locator("img").wait_for(state="visible")
        page.wait_for_function("document.images[0].complete && document.images[0].naturalWidth > 0")
        page.screenshot(path=str(destination))
        browser.close()


if __name__ == "__main__":
    main()
