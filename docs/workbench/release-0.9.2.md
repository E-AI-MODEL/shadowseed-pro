# Shadowseed Workbench 0.9.2

Shadowseed Workbench 0.9.2 is a patch release for the Dutch chat-first Workbench.
It packages the A/B comparison correction merged after 0.9.1 while keeping the
same canonical Shadow Seed Learning runtime, Validation Gate and point-of-use
authorization model.

## Main fix: independent vanilla A/B baseline

The live comparison no longer treats "SSL off" as the same Shadowseed
conversation with the current seed context removed.

The control arm now has its own persisted `vanilla_history`:

- it receives the same user questions as the Shadowseed arm;
- it stores only its own vanilla model answers;
- earlier SSL-influenced answers are never copied into the control trajectory;
- when A/B is enabled after earlier live turns, the missing vanilla history is
  reconstructed from those earlier user questions;
- OpenAI and Ollama use role-structured chat messages for the vanilla path;
- supported Hugging Face backends use a chat template when available;
- comparison provenance records whether the control history was isolated, which
  transport was used and how many earlier vanilla turns were replayed.

The live comparison therefore measures cumulative path divergence:

```text
A: same user turns -> independent vanilla chat history -> vanilla answer
B: same user turns -> Shadowseed chat history -> possible SSL-influenced answer
```

A textual difference is not automatically a current-turn SSL effect. The
Workbench reports current-turn seed influence separately from SSL influence
already present in earlier Shadowseed answers.

## Comparison and UI changes

- the Workbench labels the control as **Vanilla baseline**;
- comparison records use `independent_vanilla_vs_ssl_path` for the normal live
  comparison;
- experimental shadow-pressure comparison uses an independent vanilla control
  as well;
- persisted vanilla history fails closed if its user-question sequence no longer
  matches the live conversation;
- historical evaluation mode remains baseline-isolated and does not inherit
  cumulative live-session SSL provenance.

## Regression coverage

0.9.2 adds or strengthens tests for:

- SSL-answer leakage into the vanilla history;
- enabling A/B only after earlier live turns;
- role-structured OpenAI and Ollama chat requests;
- vanilla-history persistence and restore validation;
- distinction between current-turn and prior SSL influence;
- compatibility with the existing Workbench comparison interface.

## Distribution and release integrity

Publication requires the same release contract as 0.9.1:

- exact protected-`main` source SHA;
- required CI and production-local acceptance;
- Linux, macOS and Windows standalone evidence;
- frozen product self-tests;
- Python wheel and source distribution;
- `SHA256SUMS`;
- CycloneDX SBOM;
- `PROVENANCE.json`;
- dependency-lock and license verification;
- trusted artifact attestations;
- post-download verification.

The macOS distribution boundary remains unchanged: the app is ad-hoc signed,
not Apple-notarized.

## Claim boundary

Version 0.9.2 corrects the comparison design. It does not by itself establish
that SSL improves answer quality, proves semantic truth, retrains the base
model, or makes the system suitable for high-impact decisions. The independent
vanilla arm makes the comparison more interpretable, but causal claims still
depend on the study design and the recorded provenance.
