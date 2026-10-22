#!/usr/bin/env python3
"""Layer G vNext synthetic preflight. Refuses real/human-labelled experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shadowseed_research.benchmark.layer_g_vnext import write_preflight


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--fixture", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    report = write_preflight(args.fixture, args.output)
    if report["status"] != "synthetic_preflight_only" or report["research_claim"] != "none":
        raise RuntimeError("research claim boundary violated")
    print(json.dumps({
        "status": report["status"], "research_claim": report["research_claim"],
        "n_cases": len(report["cases"]), "fixture_sha256": report["fixture_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
