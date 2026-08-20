"""Verify that built Python distributions carry the exact repository license."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path


def _license_member(names: list[str]) -> str | None:
    matches = [name for name in names if Path(name).name in {"LICENSE", "LICENSE.txt"}]
    if len(matches) != 1:
        return None
    return matches[0]


def verify_distribution(path: Path, expected: bytes) -> str:
    path = path.resolve()
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            member = _license_member(archive.namelist())
            if member is None:
                raise ValueError(f"{path.name} must contain exactly one LICENSE file")
            actual = archive.read(member)
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            names = [member.name for member in archive.getmembers() if member.isfile()]
            member = _license_member(names)
            if member is None:
                raise ValueError(f"{path.name} must contain exactly one LICENSE file")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise ValueError(f"could not read LICENSE from {path.name}")
            actual = extracted.read()
    else:
        raise ValueError(f"unsupported distribution type: {path.name}")
    if actual != expected:
        raise ValueError(f"{path.name} contains a LICENSE that differs from repository LICENSE")
    return member


def verify_distributions(dist_dir: Path, license_path: Path) -> dict[str, str]:
    expected = license_path.read_bytes()
    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(
        path for path in dist_dir.glob("*.tar.gz") if not path.name.startswith("shadowseed-workbench-")
    )
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("expected exactly one wheel and one Python source distribution")
    return {
        wheels[0].name: verify_distribution(wheels[0], expected),
        sdists[0].name: verify_distribution(sdists[0], expected),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--license", type=Path, default=Path("LICENSE"))
    args = parser.parse_args(argv)
    verified = verify_distributions(args.dist_dir, args.license)
    for filename, member in verified.items():
        print(f"{filename}: {member}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
