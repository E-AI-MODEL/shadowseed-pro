"""Production-local readiness checks shared by the doctor command."""

from __future__ import annotations

import os

from shadowseed.application.models import HealthCheck
from shadowseed.application.workspace import WorkspaceService


def workspace_integrity_check(service: WorkspaceService) -> HealthCheck:
    report = service.repository.verify_production_integrity()
    return HealthCheck(
        "production_integrity",
        "ok",
        f"verified ledger head sequence {report['sequence_no']}",
    )


def workspace_permission_check(service: WorkspaceService) -> HealthCheck:
    if os.name == "nt":
        return HealthCheck(
            "workspace_permissions",
            "ok",
            "Windows current-user ACL boundary",
        )
    expected = {
        service.paths.root: 0o700,
        service.paths.exports: 0o700,
        service.paths.attachments: 0o700,
        service.paths.logs: 0o700,
        service.paths.config: 0o600,
        service.paths.identity: 0o600,
        service.paths.database: 0o600,
    }
    broad = [
        f"{path.name}:{path.stat().st_mode & 0o777:o}"
        for path, mode in expected.items()
        if path.exists() and path.stat().st_mode & 0o777 != mode
    ]
    if broad:
        return HealthCheck(
            "workspace_permissions",
            "error",
            "unexpected permissions: " + ", ".join(broad),
            "Restrict workspace directories to owner-only access and files to owner read/write.",
        )
    return HealthCheck(
        "workspace_permissions",
        "ok",
        "owner-only local workspace permissions",
    )
