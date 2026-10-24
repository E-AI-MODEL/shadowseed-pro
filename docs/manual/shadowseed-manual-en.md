---
title: "Shadowseed — Manual"
subtitle: "Version 0.12.4 · Research Preview"
lang: en
---

# Shadowseed — Manual

**Version 0.12.4 · Research Preview · October 2026**

This manual covers the downloadable Shadowseed web application and the Python
package it is built from. It is written for five groups of readers. Everyone
should read Part 1. After that, go to the part that fits your role.

| You are… | Read |
| --- | --- |
| A **user** who wants to chat with Shadowseed | Parts 1 and 2 |
| A **tester** who reports findings | Parts 1, 2 and 3 |
| A **researcher** who studies Shadow Seed Learning | Parts 1, 2 and 4 |
| A **developer** who builds on or changes Shadowseed | Parts 1, 4 and 5 |
| A **specialist** in security, privacy or operations | Parts 1, 5 and 6 |

The glossary at the end translates every term into Dutch. A Dutch edition of
this manual is available as `shadowseed-handleiding-nl.md`.

> **Status.** Shadowseed is a *Research Preview*. It works and is tested, but it
> is not certified for decisions in healthcare, finance, law, employment,
> education or other high-impact areas. Chapter 14 lists its limitations.

## Contents

- Part 1 — Getting started
  1. What Shadowseed is
  2. System requirements
  3. Installing Shadowseed
  4. Setting up a local model with Ollama
  5. Your first conversation
- Part 2 — Using Shadowseed
  6. The screen
  7. Seeds and their statuses
  8. Authority modes
  9. Adding verified evidence
  10. Contradictions
  11. When a seed influences an answer
  12. Using OpenAI
  13. Your data and privacy
  14. Limitations
  15. Troubleshooting
- Part 3 — Testing
  16. Testing Shadowseed
- Part 4 — Research
  17. The Shadow Seed Learning model
  18. Showing that SSL had an effect
  19. Studies and evidence
- Part 5 — Development
  20. Working from source
  21. Architecture
  22. Command-line reference
  23. Web API reference
  24. Builds and releases
- Part 6 — Security and operations
  25. Security model
  26. Running Shadowseed reliably
  27. Configuration reference
- Appendices
  - A. Glossary (English–Dutch)
  - B. Frequently asked questions
  - C. About this document

---

# Part 1 — Getting started

## 1. What Shadowseed is

Shadowseed is a chat application with an extra memory layer called **Shadow
Seed Learning (SSL)**. You talk to a language model as usual. Next to the
conversation, Shadowseed watches each answer for points that are still open:
an assumption that was not checked, a number that was not given, a case that
was not covered. It stores such a point as a **seed**.

A seed starts with no influence at all. It can gain influence only through the
**Validation Gate**, and in the default mode the Gate wants a source that *you*
have checked. Once a seed has passed the Gate, Shadowseed may bring it back into
a later answer — but only when it is relevant to the question at that moment.

Three ideas carry the whole design:

- **Observe broadly, grant authority selectively, retrieve narrowly.** Many
  seeds are noticed; few are allowed to steer; only the relevant ones are used.
- **Authority comes from evidence, not from repetition.** A seed that comes back
  often is interesting, but repetition alone does not make it true.
- **Every decision is visible.** Each seed has a timeline of events, and every
  Gate decision is recorded.

Shadowseed does not retrain the model. The model stays the same; the memory
around it grows. Two installations with the same model can therefore develop
different memories.

What Shadowseed does **not** claim:

- that seeds are true;
- that answers become better (this is the subject of ongoing research);
- that a source you mark as checked is actually correct — that is your
  responsibility.

## 2. System requirements

| Item | Requirement |
| --- | --- |
| Operating system | Windows 10/11 (64-bit), macOS on Apple silicon (M1 or later), Linux x86_64 |
| Disk space | About 200 MB for Shadowseed, plus space for models (a 7B model takes about 4.7 GB) |
| Memory | 8 GB RAM minimum for a 7B model; 16 GB recommended |
| Ollama | Version 0.11.10 or later, for real conversations |
| Browser | A current Chrome, Edge, Firefox or Safari |
| Network | Not needed for local use, except to download the program and the models |

**Speed.** On a computer without a suitable graphics card, a 7B model needs
about two to three minutes per turn. A GPU or a smaller model shortens this
considerably. The offline demo needs no model and responds instantly.

## 3. Installing Shadowseed

### 3.1 Download

Go to the release page of the project on GitHub and download the archive for
your system:

