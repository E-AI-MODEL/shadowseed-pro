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

Issue #66 is verified with a disposable pull request created after the ruleset became active:

1. confirm the branch API reports `main` as protected;
2. open the pull request with deliberately failing CI and verify merge is rejected while checks are pending and after CI fails;
3. remove the deliberate failure and verify the exact required checks pass;
4. merge the passing pull request normally through the protected branch;
5. confirm the resulting commit is on `main` and close issue #66 with the verification evidence.

This procedure tests enforcement rather than relying only on the ruleset configuration screen.
