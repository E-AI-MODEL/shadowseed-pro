# What is Shadow Seed Learning?

Shadow Seed Learning (SSL) is a model-independent learning layer that runs
alongside a language model. It does not retrain the model weights. Instead, it
builds an external, persistent and inspectable memory of candidate perspectives
that may become useful later.

The shortest description is:

> **SSL watches what a model and its information environment may be missing,
> stores promising missing perspectives as shadow seeds, lets those seeds earn
> or lose authority over time, and may bring an authorized seed back when it is
> relevant later.**

That makes SSL closer to an inspectable experience layer than to classic model
training.

---

## 1. Why SSL exists

A language model normally answers from three main things:

1. its trained model weights;
2. the current prompt and conversation;
3. any external context supplied for the current request.

Once a conversation, document or retrieved context disappears from the active
window, the model does not automatically maintain a structured, inspectable
record of what was repeatedly absent, contradicted, useful or worth revisiting.

SSL adds a separate shadow process beside the model. The shadow process can
observe candidate omissions or alternative frames, track whether they recur,
record evidence and contradictions, and decide whether a seed has earned enough
authority to become eligible for later use.

The LLM remains the language model. SSL is the memory, authority and surfacing
layer around it.

---

## 2. The core lifecycle

The canonical product flow is:

**Observe -> Seed -> Recur / gather evidence -> Validate -> Promote -> Relevance
check -> Point-of-use influence**

Those stages are deliberately separate.

### Observe

SSL looks at a chat turn or source-text chunk and asks what useful perspective,
missing explanation, assumption or alternative frame might be absent.

Observation is not authority. It is only detection.

### Seed

A detected candidate becomes a **shadow seed**.

A seed is a hypothesis or candidate perspective. It is not automatically a
fact, instruction or truth claim.

### Recur / gather evidence

A seed may appear again semantically across later turns or source chunks.
Evidence may also support or challenge it.

Recurrence matters because a one-off candidate should not automatically become
important merely because one detector produced it once.

### Validate

Signals are evaluated through the configured Validation Gate policy.

Validation is an authority decision, not a writing decision.

### Promote

A seed that satisfies the policy can become **PROMOTED**.

Promotion means the seed is eligible to participate later. It does **not** mean
that it will be injected into every answer.

### Relevance check

When a new question arrives, promoted seeds are compared with the current
question. Only sufficiently relevant seeds are eligible to surface.

### Point-of-use influence

A seed that is both authorized and relevant may be exposed to the answer
generation path as bounded, untrusted candidate context.

This is the moment at which SSL can actually affect a response.

---

## 3. What a shadow seed is

A useful mental model is:

> A shadow seed is a small, traceable piece of possible missing context that can
> develop a history.

A seed can have:

- its original text;
- an embedding;
- recurrence / occurrence information;
- trace strength;
- evidence count;
- contradiction state;
- Gate decisions;
- authority versions;
- lifecycle events;
- provenance;
- a record of whether it ever surfaced.

That history is what makes a seed different from simply adding another sentence
to a prompt.

---

## 4. Authority is separate from relevance

This distinction is central to SSL.

A seed can be:

- relevant but not authorized;
- authorized but irrelevant to the current question;
- both authorized and relevant;
- blocked by a contradiction.

Only the third case can normally lead to influence.

This is why **PROMOTED does not mean USED**.

A promoted seed can sit in shadow memory for a long time without appearing in a
response. That is expected behavior when the later questions are not relevant.

---

## 5. The Validation Gate

The Validation Gate protects the transition from observation to authority.

Instead of allowing a detector or language model to decide by itself that a
candidate idea is now trusted, SSL evaluates explicit signals under a policy.

Depending on the configured profile and policy, relevant signals can include
things such as:

- independently verified external support;
- recurrence;
- contradiction;
- human feedback;
- system-observed evidence where policy explicitly permits it.

The Gate creates a traceable decision record. That record can include the
policy, reason, status transition, weight transition and authority version.

A key design principle is:

**the system may automate authority decisions, but it should not make them
invisible.**

---

