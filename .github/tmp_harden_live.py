from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


# 1. Block every detector few-shot example, including the generative variant,
# and make the generated candidate format plain text.
path = "src/shadowseed/detection/model_detector.py"
text = read(path)
text = replace_once(
    text,
    "_FEWSHOT_NORMALIZED = frozenset(\n    _normalize_for_match(example) for example in (_FEWSHOT_GOOD + _FEWSHOT_BAD)\n)\n_FEWSHOT_TOKEN_SETS = tuple(_token_set(example) for example in (_FEWSHOT_GOOD + _FEWSHOT_BAD))",
    "_ALL_FEWSHOT_EXAMPLES = _FEWSHOT_GOOD + _FEWSHOT_GOOD_GENERATIVE + _FEWSHOT_BAD\n\n_FEWSHOT_NORMALIZED = frozenset(\n    _normalize_for_match(example) for example in _ALL_FEWSHOT_EXAMPLES\n)\n_FEWSHOT_TOKEN_SETS = tuple(_token_set(example) for example in _ALL_FEWSHOT_EXAMPLES)",
    path=path,
)
text = replace_once(
    text,
    'return re.sub(r"\\s+", " ", text).strip(" .,:;-").lower()',
    'return re.sub(r"\\s+", " ", text).strip(" .,:;-*_`#>").lower()',
    path=path,
)
text = text.replace(
    "- Do not combine multiple analytical frames or lists in one candidate.\n- Do not use vague meta-categories without a concrete relation.",
    "- Do not combine multiple analytical frames or lists in one candidate.\n- Return plain text after each number. Do not use Markdown headings, bold, italics, bullets, or labels.\n- Do not use vague meta-categories without a concrete relation.",
)
text = text.replace(
    "- Do not combine several frames or lists in one candidate.\n- Do not return isolated words or acronyms without a relation.",
    "- Do not combine several frames or lists in one candidate.\n- Return plain text after each number. Do not use Markdown headings, bold, italics, bullets, or labels.\n- Do not return isolated words or acronyms without a relation.",
)
write(path, text)


# 2. Live generation is English-only. Evaluation callers keep the historical
# language-neutral prompt because response_language defaults to None.
path = "src/shadowseed/surfacing.py"
text = read(path)
text = replace_once(
    text,
    "def build_chat_prompt(\n    history: list[tuple[str, str]],\n    question: str,\n    surfaced: list[str],\n    boundary: PromptBoundary = DEFAULT_PROMPT_BOUNDARY,\n) -> str:",
    "def build_chat_prompt(\n    history: list[tuple[str, str]],\n    question: str,\n    surfaced: list[str],\n    boundary: PromptBoundary = DEFAULT_PROMPT_BOUNDARY,\n    response_language: str | None = None,\n) -> str:",
    path=path,
)
text = replace_once(
    text,
    "    prompt = (\n        _history_block(history)\n        + f\"Answer this follow-up question thoroughly and insightfully.\\n\\nQuestion: {question}\\n\\n\"",
    "    language_instruction = (\n        f\"Respond in {response_language} only.\\n\\n\" if response_language else \"\"\n    )\n    prompt = (\n        _history_block(history)\n        + language_instruction\n        + f\"Answer this follow-up question thoroughly and insightfully.\\n\\nQuestion: {question}\\n\\n\"",
    path=path,
)
write(path, text)

path = "src/shadowseed/chat.py"
text = read(path)
text = replace_once(
    text,
    "        final_answer = self.model.generate(\n            build_chat_prompt(self.history, question, surfaced),",
    "        final_answer = self.model.generate(\n            build_chat_prompt(\n                self.history, question, surfaced, response_language=\"English\"\n            ),",
    path=path,
)
write(path, text)


