#!/usr/bin/env python3
"""Responsive browser smoke test for the Bayou Brilliance website."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:4176"
PHONE = "tel:+13464873778"
SCHEDULER = "https://cal.com/sumitdatta/auto-detail-service"
ARTIFACTS = Path(__file__).resolve().parents[1] / "qa-artifacts"


def main() -> None:
    failures: list[str] = []
    ARTIFACTS.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        for width, height in ((1440, 1000), (1024, 900), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            console_errors: list[str] = []
            page_errors: list[str] = []
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.goto(URL, wait_until="load")
            page.wait_for_timeout(500)

            for image in page.locator("img[loading='lazy']").all():
                image.scroll_into_view_if_needed()
                page.wait_for_timeout(70)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(180)

            metrics = page.evaluate(
                """([phone, scheduler]) => ({
                    viewport: innerWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    h1: document.querySelectorAll("h1").length,
                    images: [...document.images].map(image => ({
                        src: image.getAttribute("src"),
                        complete: image.complete,
                        width: image.naturalWidth
                    })),
                    headerBackground:
                        getComputedStyle(document.querySelector(".site-header")).backgroundColor,
                    phoneLinks: document.querySelectorAll(`a[href="${phone}"]`).length,
                    schedulerLinks:
                        document.querySelectorAll(`a[href="${scheduler}"]`).length,
                    forms: document.querySelectorAll("form").length,
                    emailLinks: document.querySelectorAll('a[href^="mailto:"]').length,
                    heroImage:
                        document.querySelector(".hero-visual img").getAttribute("src"),
                    navCallColor:
                        getComputedStyle(document.querySelector(".nav-actions .button-call")).color,
                    navCallBackground:
                        getComputedStyle(document.querySelector(".nav-actions .button-call")).backgroundColor
                })""",
                [PHONE, SCHEDULER],
            )
            print(f"{width}px: {metrics}")

            if metrics["scrollWidth"] > metrics["viewport"]:
                failures.append(f"{width}px has horizontal overflow")
            if metrics["h1"] != 1:
                failures.append(f"{width}px has {metrics['h1']} H1 elements")
            if metrics["phoneLinks"] < 6 or metrics["schedulerLinks"] < 6:
                failures.append(f"{width}px is missing repeated call or booking links")
            if metrics["forms"] != 0 or metrics["emailLinks"] != 0:
                failures.append(f"{width}px contains a public form or email link")
            if any(not image["complete"] or image["width"] < 1 for image in metrics["images"]):
                failures.append(f"{width}px has an incomplete image")
            if metrics["headerBackground"] in {"rgba(0, 0, 0, 0)", "transparent"}:
                failures.append(f"{width}px header has no independent background")
            if "hero-foam-car.jpg" not in metrics["heroImage"]:
                failures.append(f"{width}px hero image is missing")
            if metrics["navCallColor"] == metrics["navCallBackground"]:
                failures.append(f"{width}px nav call button text is not distinguishable")

            page.evaluate(
                "document.documentElement.style.scrollBehavior = 'auto'; window.scrollTo({top: 0, left: 0, behavior: 'instant'})"
            )
            page.wait_for_timeout(400)
            resting = page.evaluate(
                "({scrollY, headerTop: document.querySelector('.site-header').getBoundingClientRect().top})"
            )
            print(f"resting header: {resting}")
            if resting["scrollY"] != 0 or resting["headerTop"] != 0:
                failures.append(f"{width}px did not return the header to its resting position")

            if width == 1440:
                page.locator(".site-header").screenshot(path=str(ARTIFACTS / "header-desktop.png"))
                page.screenshot(path=str(ARTIFACTS / "desktop.png"), full_page=True)

            if width == 390:
                page.locator(".menu-toggle").click()
                expanded = page.locator(".menu-toggle").get_attribute("aria-expanded")
                nav_open = page.locator("#site-nav").evaluate(
                    "element => element.classList.contains('is-open')"
                )
                print(f"mobile menu: open={nav_open}; aria-expanded={expanded}")
                if expanded != "true" or not nav_open:
                    failures.append("mobile menu did not enter its visible state")
                page.locator(".menu-toggle").click()

                page.locator("#questions details:first-child summary").click()
                faq_open = page.locator("#questions details:first-child").get_attribute("open")
                print(f"question panel opens: {faq_open is not None}")
                if faq_open is None:
                    failures.append("question panel did not open")

                page.evaluate("window.scrollTo({top: 0, left: 0, behavior: 'instant'})")
                page.wait_for_timeout(150)
                page.locator(".site-header").screenshot(path=str(ARTIFACTS / "header-mobile.png"))
                page.screenshot(path=str(ARTIFACTS / "mobile.png"), full_page=True)

            if console_errors:
                failures.append(f"{width}px console errors: {console_errors}")
            if page_errors:
                failures.append(f"{width}px page errors: {page_errors}")
            page.close()

        browser.close()

    if failures:
        raise SystemExit("QA failures:\n- " + "\n- ".join(failures))
    print("PASS browser QA")


if __name__ == "__main__":
    main()