## 6. Contradictions matter

SSL should not only accumulate supporting material.

A useful long-running memory system must also be able to discover that a seed is
wrong, misleading, obsolete or contextually unsafe.

Contradictions can therefore:

- reduce confidence;
- block a seed;
- prevent future influence;
- require explicit resolution;
- remain visible in the audit trail.

This is one reason SSL is not intended to be an ever-growing pile of remembered
sentences.

---

## 7. Trace, decay and memory hygiene

More text is not automatically better memory.

If every detected idea stayed equally strong forever, a large corpus would
eventually produce an unusable memory layer.

SSL therefore needs memory hygiene such as:

- semantic deduplication;
- clustering;
- recurrence tracking;
- provenance;
- evidence tracking;
- contradiction handling;
- trace decay;
- expiry / dormancy;
- selective surfacing.

The design goal is:

> **Observe broadly, grant authority selectively, retrieve narrowly.**

---

## 8. Is SSL training?

Not in the classic machine-learning sense.

### Classic training / fine-tuning

Training changes the model parameters or weights. The learned behavior becomes
part of the model itself.

### SSL

SSL keeps its experience outside the model weights.

The base LLM can remain exactly the same while the surrounding Shadowseed memory
changes over time.

That means two Shadowseed installations can use the same base model and still
become increasingly different if they process different conversations,
documents or corpora.

The difference is not stored inside the neural weights. It is stored in the
external, inspectable shadow memory and its authority history.

That is why it is reasonable to describe SSL as **experience accumulation**,
but misleading to call it ordinary fine-tuning.

---

## 9. How SSL differs from RAG

Retrieval-Augmented Generation normally starts from a user question and searches
a document store for relevant information.

SSL starts from a different idea.

It maintains candidate perspectives that were previously observed as potentially
missing or useful. Later, those seeds themselves can become part of the
retrieval or surfacing process.

So RAG is primarily:

**question -> retrieve relevant source material -> answer**

while SSL is closer to:

**observe -> build candidate experience -> authorize -> later surface when
relevant -> answer**

The two approaches can complement each other.

---

## 10. Chat and corpus ingestion

SSL can learn from more than conversation turns.

The 0.8 product line introduces a **Sources** workspace for:

- pasted text;
- TXT;
- Markdown;
- JSON;
- CSV;
- multiple uploaded files.

Source ingestion follows a separate path:

**extract -> chunk -> detect -> cluster / recur -> Gate -> shadow memory**

Uploaded chunks do not become fake chat turns.

The upload itself also does not become trusted evidence merely because the user
uploaded it. It remains observation input unless a policy explicitly grants a
stronger role to a verified source.

This separation matters for both auditability and future large-corpus work.

---

## 11. Why large amounts of text can make a Shadowseed system distinctive

If SSL processes a large and varied history, its shadow memory can develop a
distinctive structure:

- some candidate ideas disappear;
- some recur;
- some cluster into stronger themes;
- some gain support;
- some are contradicted;
- some are promoted;
- only a small subset eventually surfaces in later use.

So two installations with the same LLM but different histories can gradually
behave differently.

That is the intended form of differentiation: not hidden retraining, but a
different, inspectable experience layer.

The value does not come from volume alone. It comes from **selection over time**.

---

## 12. Authority profiles

The 0.8 product direction exposes four authority profiles.

### Controlled

The current backwards-compatible mode.

- detection can happen automatically;
- authority-bearing evidence remains user-controlled;
- promotion still goes through the Gate;
- relevant promoted seeds may surface under the existing point-of-use checks;
- contradictions require explicit resolution.

### Assisted

Intended to automate low-risk lifecycle work while asking the user at genuine
authority decisions or uncertainty.

### Autonomous

Intended to let SSL validate, activate, promote and surface seeds automatically
where provenance, policy, Gate and point-of-use checks permit it.

### Open research

Intended for the least restrictive experimental runs while retaining provenance,
Gate decisions and audit records.