# 3. Make recovery measurable only when a later uninfluenced observation window
# exists. A missing observation window is null/unknown, never a zero recovery.
path = "src/shadowseed/benchmark/live_session_measurement.py"
text = read(path)
start = text.index("def _deferral_metrics(")
end = text.index("\ndef run_live_session_measurement(", start)
new_metrics = '''def _deferral_metrics(\n    session: ShadowChatSession,\n    turns: list[dict[str, Any]],\n) -> dict[str, Any]:\n    \"\"\"Measure deferral and recovery only where recovery is observable.\n\n    A suppressed candidate can be scored for later recovery only when at least\n    one later turn was generated without surfaced SSL context. Continuous\n    surfacing therefore yields a null recovery rate instead of a misleading\n    zero. Matching uses the measured session's embedder and dedup threshold.\n    \"\"\"\n\n    records: list[dict[str, Any]] = []\n    influenced_turns = sum(bool(turn.get(\"surfaced_seed_ids\")) for turn in turns)\n    detected_on_influenced_turns = sum(\n        len(turn.get(\"detected_candidates\", []))\n        for turn in turns\n        if turn.get(\"surfaced_seed_ids\")\n    )\n    embedding_cache: dict[str, np.ndarray] = {}\n\n    def _embedding(value: str) -> np.ndarray:\n        if value not in embedding_cache:\n            embedding_cache[value] = session.manager.get_embedding(value)\n        return embedding_cache[value]\n\n    max_words = session.manager.config.max_seed_words\n    threshold = session.manager.config.dedup_threshold\n    for turn in turns:\n        suppressed_turn = int(turn[\"turn\"])\n        later_clean_turns = [\n            later_turn\n            for later_turn in turns\n            if int(later_turn[\"turn\"]) > suppressed_turn\n            and not later_turn.get(\"surfaced_seed_ids\")\n        ]\n        for raw_candidate in turn.get(\"suppressed_self_attributed_candidates\", []):\n            normalized = _normalized_candidates(str(raw_candidate), max_words)\n            evaluable = bool(normalized) and bool(later_clean_turns)\n            best_match: dict[str, Any] | None = None\n            best_similarity = float(\"-inf\")\n            if evaluable:\n                for later_turn in later_clean_turns:\n                    for later_raw in later_turn.get(\"detected_candidates\", []):\n                        later_normalized = _normalized_candidates(str(later_raw), max_words)\n                        for candidate in normalized:\n                            for later_candidate in later_normalized:\n                                similarity = _cosine(\n                                    _embedding(candidate), _embedding(later_candidate)\n                                )\n                                if similarity > best_similarity:\n                                    best_similarity = similarity\n                                    best_match = {\n                                        \"turn\": int(later_turn[\"turn\"]),\n                                        \"candidate\": str(later_raw),\n                                        \"normalized_candidate\": later_candidate,\n                                        \"similarity\": round(similarity, 6),\n                                    }\n            recovered = bool(\n                evaluable and best_match is not None and best_similarity >= threshold\n            )\n            records.append(\n                {\n                    \"turn\": suppressed_turn,\n                    \"candidate\": str(raw_candidate),\n                    \"normalized_candidates\": normalized,\n                    \"normalization_admissible\": bool(normalized),\n                    \"recovery_evaluable\": evaluable,\n                    \"later_uninfluenced_turn_count\": len(later_clean_turns),\n                    \"later_recovered\": recovered,\n                    \"recovery_match\": best_match if recovered else None,\n                }\n            )\n\n    suppressed_count = len(records)\n    admissible_count = sum(record[\"normalization_admissible\"] for record in records)\n    evaluable_count = sum(record[\"recovery_evaluable\"] for record in records)\n    not_evaluable_count = sum(\n        record[\"normalization_admissible\"] and not record[\"recovery_evaluable\"]\n        for record in records\n    )\n    recovered_count = sum(record[\"later_recovered\"] for record in records)\n    unrecovered_evaluable_count = sum(\n        record[\"recovery_evaluable\"] and not record[\"later_recovered\"]\n        for record in records\n    )\n    affected_turns = len({record[\"turn\"] for record in records})\n    distinct_candidates = len(\n        {candidate.casefold() for record in records for candidate in record[\"normalized_candidates\"]}\n    )\n    return {\n        \"method\": \"normalization admissibility plus recovery on later uninfluenced turns\",\n        \"dedup_similarity_threshold\": threshold,\n        \"influenced_turns\": influenced_turns,\n        \"affected_turns\": affected_turns,\n        \"detected_on_influenced_turns\": detected_on_influenced_turns,\n        \"suppressed_candidate_occurrences\": suppressed_count,\n        \"distinct_normalized_suppressed_candidates\": distinct_candidates,\n        \"normalization_admissible_occurrences\": admissible_count,\n        \"recovery_evaluable_occurrences\": evaluable_count,\n        \"recovery_not_evaluable_occurrences\": not_evaluable_count,\n        \"later_recovered_occurrences\": recovered_count,\n        \"unrecovered_evaluable_occurrences\": unrecovered_evaluable_count,\n        \"unrecovered_admissible_occurrences\": unrecovered_evaluable_count,\n        \"suppression_rate_on_influenced_turns\": (\n            round(suppressed_count / detected_on_influenced_turns, 6)\n            if detected_on_influenced_turns\n            else 0.0\n        ),\n        \"later_recovery_rate\": (\n            round(recovered_count / evaluable_count, 6) if evaluable_count else None\n        ),\n        \"candidate_records\": records,\n        \"interpretation\": (\n            \"These counts measure deferred candidate opportunities and observable later \"\n            \"recovery. A null recovery rate means that no later uninfluenced observation \"\n            \"window existed; it is not zero recovery. No truth or usefulness label is inferred.\"\n        ),\n    }\n\n\ndef _aggregate_deferrals(conversations: list[dict[str, Any]]) -> dict[str, Any]:\n    metrics = [conversation[\"deferral_metrics\"] for conversation in conversations]\n    additive = (\n        \"influenced_turns\",\n        \"affected_turns\",\n        \"detected_on_influenced_turns\",\n        \"suppressed_candidate_occurrences\",\n        \"normalization_admissible_occurrences\",\n        \"recovery_evaluable_occurrences\",\n        \"recovery_not_evaluable_occurrences\",\n        \"later_recovered_occurrences\",\n        \"unrecovered_evaluable_occurrences\",\n    )\n    totals = {key: sum(int(metric[key]) for metric in metrics) for key in additive}\n    totals[\"unrecovered_admissible_occurrences\"] = totals[\"unrecovered_evaluable_occurrences\"]\n    unique_candidates = {\n        candidate.casefold()\n        for metric in metrics\n        for record in metric[\"candidate_records\"]\n        for candidate in record[\"normalized_candidates\"]\n    }\n    totals[\"distinct_normalized_suppressed_candidates\"] = len(unique_candidates)\n    detected = totals[\"detected_on_influenced_turns\"]\n    evaluable = totals[\"recovery_evaluable_occurrences\"]\n    totals[\"suppression_rate_on_influenced_turns\"] = (\n        round(totals[\"suppressed_candidate_occurrences\"] / detected, 6)\n        if detected\n        else 0.0\n    )\n    totals[\"later_recovery_rate\"] = (\n        round(totals[\"later_recovered_occurrences\"] / evaluable, 6)\n        if evaluable\n        else None\n    )\n    totals[\"interpretation\"] = (\n        \"Aggregate opportunity-cost proxies. Recovery uses only candidates with a later \"\n        \"uninfluenced observation window; null means not observable, not zero. No truth or \"\n        \"usefulness label is inferred.\"\n    )\n    return totals\n\n'''
text = text[:start] + new_metrics + text[end + 1 :]
text = replace_once(
    text,
    "    return conversations\n\n\ndef _effective_config",
    "    if data.get(\"language\") != \"en\":\n        raise ValueError(\n            \"live session measurement requires an English suite with language='en'\"\n        )\n    return conversations\n\n\ndef _effective_config",
    path=path,
)
text = replace_once(
    text,
    '            "input_version": data.get("version"),\n            "input_sha256": suite_digest,',
    '            "input_version": data.get("version"),\n            "language": data.get("language"),\n            "response_language": "English",\n            "input_sha256": suite_digest,',
    path=path,
)
write(path, text)


