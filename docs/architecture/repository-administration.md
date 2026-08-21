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

## Independent assurance for sensitive changes

The repository currently has one maintainer. Requiring one GitHub approval on every pull request would create a self-blocking rule because an author cannot approve their own pull request. The ruleset therefore does not treat a maintainer self-review as an independent approval.

Architecture/security-sensitive production changes still require independent assurance before a `production-ready/local` claim. Acceptable evidence is a review by a person other than the author, or an explicitly approved external review mechanism whose reviewed commit, findings and disposition are preserved in the repository record. Maintainer self-review remains useful but must be labelled as self-review and cannot be represented as independent assurance.

Issue #95 tracks the independent post-acceptance review of the Phase 0 production contracts. Material findings are resolved through a protected pull request and do not rewrite the history of PR #89.

This assurance requirement is deliberately narrower than an unconditional one-approval repository rule. Routine single-maintainer development continues through protected pull requests and required automated checks; production architecture/security acceptance additionally requires the independent evidence above.

## Dependency and Action update policy

Python dependency resolution is recorded in `uv.lock`. The resolver version is pinned in `pyproject.toml`; updates to direct dependency ranges or the resolver must refresh the lock and pass supply-chain validation. The bounded local product is CPU-first: Linux and Windows resolve PyTorch from the explicit CPU wheel index, while macOS uses the native PyPI wheel. This prevents the production lock from silently turning a CPU-first Workbench into a CUDA dependency closure.

Dependabot checks Python and GitHub Actions dependencies weekly. Update pull requests use the same protected-main process as other changes. Mutable Action tags are not accepted in repository workflows: Actions are recorded by full immutable commit SHA with a human-readable version comment. Version comments are informative only; the SHA is the executed identity.

Dependency updates are not auto-merged. They must pass the repository checks and the dependency-security scan. A security update may be prioritized, but urgency does not convert it into a break-glass event by default.

The required vulnerability gate audits the dependency closure that can ship in or build the `production-ready/local` candidate: core runtime, Workbench, build tooling and standalone-build tooling. Optional vector-store extras are not silently folded into that production claim. In particular, the current Chroma extra resolves to `chromadb 1.5.9`, for which pip-audit reports `PYSEC-2026-311`; the advisory has no fixed release listed as of 2026-08-20. `vector-chroma` therefore remains outside the `production-ready/local` supported dependency surface until a non-vulnerable upstream release is available and the lock/security gate is refreshed. This is a bounded unsupported-production dependency, not an ignored passing scan.

Release SBOMs describe the same production dependency closure as the required vulnerability gate. Research-only or unsupported optional extras may remain installable for research, but they must not be represented as covered by the production SBOM or production security verdict until separately cleared.

## Break-glass

A ruleset bypass or temporary ruleset relaxation is emergency-only. It must be deliberate, time-bounded, and followed by restoration of the normal ruleset. Break-glass must never be used to make ordinary development faster or to evade a reproducible failing quality gate.

Before use, the administrator records the incident/change reference, reason normal protected flow cannot be used, exact intended commit or pull request, checks or rules that would be bypassed, the narrowest required time window, and the rollback/restoration plan. No break-glass procedure authorizes force-rewriting repository history or deleting the historical red verification commit `e9e47d9708e3291f555ba08c1022a52071ee2cc1`.

After use, the administrator restores the normal ruleset immediately and records the resulting commit, checks that ran or were unavailable, any compensating verification, the restoration time, and confirmation that `main` is protected again. The event remains auditable even when the emergency change was later reverted.

Before a `production-ready/local` claim, break-glass is validated non-destructively by a tabletop exercise. The exercise walks the record, authorization, bounded bypass, restoration and post-event verification steps without weakening a working ruleset merely to prove that bypass exists.

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
