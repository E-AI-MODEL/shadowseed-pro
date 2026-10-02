# ADR-009: Runtime component ownership and human-SSL orchestration

Status: Proposed  
Date: 2026-10-02  
Owners: Shadowseed maintainers  
Target release: 0.11.0 Research Preview  
Refines: ADR-001, ADR-002, ADR-003, ADR-005 and ADR-008

## Context

Shadowseed Pro now has a working end-to-end live path. A candidate can be detected, recur, gain authority through the Validation Gate, become promoted, pass relevance and point-of-use checks, and influence a generated answer.

Live testing also showed that the runtime, configuration and Workbench do not always expose the same component boundaries. The main gaps are:

- chat detection currently sees the generated answer without the current user question;
- the terms current, pair, seed, cluster, Gate, authority and surfacing are not consistently tied to one owning component in the UX;
- the application can identify Assisted seeds that need human review, while vNext does not make that handoff first-class;
- current Gate revalidation can apply semantics that differ from the named canonical Gate policy;
- legacy_evidence_required can appear as a normal strictness endpoint although it is a compatibility policy;
- one allow_self_reinforcement flag controls both same-turn answer revision and SSL-generated recurrence;
- recurrence mode, cluster threshold and embedding-space changes are stateful but can look like ordinary hot settings;
- generation, detection and revision are separate roles but normally share one physical model;
- live prompts are distributed across modules and are not represented as one versioned runtime contract;
- the Workbench exposes many facts about state but does not consistently answer the user-facing question: who is expected to act now, Shadowseed or the human?

The existing SSL doctrine remains valid:

- observation is not authority;
- recurrence is not external evidence;
- the Validation Gate is the sole authority decision boundary;
- promotion is eligibility, not mandatory influence;
- point-of-use authorization is mandatory before influence;
- SSL-exposed output is not independent recurrence by default;
- the Workbench is a presentation layer and must not reimplement authority semantics.

This ADR aligns implementation, configuration and UX around those boundaries before prompt wording and 0.11.0 implementation are changed.

## Decision

### 1. Canonical component model

The live path is:

~~~text
USER QUESTION
    |
    v
[1] ANSWER GENERATION
    |
    v
[2] DETECTION CONTEXT
    |
    v
[3] DETECTOR
    |
    v
[4] OBSERVATION LEDGER + INTAKE
    |
    v
[5] SEMANTIC REPRESENTATION
    |
    v
[6] RECURRENCE
    |
    v
[7] LIFECYCLE
    |
    v
[8] VALIDATION GATE
    |
    +----> HUMAN / SSL HANDOFF
    |
    v
[9] PROMOTED ELIGIBILITY
    |
    v
[10] RELEVANCE / SURFACING
    |
    v
[11] POINT-OF-USE AUTHORIZATION
    |
    v
[12] INFLUENCE / REVISION
    |
    v
FINAL ANSWER
    |
    +----> VERIFY / A-B / AUDIT
~~~

The components have non-overlapping ownership:

| Component | Primary input | Owns | May mutate | Must not decide |
| --- | --- | --- | --- | --- |
| Answer generation | history + current question | ordinary draft | draft text | seed authority |
| Detection context | question/draft or source observation | detector context package | context metadata | truth or authority |
| Detector | detection context | candidate directions | candidate observations | evidence, validation, promotion |
| Observation ledger + intake | candidate + provenance | atomicity, provenance, dedup | observation records, seed creation/dedup | truth, authority |
| Semantic representation | atomic seed text | vector representation | embedding | authority |
| Recurrence | seed embedding + existing memory | independent recurrence identity | occurrence / cluster state | external evidence |
| Lifecycle | seed state + turn/time | trace, dormancy, reactivation, expiry | lifecycle state | positive authority |
| Validation Gate | typed validation signals | authority transition | weight, evidence count, promotion, contradiction authority state | answer wording |
| Human authority actions | review/evidence/contradiction basis | trusted signal submission | canonical Gate requests | direct weight/status assignment |
| Relevance / surfacing | current question + eligible seeds | relevance selection | selection / resurfacing metadata | authority |
| Point-of-use | current authorized seed + action | concrete allow/deny | influence ledger record | new authority |
| Influence / revision | question + draft + allowed seed context | bounded answer change | final answer | seed authority |
| Verify / A-B | stored control/treatment outputs | comparison and human judgment | comparison/feedback records | runtime authority/history |
| Config / God mode | researcher choice | active component contracts | configuration state | silent state reinterpretation |
| UX orchestration | canonical runtime state | who acts next and why | presentation only | authority logic |