# 4. Canonical active session suites are now English. Historical recorded result
# artifacts remain untouched and keep their original input digests.
session_suite = {
    "version": "ssl-session-0.3",
    "language": "en",
    "description": (
        "Multi-turn conversations for the real SSL session pipeline: weight-zero seeding, "
        "recurrence deduplication, Validation Gate decisions across turns, TTL/TrTL lifecycle, "
        "and cross-turn surfacing only after promotion. The conversations deliberately return "
        "to themes so recurrence can emerge without planted answers. Whether a candidate "
        "recurs, promotes, and adds value is left to the pipeline and model."
    ),
    "conversations": [
        {
            "id": "CONV_IR_SHORT",
            "domain": "history and economics",
            "turns": [
                {"question": "Briefly explain why the Industrial Revolution began in Great Britain."},
                {"question": "How did industrialization then spread to continental Europe?"},
                {"question": "What explains why some regions industrialized much faster than others?"},
                {"question": "Which factor is most often underestimated in standard explanations?"},
            ],
        },
        {
            "id": "CONV_STARTUP",
            "domain": "product and growth",
            "turns": [
                {"question": "I am building a social app for teenagers. How do I get the first thousand users?"},
                {"question": "Which features are most effective at retaining users?"},
                {"question": "How do I make the app viral so users invite their friends?"},
                {"question": "What is the best business model for an app aimed at young users?"},
                {"question": "How should I use user data to improve recommendations?"},
                {"question": "How do I scale the infrastructure if growth accelerates?"},
                {"question": "Which metrics should I show investors?"},
                {"question": "How should I handle negative publicity if it occurs?"},
                {"question": "What is the biggest long-term threat to this kind of app?"},
            ],
        },
        {
            "id": "CONV_CITY",
            "domain": "urban development",
            "turns": [
                {"question": "Our city wants to revitalize the downtown area. Where should we start?"},
                {"question": "How can we attract more shops, restaurants, and cafes?"},
                {"question": "How should we improve accessibility and traffic?"},
                {"question": "How can we make downtown more attractive to tourists?"},
                {"question": "What role should housing development play in the city center?"},
                {"question": "How should we add more green public space?"},
                {"question": "How do we keep downtown safe and lively in the evening?"},
                {"question": "How can the municipality finance all of this?"},
                {"question": "What most often goes wrong in downtown revitalization projects?"},
            ],
        },
    ],
}
write("src/shadowseed/data/ssl_session_suite.json", json.dumps(session_suite, indent=2) + "\n")

