from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    intake = Path("src/shadowseed/intake.py")
    replace_once(
        intake,
        "    if manager._embedding_fn is not None:\n"
        "        return normalize_embedding(manager._embedding_fn(text))\n"
        "    embedder = load_embedder(manager)\n",
        "    if manager._embedding_fn is not None:\n"
        "        return manager._normalize_embedding(manager._embedding_fn(text))\n"
        "    embedder = manager._load_embedder()\n",
    )
    replace_once(
        intake,
        "    normalized = normalize_detection_candidates(\n"
        "        raw_candidates,\n",
        "    normalized = manager.normalize_detection_candidates(\n"
        "        raw_candidates,\n",
    )
    replace_once(
        intake,
        "            seed_id = add_or_update_seed(\n"
        "                manager,\n"
        "                candidate,\n",
        "            seed_id = manager.add_or_update_seed(\n"
        "                candidate,\n",
    )
    replace_once(
        intake,
        "    if not is_atomic_seed(text, max_seed_words=manager.config.max_seed_words):\n"
        "        raise ValueError(\"Seed appears too broad. Split it into atomic seeds first.\")\n\n"
        "    new_embedding = get_embedding(manager, text)\n"
        "    if deduplicate:\n"
        "        deduplicated = maybe_deduplicate_seed(manager, new_embedding)\n"
        "        if deduplicated is not None:\n"
        "            seed_id, similarity = deduplicated\n"
        "            return activate_existing_seed(manager, seed_id, similarity)\n\n"
        "    return create_seed(\n"
        "        manager,\n"
        "        text,\n"
        "        new_embedding,\n"
        "        trigger_keywords,\n"
        "        origin=origin,\n"
        "    )\n",
        "    if not manager.is_atomic_seed(\n"
        "        text, max_seed_words=manager.config.max_seed_words\n"
        "    ):\n"
        "        raise ValueError(\"Seed appears too broad. Split it into atomic seeds first.\")\n\n"
        "    new_embedding = manager.get_embedding(text)\n"
        "    if deduplicate:\n"
        "        deduplicated = manager._maybe_deduplicate_seed(new_embedding)\n"
        "        if deduplicated is not None:\n"
        "            seed_id, similarity = deduplicated\n"
        "            return manager._activate_existing_seed(seed_id, similarity)\n\n"
        "    return manager._create_seed(\n"
        "        text,\n"
        "        new_embedding,\n"
        "        trigger_keywords,\n"
        "        origin=origin,\n"
        "    )\n",
    )

    manager = Path("src/shadowseed/manager.py")
    text = manager.read_text(encoding="utf-8")
    text = text.replace(
        "from shadowseed.seed_normalization import normalize_detection_candidates\n",
        "",
        1,
    )
    old = "        return intake_engine.is_atomic_seed(text, max_seed_words=max_seed_words)\n"
    new = (
        "        effective_limit = (\n"
        "            DEFAULT_CONFIG.max_seed_words\n"
        "            if max_seed_words is None\n"
        "            else max_seed_words\n"
        "        )\n"
        "        return intake_engine.is_atomic_seed(\n"
        "            text, max_seed_words=effective_limit\n"
        "        )\n"
    )
    if text.count(old) != 1:
        raise SystemExit("manager atomicity facade anchor not found")
    manager.write_text(text.replace(old, new, 1), encoding="utf-8")

    tests = Path("tests/test_intake_extraction.py")
    text = tests.read_text(encoding="utf-8").rstrip()
    text += '''


def test_get_embedding_keeps_the_historical_normalization_override_point() -> None:
    class HookedManager(SSLManager):
        @staticmethod
        def _normalize_embedding(_embedding: np.ndarray) -> np.ndarray:
            return np.array([9.0, 8.0, 7.0])

    manager = HookedManager(embedding_fn=lambda _text: np.array([1.0, 2.0, 3.0]))

    assert np.array_equal(
        manager.get_embedding("candidate"), np.array([9.0, 8.0, 7.0])
    )


def test_ingest_keeps_normalization_and_add_override_points() -> None:
    class HookedManager(SSLManager):
        def normalize_detection_candidates(
            self,
            candidates,
            expand_short_fragments: bool = True,
            split_broad: bool = True,
        ) -> list[str]:
            del candidates, expand_short_fragments, split_broad
            return ["hooked candidate"]

        def add_or_update_seed(self, text, **_kwargs) -> str:
            assert text == "hooked candidate"
            return "hooked-id"

    manager = HookedManager(embedding_fn=_embedding)

    result = manager.ingest_detection_candidates(["raw candidate"])

    assert result["accepted"] == [
        {"seed_id": "hooked-id", "text": "hooked candidate"}
    ]


def test_add_or_update_keeps_internal_manager_override_points() -> None:
    class HookedManager(SSLManager):
        @staticmethod
        def is_atomic_seed(_text: str, max_seed_words: int | None = None) -> bool:
            assert max_seed_words is not None
            return True

        def get_embedding(self, _text: str) -> np.ndarray:
            return np.array([1.0, 0.0, 0.0])

        def _maybe_deduplicate_seed(self, _embedding: np.ndarray):
            return "existing-id", 0.99

        def _activate_existing_seed(self, seed_id: str, similarity: float) -> str:
            assert (seed_id, similarity) == ("existing-id", 0.99)
            return "hooked-result"

    manager = HookedManager(embedding_fn=_embedding)

    assert manager.add_or_update_seed("candidate") == "hooked-result"
'''
    tests.write_text(text + "\n", encoding="utf-8")

    Path(".github/workflows/harden-intake-extraction.yml").unlink()
    Path(".github/scripts/harden_intake_extraction.py").unlink()


if __name__ == "__main__":
    main()
