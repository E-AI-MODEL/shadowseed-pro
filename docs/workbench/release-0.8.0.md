# Shadowseed Workbench 0.8.0

Shadowseed Workbench 0.8.0 moves Shadow Seed Learning from a tester-oriented
preview toward a product-oriented local Workbench while preserving the
Validation Gate, audit trail and point-of-use safety boundary.

## What changed

- authority profiles are first-class: Controlled, Assisted, Autonomous and Open research;
- Controlled preserves the evidence-backed production behavior;
- Assisted detects mature recurrence and raises explicit review requests when verified support is still required;
- Autonomous and Open can let recurrence earn authority through the existing exploratory Validation Gate;
- promotion still occurs only through the canonical Gate and later influence still requires relevance plus point-of-use checks;
- a dedicated Control workspace shows the selected profile, effective Gate and review state;
- a dedicated Verify surface supports SSL-on / SSL-off attribution checks;
- the Workbench contains a layered explanation of what Shadow Seed Learning is and is not;
- pasted text and multiple TXT, Markdown, JSON and CSV files can be processed through the non-chat Sources path;
- uploaded material remains observation input and is not silently converted into trusted evidence;
- corpus summaries expose new seeds, promotions and Assisted review needs.

## Shadow Seed Learning in 0.8.0

SSL remains an external, inspectable experience layer around the base model.
It does not retrain model weights.

The operational path is:

```text
observe -> seed -> recur/evidence -> Validation Gate -> promote
        -> relevance -> point-of-use decision -> possible influence
```

A promoted seed is eligible for later use. It is not injected into every answer.
A different answer is not, by itself, proof that SSL caused the difference.

## Authority profiles

### Controlled

The backwards-compatible default. Live authority remains evidence-backed.
Recurrence alone does not grant authority.

### Assisted

Live authority remains evidence-backed. Mature recurrence can trigger an
explicit review request, but independently verified support is still required
where the Gate requires it.

### Autonomous

Uses the existing exploratory Gate by default. Recurrence remains a recurrence
signal, never fake external evidence, and may earn authority through that policy.
Relevant promoted seeds may later surface only after the normal point-of-use
checks.

### Open research

Uses the same auditable Gate path with the least restrictive research
permissions. The profile does not invent machine evidence. Any future
system-evidence producer must be explicit, attributable and accepted by policy.

## Source ingestion

The Sources workspace currently supports:

- pasted text;
- TXT;
- Markdown;
- JSON;
- CSV;
- multiple files per run.

The source path is:

```text
extract -> chunk -> detect candidates -> cluster/recur -> Gate -> shadow memory
```

Source chunks do not become fake chat turns. PDF/DOCX extraction, asynchronous
large-corpus progress/cancel/resume, machine-evidence producers and automatic
contradiction resolution are not part of 0.8.0.

## Verification

Use:

- **Shadow** to inspect lifecycle state, evidence, contradictions and use;
- **Verify** to inspect paired SSL-on / SSL-off comparisons and attribution;
- **Control** to inspect the selected authority profile and effective Gate;
- **About SSL** for the conceptual and operational explanation;
- **Technical inspection** for raw JSON, Gate events, trace and influence records.

## Distribution and release integrity

Publication still requires:

- the exact protected-`main` source SHA;
- required CI and production-local acceptance;
- Linux/macOS/Windows standalone evidence;
- frozen product self-tests;
- `SHA256SUMS`;
- CycloneDX SBOM;
- `PROVENANCE.json`;
- repository license verification;
- dependency-lock verification;
- trusted artifact attestations;
- post-download verification;
- the repository's unchanged-candidate soak and production acceptance gates.

The credential-free macOS first-launch boundary from 0.7.2 remains unchanged:
the app is ad-hoc signed, not Apple-notarized, and the supported first-launch
helper remains part of the distribution contract.

## Claim boundary

Version 0.8.0 does not claim universal answer-quality improvement, semantic
truth, hostile-network production safety, hosted/multi-user readiness, Apple
Developer ID signing, Apple notarization, Windows Authenticode signing, or
certified suitability for high-impact decisions.

The new autonomy profiles change which existing Gate policy is selected and how
review needs are presented. They do not create a second authority path and do
not bypass the Validation Gate or point-of-use safety contract.
