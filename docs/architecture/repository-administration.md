# Repository Administration

**Authority:** CANONICAL_SPEC  
**Recorded:** 2026-08-20  
**Responsible repository administrator:** `E-AI-MODEL`

## Protected main contract

The default branch `main` is protected by the active GitHub repository ruleset `Protect main`.

Normal changes to `main` must go through a pull request. The ruleset blocks force pushes and branch deletion and requires the branch to be up to date with `main` before merge.

The unconditional required CI checks are:

- `test (3.10)`
- `test (3.12)`
- `build`

These checks are emitted by `.github/workflows/ci.yml`, which runs for every pull request.

`Workbench CI` and `Workbench Portability` are intentionally not configured as unconditional required checks because their workflows are path-filtered. Applicable changes must still pass those workflows when GitHub runs them. If they later become mandatory at the ruleset layer, the workflow structure must first provide an always-reporting terminal check or aggregate check so non-applicable pull requests cannot remain permanently pending.

Pull-request conversations must be resolved before merge where enforced by the ruleset. There is no standing bypass path for routine administration.

## Break-glass

A ruleset bypass or temporary ruleset relaxation is emergency-only. It must be deliberate, time-bounded, and followed by restoration of the normal ruleset. The administrator must record why the bypass was needed, the affected commit or pull request, what checks were unavailable or overridden, and confirmation that the protection was restored. Break-glass must never be used to make ordinary development faster.

## Verification procedure

Issue #66 is verified with an end-to-end pull-request test after the ruleset becomes active:

1. confirm the branch API reports `main` as protected;
2. open a pull request and verify merge is rejected while required checks are pending;
3. introduce a deliberate CI failure and verify merge is rejected after CI fails;
4. remove the deliberate failure and verify the exact required checks pass;
5. merge the passing pull request normally through the protected branch;
6. confirm the resulting commit is on `main` and record the verification evidence on issue #66.

This procedure tests enforcement rather than relying only on the ruleset configuration screen.

## Verification history

On 2026-08-20, PR #90 exposed an initial ruleset misconfiguration. `main` was marked protected, but the CI jobs were not yet configured as required checks, so a deliberately failing probe could still merge. Its squash commit was `e9e47d9708e3291f555ba08c1022a52071ee2cc1`, and push CI run `32410451231` failed. That historical red commit is intentionally preserved as evidence of the discovered configuration defect; repository history must not be rewritten to hide it. PR #91 immediately removed the probe, passed CI run `32410499490`, merged as `bf6057b65c0fc5e8fade4f603955677e5f00a81e`, and issue #66 was reopened pending a real enforcement proof.

After the ruleset was corrected, PR #93 provided the successful end-to-end verification. On intentional-failure head `c91ce70c10380b83e7ed9309543bd857e4fae152`, CI run `32412267031` failed and GitHub rejected merge because the three required checks were not satisfied. After the probe was removed, head `4770bd5ca3103019a03ea93b5ed760caaff143b0` passed CI run `32412395533`. The final PR head `20b89917694fa60874483bbe95b16705e681811a` passed CI run `32412427149` with the required jobs `test (3.10)`, `test (3.12)`, and `build`, after which PR #93 merged normally through protected `main` as verified GitHub squash commit `7e8b3f20ec5e330ecbbc8cd26b627ec5b0586447`.

The final verification evidence is recorded directly on issue #66. PR #93 is the successful enforcement proof. PR #90 remains part of the audit trail only as the failed initial verification that revealed the ruleset misconfiguration.
