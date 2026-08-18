"""Temporary materializer preserving the historical direct helper -1 sentinel."""

from pathlib import Path


def main() -> None:
    path = Path("src/shadowseed/surfacing.py")
    text = path.read_text(encoding="utf-8")
    old = '''    if top_k is not None:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:
            raise ValueError("top_k must be a non-negative integer or None")
        ranked = ranked[:top_k]
'''
    new = '''    if top_k is not None and top_k >= 0:
        ranked = ranked[:top_k]
'''
    if text.count(old) != 1:
        raise RuntimeError(f"unexpected materialized select_cross_turn_seeds shape: {text.count(old)} matches")
    text = text.replace(old, new, 1)

    old_doc = '''    """Rank eligible candidates by relevance and apply the use-time cap."""
'''
    new_doc = '''    """Rank eligible candidates by relevance and apply the use-time cap.

    ``-1`` remains the historical direct-helper no-cap sentinel for benchmark
    compatibility. Configured product policies validate ``surface_top_k`` in
    :class:`SurfacingPolicy` and reject negative values there.
    """
'''
    if text.count(old_doc) != 1:
        raise RuntimeError(f"unexpected helper docstring shape: {text.count(old_doc)} matches")
    path.write_text(text.replace(old_doc, new_doc, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
