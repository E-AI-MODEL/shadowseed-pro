"""Agent-facing safety helpers for Shadow Seed Learning.

This package is intentionally separate from the core `shadowseed` runtime. It
contains adapter-level policy checks for agent and RAG integrations, not new SSL
mechanics.
"""

from shadowseed_agent.agent_contract import (
    AgentSafetyContract,
    InfluenceAction,
    InfluenceDecision,
    evidence_can_support_gate,
    has_logged_promotion,
)
from shadowseed_agent.audit_policy import (
    AgentInfluenceRecord,
    InfluenceReplayError,
    WeightlessInfluenceError,
    assert_influence_records_valid,
    assert_no_weightless_influence,
)
from shadowseed_agent.retrieval_policy import can_seed_trigger_retrieval

__all__ = [
    "AgentInfluenceRecord",
    "AgentSafetyContract",
    "InfluenceAction",
    "InfluenceDecision",
    "InfluenceReplayError",
    "WeightlessInfluenceError",
    "assert_influence_records_valid",
    "assert_no_weightless_influence",
    "can_seed_trigger_retrieval",
    "evidence_can_support_gate",
    "has_logged_promotion",
]
