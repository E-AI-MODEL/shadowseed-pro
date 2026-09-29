"""Process-local serialization for persisted session mutations."""

from __future__ import annotations

from threading import Lock, RLock

from shadowseed.storage.sqlite import SQLiteWorkspaceRepository


_LOCKS_GUARD = Lock()
_SESSION_LOCKS: dict[tuple[str, str], RLock] = {}


def session_mutation_lock(
    repository: SQLiteWorkspaceRepository,
    session_id: str,
) -> RLock:
    """Return the shared mutation lock for one repository-backed session."""

    key = (str(repository.database_path), str(session_id))
    with _LOCKS_GUARD:
        lock = _SESSION_LOCKS.get(key)
        if lock is None:
            lock = RLock()
            _SESSION_LOCKS[key] = lock
        return lock