No prompt, UI control or helper may silently collapse two independent component decisions into one user concept.

### 2. Current, pair, seed and cluster are component-scoped terms

These words are not global modes.

For chat detection:

~~~text
detection context = current pair
current pair = current user question + current draft answer
~~~

For source ingestion:

~~~text
detection context = current source observation
current source observation = source chunk + source provenance
~~~

After detection:

~~~text
recurrence representation = atomic seed
cluster = semantic grouping of seed representations
~~~

For relevance:

~~~text
surfacing query = current user question
comparison = current question <-> promoted seed
~~~

For same-turn influence:

~~~text
revision context = current question + existing draft + allowed seed context
~~~

The Workbench therefore uses component-qualified labels such as Detectiecontext, Recurrence, Relevantiematch and Invloed op antwoord. A generic Context: current/pair control is not sufficient.

### 3. Golden path: autonomous exploratory

The normal happy flow for an autonomous exploratory session is:

~~~text
1. User asks a question.
2. Generation role writes a draft answer.
3. Detection receives the current pair.
4. Detector returns zero or more atomic candidate directions.
5. Observation ledger stores provenance.
6. Intake accepts, rejects or deduplicates candidates.
7. Accepted seed text is embedded.
8. A later independent observation maps to the same seed/cluster.
9. Recurrence creates a recurrence signal when its policy threshold is met.
10. Validation Gate evaluates that signal.
11. Authority may move 0.0 -> 0.2 -> 0.4 -> 0.6.
12. At promotion threshold the seed becomes PROMOTED.
13. On a relevant current question the promoted seed is selected.
14. Point-of-use records allow/deny for answer modification.
15. If allowed, influence performs a bounded revision.
16. Final answer is shown.
17. Optional A/B and human quality review remain non-mutating.
~~~

Promotion does not force step 13 or step 15.

### 4. Golden path: Assisted evidence-backed

Assisted mode has the same path until mature recurrence is reached.

~~~text
mature recurrence
  -> orchestration state: JIJ BENT AAN ZET
  -> human inspects candidate
  -> independently verified support is submitted
  -> Validation Gate evaluates support
  -> authority changes when policy permits
  -> promotion when threshold is reached
~~~

The UI must expose this handoff before the user has to infer it from raw JSON.

### 5. Validation Gate semantics are singular

ADR-001 remains authoritative.

The following do not grant authority:

- detector output;
- semantic similarity;
- cluster membership;
- recurrence count by itself;
- raw uploaded source text;
- retrieval hits;
- prompt wording;
- UI inspection;
- A/B comparison;
- audit-only tester feedback.

Authority changes continue to flow through typed Validation Signals and the canonical Validation Gate.

A promoted seed is eligible for later influence. It is not automatically relevant, surfaced or used.

### 6. Current Gate revalidation uses canonical policy semantics

Historical promotion remains immutable audit history.

When revalidate_current_gate is enabled, point-of-use may require a promoted seed to satisfy the policy active now. That current check must use the same meaning as the named canonical Gate policy.

The present code can require recurrence AND evidence under evidence_backed during current revalidation, while the canonical EvidenceBackedPolicy does not use that same conjunction. 0.11.0 removes this semantic split.

A separate current-eligibility policy is allowed only if it is explicitly named and documented as a different policy.

### 7. Compatibility policies are not normal product modes

legacy_evidence_required remains available for compatibility, historical replay and explicit research.

It is not the normal maximum-strictness endpoint and must not appear as an ordinary Gate choice without a compatibility label.

Normal product presets use current canonical policies.

### 8. Human-SSL orchestration is first-class

Every session and every seed exposes one of four orchestration states.