| System | File |
| --- | --- |
| Windows | `shadowseed-web-0.12.4-windows-amd64.zip` |
| macOS (Apple silicon) | `shadowseed-web-0.12.4-darwin-arm64.zip` |
| Linux | `shadowseed-web-0.12.4-linux-x86_64.tar.gz` |

Also download `SHA256SUMS` if you want to verify the file.

### 3.2 Verify the download (recommended)

The checksum proves that your file is exactly the one that was published.

- **Windows (PowerShell):** `Get-FileHash .\shadowseed-web-0.12.4-windows-amd64.zip`
- **macOS:** `shasum -a 256 shadowseed-web-0.12.4-darwin-arm64.zip`
- **Linux:** `sha256sum shadowseed-web-0.12.4-linux-x86_64.tar.gz`

Compare the result with the matching line in `SHA256SUMS`. They must be
identical.

### 3.3 Unpack and start

**Windows.** Right-click the ZIP and choose *Extract All*. Open the extracted
folder, then the `Shadowseed` folder, and start `Shadowseed.exe`. Windows may show a SmartScreen warning,
because the program is not signed with a Microsoft certificate. Choose *More
info* and then *Run anyway*.

**macOS.** Double-click the ZIP to unpack it. The application is signed for
integrity but not notarized by Apple, so macOS blocks the first start of a
downloaded copy. Right-click `Shadowseed` and choose *Open*, then confirm. If
macOS still refuses, run once in Terminal:
`xattr -dr com.apple.quarantine /path/to/Shadowseed.app`.

**Linux.** Unpack with `tar -xzf shadowseed-web-0.12.4-linux-x86_64.tar.gz` and
start the `Shadowseed` program in the extracted folder.

After starting, Shadowseed opens your web browser at an address such as
`http://127.0.0.1:8765/`. That address exists only on your own computer; no
one else can reach it. If port 8765 is taken, Shadowseed picks another free
port and opens that instead.

Keep the window or terminal of Shadowseed open while you work. Closing it stops
the program. Your conversations are kept.

### 3.4 Where your data is stored

Shadowseed keeps everything in one folder in your home directory:

| System | Folder |
| --- | --- |
| Windows | `C:\Users\<name>\.shadowseed` |
| macOS | `/Users/<name>/.shadowseed` |
| Linux | `/home/<name>/.shadowseed` |

Next to it, a folder `.shadowseed-integrity` holds the protected key and
anchor of the audit ledger. Do not copy, move or delete these folders by hand;
use the commands in chapter 13: `workspace delete` removes both folders, and a
backup goes back only through `workspace restore`. Chapter 13 also explains what
is stored.

## 4. Setting up a local model with Ollama

The offline demo shows how Shadowseed works without a model. For real
conversations Shadowseed uses **Ollama**, which runs language models on your
own computer.

1. Install Ollama from ollama.com (version 0.11.10 or later) and start it.
2. Download a chat model. For example, in a terminal:
   `ollama pull qwen2.5:7b-instruct`
3. Download the embedding model that Shadowseed needs to compare texts:
   `ollama pull embeddinggemma`
4. Check that both are present: `ollama list`

Any chat model that Ollama can run will work. Larger models give better
answers and find more useful seeds, but need more memory and time.

**Which model?** In our measurements, a 7B model on a normal computer finds a
seed in about one turn in eight, and about a quarter of those seeds are
useful. Larger hosted models find far more useful seeds (51 of 60 in a sample).
If you mainly want to see the mechanism, the offline demo or a small model is
enough. If you want useful seeds, use the largest model your computer can run.

## 5. Your first conversation

### 5.1 Start with the offline demo

The offline demo uses no model. Its answers are simple echoes and its seeds
are marked `[FIXTURE]`. It is meant to show the controls, not to give good
answers.

1. In the left panel under **New conversation**, give the conversation a title.
2. Leave **Model** on *Offline demo (no model)*.
3. Leave **Authority mode** on *Controlled*.
4. Click **Start conversation**.
5. Type a message and press **Enter**.

![The start screen](images/01-start.png)

*Figure 1 — The start screen. Left: new conversation. Middle: the chat.
Right: Shadow memory.*

### 5.2 A real conversation with Ollama

1. Click **New conversation**.
2. Under **Model**, choose *Ollama (local)*.
3. Under **Ollama model**, enter the exact name of an installed model, for
   example `qwen2.5:7b-instruct`. Use the name exactly as `ollama list` shows it.