transfer_suite = {
    "version": "ssl-session-transfer-0.2",
    "language": "en",
    "description": (
        "Doctrine-transfer conversations for the same SSL session pipeline in domains outside "
        "the primary suite. Each conversation returns to its theme across at least seven turns "
        "so a candidate can recur and earn promotion without a planted signal. Results are "
        "reported per domain rather than collapsed into one score."
    ),
    "conversations": [
        {
            "id": "CONV_EDU",
            "domain": "education",
            "turns": [
                {"question": "I am designing a new digital literacy module for lower-secondary students. Where should I start?"},
                {"question": "How should I handle large differences in students' prior knowledge?"},
                {"question": "Which learning activities work best for this topic?"},
                {"question": "How do I assess whether students genuinely understand it instead of merely repeating it?"},
                {"question": "How do I include students who have little digital support at home?"},
                {"question": "How do I make sure colleagues actually adopt the module?"},
                {"question": "What most often goes wrong in curriculum renewal projects like this?"},
            ],
        },
        {
            "id": "CONV_HEALTH",
            "domain": "public health",
            "turns": [
                {"question": "We want to encourage teenagers to drink fewer energy drinks. How should we design the campaign?"},
                {"question": "Which message works better than simply saying that energy drinks are unhealthy?"},
                {"question": "Which channels actually reach this group?"},
                {"question": "How do we measure whether the campaign works?"},
                {"question": "How do we avoid reaching mainly the teenagers who are already health-conscious?"},
                {"question": "What role should schools and parents play?"},
                {"question": "What most often goes wrong in lifestyle campaigns like this?"},
            ],
        },
        {
            "id": "CONV_POLICY",
            "domain": "policy",
            "turns": [
                {"question": "Our municipality wants a climate-adaptation plan for heavy rainfall and flooding. Where should we start?"},
                {"question": "Which measures provide the most impact per euro?"},
                {"question": "How should we involve residents in the choices?"},
                {"question": "How do we finance the plan over several years?"},
                {"question": "Who bears the costs and who receives the benefits of these measures?"},
                {"question": "How do we keep the plan durable across changes in local government?"},
                {"question": "What most often goes wrong in adaptation plans like this?"},
            ],
        },
    ],
}
write(
    "src/shadowseed/data/ssl_session_transfer_suite.json",
    json.dumps(transfer_suite, indent=2) + "\n",
)


