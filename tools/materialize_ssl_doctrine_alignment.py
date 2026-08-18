"""Temporary branch materializer for the 2026-08 SSL doctrine alignment.

The script is intentionally exact-match based. It must fail if main changed in a
way that makes a reviewed replacement ambiguous. It is removed before the final
PR head; the resulting runtime changes and regression tests are the deliverable.
"""

from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"expected exactly one match in {path}, found {count}: {old!r}"
        )
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_exact_count(path: str, old: str, new: str, expected: int) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"expected {expected} matches in {path}, found {count}: {old!r}"
        )
    target.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_once(
        "src/shadowseed/chat.py",
        "        ingest = self.manager.ingest_detection_candidates(candidates, origin=origin)\n",
        "        ingest = self.manager.ingest_detection_candidates(\n"
        "            candidates,\n"
        "            expand_short_fragments=False,\n"
        "            split_broad=False,\n"
        "            origin=origin,\n"
        "        )\n",
    )
    replace_once(
        "src/shadowseed/chat.py",
        "        ingest = self.manager.ingest_detection_candidates(candidates)\n",
        "        ingest = self.manager.ingest_detection_candidates(\n"
        "            candidates,\n"
        "            expand_short_fragments=False,\n"
        "            split_broad=False,\n"
        "        )\n",
    )
    replace_once(
        "src/shadowseed/benchmark/live_session_measurement.py",
        "normalize_detection_candidates([text])",
        "normalize_detection_candidates(\n"
        "            [text], expand_short_fragments=False, split_broad=False\n"
        "        )",
    )

    replace_once(
        "src/shadowseed/intake.py",
        "    lowered = text.lower().strip()\n    separators =",
        "    lowered = text.lower().strip()\n"
        "    if not lowered:\n"
        "        return False\n"
        "    separators =",
    )
    replace_once(
        "src/shadowseed/intake.py",
        '    seed_id = f"ss_{len(manager._seeds) + 1:03d}"\n',
        "    numeric_ids: list[int] = []\n"
        "    for existing_id in manager._seeds:\n"
        "        match = re.fullmatch(r\"ss_(\\d+)\", existing_id)\n"
        "        if match is not None:\n"
        "            numeric_ids.append(int(match.group(1)))\n"
        '    seed_id = f"ss_{max(numeric_ids, default=0) + 1:03d}"\n',
    )

    replace_once(
        "src/shadowseed/core_config.py",
        "    contradiction_trace_penalty: float = 0.5\n\n    def to_dict",
        "    contradiction_trace_penalty: float = 0.5\n\n"
        "    def __post_init__(self) -> None:\n"
        "        numeric_fields = (\n"
        "            \"trace_start\",\n"
        "            \"half_life_turns\",\n"
        "            \"dedup_threshold\",\n"
        "            \"promotion_threshold\",\n"
        "            \"dormant_threshold\",\n"
        "            \"validation_increment\",\n"
        "            \"contradiction_penalty\",\n"
        "            \"reward_step\",\n"
        "            \"penalty_step\",\n"
        "            \"max_trace\",\n"
        "            \"reactivation_increment\",\n"
        "            \"min_trace_for_gate\",\n"
        "            \"contradiction_trace_penalty\",\n"
        "        )\n"
        "        for name in numeric_fields:\n"
        "            value = getattr(self, name)\n"
        "            if isinstance(value, bool) or not isinstance(value, (int, float)):\n"
        "                raise ValueError(f\"{name} must be a finite number\")\n"
        "            if not math.isfinite(float(value)):\n"
        "                raise ValueError(f\"{name} must be finite\")\n\n"
        "        integer_fields = (\n"
        "            \"min_occurrences_for_gate\",\n"
        "            \"min_evidence_for_gate\",\n"
        "            \"max_seed_words\",\n"
        "            \"dormant_ttl_turns\",\n"
        "        )\n"
        "        for name in integer_fields:\n"
        "            value = getattr(self, name)\n"
        "            if isinstance(value, bool) or not isinstance(value, int):\n"
        "                raise ValueError(f\"{name} must be an integer\")\n\n"
        "        if self.trace_start <= 0.0:\n"
        "            raise ValueError(\"trace_start must be > 0\")\n"
        "        if self.half_life_turns <= 0.0:\n"
        "            raise ValueError(\"half_life_turns must be > 0\")\n"
        "        if not -1.0 <= self.dedup_threshold <= 1.0:\n"
        "            raise ValueError(\"dedup_threshold must be between -1 and 1\")\n"
        "        if not 0.0 < self.promotion_threshold <= 1.0:\n"
        "            raise ValueError(\"promotion_threshold must be in (0, 1]\")\n"
        "        if self.dormant_threshold < 0.0:\n"
        "            raise ValueError(\"dormant_threshold must be >= 0\")\n"
        "        for name in (\n"
        "            \"validation_increment\",\n"
        "            \"contradiction_penalty\",\n"
        "            \"reward_step\",\n"
        "            \"penalty_step\",\n"
        "        ):\n"
        "            value = float(getattr(self, name))\n"
        "            if not 0.0 <= value <= 1.0:\n"
        "                raise ValueError(f\"{name} must be between 0 and 1\")\n"
        "        if self.max_trace <= 0.0:\n"
        "            raise ValueError(\"max_trace must be > 0\")\n"
        "        if self.max_trace < self.trace_start:\n"
        "            raise ValueError(\"max_trace must be >= trace_start\")\n"
        "        if self.reactivation_increment < 0.0:\n"
        "            raise ValueError(\"reactivation_increment must be >= 0\")\n"
        "        if self.min_occurrences_for_gate < 1:\n"
        "            raise ValueError(\"min_occurrences_for_gate must be >= 1\")\n"
        "        if self.min_evidence_for_gate < 0:\n"
        "            raise ValueError(\"min_evidence_for_gate must be >= 0\")\n"
        "        if self.min_trace_for_gate < 0.0:\n"
        "            raise ValueError(\"min_trace_for_gate must be >= 0\")\n"
        "        if self.max_seed_words < 1:\n"
        "            raise ValueError(\"max_seed_words must be >= 1\")\n"
        "        if self.dormant_ttl_turns < 0:\n"
        "            raise ValueError(\"dormant_ttl_turns must be >= 0\")\n"
        "        if self.contradiction_trace_penalty < 0.0:\n"
        "            raise ValueError(\"contradiction_trace_penalty must be >= 0\")\n\n"
        "    def to_dict",
    )

    replace_once(
        "src/shadowseed/surfacing.py",
        "        if self.surface_threshold < -1.0 or self.surface_threshold > 1.0:\n"
        "            raise ValueError(\"surface_threshold must be between -1.0 and 1.0\")\n",
        "        if self.surface_threshold < -1.0 or self.surface_threshold > 1.0:\n"
        "            raise ValueError(\"surface_threshold must be between -1.0 and 1.0\")\n"
        "        if self.surface_top_k is not None:\n"
        "            if isinstance(self.surface_top_k, bool) or not isinstance(self.surface_top_k, int):\n"
        "                raise ValueError(\"surface_top_k must be an integer or None\")\n"
        "            if self.surface_top_k < 0:\n"
        "                raise ValueError(\"surface_top_k must be >= 0 or None\")\n",
    )
    replace_once(
        "src/shadowseed/surfacing.py",
        "    if top_k is not None and top_k >= 0:\n        ranked = ranked[:top_k]\n",
        "    if top_k is not None:\n"
        "        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:\n"
        "            raise ValueError(\"top_k must be a non-negative integer or None\")\n"
        "        ranked = ranked[:top_k]\n",
    )

    replace_once(
        "src/shadowseed/models.py",
        "    if not isinstance(data[\"text\"], str):\n"
        "        raise TypeError(f\"seed 'text' must be a string, got {type(data['text']).__name__}\")\n",
        "    if not isinstance(data[\"text\"], str):\n"
        "        raise TypeError(f\"seed 'text' must be a string, got {type(data['text']).__name__}\")\n"
        "    if not data[\"text\"].strip():\n"
        "        raise ValueError(\"seed 'text' must be a non-empty string\")\n",
    )

    replace_once(
        "src/shadowseed/gate/runtime_adapter.py",
        "    External evidence is one observation per source and kind. The\n",
        "    External evidence is one observation per underlying source reference, regardless\n"
        "    of external signal kind. The\n",
    )
    replace_once(
        "src/shadowseed/gate/runtime_adapter.py",
        '        return f"external:{signal.kind.value}:{identity}"\n',
        '        return f"external:{identity}"\n',
    )

    replace_once(
        "src/shadowseed/storage/sqlite.py",
        "        self.database_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "        temporary = self.database_path.with_suffix(\".restore.tmp\")\n"
        "        shutil.copy2(source_path, temporary)\n"
        "        os.replace(temporary, self.database_path)\n"
        "        self.initialize()\n",
        "        self.database_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "        temporary = self.database_path.with_suffix(\".restore.tmp\")\n"
        "        temporary.unlink(missing_ok=True)\n"
        "        shutil.copy2(source_path, temporary)\n"
        "        try:\n"
        "            candidate = SQLiteWorkspaceRepository(temporary)\n"
        "            candidate.initialize()\n"
        "        except Exception:\n"
        "            temporary.unlink(missing_ok=True)\n"
        "            raise\n"
        "        os.replace(temporary, self.database_path)\n"
        "        self.initialize()\n",
    )

    replace_once(
        "docs/architecture/overview.md",
        "Verified external support requires a non-empty `source_ref`; repeated\n"
        "  use of the same source-and-kind pair is idempotent. The same reference under a\n"
        "  different signal kind is distinct support.",
        "Verified external support requires a non-empty `source_ref`; repeated\n"
        "  use of the same underlying source reference is idempotent across external signal\n"
        "  kinds. Signal kind remains channel provenance, not a second evidence identity.",
    )
    replace_once(
        "docs/architecture/gate-contracts.md",
        "Evidence identity is the source-and-kind pair, so the\n"
        "  same `source_ref` under a different external signal kind is distinct support.",
        "Evidence identity is the underlying `source_ref`, so the same source does not\n"
        "  accumulate authority merely by arriving under a different external signal kind.",
    )
    replace_once(
        "docs/architecture/adr/ADR-001-validation-gate-authority.md",
        "repeated use of the same source-and-kind pair is\n"
        "   idempotent, while the same reference under a different signal kind is\n"
        "   distinct support.",
        "repeated use of the same underlying source reference is\n"
        "   idempotent across external signal kinds. Signal kind records the channel; it\n"
        "   does not create an independent evidence unit (ADR-004).",
    )
    replace_exact_count(
        "docs/workbench/README.md",
        "shadowseed-workbench:0.4.1",
        "shadowseed-workbench:0.4.2",
        2,
    )


if __name__ == "__main__":
    main()