**Release-candidate note:** in 0.8.0rc1 the profile model and UI are being built
first. Controlled preserves the existing runtime behavior. Assisted, Autonomous
and Open research should not be assumed to have their full automation semantics
until that runtime wiring is explicitly completed and tested.

---

## 13. How to verify whether SSL actually worked

A user should never have to infer SSL influence from the wording of two answers.

Two stochastic model generations can differ even when no shadow seed was used.

The correct verification path is:

1. inspect the current shadow memory;
2. identify whether a seed is promoted;
3. inspect which seeds were eligible for the turn;
4. inspect which seeds were selected;
5. verify which seeds actually surfaced;
6. inspect the point-of-use decision;
7. only then attribute answer differences to SSL.

The product therefore exposes:

- **Shadow** for seed lifecycle and status;
- **Verify** for stored SSL-on / SSL-off comparisons and attribution;
- **Technical inspection** for raw JSON, Gate events, trace, relevance,
  contradictions and influence records.

A textual difference by itself is not evidence of SSL influence.

---

## 14. A concrete example

Imagine a long-running discussion about AI policy.

Early in the conversation, SSL repeatedly detects a candidate perspective:

> "Long-term implementation costs are being underweighted."

At first this is merely a seed.

Later:

- related wording recurs in several documents;
- an independently checked source supports the point;
- the seed passes the configured Gate;
- its status becomes PROMOTED.

Three weeks later the user asks a question about the cost of scaling the policy.

The seed is now relevant. If it passes the point-of-use checks, it can surface as
candidate context for the answer.

If the user instead asks for the weather, the promoted seed should remain
silent.

That difference is the heart of selective surfacing.

---

## 15. What the user should be able to inspect

For every important seed, the product should answer:

- What did Shadowseed notice?
- Where did it come from?
- How often did it recur?
- What evidence supports it?
- What contradicts it?
- Why is it in its current state?
- Which Gate decision changed its authority?
- Has it ever surfaced?
- Which answer did it influence?
- Why was it relevant at that moment?
- What is the raw technical record?

The plain-language view and the raw JSON should describe the same underlying
events at different levels of detail.

---

## 16. What SSL does not claim

SSL does not make every model answer correct.

It does not guarantee that detected seeds are true.

It does not make uploaded documents trustworthy.

It does not mean every promoted seed should be used.

It does not eliminate normal LLM uncertainty or stochasticity.

It does not automatically become better simply because it has seen more text.

Its value depends on the quality of detection, evidence, contradiction handling,
memory hygiene, authority policy and point-of-use selection.

---

## 17. Product design principle

The user experience should make SSL understandable before it makes it technical.

The primary product journey is:

**Start -> Run -> Observe -> Understand -> Verify -> Control -> Inspect**

A new user should be able to operate Shadowseed without reading raw JSON.

A technical user should still be able to drill all the way down to:

- lifecycle events;
- embeddings;
- similarity / relevance;
- Gate decisions;
- authority versions;
- evidence;
- contradictions;
- ledger references;
- raw JSON.

Progressive disclosure is therefore a product requirement, not a cosmetic
choice.

---

## 18. Glossary

**Shadow seed**  
A traceable candidate perspective or missing-context hypothesis.

**Shadow memory**  
The persistent collection of seeds and their lifecycle state.

**Trace**  
A decaying measure used in the seed lifecycle.

**Evidence**  
A signal that may contribute to authority under a Gate policy.

**Contradiction**  
A signal that challenges a seed and may block or weaken it.

**Validation Gate**  
The policy-controlled boundary that decides whether signals may change seed
authority.

**Promoted**  
A seed has gained sufficient authority to become eligible for later use.

**Surfacing**  
Selecting an authorized seed as candidate context for a later turn.

**Point of use**  
The final decision point at which an authorized and relevant seed may influence
generation.

**Authority profile**  
The configuration that determines which lifecycle actions are manual,
assisted or automated.

---

## 19. One-sentence summary

**Shadow Seed Learning is an inspectable experience layer around an LLM that
observes possible missing perspectives, lets them earn or lose authority over
time, and selectively reintroduces authorized perspectives when they become
relevant later.**
