from __future__ import annotations

import tools.materialize_capability_parser_diagnostics as materializer


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
