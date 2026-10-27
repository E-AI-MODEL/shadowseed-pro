# Branch and research-PR map — 27 October 2026

> **Purpose:** Make the active experiments discoverable while retaining historical source state. A draft PR is not merged evidence, and a successful workflow badge is not a scientific result.
> **Snapshot:** PR metadata inspected on 27 October 2026. Refresh the GitHub PR pages before any changes.

## Research pull-request stack

Every arrow below means the next draft PR targets the preceding PR's **head branch**, not `main`:

```text
main
  |
  PR #250  research/g0-exploratory-real-model-stage1-20261025
  |
  PR #251  research/q1-q2-real-seed-rf-20261025
  |
  PR #254  research/g0-exact-seed-ablation-20261025
  |
  PR #255  research/g0-multicase-real-ab-20261026
  |
  PR #256  research/g0-method-readiness-20261027
  |
  PR #257  research/g0-late-birth-two-followups-20261027
  |
  PR #258  research/g0-dual-model-gpt5-luna-ab-20261027
```

All seven were **open drafts** when checked. Their respective bases are:

| PR | Base branch | Head branch | Archived meaning |
|---|---|---|---|
| [#250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250) | `main` | `research/g0-exploratory-real-model-stage1-20261025` | Real-model feasibility in canonical multi-turn engine |
| [#251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251) | #250 head | `research/q1-q2-real-seed-rf-20261025` | Seeded inquiry and failed/blocked continuation |
| [#254](https://github.com/E-AI-MODEL/shadowseed-pro/pull/254) | #251 head | `research/g0-exact-seed-ablation-20261025` | Single-case, four-arm deletion/placebo comparison |
| [#255](https://github.com/E-AI-MODEL/shadowseed-pro/pull/255) | #254 head | `research/g0-multicase-real-ab-20261026` | Multi-case longitudinal A/B |
| [#256](https://github.com/E-AI-MODEL/shadowseed-pro/pull/256) | #255 head | `research/g0-method-readiness-20261027` | Next-protocol readiness |
| [#257](https://github.com/E-AI-MODEL/shadowseed-pro/pull/257) | #256 head | `research/g0-late-birth-two-followups-20261027` | Five-turn, late-birth A/B/C controls |
| [#258](https://github.com/E-AI-MODEL/shadowseed-pro/pull/258) | #257 head | `research/g0-dual-model-gpt5-luna-ab-20261027` | Two-model, four-turn recorded run |

**Consequences:** the final PR includes the ancestry of the preceding experimental branches in its comparison base. Do not report every PR as an independent production release or independent cohort. Do not fast-forward the entire chain simply to make a green cumulative diff. Some steps may be superseded by later experiments while retaining independent historical value.

## Separate source-of-truth / relation safety stack

```text
main
  |
  PR #243  fix/ssot-explicit-relation-review-20261025
  |
  PR #244  research/ssot-legacy-review-preflight-20261025
```

| PR | Focus | Status checked |
|---|---|---|
| [#243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243) | Explicit relation inspection; quarantine legacy auto-support | Open draft |
| [#244](https://github.com/E-AI-MODEL/shadowseed-pro/pull/244) | Read-only legacy evidence audit before requalification | Open draft |

These are not alternative Q1/Q2 study arms. Keep them separate from the research stack and assess them for runtime/security implications before proposing any merge.

## How to organise without destroying provenance

- **Discoverability:** keep the [retrospective evidence map](retrospective-evidence-map-2026-10-27.md) and link it from the research index. It distinguishes data sources, actual exposure and what each run establishes.
- **Historical records:** retain original issue/PR links, commit hashes, runner source, protocol versions and Actions artifact IDs. Never silently replace historical verdicts with a later code replay.
- **Raw data:** do not commit owner keys, allocation keys, unreleased blind review records, complete raw archives or other confidential artifacts to this public repository. Store protected evidence in a separate access-controlled archive with an integrity manifest and publication-safe derived tables only.
- **Code versus paper:** the canonical [systems manuscript](../../../paper/README.md) and its LaTeX/PDF source chain remain separate from the exploratory possibility-space preprint. Keep a draft preprint local or in a dedicated review location until source/figure checks are complete.
- **Branch cleanup:** first map each PR to a scientific result and check descendants, tests and reviewers. Only then choose to merge, supersede or archive individual branches. **No PR merges, ref rewrites or branch deletions were performed by this documentation change.**
- **Claim-level checks:** distinguish a detector's raw candidate, intake acceptance, weightless persistence, actual Gate-authorised exposure, and later response differences. Tests without exposure cannot be scored as treatment failures.

## Suggested review order (not a merge order)

Start with the direct raw-data anchors for #254 and #258, cross-check the unmerged runner source against the archived artifact IDs, and then reconcile #250/#251/#255/#256/#257 as experimental context. Keep #243/#244 as a separate source-of-truth integrity lane. This is an indexing task; publication and branch lifecycle decisions remain separate.

## Related references

- [Foundational thesis](../possibility-space-thesis.md)
- [Retrospective evidence map](retrospective-evidence-map-2026-10-27.md)
- [Existing research index](README.md)
- [Source-code research status](../status.md)