**Shadowseed is aan zet**  
The configured runtime can continue automatically. No human action is required.

**Menselijke review is optioneel**  
Human inspection or trusted support may be useful, but SSL is not blocked on it.

**Jij bent aan zet**  
A human action is required for the next authority step under the configured regime.

**Geblokkeerd**  
A blocking contradiction or equivalent hard stop prevents influence until an authorized resolution occurs.

Every orchestration state answers:

1. Why is this the current state?
2. Which exact action can the human take?
3. What happens if the human does nothing?

The application layer derives orchestration state from canonical runtime state. The Gradio UI only presents it.

### 9. Orchestration rules by authority regime

| Regime | Detect | Recurrence | Validation | Promotion | Relevance | Influence | Typical human handoff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Controlled / Strict | SSL | SSL | human/trusted support through Gate | SSL after Gate | SSL | SSL after point-of-use | support or contradiction review |
| Assisted | SSL | SSL | SSL monitors, human supplies missing trusted support | SSL after Gate | SSL | SSL after point-of-use | proactive review of mature recurrence |
| Autonomous | SSL | SSL | SSL through exploratory Gate | SSL | SSL | SSL after point-of-use | optional inspection; contradiction resolution |
| Open research | SSL | SSL | SSL through exploratory Gate unless explicitly overridden | SSL | SSL | SSL after point-of-use | optional inspection; contradiction resolution |

Blocking contradiction is never hidden by a permissive profile.

### 10. Authority profile and Gate policy remain distinct

An authority profile defines the default human/SSL division of labor.

The effective Gate policy defines the authority rule actually active.

If God mode overrides the profile's default Gate, the Workbench shows that relationship explicitly, for example:

~~~text
Open research
Default Gate: exploratory
Override active: evidence-backed
~~~

Profile and Gate remain independently inspectable, but they are not presented as unrelated flat settings.

### 11. Assisted review-required state must reach vNext

The application already computes authority_review_seed_ids for Assisted evidence-backed sessions.

vNext must consume this state.

At session level the Workbench can show:

~~~text
Jij bent aan zet voor 2 geheugenpunten
~~~

At seed level it explains the exact reason, for example:

~~~text
Validation Gate wacht op geverifieerde ondersteuning.
Zonder actie blijft dit punt in Shadow en kan het nog niet worden gebruikt.
~~~

Verified support and contradiction controls are contextual actions. They are not presented as equally necessary for every seed.

### 12. Contradiction submission and contradiction resolution are separate

A contradiction signal opens canonical contradiction state and blocks point-of-use.

The UX must distinguish:

- Tegenspraak registreren
- Tegenspraak oplossen

A blocking seed shows Geblokkeerd and identifies the required human resolution path where the backend supports it.

Verified support does not silently close an open contradiction.

### 13. Split self-reinforcement into two mechanisms

The current allow_self_reinforcement flag conflates:

1. whether SSL-exposed/generated output may later contribute recurrence/authority;
2. whether a seed promoted during the current turn may trigger one bounded answer revision.

These become conceptually separate settings:

~~~text
allow_ssl_generated_recurrence
allow_same_turn_revision
~~~

Research-safe default:

~~~text
allow_ssl_generated_recurrence = false
allow_same_turn_revision = configurable
~~~

ADR-003 remains the fail-closed default for contaminated observations.

Same-turn revision does not automatically make revised output recurrence-eligible.

### 14. Same-turn influence is revision, not free regeneration

Same-turn influence receives the existing draft explicitly.

Contract:

~~~text
question + existing draft + authorized relevant seed(s)
    -> bounded revision
~~~

Not:

~~~text
question + seed(s)
    -> completely new answer
~~~

The revision may return the existing draft unchanged when no seed materially improves it.

The exact wording belongs to the Prompt Contract PvA, not this ADR.

### 15. Generation, detection and revision are explicit model roles

Generation role, detection role and revision role are distinct components even when one physical model performs all three.

A model/provider setting must make clear which role or roles it changes.

Future role-specific models do not require a new component model.

### 16. Embedding configuration is shared semantic infrastructure

The embedding backend/model influences at least:

