"""SQLite schema used by the local tester workspace."""

from __future__ import annotations

SCHEMA_VERSION = 2
PREVIOUS_SCHEMA_VERSION = 1

DDL = (
    """
    CREATE TABLE IF NOT EXISTS workspace_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        profile_id TEXT NOT NULL,
        backend TEXT NOT NULL,
        model_id TEXT,
        config_json TEXT NOT NULL,
        state_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS turns (
        session_id TEXT NOT NULL,
        turn_index INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        baseline_answer TEXT NOT NULL,
        ssl_answer TEXT NOT NULL,
        report_json TEXT NOT NULL,
        PRIMARY KEY (session_id, turn_index),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS seeds (
        session_id TEXT NOT NULL,
        seed_id TEXT NOT NULL,
        snapshot_json TEXT NOT NULL,
        PRIMARY KEY (session_id, seed_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        session_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_key TEXT NOT NULL,
        sequence_no INTEGER NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY (session_id, event_type, event_key),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tester_feedback (
        feedback_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        turn_index INTEGER NOT NULL,
        seed_id TEXT,
        overall TEXT NOT NULL,
        seed_effect TEXT NOT NULL,
        note TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS production_ledger (
        sequence_no INTEGER PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        workspace_id TEXT NOT NULL,
        audit_epoch TEXT NOT NULL,
        session_id TEXT,
        seed_id TEXT,
        event_type TEXT NOT NULL,
        request_id TEXT UNIQUE,
        actor_id TEXT,
        actor_scope_id TEXT,
        capability TEXT,
        auth_method TEXT,
        policy_version TEXT,
        payload_json TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        event_format_version INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_session ON tester_feedback(session_id, turn_index)",
    "CREATE INDEX IF NOT EXISTS idx_production_ledger_session ON production_ledger(session_id, sequence_no)",
    "CREATE INDEX IF NOT EXISTS idx_production_ledger_type ON production_ledger(event_type, sequence_no)",
)

MIGRATION_1_TO_2 = (
    """
    CREATE TABLE production_ledger (
        sequence_no INTEGER PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        workspace_id TEXT NOT NULL,
        audit_epoch TEXT NOT NULL,
        session_id TEXT,
        seed_id TEXT,
        event_type TEXT NOT NULL,
        request_id TEXT UNIQUE,
        actor_id TEXT,
        actor_scope_id TEXT,
        capability TEXT,
        auth_method TEXT,
        policy_version TEXT,
        payload_json TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        event_format_version INTEGER NOT NULL
    )
    """,
    "CREATE INDEX idx_production_ledger_session ON production_ledger(session_id, sequence_no)",
    "CREATE INDEX idx_production_ledger_type ON production_ledger(event_type, sequence_no)",
)