4. Choose an authority mode (chapter 8) and click **Start conversation**.

![New conversation with Ollama](images/02-new-ollama.png)

*Figure 2 — Creating a conversation with a local Ollama model.*

If Ollama is not running, or `embeddinggemma` is missing, Shadowseed shows
what to do and does not create the conversation. Fix the problem and try again.

Ask a real question and continue the conversation for a while. Seeds appear in
the right panel as Shadowseed finds open points. The longer the conversation,
the more chance that a point comes back.

---

# Part 2 — Using Shadowseed

## 6. The screen

![A conversation in progress](images/03-conversation.png)

*Figure 3 — A conversation with one seed in Shadow memory.*

The screen has three panels.

**Left — Conversations.** Your conversations, newest first, with the model,
the number of turns and the number of seeds. **New conversation** opens the
form. At the bottom, **Providers** shows whether OpenAI is available (chapter 12).

**Middle — The chat.** The header shows the title, the model, the authority
mode and the Gate policy badge (for example *Evidence-backed*). Type below and
press **Enter** to send; **Shift+Enter** starts a new line. While the model is
working you see *Waiting for response…*.

**Right — Shadow memory.** All seeds of this conversation. Each card shows the
status, the text, how often it was seen, how many verified sources support it,
how often it was used, and whether a contradiction is open. Click a card to
open the seed. At the bottom, **Technical details and raw data** shows the Gate
policy, the authority profile, the behavior digest and the full session data as
JSON.

On a phone or narrow window, the side panels fold away. Use the menu button for
conversations and the **Shadow** button for Shadow memory.

## 7. Seeds and their statuses

A seed is a short, traceable note about a point that may be open. It is a
*hypothesis*, not a fact and not an instruction.

Every seed has a status. The status tells you what the seed may do.

| Status | Meaning | Can it influence an answer? |
| --- | --- | --- |
| **Found** | Noticed once. | No |
| **Recurring** | Noticed again in a later turn. | No |
| **Supported** | Has at least one verified source, but the Gate has not given it weight. | No |
| **Validated** | Has weight from the Gate, but is not (or no longer) promoted. | No |
| **Promoted** | Passed the Gate. Eligible for use when relevant. | Yes, when relevant |
| **Used** | Promoted and actually used in at least one answer. | Yes, when relevant |
| **Blocked** | Has an open contradiction. | No |
| **Dormant** | Not seen for a while; its trace has faded. Can wake up when the topic returns. | No |
| **Expired** | Faded completely. Kept for the record. | No |

A *Recurring* seed in **Assisted** mode can carry the mark *Action required*:
it keeps coming back without a source. Shadowseed then asks you to look at it
instead of granting influence on its own.

### Opening a seed

![A seed in detail](images/04-seed-detail.png)

*Figure 4 — An opened seed with its counters and the evidence form.*

The detail view shows:

- **Seen** — in how many turns the seed was observed;
- **Verified sources** — how many distinct checked sources support it;
- **Contradiction** — whether a contradiction is open;
- **Weight** — its steering power, between 0 and 1. New seeds start at 0;
- **Used in answers** — how often it influenced an answer;
- **Trace** — a fading measure of recent presence;
- forms for evidence and contradiction, the **Timeline**, and **Raw data**.

![The timeline of a seed](images/06-timeline.png)

*Figure 5 — The timeline. Every memory event, validation and Gate decision is
listed with its time. Open an event to see the full record.*

### How seeds recur

When a new note might be the same open point as an earlier seed, Shadowseed
asks the model one short question: is this the same open question, or only the
same topic? Only a "same question" answer counts as recurrence. If the model
cannot answer, Shadowseed falls back to text similarity with a conservative
threshold. Recurrence is recorded but never gives authority on its own in
Controlled and Assisted mode.

## 8. Authority modes

You choose the authority mode when you create a conversation. It decides how a
seed can gain influence.

| Mode | Gate policy | How a seed gains authority | Use it for |
| --- | --- | --- | --- |
| **Controlled** (default) | Evidence-backed | Only through a source you have checked. One verified source promotes the seed. | Normal use |
| **Assisted** | Evidence-backed | As Controlled, and Shadowseed asks for your attention when a seed keeps recurring without a source. | When you want to be prompted |
| **Autonomous** | Exploratory | Recurrence counts as support; no external source is needed. | Research only |

In the technical details, Controlled appears as authority profile `strict`.

Autonomous mode lets the system grant authority without your involvement. Use
it to study the mechanism, not for answers you rely on.