- intake deduplication;
- cluster membership;
- semantic recurrence;
- TrTL reactivation;
- current-question relevance;
- surfacing;
- vector workflows;
- retrieval probes;
- SSOT search.

Changing embedding space after seeds exist is not an ordinary hot setting.

Supported semantics are:

- new session;
- explicit re-embedding migration;
- explicit rebuild under a new behavior/configuration epoch.

A generic force switch must not leave old vectors silently interpreted in a different embedding space.

### 17. Recurrence mode and cluster threshold are stateful structural settings

recurrence_mode and cluster_threshold affect persisted recurrence state.

Changing them must not leave restored state contradicting active configuration.

The restore path must not recreate a clusterer from stale cluster_state when active recurrence_mode is pairwise. A stored cluster threshold must not silently override a newly selected threshold.

A structural recurrence change requires a defined new-session, rebuild/migration or new-epoch path.

### 18. God mode is organized by component

God mode remains available and continues to write runtime configuration only. It never edits source code or Git.

Advanced settings are grouped under:

- Generation
- Detection
- Semantic representation
- Recurrence
- Lifecycle
- Validation Gate
- Relevance / surfacing
- Influence / revision
- Evaluation

Every setting exposes:

- owning component;
- plain-language effect;
- whether the change is immediate or stateful;
- whether existing state is reinterpreted;
- whether a rebuild, migration or new session is required.

A product preset is a starting configuration, not hidden alternate logic.

### 19. Convenience controls may not imply false continuity

One control may change multiple fields only when those fields implement one coherent user intent.

A surfacing preset may alter relevance threshold and top-k when clearly described as surfacing behavior.

A continuous Gate strictness slider must not silently switch authority profile, Gate policy, compatibility policy and unrelated thresholds unless that whole mapping is a stable documented policy contract.

Named authority regimes are preferred over pseudo-continuous percentages.

### 20. Live prompts become versioned runtime assets

Each live prompt has:

- prompt_id;
- prompt_version;
- component owner;
- trigger moment;
- input contract;
- exact template;
- output contract;
- stable content hash.

The live registry distinguishes at minimum:

- answer-generation prompt;
- chat detector prompt;
- source detector prompt where materially different;
- candidate-context / point-of-use framing;
- same-turn revision prompt.

Legacy and research prompts remain identifiable as such.

Prompt wording is governed by the follow-up Prompt Contract PvA.

### 21. Same-turn A/B remains non-mutating

The ordinary same-turn comparison keeps:

- the same model configuration;
- the same current user message;
- the same visible pre-turn history;
- no SSL candidate context in the control;
- no control output in detection, recurrence, Gate state or later conversation history;
- at most one extra current-turn generation.

A/B runs at generation time rather than being reconstructed later.

Comparison language distinguishes:

- SSL context was exposed;
- answer text differed;
- a human judged one answer better.

Context exposure is not proof of quality improvement.

Longitudinal vanilla trajectories and pre-authority pressure experiments remain Research-only.

### 22. Source ingestion follows the same governance

Source ingestion is an observation route:

~~~text
source observation
  -> detector
  -> observation/intake
  -> semantic memory
  -> recurrence/lifecycle
  -> Validation Gate
  -> possible human/SSL handoff
~~~

Uploaded source text is not verified evidence merely because it was uploaded.

After source ingestion the same orchestration state is recalculated and shown.

### 23. SSOT, retrieval probes and external feedback are explicit side channels

Verified SSOT chunks, retrieval probes, vector feedback and related research mechanisms may feed or inspect the system only through their documented boundaries.

They do not bypass the Validation Gate or point-of-use authorization.

They are explicit side channels around the golden path and remain named in provenance/audit.

### 24. Behavior/configuration epoch extends reproducibility

The production ledger already records runtime reconfiguration and authority-related configuration digests.

0.11.0 adds a broader behavior/configuration fingerprint covering settings that materially affect runtime behavior, including:

- generation/detection/revision model-role configuration;
- prompt IDs, versions and hashes;
- embedding backend/model;
- dedup threshold;
- max seed words;
- recurrence mode;
- cluster threshold;
- Validation Gate profile/policy and authority thresholds;
- SSL-generated recurrence policy;
- same-turn revision policy;
- surfacing policy.

