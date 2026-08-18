from __future__ import annotations

import importlib.util
from pathlib import Path


path = Path(__file__).with_name("materialize_capability_parser_diagnostics.py")
spec = importlib.util.spec_from_file_location("capability_parser_materializer", path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"unable to load materializer from {path}")
materializer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materializer)

_original_replace_once = materializer.replace_once


def _scoped_replace_once(text: str, old: str, new: str, label: str) -> str:
    if label == "HF model constructor":
        count = text.count(old)
        if count != 2:
            raise RuntimeError(
                f"HF model constructor: expected HF + OpenAI shape matches, found {count}"
            )
        # HFTransformersBackend appears before OpenAIBackend in adapters/models.py.
        # Replace only that first constructor; the OpenAI constructor remains unchanged.
        return text.replace(old, new, 1)
    return _original_replace_once(text, old, new, label)


materializer.replace_once = _scoped_replace_once
materializer.main()
