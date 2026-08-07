from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    test_path = Path("tests/test_intake_extraction.py")
    replace_once(
        test_path,
        '''    assert [item["text"] for item in result["accepted"]] == [
        "alpha omission",
        "beta omission",
    ]
    assert result["rejected"] == [
        {"text": "alpha omission", "reason": "duplicate"}
    ]
''',
        '''    assert [item["text"] for item in result["accepted"]] == [
        "alpha omission.",
        "beta omission.",
    ]
    assert result["rejected"] == [
        {"text": "alpha omission.", "reason": "duplicate"}
    ]
''',
    )

    language_path = Path("tests/test_language_alignment.py")
    replace_once(
        language_path,
        '''    "shadowseed/manager.py": {
        "zoals", "bijvoorbeeld", "analysekader", "oorzaken", "gevolgen",
        "contexten", "perspectieven", "meerdere", "schaalbaarheid",
        "kolonialisme", "ontbreekt", "ontbreken",
    },
''',
        '''    "shadowseed/intake.py": {
        "zoals", "bijvoorbeeld", "analysekader", "oorzaken", "gevolgen",
        "contexten", "perspectieven", "meerdere", "schaalbaarheid",
        "kolonialisme", "ontbreekt", "ontbreken",
    },
''',
    )

    Path(".github/workflows/fix-intake-ci.yml").unlink()
    Path(".github/scripts/fix_intake_ci.py").unlink()


if __name__ == "__main__":
    main()