Each turn report references the active epoch or digest.

Historical turn meaning is never silently rewritten after a God-mode change.

## Governance rules

1. Detector proposes. It never validates.
2. Intake structures. It never grants truth or authority.
3. Recurrence records independent repetition. It never becomes external evidence by relabeling.
4. Lifecycle can weaken or expire memory. It does not create positive authority.
5. Validation Gate is the only authority transition boundary.
6. Human actions submit typed evidence/contradiction/resolution to canonical services. Humans do not edit weight or promotion directly.
7. Relevance selects among eligible seeds. It does not validate them.
8. Point-of-use must record allow/deny before influence.
9. Revision may alter answer wording but cannot strengthen the seed that caused it unless a separately configured later clean observation qualifies under ADR-003.
10. A/B control output never enters live SSL state.
11. UI state never substitutes for runtime state.
12. God-mode changes are auditable and cannot silently reinterpret incompatible persisted state.

## Failure and handoff behavior

**No detector candidate**  
The turn continues normally. No seed is required.

**Candidate rejected by intake**  
Record the reason where useful. Do not create authority.

**Recurrence below policy threshold**  
Shadowseed is aan zet. No human action is required.

**Evidence-backed authority lacks trusted support**  
Assisted mode surfaces a human handoff. Controlled mode remains human-dependent when the user chooses to progress that seed.

**Blocking contradiction**  
Influence is blocked. Authorized human resolution is required unless a future automated resolution policy is separately specified.

**Promoted but irrelevant**  
No action required. The seed remains eligible.

**Relevant but point-of-use denied**  
No influence occurs. Record the reason.

**Revision adds no value**  
Return the draft unchanged.

**Structural config change needs migration**  
Do not partially apply it. Explain whether a rebuild or new session is required.

## Consequences

### Positive

- every SSL concept has one owner;
- the Validation Gate remains the single authority boundary;
- human intervention becomes understandable without raw JSON;
- current/pair/seed/cluster terminology becomes unambiguous;
- God mode becomes more useful rather than less powerful;
- same-turn influence becomes measurable bounded revision rather than seed-dominated regeneration;
- prompt research can proceed without changing authority doctrine;
- research runs become more reproducible.

### Costs

- vNext needs an orchestration presentation layer;
- advanced controls need regrouping and migration semantics;
- current-Gate tests need policy alignment;
- self-reinforcement tests/config need splitting;
- prompt/version metadata must be added;
- old sessions may require compatibility presentation instead of silent reinterpretation.

## Release policy

This alignment targets 0.11.0 Research Preview.

Published 0.10.1 semantics remain reproducible and are not silently replaced.

A 0.10.x patch remains appropriate only for isolated operational fixes that do not change SSL research semantics, such as packaging/launcher corrections or unambiguous presentation defects.

## Acceptance criteria

1. Chat detection can consume current question + current draft as an explicit pair.
2. Source detection remains a separately named source-observation context.
3. Recurrence remains seed/cluster based rather than pair based.
4. Current Gate revalidation and canonical Gate policy cannot disagree under the same policy name.
5. legacy_evidence_required is removed from normal product strictness choices.
6. vNext exposes session- and seed-level human/SSL orchestration state.
7. Assisted review-required seeds are visible in normal vNext UX.
8. Blocking contradictions expose authorized resolution where supported.
9. Same-turn revision and SSL-generated recurrence are independently configurable.
10. Same-turn revision receives the existing draft and may return it unchanged.
11. Recurrence-mode/cluster-threshold changes cannot restore contradictory stale state.
12. Embedding-space changes require new-session, rebuild or re-embedding semantics.
13. Advanced settings are grouped by owning component and statefulness.
14. Prompt IDs, versions and hashes are available for the active live prompt set.
15. Same-turn A/B distinguishes exposure, textual change and human quality judgment.
16. Source ingestion refreshes the same human/SSL handoff model.
17. Turn reports carry a behavior/configuration epoch or digest.
18. Existing Gate, contaminated-observation, point-of-use and production-audit invariants remain covered by regression tests.
