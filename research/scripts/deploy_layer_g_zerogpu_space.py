"""Publish the Shadowseed Space ONLY to free ZeroGPU.

Hugging Face token must be preconfigured by the owner; never print, store or
forward it into the Space. There is no paid-hardware fallback.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

from build_layer_g_zerogpu_space import build_space, git_sha

TARGET = "EAImodelserie5/shadowseed-layerg-zero"
OWNER = "EAImodelserie5"
FREE_HARDWARE = "zero-a10g"


def publish_space(*, token: str, source_sha: str) -> str:
    if not token:
        raise RuntimeError("HF_TOKEN missing: no Hugging Face Space created")
    from huggingface_hub import HfApi
    from huggingface_hub.utils import RepositoryNotFoundError

    api = HfApi(token=token)
    identity = api.whoami()
    if identity.get("name") != OWNER:
        raise RuntimeError("Token owner does not match target Space owner")
    existed = True
    try:
        api.repo_info(repo_id=TARGET, repo_type="space")
    except RepositoryNotFoundError:
        existed = False

    if not existed:
        # Important: free account must have ZeroGPU eligibility.
        # Never create on a default/paid fallback.
        api.create_repo(
            repo_id=TARGET,
            repo_type="space",
            space_sdk="gradio",
            space_hardware=FREE_HARDWARE,
            private=False,
            exist_ok=False,
        )
    runtime = api.get_space_runtime(repo_id=TARGET)
    hardware = getattr(runtime, "requested_hardware", None) or getattr(
        runtime, "hardware", None
    )
    if hardware != FREE_HARDWARE:
        raise RuntimeError(
            "ZeroGPU hardware is not confirmed. Refusing deployment to "
            "unverified or paid hardware."
        )
    with tempfile.TemporaryDirectory(prefix="shadowseed_zero_bundle_") as tmp:
        root = Path(tmp) / "space"
        build_space(root, source_sha=source_sha)
        api.upload_folder(
            folder_path=str(root),
            repo_id=TARGET,
            repo_type="space",
            commit_message="Deploy Shadowseed canonical L2 source " + source_sha[:12],
        )
    return "https://huggingface.co/spaces/" + TARGET


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args()
    sha = args.source_sha or git_sha()
    # Never print tokens, authorization responses or user environment values.
    url = publish_space(token=os.environ.get("HF_TOKEN", "").strip(), source_sha=sha)
    print("Source uploaded to verified ZeroGPU Space: " + url)
    print("A successful upload does NOT mean that 14B has generated activations.")


if __name__ == "__main__":
    main()