## 9. Adding verified evidence

A seed in Controlled or Assisted mode can only become *Promoted* through a
source that you have checked yourself.

1. Open the seed.
2. Under **Add verified evidence**, enter a **Source reference**: a URL, a DOI
   or another stable reference.
3. Optionally add a **Note** explaining why the source supports the seed.
4. Tick **I checked this source and confirm it supports this seed.**
5. Click **Record evidence**.

![A seed after verified evidence](images/05-seed-promoted.png)

*Figure 6 — After one verified source the seed is Promoted, with weight 0.20.*

Rules that protect the Gate:

- **Only check what you have read.** The confirmation is recorded in the audit
  ledger as your statement.
- **One source counts once.** Entering the same reference again does not add
  authority, even through another route.
- **Model output is not evidence.** Do not cite an answer of the model or a
  summary it wrote.
- **Recurrence is not evidence.** A seed that came back often still needs a
  source.

## 10. Contradictions

If you find that a seed is wrong, misleading or out of date:

1. Open the seed.
2. Under **Contradiction**, click **Mark as contradicted**.

The seed is now **Blocked** and cannot influence any answer.

To lift the block, enter a **Basis for resolution** — why the contradiction no
longer applies — and click **Resolve contradiction**. Resolving only removes the
block. The seed does **not** get its authority back automatically; it must pass
the Gate again with a new verified source.

## 11. When a seed influences an answer

A seed influences an answer only if all of these hold at the moment you ask:

1. it is **Promoted**, with weight above zero;
2. its promotion is backed by a current Gate decision;
3. it has no open contradiction;
4. it is **relevant** to your current question;
5. the **point-of-use check** allows it for this turn.

So *Promoted* does not mean *used*. A promoted seed about backup retention stays
silent when you ask about something else. That is intended.

When a seed is used, its status becomes **Used** and the counter **Used in
answers** goes up. The seed reaches the model as bounded context marked as
untrusted; the model is not told to treat it as fact.

One more rule: when a seed was used in an answer, new seeds found in that same
answer are set aside for that turn, so Shadowseed does not learn from its own
influence.

## 12. Using OpenAI

The downloadable application works with local models only. OpenAI models are
available when Shadowseed is installed as a Python package with the `openai`
extra (chapter 20). In that case:

- enter a key under **Providers → Temporary API key**. The key stays in memory
  only; it is not saved and disappears when Shadowseed stops;
- when you create an OpenAI conversation, you must agree that prompts, shadow
  context and embeddings are sent to OpenAI;
- you confirm this again for each message you send.

## 13. Your data and privacy

**What is stored.** The folder `.shadowseed` in your home directory contains a
local database with your conversations, the model answers, seeds, Gate
decisions, evidence references and notes, and the audit ledger. Its protected
integrity key lives in the neighbouring folder `.shadowseed-integrity`.
Nothing is sent anywhere unless you use OpenAI.

**What not to type.** Do not paste passwords, API keys, access tokens or other
secrets into conversations, evidence references or notes. Use made-up or
anonymized material when real personal data is not needed.

**Backups and deletion.** The web application has no export button yet. With
the Python package installed you can use:

- `shadowseed workspace info` — show where the data is and how much there is;
- `shadowseed workspace backup --output <file>` — make a consistent copy of the
  database. Always give a file **outside** `.shadowseed`: without `--output` the
  copy goes to `.shadowseed/exports`, and deleting the workspace deletes it too;
- `shadowseed workspace restore <file>` — restore a copy;
- `shadowseed workspace delete --yes` — delete the complete workspace;
- `shadowseed export-workbench-report <session>` — export one conversation as a
  verified report (contains the full content);
- `shadowseed export-support-bundle <session>` — export a privacy-minimized
  support bundle (no conversation or seed text).

The `<session>` id is shown under **Technical details and raw data** →
**Session**.

A backup contains the same content as the original and must be protected in
the same way. Deleting the workspace removes everything inside `.shadowseed`,
including `.shadowseed/exports`; copies you saved elsewhere are kept.

## 14. Limitations

- **Few seeds with small local models.** With a 7B model, a seed appears in
  about one turn in eight and about a quarter of the seeds are useful.
- **Speed on CPU.** Two to three minutes per turn with a 7B model on a computer
  without a suitable GPU.
- **No proof of better answers.** Whether SSL improves answers is the subject
  of ongoing studies. A pilot study exists; a full result does not yet.
- **Seeds can be wrong.** A seed is a hypothesis. A promoted seed is supported
  by your source, not proven true.