# 5. Regression contracts.
path = "tests/test_open_set_model_detector.py"
text = read(path)
anchor = "\ndef test_parse_numbered_seeds_keeps_legitimate_seed_sharing_a_few_common_words() -> None:\n"
new_test = '''\ndef test_parse_numbered_seeds_drops_generative_fewshot_leaks_with_markdown() -> None:\n    raw = \"\"\"\n1. **Colonial capital as an explanatory frame alongside technological innovation.**\n2. Privacy by design as a principle affecting the entire architecture.\n3. **Private international law as a framing dimension for this consumer case.**\n4. Supply-chain concentration as a risk to the announced expansion.\n\"\"\".strip()\n    assert parse_numbered_seeds(raw) == [\n        \"Supply-chain concentration as a risk to the announced expansion.\"\n    ]\n\n'''
if new_test.strip() not in text:
    text = text.replace(anchor, new_test + anchor)
write(path, text)

path = "tests/test_live_runtime.py"
text = read(path)
text = replace_once(
    text,
    '    assert len(model.calls) == 1\n    assert report["runtime_mode"] == "live"',
    '    assert len(model.calls) == 1\n    assert "Respond in English only." in model.calls[0][0]\n    assert report["runtime_mode"] == "live"',
    path=path,
)
write(path, text)

