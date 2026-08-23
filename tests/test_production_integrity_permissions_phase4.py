from __future__ import annotations

import os
from pathlib import Path

import pytest

from shadowseed.application.workspace import WorkspaceService
from shadowseed.storage.integrity import load_integrity_key


@pytest.mark.skipif(os.name == "nt", reason="POSIX file-mode check")
def test_protected_integrity_material_is_owner_only(tmp_path: Path) -> None:
    service = WorkspaceService(tmp_path / "workspace")
    service.initialize()
    integrity = service._integrity_dir(service.workspace_id)

    assert (integrity / "integrity.key").stat().st_mode & 0o777 == 0o600
    assert (integrity / "anchor.json").stat().st_mode & 0o777 == 0o600
    assert integrity.stat().st_mode & 0o777 == 0o700


@pytest.mark.skipif(os.name == "nt", reason="POSIX file-mode check")
def test_overbroad_integrity_key_fails_closed(tmp_path: Path) -> None:
    service = WorkspaceService(tmp_path / "workspace")
    service.initialize()
    key_path = service._integrity_dir(service.workspace_id) / "integrity.key"
    key_path.chmod(0o644)

    with pytest.raises(ValueError, match="permissions are too broad"):
        load_integrity_key(key_path)
