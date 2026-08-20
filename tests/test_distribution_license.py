from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.verify_distribution_license import verify_distribution, verify_distributions


def test_distribution_license_verifier_accepts_exact_wheel_and_sdist(tmp_path: Path) -> None:
    license_path = tmp_path / "LICENSE"
    expected = b"PolyForm terms\nRequired Notice: test\n"
    license_path.write_bytes(expected)
    dist = tmp_path / "dist"
    dist.mkdir()

    wheel = dist / "shadowseed-0.6.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("shadowseed-0.6.0.dist-info/licenses/LICENSE", expected)

    sdist = dist / "shadowseed-0.6.0.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        info = tarfile.TarInfo("shadowseed-0.6.0/LICENSE")
        info.size = len(expected)
        archive.addfile(info, io.BytesIO(expected))

    verified = verify_distributions(dist, license_path)
    assert set(verified) == {wheel.name, sdist.name}


def test_distribution_license_verifier_rejects_missing_or_changed_terms(tmp_path: Path) -> None:
    expected = b"expected\n"
    wheel = tmp_path / "shadowseed-0.6.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("shadowseed-0.6.0.dist-info/licenses/LICENSE", b"changed\n")
    with pytest.raises(ValueError, match="differs"):
        verify_distribution(wheel, expected)

    missing = tmp_path / "shadowseed-0.6.1-py3-none-any.whl"
    with zipfile.ZipFile(missing, "w") as archive:
        archive.writestr("shadowseed/__init__.py", "")
    with pytest.raises(ValueError, match="exactly one LICENSE"):
        verify_distribution(missing, expected)
