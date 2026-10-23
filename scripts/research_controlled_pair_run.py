#!/usr/bin/env python3
"""Fixed-question sequential research arms.

zero: pure hosted answer loop; does NOT import or initialize Shadowseed.
ssl: real ShadowChatSession with v0.6 detector, semantic embeddings, TTL/TrTL,
     exploratory Gate and no external evidence. Recurrence is NOT truth.

Both arms use the same checked-in, unmodified question suite, model, provider,
generation contract and bounded role history. Research-only. No auto-scoring.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

DEFAULT_SUITE = "src/shadowseed/data/ssl_session_suite.json"
MAX_ANSWER_TOKENS = 1400
MAX_DETECTOR_TOKENS = 500
REASONING_EFFORT = "low"
MAX_HISTORY_TURNS = 6
MAX_HISTORY_CHARS = 12000


def hash_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def product_system_prompt() -> str:
    """Read the canonical answer contract as text without importing Shadowseed."""
    source = Path("src/shadowseed/surfacing.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(t, ast.Name) and t.id == "_ANSWER_GENERATION_SYSTEM_CONTRACT"
            for t in node.targets
        ):
            template = ast.literal_eval(node.value)
            return template.strip().format(
                language_instruction=(
                    "Respond in the same language as the user's current question only."
                ),
            )
    raise RuntimeError("canonical answer contract missing")


def bounded_history(history: list[tuple[str, str]]) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    total = 0
    for q, a in reversed(history[-MAX_HISTORY_TURNS:]):
        pair = (str(q), str(a))
        size = len(pair[0]) + len(pair[1])
        if selected and total + size > MAX_HISTORY_CHARS:
            break
        selected.append(pair)
        total += size
    return list(reversed(selected))


def vanilla_messages(
    history: list[tuple[str, str]], question: str, system_prompt: str
) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": system_prompt}]
    for q, a in bounded_history(history):
        messages.extend(
            [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
        )
    messages.append({"role": "user", "content": question})
    return messages


class ResponsesProvider:
    """Thin standard-library OpenAI Responses transport, not a Shadowseed path."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.key:
            raise RuntimeError("API secret not available; no model calls were made")
        self.calls: list[dict[str, Any]] = []
        self.total = {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}
        self.resolved_models: set[str] = set()

    def _request(self, route: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        req = urllib.request.Request(
            url="https://api.openai.com/v1/" + route,
            method="POST" if data is not None else "GET",
            data=(json.dumps(data, ensure_ascii=False).encode("utf-8")
                  if data is not None else None),
            headers={
                "Authorization": "Bearer " + self.key,
                "Content-Type": "application/json",
            },
        )
        last_error = ""
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                # Never log Authorization headers, environment, or raw secret.
                last_error = f"OpenAI HTTP {exc.code}: {body[:450]}"
                if exc.code not in (429, 500, 502, 503, 504):
                    break
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = f"OpenAI transport failed ({type(exc).__name__})"
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError(last_error)

    def check_access(self) -> dict[str, Any]:
        obj = self._request("models/" + self.model)
        return {"id": obj.get("id"), "owned_by": obj.get("owned_by")}

    def generate(
        self, messages: list[dict[str, str]], *, max_tokens: int, role: str
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "input": [dict(item) for item in messages],
            "store": False,
            "reasoning": {"effort": REASONING_EFFORT},
            "max_output_tokens": int(max_tokens),
        }
        started = time.monotonic()
        response = self._request("responses", payload)
        pieces: list[str] = []
        for output in response.get("output", []):
            if output.get("type") == "message":
                for item in output.get("content", []):
                    if item.get("type") == "output_text":
                        pieces.append(str(item.get("text", "")))
        text = "\n".join(pieces).strip()
        usage = response.get("usage") or {}
        details = usage.get("output_tokens_details") or {}
        raw_usage = {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "reasoning_tokens": int(details.get("reasoning_tokens") or 0),
        }
        for key in self.total:
            self.total[key] += raw_usage[key]
        returned = str(response.get("model") or "")
        if returned:
            self.resolved_models.add(returned)
        self.calls.append({
            "role": role,
            "request_id": response.get("id"),
            "model": returned,
            "status": response.get("status"),
            "usage": raw_usage,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output_chars": len(text),
        })
        if not text or response.get("status") != "completed":
            raise RuntimeError(
                f"Model did not complete a readable {role} response: "
                f"status={response.get('status')}, chars={len(text)}"
            )
        return text


class ResponsesModelBackend:
    """Same Responses transport for the live SSL answer role."""

    def __init__(self, provider: ResponsesProvider):
        self.provider = provider
        self.model_id = provider.model
        self.name = f"openai-responses:{provider.model}"

    def generate_messages(self, messages: list[dict[str, str]]) -> str:
        return self.provider.generate(messages, max_tokens=MAX_ANSWER_TOKENS, role="answer")

    def generate_chat(self, history: list[tuple[str, str]], question: str) -> str:
        return self.generate_messages(
            vanilla_messages(history, question, product_system_prompt())
        )

    def generate(self, prompt: str, scenario: dict, mode: str, ssl_seeds: list[str]) -> str:
        return self.provider.generate(
            [{"role": "user", "content": prompt}],
            max_tokens=MAX_ANSWER_TOKENS,
            role="revision",
        )


class ResponsesDetectorClient:
    """Transport bridge to the checked-in CURRENT_PAIR detector and parser."""

    def __init__(self, provider: ResponsesProvider):
        self.provider = provider

    def generate(self, prompt: str, max_new_tokens: int = MAX_DETECTOR_TOKENS) -> str:
        return self.provider.generate(
            [{"role": "user", "content": prompt}],
            max_tokens=max_new_tokens,
            role="detector",
        )


def load_suite(path: str) -> list[dict[str, Any]]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    conversations = obj.get("conversations")
    if not isinstance(conversations, list) or len(conversations) != 3:
        raise RuntimeError("expected the registered three-conversation primary suite")
    if sorted(len(c["turns"]) for c in conversations) != [4, 9, 9]:
        raise RuntimeError("fixed suite has changed; expected 4+9+9 turns")
    for c in conversations:
        for t in c["turns"]:
            if not isinstance(t.get("question"), str) or not t["question"].strip():
                raise RuntimeError("empty or changed question entry")
    return conversations


def run_zero(
    conversations: list[dict[str, Any]],
    provider: ResponsesProvider,
    system_prompt: str,
    save: Any,
) -> list[dict[str, Any]]:
    # No import or construction of shadowseed*, SSLManager, detector, embeddings or Gate.
    assert not any(m == "shadowseed" or m.startswith("shadowseed.") for m in sys.modules)
    output: list[dict[str, Any]] = []
    for conversation in conversations:
        history: list[tuple[str, str]] = []
        record = {
            "conversation_id": conversation["id"],
            "domain": conversation.get("domain"),
            "turns": [],
        }
        output.append(record)
        for index, t in enumerate(conversation["turns"]):
            question = t["question"]
            answer = provider.generate(
                vanilla_messages(history, question, system_prompt),
                max_tokens=MAX_ANSWER_TOKENS,
                role="answer",
            )
            history.append((question, answer))
            record["turns"].append({
                "index": index,
                "question": question,
                "answer": answer,
                "shadowseed_used": False,
                "candidate_detection_used": False,
                "gate_used": False,
            })
            save(output)
    return output


def run_ssl(
    conversations: list[dict[str, Any]],
    provider: ResponsesProvider,
    system_prompt: str,
    save: Any,
) -> list[dict[str, Any]]:
    # Lazy import guarantees the ZERO arm never enters or loads the SSL runtime.
    from shadowseed.chat import ShadowChatSession
    from shadowseed.detection.model_detector import OpenAIDetectorBackend
    from shadowseed.surfacing import build_role_chat_messages

    first_q = conversations[0]["turns"][0]["question"]
    expected = vanilla_messages([], first_q, system_prompt)
    actual = build_role_chat_messages(
        [], first_q, [], response_language="the same language as the user's current question"
    )
    if list(actual) != expected:
        raise RuntimeError("control and SSL zero-candidate generation prompts diverge")

    output: list[dict[str, Any]] = []
    for conv in conversations:
        model = ResponsesModelBackend(provider)
        detector = OpenAIDetectorBackend(
            provider.model, max_new_tokens=MAX_DETECTOR_TOKENS, prompt_variant="current_pair"
        )
        detector.client = ResponsesDetectorClient(provider)
        session = ShadowChatSession(
            backend="openai",
            model_id=provider.model,
            embedding_backend="openai",
            embedding_model="text-embedding-3-small",
            runtime_mode="live",
            authority_profile_id="autonomous",
            recurrence_mode="cluster",
            surface_top_k=2,
            max_seeds_per_turn=5,
            allow_same_turn_revision=False,
            self_derived_signal_policy="fail_closed",
            model_backend=model,
            revision_model_backend=model,
            detector_backend=detector,
        )
        record: dict[str, Any] = {
            "conversation_id": conv["id"],
            "domain": conv.get("domain"),
            "gate_policy_id": session.gate_policy_id,
            "authority_profile_id": session.authority_profile_id,
            "turns": [],
            "final_seeds": [],
        }
        output.append(record)
        for index, t in enumerate(conv["turns"]):
            report = session.turn(t["question"])
            entry = {
                "index": index,
                "question": t["question"],
                "answer": report["answer"],
                "surfaced_seed_ids": report.get("surfaced_seed_ids", []),
                "surfaced_seeds": report.get("surfaced_seeds", []),
                "detected_candidates": report.get("detected_candidates", []),
                "detector_raw": detector.last_raw_output,
                "detector_diagnostics": detector.last_parse_diagnostics,
                "intake_diagnostics": report.get("intake_diagnostics"),
                "seeds_born_weightless": report.get("seeds_born_weightless", []),
                "promoted_this_turn": report.get("promoted_this_turn", []),
                "reactivated_trtl": report.get("reactivated_trtl", []),
                "shadow_size": report.get("shadow_size"),
                "authority_runtime": report.get("authority_runtime"),
                "evidence_count": sum(
                    int(seed.evidence_count) for seed in session.manager.seeds.values()
                ),
            }
            record["turns"].append(entry)
            record["final_seeds"] = [
                {
                    "id": sid,
                    "text": seed.text,
                    "weight": seed.weight,
                    "trace": seed.trace,
                    "status": seed.status.value,
                    "evidence_count": seed.evidence_count,
                    "occurrence_count": seed.occurrence_count,
                }
                for sid, seed in sorted(session.manager.seeds.items())
            ]
            save(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["zero", "ssl"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--suite", default=DEFAULT_SUITE)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data = load_suite(args.suite)
    system_prompt = product_system_prompt()
    result: dict[str, Any] = {
        "protocol": "fixed22-sequential-zero-vs-ssl-v1",
        "status": "initialized",
        "arm": args.arm,
        "model_requested": args.model,
        "suite": args.suite,
        "suite_sha256": hash_file(args.suite),
        "answer_system_prompt_sha256": hashlib.sha256(
            system_prompt.encode("utf-8")
        ).hexdigest(),
        "source_git_sha": os.environ.get("GITHUB_SHA") or "unavailable",
        "started_at": utc_now(),
        "generation": {
            "provider_api": "OpenAI Responses",
            "reasoning_effort": REASONING_EFFORT,
            "max_answer_output_tokens": MAX_ANSWER_TOKENS,
            "max_detector_output_tokens": MAX_DETECTOR_TOKENS,
            "history_turn_limit": MAX_HISTORY_TURNS,
            "history_character_limit": MAX_HISTORY_CHARS,
            "store": False,
        },
        "suite_turn_count": sum(len(c["turns"]) for c in data),
        "conversations": [],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    provider: ResponsesProvider | None = None

    def save(conversations: list[dict[str, Any]]) -> None:
        result["conversations"] = conversations
        if provider is not None:
            result["provider_calls"] = list(provider.calls)
            result["provider_token_totals_excluding_embeddings"] = dict(provider.total)
            result["resolved_models"] = sorted(provider.resolved_models)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(out)

    try:
        provider = ResponsesProvider(args.model)
        result["model_access"] = provider.check_access()
        result["status"] = "running"
        save([])
        if args.arm == "zero":
            run_zero(data, provider, system_prompt, save)
        else:
            run_ssl(data, provider, system_prompt, save)
        result["status"] = "completed"
        result["completed_at"] = utc_now()
        save(result["conversations"])
        print(json.dumps({
            "status": "completed",
            "arm": args.arm,
            "model_requested": args.model,
            "resolved_models": sorted(provider.resolved_models),
            "conversations": len(result["conversations"]),
            "turns": sum(len(c["turns"]) for c in result["conversations"]),
            "provider_calls": len(provider.calls),
            "provider_token_totals_excluding_embeddings": provider.total,
            "suite_sha256": result["suite_sha256"],
            "answer_system_prompt_sha256": result["answer_system_prompt_sha256"],
            "output": str(out),
        }, indent=2))
        return 0
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {str(exc)[:700]}"
        result["completed_at"] = utc_now()
        save(result.get("conversations", []))
        print(f"Run failed for {args.arm}/{args.model}: {type(exc).__name__}: {str(exc)[:220]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