- **Single user, single computer.** Shadowseed is not a multi-user or network
  service.
- **Not signed by Apple or Microsoft.** Your system warns on first start.
- **Interface in English.** The application itself is currently English only.
- **No comparison button.** The web application does not yet offer the
  "same question without SSL" comparison; it is available through the web API
  (chapter 18).

## 15. Troubleshooting

| Problem | Likely cause | What to do |
| --- | --- | --- |
| The browser does not open | Blocked by the system or the default browser is missing | Open the address shown in the Shadowseed window yourself |
| macOS: "cannot be opened" | Quarantine on a downloaded app | Right-click → Open, or run the `xattr` command from 3.3 |
| Windows: SmartScreen warning | Program not signed | More info → Run anyway |
| "Ollama not reachable" | Ollama is not running | Start Ollama and try again |
| Message about `embeddinggemma` | Embedding model missing or Ollama too old | `ollama pull embeddinggemma`; update Ollama to 0.11.10 or later |
| "Model not found" | Model name differs from the installed name | Use the exact name from `ollama list` |
| A turn takes minutes | Model runs on CPU | Expected for 7B on CPU; use a smaller model or a GPU |
| No seeds appear | Small models often find nothing | Continue the conversation; try a larger model |
| *Provider needed* badge | The model of this conversation is not available | Start Ollama or configure OpenAI |

### The doctor

The Python package contains a diagnostic tool:

```bash
shadowseed doctor
```

It checks Python, the workspace, the database, the audit ledger, permissions,
disk space, Ollama, the embedding setup and the optional providers, and tells
you how to fix what it finds. Typical output:

```text
python                   OK    3.11.15
workspace                OK    /home/you/.shadowseed
production_integrity     OK    verified ledger head sequence 7
ollama                   WARN  not detected at http://127.0.0.1:11434
                               Start `ollama serve`, pull a model, and rerun `shadowseed doctor`.
Workbench can start.
```

To use the doctor with the downloaded application, install the Python package
from the same release (see 20.1) and run `shadowseed doctor`; it checks the same
`.shadowseed` folder.

---

# Part 3 — Testing

## 16. Testing Shadowseed

### 16.1 What to look at

- Can you download, start and use the application without any other software?
- Is it clear which model is active and which authority mode applies?
- Does it feel like a normal chat before you look at the seeds?
- Are seed statuses and explanations understandable?
- Is it clear that evidence must be checked by you, and that recurrence is not
  evidence?
- Are error messages actionable when Ollama or a model is missing?
- Can you close and reopen a conversation without losing anything?

### 16.2 How to test

1. Start with the offline demo. It proves the mechanics, not the quality.
2. Then use Ollama with a real model and longer conversations (eight turns or
   more), because seeds and recurrence need time.
3. Note the model, the authority mode and what you did.

### 16.3 Reporting a problem

Include what you tried, the model and settings, the smallest sequence of steps
that shows the problem, what you expected and what happened, and whether a seed
was used in that turn. Do not include personal data or secrets.

Behavior that seems to let anyone change a seed's weight or promotion directly,
outside the Gate, is a serious defect. Report it with priority.

### 16.4 Support bundles

With the Python package, `shadowseed export-support-bundle <session>` produces a
privacy-minimized support bundle. It keeps structure and counts but leaves out conversation and seed text. Study
coordinators combine bundles with `scripts/aggregate_support_bundles.py`. Do not
edit a bundle by hand; its integrity check will fail.

---

# Part 4 — Research

## 17. The Shadow Seed Learning model

### 17.1 Lifecycle

**Observe → Seed → Recur / gather evidence → Validate → Promote → Relevance
check → Point-of-use influence.** Each step is separate, and only the Gate
changes authority.

- **Detection** reads the question, the draft answer and a bounded window of
  earlier turns, and proposes up to five atomic candidate gaps. The prompt is
  `detector_current_pair` v0.6.
- **Intake** admits a candidate as a weightless seed if it is a single
  question, or a single English statement that is not a bare list of
  categories.
- **Recurrence** is recognized by the session model (ADR-012), with embedding
  similarity as a floor (0.3) and as fallback.
- **Trace** records presence and decays with a half-life; seeds become dormant
  and later expire. A dormant seed can be reactivated when its topic returns.
- **Weight** is steering power. New seeds start at 0. Only the Gate raises it.

### 17.2 Gate policies

