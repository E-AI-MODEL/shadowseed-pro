#!/usr/bin/env python3
"""Combine verified privacy-minimized Workbench support bundles into one dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from shadowseed.support_collection import write_support_dataset


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Shadowseed Workbench support ZIPs and aggregate their "
            "privacy-minimized records into one versioned JSON dataset."
        )
    )
    parser.add_argument("bundles", nargs="+", type=Path, help="support ZIP files")
    parser.add_argument(
        "--collection-id",
        required=True,
        help="stable study or collection identifier, for example pilot-2026-08",
    )
    parser.add_argument("--output", required=True, type=Path, help="output JSON file")
    args = parser.parse_args()

    target = write_support_dataset(
        args.bundles,
        collection_id=args.collection_id,
        output=args.output,
    )
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
