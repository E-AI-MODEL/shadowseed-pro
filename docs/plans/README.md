# Execution plans

Files in this directory are implementation and alignment records. They preserve why work was sequenced a certain way and which constraints applied at the time.

They are **not the current architecture authority**. When a plan conflicts with later runtime behavior or documentation, use this precedence:

1. `docs/architecture/**` for current architecture and authority contracts;
2. current runtime code and contract tests for executable behavior;
3. `docs/research/status.md` for current evidence/claim status;
4. current Workbench/usage documentation for the tester product surface;
5. files in `docs/plans/` as historical execution context.

A plan may be annotated after completion to point to a later ADR or correction, but its original sequencing should not be rewritten into a false history.
