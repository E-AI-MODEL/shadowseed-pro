# G0 F1 — T0 model input envelope (DRAFT, NOT APPROVED) — RETIRED AS THESIS TEST

> **Research decision 2026-10-25:** This v1 model-facing envelope has been **retired as a primary Q1/Q2 thesis test** by [internal critical audit](internal-adversarial-audit-2026-10-25.md). Do not use it to run the new paid model experiment. It is retained only for historical calibration and failure analysis.
>
> **Operational rule:** Only the text between the horizontal delimiters below may be supplied to a later model at **T0**. The research team must freeze the selected model/backend, prompt strategy and budget first. Do not concatenate links, reviewer documents, file names or assessor keys. This file is a public *illustrative case*, not a secure held-out benchmark.

---

**Synthetic system.** A controller issues a binary command `u` once per tick. An archive stores one binary measurement `r` per tick. The archive was created by an unspecified chain of physical dynamics, sensors and recording equipment. The clock ticks are aligned at the archive interface; internal dynamics and acquisition delays have not been independently measured. The controller was at command 0 before tick 0.

| Tick | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Command `u` | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| Archived `r` | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 |

One additional bounded observation or test may become available at a later stage, but no result or method is guaranteed in advance. You may *propose* an investigation; you may not assume access to an instrument until that access is independently confirmed.

**Task.** Distinguish what the archive establishes from what remains possible but unconfirmed. Propose no more than two *specific, falsifiable candidate directions* for investigation, and say what future observation would make an important new distinction or next question available. If the record already settles the issue or no useful investigation exists, say so. Never assert a proposed interpretation as verified. Concise text is preferred; no invented measurements.

---