| Policy | Accepts |
| --- | --- |
| `evidence_backed` | Verified external support only. In Controlled and Assisted live sessions one source promotes (threshold 0.2, ADR-011). |
| `exploratory` | Qualifying recurrence *or* verified external support. |
| `legacy_evidence_required` | Historical thresholds for recurrence, trace and evidence; kept for compatibility. |

Verified support needs a non-empty `source_ref`, which is the identity of the
evidence: the same reference never counts twice. Contradictions are explicit
records with an id, reason, status and resolution basis; a seed with an open
contradiction is blocked. Resolution unblocks but does not restore weight.

### 17.3 Point of use

Before a seed may influence generation, `AgentSafetyContract.decide_and_record`
checks positive weight, promoted status, no blocking contradiction, and a live
Gate event for the seed's current authority version. Allowed and denied
decisions are both recorded, and each allowed decision is linked to the Gate
event that authorized it. Replay can detect a stale authorization.

### 17.4 Two kinds of memory

Under `evidence_backed`, recurrence is observation: a *trace*. Under
`exploratory`, recurrence may become a support signal after three
occurrences. The product default is `evidence_backed`.

## 18. Showing that SSL had an effect

A different wording between two answers is not evidence of SSL influence,
because two generations differ anyway. Attribute an effect only when:

1. the seed was promoted;
2. it was selected as relevant for the turn;
3. the point-of-use decision allowed it;
4. it actually surfaced, as recorded in the turn report and the seed timeline.

For a paired comparison, a turn can be sent with `compare_without_ssl: true`
through the web API (chapter 23). The control uses the same model, the same visible history and the same
message, receives no seed context, and does not change any state. The web
application stores the comparison in **Technical details → Last turn
comparison**; it does not yet have a button for it.

## 19. Studies and evidence

The repository contains preregistered study designs and their results:

- **Seed calibration** (`docs/research/seed-calibration.md`): usefulness of
  detected seeds and the reliability of recurrence recognition.
- **Detector calibration** (`docs/research/detector-calibration.md`): two
  blind-rated runs on Qwen 2.5 7B showing that prompt changes alter the number
  of seeds but not their usefulness on that model.
- **Evidence efficacy** (`docs/research/evidence-efficacy.md`): does an
  authorized seed improve answers against SSL-off and a self-critique control?
  Study 1 is a pilot.

Principles that apply to every study:

- fix the design and decision rule before the run;
- rate blind, and record the labels before decoding the key;
- record the exact model digest, the source commit and the prompt versions;
- treat model output as observation, never as evidence.

Research tooling lives in the separate `research/` package and in `scripts/`.
Results are committed under `benchmarks/` with their provenance.

---

# Part 5 — Development

## 20. Working from source

### 20.1 Installing the package

From a release, without Git:

```bash
python -m pip install shadowseed-0.12.4-py3-none-any.whl
```

From the repository:

```bash
git clone https://github.com/E-AI-MODEL/shadowseed-pro.git
cd shadowseed-pro
python -m pip install -e ".[test]"
```

Optional extras: `models` (Hugging Face and Sentence Transformers), `openai`,
`workbench` (legacy Gradio interface), `vector`, `build`, `standalone-build`,
`security`, and `dev` for everything. Python 3.10 or later is required.

### 20.2 Tests and checks

```bash
python -m pytest -q          # full suite
ruff check src tests scripts # lint
uv lock --check              # lockfile matches pyproject
```

The web client is a Next.js application in `apps/web`. Build it and copy the
static output into the Python package with `scripts/sync_web_assets.py`.

### 20.3 Rules for changes

- The Validation Gate is the only path that may raise authority. Do not add
  another.
- Authority fields (`weight`, `status`, `evidence_count`,
  `contradiction_score`) cannot be assigned directly; tests enforce this.
- Changes to the authority model need an ADR in `docs/architecture/adr/`.
- Every change goes through a pull request with green CI.

## 21. Architecture

| Part | Location | Role |
| --- | --- | --- |
| Core | `src/shadowseed/` (`manager.py`, `lifecycle.py`, `chat.py`) | Seeds, lifecycle, chat session |
| Gate | `src/shadowseed/gate/` | The canonical Validation Gate and its ledger |
| Detection | `src/shadowseed/detection/` | Detector prompts and parsers |
| Intake and recurrence | `intake.py`, `recurrence_*.py` | Admission and recurrence |
| Storage | `src/shadowseed/storage/` | SQLite workspace, integrity ledger |
| Application | `src/shadowseed/application/` | Workspace, limits, health checks |
| Adapters | `src/shadowseed/adapters/` | Ollama, OpenAI, Hugging Face, embeddings |
| Web API | `src/shadowseed_webapi/` | Loopback HTTP server and launcher |
| Web client | `apps/web/` | The browser interface |
| Legacy Workbench | `src/shadowseed/workbench/` | Gradio interface (opt-in) |
| Research | `research/` | Benchmarks and studies |