path = "tests/test_live_session_measurement.py"
text = read(path)
text = replace_once(
    text,
    '                "version": "test",\n                "conversations": [',
    '                "version": "test",\n                "language": "en",\n                "conversations": [',
    path=path,
)
text = replace_once(
    text,
    '    assert payload["summary"]["model_id"] == "fake"\n',
    '    assert payload["summary"]["model_id"] == "fake"\n    assert payload["summary"]["language"] == "en"\n    assert payload["summary"]["response_language"] == "English"\n',
    path=path,
)
append_anchor = "\n\n@pytest.mark.parametrize(\n    \"payload, match\",\n"
extra_tests = '''\n\ndef test_live_measurement_requires_explicit_english_suite(\n    tmp_path: Path, monkeypatch: pytest.MonkeyPatch\n) -> None:\n    suite = _suite(tmp_path, turns=1)\n    payload = json.loads(suite.read_text(encoding=\"utf-8\"))\n    payload.pop(\"language\")\n    suite.write_text(json.dumps(payload), encoding=\"utf-8\")\n    monkeypatch.setattr(live_measurement, \"make_backend\", lambda **kwargs: _Model())\n    monkeypatch.setattr(\n        live_measurement, \"make_detector_backend\", lambda *args, **kwargs: _Detector()\n    )\n    monkeypatch.setattr(live_measurement, \"make_embedding_fn\", _semantic_embedder)\n\n    with pytest.raises(ValueError, match=\"English suite\"):\n        run_ssl_session(\n            str(suite),\n            str(tmp_path / \"out.json\"),\n            backend=\"openai\",\n            model_id=\"fake\",\n            embedding_backend=\"sentence-transformers\",\n            runtime_mode=\"live\",\n        )\n\n\ndef test_deferral_recovery_is_null_without_later_uninfluenced_window() -> None:\n    embed, _dimension = _semantic_embedder(\"sentence-transformers\")\n    session = ShadowChatSession(\n        backend=\"fixture\",\n        embedding_backend=\"sentence-transformers\",\n        runtime_mode=\"live\",\n        recurrence_mode=\"pairwise\",\n        model_backend=_Model(),\n        detector_backend=_Detector(),\n        embedding_fn=embed,\n    )\n    turns = [\n        {\n            \"turn\": 0,\n            \"surfaced_seed_ids\": [\"seed-a\"],\n            \"detected_candidates\": [\"Recurring causal mechanism omitted from the answer.\"],\n            \"suppressed_self_attributed_candidates\": [\n                \"Recurring causal mechanism omitted from the answer.\"\n            ],\n        },\n        {\n            \"turn\": 1,\n            \"surfaced_seed_ids\": [\"seed-a\"],\n            \"detected_candidates\": [\"Recurring causal mechanism omitted from the answer.\"],\n            \"suppressed_self_attributed_candidates\": [\n                \"Recurring causal mechanism omitted from the answer.\"\n            ],\n        },\n    ]\n    metrics = live_measurement._deferral_metrics(session, turns)\n    assert metrics[\"normalization_admissible_occurrences\"] == 2\n    assert metrics[\"recovery_evaluable_occurrences\"] == 0\n    assert metrics[\"recovery_not_evaluable_occurrences\"] == 2\n    assert metrics[\"later_recovery_rate\"] is None\n    assert all(\n        record[\"later_uninfluenced_turn_count\"] == 0\n        for record in metrics[\"candidate_records\"]\n    )\n\n'''
if extra_tests.strip() not in text:
    text = text.replace(append_anchor, extra_tests + append_anchor)
write(path, text)


# 6. Language-policy prose now distinguishes active English suites from frozen
# multilingual historical artifacts.
path = "tests/test_language_alignment.py"
text = read(path)
text = text.replace(
    "Benchmark suites and JSON fixtures retain documented Dutch content so benchmark\nmeaning and historical results are not altered — see\n``docs/migration/language-policy.md``. This test therefore substantiates an\nEnglish-core claim, not a whole-repository one.",
    "Active session suites are English. Frozen historical artifacts and explicitly\nmultilingual detector fixtures may retain source-language content — see\n``docs/migration/language-policy.md``. This test substantiates the core-runtime\nEnglish guarantee; active measurement inputs have their own English contract.",
)
write(path, text)

path = "docs/migration/language-policy.md"
text = read(path)
text = text.replace(
    "Some content remains in its source language for a technical reason:\n",
    "Active runtime and session-measurement inputs are English. Some frozen or explicitly multilingual content remains in its source language for a technical reason:\n",
)
text = text.replace(
    "- JSON data fixtures and current result summaries;",
    "- explicitly multilingual detector fixtures and frozen historical result artifacts;",
)
text = text.replace(
    "Historical review rounds,\nmultilingual fixtures, and compatibility tokens retain their original language\nso benchmark meaning and artifact compatibility are not altered.",
    "Historical review rounds, multilingual fixtures, and compatibility tokens retain their\noriginal language so artifact compatibility is not altered. The canonical SSL session\nsuites used for new live measurements are English and declare `language: en`; live\nmeasurement fails closed on suites that do not declare that contract.",
)
write(path, text)


