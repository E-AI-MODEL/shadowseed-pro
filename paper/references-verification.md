# Bibliography verification record

**Authority:** EVIDENCE_ARTIFACT
**Covers:** `paper/references.bib`
**Tracked by:** issue #116

Every key in `paper/references.bib` must appear in the table below, and
`tests/test_paper_citations.py` fails if it does not. The record states what was
checked, how, and what remains unresolved. It is not a claim that every cited
work is correct or relevant; it is a claim that every cited work exists at the
venue the entry names.

## Verification levels

- **venue-confirmed** — the exact title, author list and venue were located in an
  independent source, and any page range or DOI in the entry matched.
- **preprint-confirmed** — the work was located, but the entry's peer-reviewed
  venue record could not be corroborated. The entry cites the preprint.
- **canonical** — a widely indexed work whose identity is not in question, located
  through search but without a per-field match against the publisher record.
- **self** — this repository's own artifact.

A `canonical` entry is not a weaker claim about the work's existence. It records
that the individual page/volume/DOI fields were not compared one by one.

## Record

| Key | Level | Verified against | Checked |
|---|---|---|---|
| `shadowseed2026` | self | this repository | 2026-09-01 |
| `fu2025absencebench` | venue-confirmed | arXiv 2506.11440; NeurIPS 2025 Datasets and Benchmarks Track | 2026-09-01 |
| `li2025questbench` | venue-confirmed | arXiv 2503.22674; NeurIPS 2025 Datasets and Benchmarks Track proceedings page | 2026-09-01 |
| `lewis2020rag` | canonical | NeurIPS 2020 proceedings | 2026-09-01 |
| `guu2020realm` | canonical | ICML 2020, PMLR v119 | 2026-09-01 |
| `asai2024selfrag` | venue-confirmed | ICLR 2024 Oral; OpenReview `hSyW5go0v8` | 2026-09-01 |
| `jeong2024adaptiverag` | venue-confirmed | NAACL 2024, pp. 7036–7050, DOI `10.18653/v1/2024.naacl-long.389` | 2026-09-01 |
| `shinn2023reflexion` | venue-confirmed | arXiv 2303.11366; NeurIPS 2023 proceedings | 2026-09-01 |
| `packer2023memgpt` | preprint-confirmed | arXiv 2310.08560; no peer-reviewed venue located | 2026-09-01 |
| `dhuliawala2024cove` | venue-confirmed | Findings of ACL 2024, pp. 3563–3578, DOI `10.18653/v1/2024.findings-acl.212` | 2026-09-01 |
| `debenedetti2024agentdojo` | venue-confirmed | arXiv 2406.13352; NeurIPS 2024 Datasets and Benchmarks Track | 2026-09-01 |
| `zou2025poisonedrag` | venue-confirmed | USENIX Security 2025, pp. 3827–3844 | 2026-09-01 |
| `farquhar2024semanticentropy` | canonical | Nature 630, 625–630 (2024) | 2026-09-01 |
| `tan2025membench` | venue-confirmed | arXiv 2506.21605; Findings of ACL 2025 | 2026-09-01 |
| `yu2026agentic` | venue-confirmed | arXiv 2601.01885; ACL 2026 Long Papers | 2026-09-01 |
| `lan2026ema` | venue-confirmed | Findings of ACL 2026, pp. 5088–5102 | 2026-09-01 |
| `huang2026underspecified` | venue-confirmed | arXiv 2602.11938; Findings of ACL 2026 | 2026-09-01 |
| `zhao2026askbench` | venue-confirmed | arXiv 2602.11199; Findings of ACL 2026 | 2026-09-01 |
| `suri2026structured` | venue-confirmed | arXiv 2511.08798; Findings of ACL 2026 | 2026-09-01 |
| `toles2025clarification` | venue-confirmed | ACL GEM² workshop 2025, pp. 200–211 | 2026-09-01 |
| `qian2026visual` | preprint-confirmed | arXiv 2604.16966; ACL 2026 proceedings record not corroborated | 2026-09-01 |
| `ge2025conflicting` | venue-confirmed | arXiv 2505.17762; IJCAI 2025 | 2026-09-01 |

## Corrections applied on 2026-09-01

- `li2025questbench` moved from the arXiv preprint to the NeurIPS 2025
  proceedings record, matching how `fu2025absencebench` from the same track is
  cited.
- `shinn2023reflexion` gained the author **Edward Berman**, who was missing from
  the entry. The unresolved `10.52202/*` DOI was replaced with the canonical
  NeurIPS proceedings URL.
- `debenedetti2024agentdojo` had its unresolved `10.52202/*` DOI replaced with
  the canonical NeurIPS proceedings URL. Its author list was already correct.
- `fu2025absencebench` keeps the NeurIPS title *Absence Bench: Language Models
  Can't See What's Missing*. The arXiv version is titled *AbsenceBench: Language
  Models Can't Tell What's Missing*; the entry cites the proceedings, so the
  proceedings title stands and the arXiv identifier is recorded in a note.
- `packer2023memgpt` retyped from `@article` to `@misc`, because no
  peer-reviewed venue exists for it.
- `qian2026visual` moved from an unverified ACL 2026 proceedings record to the
  confirmed arXiv record.
- `ge2025conflicting` added. It was already present in the repository as an
  external research input under `data/papers/` but was cited nowhere.

## Open item

`qian2026visual` remains at `preprint-confirmed`. Two independent searches did
not corroborate the ACL 2026 proceedings record originally claimed for it. It is
also the only single-author entry and the furthest from this manuscript's
subject. Either confirm the proceedings record against the ACL Anthology and
promote it to `venue-confirmed`, or reconsider whether it earns its place in the
related-work section.

## Method and its limits

Verification on 2026-09-01 used independent web search against arXiv, publisher
and proceedings listings. Direct resolution of `doi.org` and
`aclanthology.org` was not possible from the verifying environment, whose
network egress blocks both hosts. Entries marked `venue-confirmed` had their
page ranges and DOIs matched against publisher-side listings surfaced in search
results rather than against a DOI resolution.

A future pass from an environment with open egress should resolve every DOI
directly and promote the remaining `canonical` entries to `venue-confirmed`.