Design records: `docs/architecture/adr/ADR-001` to `ADR-012`. Start with
ADR-001 (the Gate as sole authority), ADR-006 (production-local boundary),
ADR-011 (single-source promotion) and ADR-012 (model recurrence recognition).

## 22. Command-line reference

| Command | Purpose |
| --- | --- |
| `shadowseed-web [--port N] [--workspace DIR] [--no-browser]` | Start the web application (default port 8765, loopback only) |
| `shadowseed-web --self-test --workspace DIR` | Run the built-in self-test |
| `shadowseed chat --backend fixture\|ollama\|openai` | Chat in the terminal |
| `shadowseed doctor [--json] [--workspace DIR]` | Diagnose the installation |
| `shadowseed init [--workspace DIR]` | Create a workspace |
| `shadowseed workspace info\|backup\|restore\|delete` | Manage the workspace |
| `shadowseed-workbench [--legacy-gradio]` | Start the desktop launcher: the web client by default, the legacy Gradio interface with `--legacy-gradio` |
| `shadowseed export-workbench-report <session>` | Export one conversation as a verified, content-bearing report ZIP |
| `shadowseed export-support-bundle <session>` | Export a privacy-minimized support ZIP |

Run any command with `--help` for all options. `docs/usage/cli.md` documents the
research and benchmark commands.

## 23. Web API reference

The server listens on `127.0.0.1` only. All routes start with `/api/v1`.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check |
| GET | `/providers` | Provider status |
| POST | `/providers/openai/credential` | Set a temporary OpenAI key |
| POST | `/providers/openai/credential/clear` | Remove it |
| GET | `/sessions` | List conversations |
| POST | `/sessions` | Create a conversation (`title`, `backend`, `model_id`, `authority_mode`, `external_confirmed`) |
| GET | `/sessions/{id}` | Read a conversation |
| POST | `/sessions/{id}/turns` | Send a message (`question`, `request_id`, optional `compare_without_ssl`, `external_confirmed`) |
| GET | `/sessions/{id}/seeds/{seed}` | Read a seed with its timeline |
| POST | `/sessions/{id}/seeds/{seed}/evidence` | Add verified evidence (`source_ref`, `note`, `operator_verified: true`, `request_id`) |
| POST | `/sessions/{id}/seeds/{seed}/contradictions` | Mark as contradicted |
| POST | `/sessions/{id}/seeds/{seed}/contradictions/resolve` | Resolve a contradiction (basis required) |

Sending a turn and the three seed actions (evidence, contradiction,
resolution) require a `request_id`: replaying the same id is safe, and a reused
id with different content is refused. Creating a conversation and setting or
clearing the OpenAI key have no `request_id`; repeating them repeats the
action. Requests from a foreign browser origin or with a
non-loopback `Host` header are refused.

## 24. Builds and releases

- **CI** runs the tests on Python 3.10 and 3.12, production-local checks on
  Windows, macOS and Linux, a strict audit of the shipped dependencies, and
  frozen builds for all three platforms on every pull request.
- **Release Workbench** (manual) publishes the version in `pyproject.toml` from
  the exact `main` commit, after CI on that commit is green. It builds the three
  downloads, `SHA256SUMS`, `PROVENANCE.json`, an SBOM, wheel and sdist.
- **Production Release Assurance** runs automatically on the published tag and
  verifies attestations, checksums and provenance.
- Release notes live in `docs/workbench/release-<version>.md`.

---

# Part 6 — Security and operations

## 25. Security model

**Claimed for the local profile:**

- the server is reachable only through loopback (`127.0.0.1`); the `Host` header
  is validated against DNS rebinding;
- authority-changing actions are attributed to a trusted local actor;
- a client flag alone cannot create verified authority;
- the Gate and the point-of-use contract are the only path to authority and
  influence;
- tampering with the authority history, or rolling back to an older state, is
  detectable against protected integrity material;
- operational logs are content-minimized;
- releases are tied to an exact source commit with checksums and provenance.

**Not claimed:**

- protection against a compromised operating system or administrator;
- multi-user isolation or security on a hostile network;
- the factual truth of evidence that an operator marks as checked;
- universal protection against prompt injection;
- better answers in general;
- secure erasure beyond what the file system provides.

