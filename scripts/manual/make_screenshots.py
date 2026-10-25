"""Make the manual's screenshots from a scripted example conversation.

Starts the scripted Ollama stand-in (``mock_ollama.py``) and the Shadowseed web
API with a fresh workspace, plays the scenario (three turns, so two seeds
recur), then drives the web client with Playwright: evidence, the fourth turn
that uses the promoted seed, the timeline, technical details, a contradiction
and the phone layout.

Requirements: the package installed (``pip install -e .``), a built web client
(``npm run build`` in ``apps/web``) and Playwright with Chromium.

Usage:
    python scripts/manual/make_screenshots.py en docs/manual/images/en [--chromium PATH]
    python scripts/manual/make_screenshots.py nl docs/manual/images/nl
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import threading
import urllib.request
from pathlib import Path

from mock_ollama import Scenario, make_server
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MOCK_PORT = 11499
WEB_PORT = 8799
API = f"http://127.0.0.1:{WEB_PORT}/api/v1"

CALLOUTS = """() => {
  const spots = [['.conversation-list', 1], ['.messages', 2], ['.composer', 3],
                 ['.seed-list', 4], ['.tech-details', 5]];
  for (const [selector, n] of spots) {
    const el = document.querySelector(selector);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    const badge = document.createElement('div');
    badge.className = 'manual-callout';
    badge.textContent = n;
    Object.assign(badge.style, {position: 'fixed', left: (r.right - 34) + 'px', top: (r.top - 13) + 'px',
      width: '26px', height: '26px', borderRadius: '50%', background: '#d9480f', color: '#fff',
      font: '700 15px/26px sans-serif', textAlign: 'center', zIndex: 9999, boxShadow: '0 0 0 3px #fff'});
    document.body.appendChild(badge);
  }
}"""


def call(method: str, path: str, data: dict | None = None) -> dict:
    request = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def play(scenario: dict) -> None:
    """Create the conversation and run the first three turns through the API."""

    script = scenario["play"]
    session = call("POST", "/sessions", {
        "title": script["title"], "backend": "ollama",
        "model_id": "qwen2.5:7b-instruct", "authority_mode": "controlled",
    })
    for i, question in enumerate(script["questions"][:3]):
        call("POST", f"/sessions/{session['session_id']}/turns", {"question": question, "request_id": f"t{i}"})


def box(page, selector: str, index: int = 0) -> dict:
    return page.locator(selector).nth(index).bounding_box()


def clip(rect: dict, pad: float = 0, height: float | None = None) -> dict:
    return {
        "x": rect["x"] - pad,
        "y": max(rect["y"] - pad, 0),
        "width": rect["width"] + 2 * pad,
        "height": height if height is not None else rect["height"] + 2 * pad,
    }


def shoot(scenario: dict, out: Path, chromium: str | None) -> None:
    script = scenario["play"]
    url = f"http://127.0.0.1:{WEB_PORT}/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chromium) if chromium else playwright.chromium.launch()
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2).new_page()
        page.goto(url)
        page.wait_for_timeout(1500)

        # New conversation form with Ollama selected.
        page.click("text=New conversation")
        page.wait_for_timeout(500)
        page.fill(".new-chat input >> nth=0", script["new_title"])
        page.select_option(".new-chat select >> nth=0", "ollama")
        page.wait_for_timeout(800)
        model = page.locator(".new-chat").locator("input, select").nth(2)
        if model.evaluate("e => e.tagName") == "INPUT":
            model.fill("qwen2.5:7b-instruct")
        page.screenshot(path=out / "02-new-conversation.png", clip=clip(box(page, ".new-chat"), 16))
        page.click("button[aria-label='Cancel new conversation']")

        # Overview after three turns, with numbered callouts.
        page.click(f"text={script['title']}")
        page.wait_for_timeout(1500)
        page.locator(".messages").evaluate("e => e.scrollTo(0, e.scrollHeight)")
        page.evaluate(CALLOUTS)
        page.screenshot(path=out / "01-overview.png")
        page.evaluate("() => document.querySelectorAll('.manual-callout').forEach(e => e.remove())")

        # Seed list.
        column = box(page, ".shadow-column")
        seeds = box(page, ".seed-list")
        page.screenshot(path=out / "03-seed-list.png",
                        clip=clip(column, height=seeds["y"] + seeds["height"] + 16 - column["y"]))

        # Evidence form, then the promoted seed.
        page.locator(".seed-card").first.click()
        page.wait_for_timeout(1000)
        page.fill("input[placeholder^='URL']", script["source_ref"])
        page.fill("textarea", script["note"])
        page.check(".seed-detail input[type=checkbox]")
        head, form = box(page, ".seed-detail .panel", 0), box(page, ".seed-detail .panel", 1)
        page.screenshot(path=out / "04-evidence-form.png",
                        clip=clip(head, 12, height=form["y"] + form["height"] - head["y"] + 24))
        page.click("text=Record evidence")
        page.wait_for_timeout(1500)
        page.screenshot(path=out / "05-promoted.png", clip=clip(box(page, ".seed-detail .panel"), 12))

        # Fourth turn: the promoted seed is used.
        page.click("text=All seeds")
        page.fill("textarea[aria-label='Message']", script["questions"][3])
        page.press("textarea[aria-label='Message']", "Enter")
        page.wait_for_timeout(3000)
        page.locator(".messages").evaluate("e => e.scrollTo(0, e.scrollHeight)")
        page.wait_for_timeout(400)
        question = page.locator(".message--user").last.bounding_box()
        answer = page.locator(".message--assistant").last.bounding_box()
        messages = box(page, ".messages")
        page.screenshot(path=out / "06-answer.png", clip={
            "x": messages["x"], "y": question["y"] - 12, "width": messages["width"],
            "height": answer["y"] + answer["height"] - question["y"] + 24})
        page.screenshot(path=out / "06b-used-card.png", clip=clip(box(page, ".seed-card"), 10))

        # Timeline of the used seed.
        page.locator(".seed-card").first.click()
        page.wait_for_timeout(1000)
        page.locator(".seed-timeline").first.scroll_into_view_if_needed()
        panel = page.locator(".seed-detail .panel", has=page.locator(".seed-timeline")).first.bounding_box()
        page.screenshot(path=out / "07-timeline.png", clip=clip(panel, 12, height=min(panel["height"] + 24, 330)))

        # Technical details.
        page.click("text=All seeds")
        page.wait_for_timeout(500)
        page.click("text=Technical details and raw data")
        page.wait_for_timeout(800)
        page.screenshot(path=out / "09-technical.png", clip=clip(box(page, ".shadow-column")))
        page.click("text=Technical details and raw data")

        # A contradiction on the third seed.
        page.locator(".seed-card").nth(2).click()
        page.wait_for_timeout(800)
        page.click("text=Mark as contradicted")
        page.wait_for_timeout(1500)
        page.locator(".shadow-body").evaluate("e => e.scrollTo(0, 0)")
        page.screenshot(path=out / "08-contradiction.png", clip=clip(box(page, ".shadow-column")))

        # Phone layout.
        phone = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3).new_page()
        phone.goto(url)
        phone.wait_for_timeout(1500)
        phone.click("button.mobile-nav-button")
        phone.wait_for_timeout(500)
        phone.click(f"text={script['title']}")
        phone.wait_for_timeout(1500)
        phone.screenshot(path=out / "10-phone.png")
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("lang", choices=["en", "nl"])
    parser.add_argument("output", type=Path)
    parser.add_argument("--chromium", default=None)
    parser.add_argument("--static-root", type=Path, default=ROOT / "apps" / "web" / "out")
    args = parser.parse_args()

    scenario = json.loads((HERE / f"scenario-{args.lang}.json").read_text(encoding="utf-8"))
    mock = make_server(Scenario(scenario), MOCK_PORT)
    threading.Thread(target=mock.serve_forever, daemon=True).start()
    os.environ["OLLAMA_HOST"] = f"http://127.0.0.1:{MOCK_PORT}"

    from shadowseed_webapi.server import create_server

    with tempfile.TemporaryDirectory() as workspace:
        server = create_server(workspace=workspace, port=WEB_PORT, static_root=args.static_root)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            play(scenario)
            args.output.mkdir(parents=True, exist_ok=True)
            shoot(scenario, args.output, args.chromium)
        finally:
            server.shutdown()
            mock.shutdown()
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
