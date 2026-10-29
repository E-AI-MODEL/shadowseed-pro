"""Shadowseed observational HF pilot. Synthetic conversations only, no Q1/Q2 efficacy claim."""
import hashlib
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from huggingface_hub import model_info
from shadowseed.adapters.models import HFTransformersBackend
from shadowseed.detection.model_detector import HFTransformersDetectorBackend, build_detection_prompt
from shadowseed.engine import ShadowseedEngine
from shadowseed.surfacing import build_role_chat_messages

MODEL = os.getenv("SHADOWTRACE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
TURNS = int(os.getenv("SHADOWTRACE_TURNS", "6"))
CASES = int(os.getenv("SHADOWTRACE_CASES", "3"))
OUT = Path(os.getenv("SHADOWTRACE_OUT", "/tmp/shadowtrace_hf.json"))
OPENINGS = [
    ("city", "Een fictieve stad wil haar binnenstad aantrekkelijker maken. Er is weinig budget en bewoners zijn verdeeld. Hoe zou je het probleem eerst verkennen?"),
    ("sensors", "Twee fictieve sensoren geven soms andere meetwaarden voor hetzelfde proces. Er is nog geen onafhankelijke ijking. Wat kunnen we wel en niet zeggen?"),
    ("library", "Een fictieve openbare bibliotheek trekt minder bezoekers, maar meer mensen gebruiken haar digitale diensten. Wat kunnen we hieruit afleiden?"),
]

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()

class TracedDetector(HFTransformersDetectorBackend):
    last_full_prompt = ""

    def detect_seeds(self, item, max_seeds=5):
        text = str(item.get("text") or item.get("input") or "").strip()
        self.last_full_prompt = build_detection_prompt(
            text, max_seeds=max_seeds, variant=self.prompt_variant,
            question=str(item.get("question") or "").strip() or None,
            source_context=str(item.get("source_context") or "").strip() or None,
            conversation_context=str(item.get("conversation_context") or "").strip() or None
        ) if text else ""
        return super().detect_seeds(item, max_seeds=max_seeds)

def rendered(backend, messages):
    template = getattr(backend.tokenizer, "apply_chat_template", None)
    if callable(template):
        try:
            return template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            try:
                return template(backend._fold_system_for_chat_template(messages), tokenize=False, add_generation_prompt=True)
            except Exception:
                pass
    return backend._render_plain_chat(messages)

def main():
    random.seed(291026)
    torch.manual_seed(291026)
    torch.set_num_threads(2)
    revision = model_info(MODEL).sha
    print("HF_MODEL", MODEL, "PINNED_SHA", revision, flush=True)
    host = HFTransformersBackend(model_id=MODEL, revision=revision, max_new_tokens=160)
    detector = TracedDetector(model_id=MODEL, revision=revision, max_new_tokens=140, prompt_variant="current_pair")
    result = {
        "schema": "hf-shadowtrace-observation-20261029-v1",
        "started_at": now(), "model": MODEL, "model_revision": revision,
        "decoder": "HFTransformersBackend do_sample=False",
        "user_turn_origin": "same-model synthetic conversation partner; adaptive to own prior answer; NOT an independent human user",
        "research_limitations": ["Not Q1/Q2 validation", "No independent semantic labels", "No seed injected without canonical authorization"],
        "episodes": [], "errors": [], "status": "running"
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    def save():
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    for case_id, question in OPENINGS[:CASES]:
        engine = ShadowseedEngine(
            detector_backend=detector,
            embedding_backend="sentence-transformers",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            gate_policy_id="evidence_backed",
            max_seeds_per_turn=3,
        )
        history = []
        episode = {"case_id": case_id, "initial_question": question, "turns": [], "status": "running"}
        result["episodes"].append(episode)
        for i in range(TURNS):
            prepared = engine.prepare_turn(question)
            try:
                messages = build_role_chat_messages(
                    history, question, list(prepared.surfaced_seeds),
                    response_language="the same language as the user's current question"
                )
                prompt = rendered(host, messages)
                start = time.monotonic()
                answer = host.generate_messages(messages)
                report = engine.observe_turn(prepared, answer)
                event = {
                    "turn": i, "question": question, "answer": answer,
                    "host_messages": messages, "host_prompt_exact": prompt,
                    "host_prompt_sha256": sha(prompt),
                    "host_elapsed_seconds": round(time.monotonic() - start, 3),
                    "detector_prompt_exact": detector.last_full_prompt,
                    "detector_prompt_sha256": sha(detector.last_full_prompt),
                    "detector_raw": detector.last_raw_output,
                    "detector_diagnostics": detector.last_parse_diagnostics,
                    "prepared": prepared.to_dict(), "report": report,
                    "simulated_next_question": None, "simulated_user_prompt_exact": None,
                }
                episode["turns"].append(event)
                history.append((question, answer))
                save()
                print(
                    "OBS", case_id, i,
                    "candidates", len(report.get("detected_candidates", [])),
                    "born", len(report.get("seeds_born_weightless", [])),
                    "surfaced", len(report.get("surfaced_seed_ids", [])),
                    flush=True
                )
                if i < TURNS - 1:
                    context = "\n".join("User: " + q + "\nAssistant: " + a for q, a in history[-2:])
                    sim = [
                        {"role": "system", "content": "Je bent een nieuwsgierige gesprekspartner. Stel precies één natuurlijke vervolgvraag op het laatste antwoord. Reageer op wat er werkelijk gezegd is, niet op een vooraf bepaald script. Geen lijst of uitleg. Noem nooit detector, seeds, geheugen of experiment."},
                        {"role": "user", "content": "Dit is het recente gesprek:\n" + context + "\n\nGeef uitsluitend jouw volgende vraag."}
                    ]
                    sim_prompt = rendered(host, sim)
                    candidate_question = host.generate_messages(sim).strip().split("\n")[0].strip(' -"')
                    if len(candidate_question) < 12:
                        episode["status"] = "incomplete_simulated_user"
                        save()
                        break
                    event["simulated_user_prompt_exact"] = sim_prompt
                    event["simulated_next_question"] = candidate_question
                    question = candidate_question
                    save()
            except Exception as error:
                if engine.has_pending_turn:
                    engine.abort_turn(prepared)
                episode["status"] = "error"
                result["errors"].append({"case_id": case_id, "turn": i, "error": repr(error)})
                save()
                print("RUN_ERROR", case_id, i, repr(error), flush=True)
                break
        if episode["status"] == "running":
            episode["status"] = "completed"
        episode["final_engine_state"] = engine.export_state()
        save()
    result["status"] = "completed" if not result["errors"] else "completed_with_errors"
    save()
    print(
        "FINISH", result["status"],
        "turns", sum(len(x["turns"]) for x in result["episodes"]),
        "source_sha256", sha(OUT.read_text(encoding="utf-8")),
        flush=True
    )

if __name__ == "__main__":
    main()
