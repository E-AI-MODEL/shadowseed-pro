> # ⚠️ ARCHIVE — HISTORICAL MATERIAL, NOT CURRENT AUTHORITY
>
> Everything under `archive/` is **frozen source material** from the
> pre-rebuild repository. It is kept only for provenance and historical
> reference.
>
> - **Not canonical.** Do not treat anything here as current guidance.
> - **Not importable.** No runtime code may import from `archive/`; it is
>   excluded from package discovery (packaging discovers only `src/`).
> - **Not maintained.** Content is preserved as-is and may be outdated,
>   superseded, or written in Dutch.
>
> For current, authoritative information see:
> [`docs/architecture/`](../docs/architecture/) and
> [`repository-authority.yaml`](../repository-authority.yaml).

# Archive

This directory preserves the original source material that predates the
v0.3.0 rebuild, organized by origin:

| Path | Contents |
|---|---|
| `legacy/` | Superseded documentation and wiki (`HISTORICAL_REFERENCE`) |
| `source-docs/` | Original documentation, ADRs, research notes |
| `source-benchmarks-docs/` | Original benchmark documentation |
| `source-data/` | Original source data (e.g. papers) |
| `source-results/` | Imported historical result snapshots |
| `source-root/`, `source-templates/`, `source-workflows/` | Original root, templates, and workflow files |

The authoritative classification of this tree is `ARCHIVE`
(and `HISTORICAL_REFERENCE` for `legacy/`) in
[`repository-authority.yaml`](../repository-authority.yaml).
