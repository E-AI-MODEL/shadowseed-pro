# SSL Agent Safety Contract

> Status: draft adapter contract
> Date: 2026-06-27
> Evidence layer: agent/RAG integration boundary
> Current source: no — first implementation proposal

## Purpose

This document defines the first safety boundary for using `shadowseed` as an
agent or RAG middleware layer.

It does not change the core SSL runtime. It adds an adapter-level rule for any
future agent integration:

```text
trace > 0 means the seed is present
weight = 0 means the seed does not steer
```

A seed may only influence retrieval, probes, answer text, warnings, tool calls,
or decisions when the adapter can show all of the following:

1. the seed has positive weight;
2. the seed status is `PROMOTED`;
3. a Validation Gate promotion exists in the gate log;
4. no active contradiction blocks the seed;
5. generated LLM output is not counted as verified evidence.

## Implemented boundary

The first implementation lives in:

- `src/shadowseed_agent/agent_contract.py`
- `src/shadowseed_agent/retrieval_policy.py`
- `src/shadowseed_agent/audit_policy.py`

The tests live in:

- `tests/test_agent_safety_contract.py`

## Non-goals

This is not yet a production agent.

It does not:

- call external tools;
- send mail;
- update calendars;
- write documents;
- execute autonomous actions;
- make the repository production-ready.

## Adapter rule

Agent adapters should use the contract before any seed-driven action:

```python
from shadowseed_agent import AgentSafetyContract, InfluenceAction

contract = AgentSafetyContract()
decision = contract.decide(seed, InfluenceAction.RETRIEVAL, gate_log=manager.validation_log)

if decision.allowed:
    # retrieval may run
    ...
```

If the seed is weightless, not promoted, missing a logged promotion, or currently
contradicted, the action must not run.

## Audit rule

Agent adapters should emit replayable records for every seed-driven decision.
The audit helper enforces the minimum invariant:

```python
from shadowseed_agent import assert_no_weightless_influence

assert_no_weightless_influence(agent_decision_records)
```

This catches the high-severity failure mode where a seed with `weight <= 0`
steered an agent action.

## Claim boundary

This PR is `spec-ready` to `harness-ready` for the agent boundary only: it adds a
small runtime policy and tests. It is not a claim that an SSL-backed agent is
production-ready.
