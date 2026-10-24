# Shadowseed Web 0.12.4

Release notes for the Research Preview candidate. These notes do not claim that
v0.12.4 has already been published. The latest published archive remains
v0.12.3 until the exact-SHA release workflow completes successfully.

The download keeps the 0.12.3 form: a local, self-contained browser app with
the canonical Python engine behind a loopback-only server. The legacy Gradio
Workbench is still not part of the audited download (issue #200).

## Changes since 0.12.3

### Interface

- The web client is in English, with factual wording and the terms from the
  product documentation: Controlled, Assisted and Autonomous modes, "seed", and
  the statuses Found, Recurring, Supported, Validated, Promoted, Blocked,
  Dormant and Expired. Controlled is the default mode.
- A promoted seed that influenced an answer shows as Used; the session view
  reports `used_count` per seed.
- Full raw JSON inspection of the session, the last turn report and each seed;
  light and dark theme; mobile layout fixes; Enter to send follows the same
  conditions as the send button.
- `shadowseed-workbench` and the frozen bundles open the web client by default.
  The legacy Gradio Workbench starts only with `--legacy-gradio`.

### Gate

- ADR-011: in Controlled and Assisted live sessions one operator-verified
  source promotes a seed. Evidence identity, contradiction, relevance and
  point-of-use rules are unchanged. Autonomous, evaluation and explicit
  Gate-strictness sessions keep their calibration.

### Recurrence

- ADR-012: the session model recognizes a returning gap. After a turn with new
  seeds, the model gets one short question: does each new note repeat an open
  question of this conversation, an earlier note of the same turn, or neither?
  Embedding similarity is only a floor (0.3) and the fallback when the model
  call fails or returns nothing readable.
- On the fixed22 pair sample, Qwen 2.5 7B recognized 7 of 8 same-gap pairs with
  1 wrong merge in 44, against 10 wrong merges for the old 0.60 embedding
  threshold. In a live probe the model arm made no wrong merge; the embedding
  arm merged five different gaps into one cluster.
- Recurrence stays observation. It never adds weight under the product Gate.
- Sessions saved by an earlier version keep embedding recurrence.

### Intake and detector

- English declarative candidates are admitted unless they are a bare category
  stack ("Security, privacy and scalability are missing."). The Dutch
  separators no longer apply to English text.
- A leading bold label in a candidate is unwrapped, so no Markdown markers stay
  in seed text.
- The detector prompt is unchanged (current_pair v0.6).

### Security

- setuptools 84.1.0 in the build closure (GHSA-xmj3-9gf7-h52w).

## Known limitations

- **Few seeds with local 7B models.** With Qwen 2.5 7B Q4_K_M the detector finds
  a seed in about one turn in eight, and about a quarter of those seeds were
  rated useful in a blind review. Two alternative prompts raised the number of
  seeds but not their quality, so they were not adopted. With GPT-5 and
  GPT-6.1-sol the same prompt gave 51 useful seeds in a sample of 60. See
  `docs/research/detector-calibration.md`.
- **Speed on CPU.** On a machine without a GPU (measured on GitHub CPU
  runners), a turn with Qwen 2.5 7B takes about two to three minutes, and a
  recurrence recognition call adds about 10 to 20 seconds when a turn produced
  new seeds. A GPU or a smaller chat model shortens this.
- No efficacy claim: whether SSL improves answers is not shown by this release.
  The evidence efficacy study 1 is a pilot.

## Candidate acceptance

| Check | Required evidence |
| --- | --- |
| Deterministic mechanics | Full pytest, Ruff and web contract checks on the candidate |
| Distribution | Clean wheel and standalone self-tests, supported-platform CI, provenance, checksums and SBOM |
| Dependency audit | Strict audit of the locked web-only shipping closure |
| Real conversation | A local Ollama chat over several turns, close and reopen, then `shadowseed doctor` |
| Production claim | Production Release Assurance on the published tag, no open P0/P1 finding and the 24-hour soak |

Deterministic backend doubles do not establish live-model quality or latency.

## Local use after publication

Start the Shadowseed launcher; it serves the web interface on your computer's
loopback interface and opens it in your browser. Start Ollama and install a
chat model plus the embedding model:

```bash
ollama pull embeddinggemma
```

Select the installed chat model and create a conversation. Fixture remains
available without Ollama for deterministic mechanism inspection.
