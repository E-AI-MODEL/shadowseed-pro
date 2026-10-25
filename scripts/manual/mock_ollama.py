"""A scripted stand-in for Ollama, used only to make the manual's screenshots.

Shadowseed runs unchanged against it: detection, intake, recurrence, the Gate,
the point-of-use check and the timeline are the real code. Only the model text
comes from a scenario file, so the example conversation reads well and is the
same on every run. The manual says so where it shows the screenshots.

The embeddings are a small bag of scenario keywords plus hashed words. They are
tuned so that the scenario's same-gap pairs and the promoted seed's relevance
behave as a real embedding model would on this conversation.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

MODELS = [
    {"name": "qwen2.5:7b-instruct", "model": "qwen2.5:7b-instruct", "digest": "845dbda0ea48"},
    {"name": "embeddinggemma:latest", "model": "embeddinggemma:latest", "digest": "85462619ee72"},
]
HASH_DIMS = 32


class Scenario:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.topics = list(data["topics"].values())
        self.domain = data.get("domain", [])

    def embed(self, text: str) -> list[float]:
        low = text.lower()
        vec = [0.0] * (1 + len(self.topics) + HASH_DIMS)
        vec[0] = 1.0 + 0.6 * sum(low.count(word) for word in self.domain)
        for i, words in enumerate(self.topics):
            vec[1 + i] = 0.6 * float(sum(low.count(word) for word in words))
        for word in re.findall(r"\w+", low):
            index = int(hashlib.sha256(word.encode()).hexdigest(), 16) % HASH_DIMS
            vec[1 + len(self.topics) + index] += 0.3
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def turn(self, question: str) -> dict[str, Any] | None:
        return next((t for t in self.data["turns"] if t["match"] in question), None)

    def answer(self, user_message: str) -> str:
        if "Open questions noted earlier:" in user_message:
            return self.recurrence(user_message)
        turn = self.turn(user_message)
        if not turn:
            return "…"
        # A promoted seed reaches the model inside a delimited candidate block.
        if "candidate" in user_message.lower() and turn.get("answer_with_seed"):
            return turn["answer_with_seed"]
        return turn["answer"]

    def gaps(self, prompt: str) -> str:
        if "Open questions noted earlier:" in prompt:
            return self.recurrence(prompt)
        question = prompt.split("CURRENT QUESTION:")[-1].split("DRAFT ANSWER:")[0]
        gaps = (self.turn(question) or {}).get("gaps", [])
        return "\n".join(f"{i}. {gap}" for i, gap in enumerate(gaps, 1)) or "NONE"

    def recurrence(self, prompt: str) -> str:
        earlier, _, rest = prompt.partition("New notes from the latest turn:")
        opens = re.findall(r"^(\d+)\. (.+)$", earlier, re.M)
        notes = re.findall(r"^([a-z])\. (.+)$", rest.split("For each new note")[0], re.M)
        lines = []
        for letter, note in notes:
            target = self.data["recurrence"].get(note.strip())
            number = next((n for n, text in opens if target and text.strip() == target), None)
            lines.append(f"{letter}: {number or 'NONE'}")
        return "\n".join(lines)


def make_server(scenario: Scenario, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, obj: Any) -> None:
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:
            pass

        def do_GET(self) -> None:
            if self.path == "/api/version":
                return self._send({"version": "0.12.0"})
            if self.path == "/api/tags":
                return self._send({"models": MODELS})
            self._send({})

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/show":
                caps = ["embedding"] if "embed" in body.get("model", "") else ["completion"]
                return self._send({"capabilities": caps})
            if self.path == "/api/embed":
                items = body["input"]
                items = [items] if isinstance(items, str) else items
                return self._send({"embeddings": [scenario.embed(t) for t in items]})
            if self.path == "/api/chat":
                text = scenario.answer(body["messages"][-1]["content"])
                return self._send({"message": {"role": "assistant", "content": text}, "done": True})
            if self.path == "/api/generate":
                return self._send({"response": scenario.gaps(body.get("prompt", "")), "done": True})
            self._send({})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