# 7. Reclassify the 0.5B run as diagnostic and document the corrected metric.
path = "benchmarks/results/live_runtime/README.md"
text = read(path)
text = text.replace(
    "This directory records the first intentional real-model measurement of the\none-generation live runtime. The run used the complete packaged session suite\nand calculated fail-closed deferral metrics without manual candidate counting.",
    "This directory preserves the first intentional real-model pipeline run of the\none-generation live runtime. Treat it as diagnostic evidence, not an efficacy result.\nIt exposed model-language drift, a generative few-shot leakage bug, and a recovery\nmetric that was not identifiable under sustained surfacing. The raw JSON artifacts\nare preserved unchanged as historical evidence of that run.",
)
insert = '''\n## Diagnostic status\n\n`Qwen/Qwen2.5-0.5B-Instruct` did not follow the Dutch input language reliably, so\nanswer and detector language drift contaminated the run. The generative detector also\nechoed prompt examples because `_FEWSHOT_GOOD_GENERATIVE` was missing from the\nfew-shot leak blocklist. The stress run influenced 19 of 22 turns, leaving no later\nuninfluenced observation window for most suppressed candidates. Its recorded\n`later_recovery_rate = 0.0` is therefore not evidence of permanent loss.\n\nThe follow-up runtime fixes all three measurement problems. New live measurements use\nan English suite, request English responses explicitly, block all prompt few-shots, and\nreport recovery as `null` when no later uninfluenced observation window exists. An\nevidence-quality rerun should use a materially stronger instruction model; the 0.5B\nartifact remains useful only as a pipeline/regression diagnostic.\n\n'''
if "## Diagnostic status" not in text:
    text = text.replace("## Results\n", insert + "## Results\n")
write(path, text)

path = "docs/usage/cli.md"
text = read(path)
text = text.replace(
    "Live measurement rejects the fixture backend and lexical hash embeddings. It constructs",
    "Live measurement rejects the fixture backend and lexical hash embeddings and requires an\nEnglish input suite declaring `\"language\": \"en\"`. Live answers are explicitly requested\nin English. It constructs",
)
text = text.replace(
    "semantically on a later unsuppressed turn.",
    "semantically on a later uninfluenced turn. Recovery is scored only when such a later\nobservation window exists; otherwise `later_recovery_rate` is `null`, never a synthetic zero.",
)
text = text.replace(
    "The first reviewed real-model run and a separate non-production stress measurement are in",
    "The first real-model pipeline run and a separate non-production stress measurement are in",
)
text = text.replace(
    "authority and influence counts must not be presented as product behavior.",
    "authority and influence counts must not be presented as product behavior. The 0.5B run is\ndiagnostic only; evidence-quality reruns should use a stronger instruction model with stable\nEnglish instruction following.",
)
write(path, text)

path = "CHANGELOG.md"
text = read(path)
marker = "## Unreleased - Live runtime review follow-up\n\n"
bullets = (
    "- Live measurement now requires an English suite and live generation explicitly requests English output. "
    "The canonical primary and transfer session suites are English.\n"
    "- The detector leak filter now covers generative few-shot examples as well as absence examples, including Markdown-wrapped echoes. "
    "Detector prompts also require plain-text candidates.\n"
    "- Deferral recovery is now scored only when a later uninfluenced observation window exists. Runs with continuous surfacing report a null recovery rate instead of conflating unobservability with zero recovery.\n"
    "- The recorded Qwen2.5-0.5B live run is explicitly classified as diagnostic pipeline evidence rather than efficacy evidence; its raw artifacts remain unchanged.\n"
)
if bullets.splitlines()[0] not in text:
    text = text.replace(marker, marker + bullets)
write(path, text)

print("live runtime hardening patch materialized")