The full threat model is in `docs/architecture/production-threat-model.md`.

## 26. Running Shadowseed reliably

- **Limits.** Oversized input is refused before anything is stored. Model calls
  have a 120-second timeout and no automatic retries. A failure never changes the
  stored state.
- **Permissions.** On macOS and Linux, the workspace is readable by its owner
  only. On Windows, the user account protects it.
- **Integrity.** An audit ledger with protected integrity material records
  authority events. Never "repair" a workspace by deleting its integrity
  material; restore a verified backup instead.
- **Backups.** Use `shadowseed workspace backup --output <file>` with a file
  outside the workspace; the default location inside `.shadowseed/exports` is
  removed with the workspace. Keep backups as safe as the original.
- **Containers.** `Dockerfile.workbench` is for development. Publish the port on
  loopback only: `-p 127.0.0.1:7860:7860`.
- **Diagnostics.** `shadowseed doctor` separates usable state, integrity problems
  and missing dependencies.

Operational procedures: `docs/operations/production-local-recovery.md` and
`docs/operations/production-local-release.md`.

## 27. Configuration reference

| Setting | Default | Meaning |
| --- | --- | --- |
| `--port` | 8765 | Preferred port; another free port is used if it is taken |
| `--workspace` | `~/.shadowseed` | Data folder |
| `OLLAMA_HOST` | `http://localhost:11434` | Address of the Ollama server |
| `OPENAI_API_KEY` | not set | OpenAI key for the Python package; the web application uses the temporary key instead |
| Authority mode | Controlled | Set per conversation |
| Embedding model (Ollama) | `embeddinggemma` | Needed for real conversations |

---

# Appendices

## A. Glossary (English–Dutch)

| English | Dutch | Meaning |
| --- | --- | --- |
| Shadow Seed Learning (SSL) | Shadow Seed Learning (SSL) | The memory layer around the model |
| Seed | Seed (zaadje) | A traceable note about a possibly open point |
| Shadow memory | Schaduwgeheugen | All seeds and their history |
| Validation Gate | Validatiepoort (Gate) | The only place where authority changes |
| Authority | Zeggenschap | The right of a seed to influence answers |
| Weight | Gewicht | Steering power of a seed, 0 to 1 |
| Trace | Spoor | Fading measure of recent presence |
| Recurrence | Terugkeer | A seed seen again in a later turn |
| Verified evidence | Geverifieerd bewijs | A source the operator checked |
| Contradiction | Tegenspraak | A recorded objection that blocks a seed |
| Promoted | Gepromoveerd | Passed the Gate; eligible for use |
| Used | Gebruikt | Actually used in an answer |
| Point of use | Moment van gebruik | The final check before influence |
| Authority mode | Zeggenschapsmodus | Controlled, Assisted or Autonomous |
| Gate policy | Gate-beleid | `evidence_backed` or `exploratory` |
| Workspace | Werkmap | The `.shadowseed` data folder |
| Audit ledger | Auditlogboek | Protected record of authority events |
| Offline demo (fixture) | Offline demo | Mode without a model |

## B. Frequently asked questions

**Does Shadowseed send my conversations anywhere?**
No, unless you choose OpenAI. With Ollama everything stays on your computer.

**Why do I see so few seeds?**
Small models find few open points. Longer conversations and larger models help.

**I added a source, but the seed is not used. Why?**
A promoted seed is only used when it is relevant to the question you ask. Ask
about the topic of the seed.

**Can I set a seed's weight myself?**
No. Only the Gate changes authority. That is a deliberate safeguard.

**Does a seed that recurs often become promoted?**
Not in Controlled or Assisted mode. Recurrence is recorded but needs a verified
source to become authority. In Autonomous mode recurrence can count.

**Is a promoted seed true?**
Not necessarily. It is supported by the source you checked. Check sources
carefully.

**May I use Shadowseed commercially?**
The license is PolyForm Noncommercial 1.0.0. Commercial use needs separate
permission.

## C. About this document

| | |
| --- | --- |
| Applies to | Shadowseed 0.12.4 |
| Editions | English (`shadowseed-manual-en.md`), Dutch (`shadowseed-handleiding-nl.md`); PDF versions in the same folder |
| Screenshots | Offline demo in the web application of version 0.12.4 |
| Source | `docs/manual/` in the repository |
| License | PolyForm Noncommercial License 1.0.0 |

Corrections and suggestions are welcome as an issue in the repository.
