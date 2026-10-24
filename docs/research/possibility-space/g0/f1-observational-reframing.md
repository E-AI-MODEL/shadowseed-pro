# G0 / F1 — an underdetermined observation can open a different question

> **Status:** author-designed **construct probe**, not an independently approved research case.
> **Mechanism being challenged:** changing the *investigable question* with the **same underlying variable and relation vocabulary**; no new relation-kind requirement.
> **DO NOT** use this whole file as a model input. Only [model-facing-f1.md](model-facing-f1.md) can be considered as a T0 input, after review. The privately intended mechanisms, formulas and validation options below are assessor material.

## Why this is not a missing-graph-link task

A model sees a command stream and an archived response stream. The immediate temptation is to ask "what lag links command to archive?" That task is **solvable inside the supplied data** and must **not** earn Q2 credit. The actual barrier is different: even an indefinitely long record of these two channels **cannot identify whether the delay is in the process or the logger** under the two synthetic explanations specified below.

The hypothesized possibility-formation step is to **change the question** from *what lag fits the archive?* to *which intervention/observation can distinguish causal mechanism from measurement artifact?* This uses the same kinds of variables (command, physical state, archived observation) and ordinary relation language. The aim is not a new predicate or a new number of edges.

**Important skeptic's objection:** proposing an additional independent sensor is a conventional experimental-design move and could be entirely available to a strong model without Shadowseed. That is an admissible outcome; if reviewers find that this case has no nontrivial possibility-making phenomenon beyond routine troubleshooting, **fail this F1 case at G0** and replace it. Do not lower the bar because the arithmetic works.

## Formal object (assessor reference)

Time is discrete, binary command is `u[t]`, *physical plant state* is `x[t]`, and archived observation is `r[t]`. A process is initialized with `u[t]=0` for negative times. The archive has **no synchronized physical-state observation**.

Two counterfactual worlds produce the **same archive for every admissible command sequence**:

| | P: process is delayed, logger instantaneous | L: process instantaneous, logger delayed |
|---|---|---|
| Physical state | `x[t] = u[t-2]` | `x[t] = u[t]` |
| Archived channel | `r[t] = x[t]` | `r[t] = x[t-2]` |
| Observable pair | `(u[t], r[t]=u[t-2])` | `(u[t], r[t]=u[t-2])` |

**Observational equivalence proof:** substitute the definition of `x` into `r`. In both P and L, `r[t]=u[t-2]` for every `t`. Thus more `(u,r)` archives cannot separate the worlds, even with zero noise.

An **independently synchronized meter** of the physical state, `z[t]=x[t]`, would disagree whenever `u[t] != u[t-2]`: in P `z=u[t-2]`, in L `z=u[t]`. This is an *instrumental opportunity to discriminate*, not a magical creation of an existing instrument by the model.

## Initial T0 trace

Illustrative command and archive streams (index `t=0..11`, prehistory 0):

| t | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| u | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| r | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 |

These trace numbers may be supplied at T0, but **the two hidden-generative-mechanism equations and delayed/meter witness values must not be shown**.

## Candidate, causal alternative and negative cases

- **Investigable candidate (not a fact):** The record is consistent with more than one causal location for the observed delay. A useful next investigation would seek a genuinely **independent** synchronized measurement of physical state at a time when competing hypotheses predict different values.
- **Strong alternative explanation H0:** A capable ordinary model may propose this instantly with no shadow, no persistence and no new conceptual construction. Count this as a successful *control*, not a failure of the benchmark.
- **Negative candidate N1 — mere extra archive:** "Record another 100 command/archive pairs"; both P and L still fit identically, therefore zero discrimination despite more data.
- **Negative candidate N2 — duplicated delayed display:** Attach a meter downstream of the same logger/archive transformation and call it "independent"; `z[t]=r[t]` in both worlds, therefore no discrimination.
- **Negative candidate N3 — an uninformative time point:** Observe a real synchronized `x` only at a time when `u[t]=u[t-2]`; both worlds predict the same result, so the proposed sample alone has no discriminating power.
- **Negative candidate N4 — causal overclaim:** "The process definitely has two steps of delay" solely from `(u,r)`. Wrong inference: `L` is observationally equivalent.
- **Negative candidate N5 — direct meter unavailable:** If the environment cannot provide an independent physical measure or any other discriminating intervention, the proposed downstream possibility remains **conditional**, not verified or achieved. Do not score it as an executed investigation.

## Prespecified downstream opportunity (withheld from model at T0)

A selected informative input sequence at T1 lets a researcher measure `x[t]` and ask a **newly answerable question**: *is the apparent two-step delay in the physical process or the logging channel?* Require the model to specify what the two explanations predict and how its proposed measurement could distinguish them **before the outcome is revealed**.

**Precommitment requirement:** Freeze each model arm's candidate and intended diagnostic before revealing (a) any direct-meter result and (b) the assessor's mechanism equations. If no candidate was proposed, log no-candidate rather than substituting the known correct candidate from the key.

**Counterfactual ablation:** Remove the precise earlier "two potential locations" candidate; replace it with an equally long unrelated one (e.g., "the display may be aesthetically misleading"); and permit an ordinary no-shadow model an equivalent opportunity to design a test from the same T0/T1 data. If the new discriminating test is equally generated and used without the candidate, **candidate-specific mechanism value has not been shown**.

## T3: second-generation inquiry, beyond the immediate diagnosis

**Risk under examination:** Merely naming P or L after a new measurement is a **first-order diagnostic gain**. It does not yet demonstrate that the first candidate changed the *future space* of investigations.

After the T1 direct measurement and T2 diagnosis, freeze a *new, still-hidden prospective command profile* and ask for a **causally specific next experiment**:

- **If P (actual process delay):** Test whether anticipatory command scheduling can make a **known** future target coincide with the physical plant state. Predict why this requires advance knowledge, and why merely relabeling archived timestamps cannot remove a genuine physical delay.
- **If L (recording delay):** Test whether timestamp correction makes archived `r` contemporaneous with a trusted physical-state meter, while keeping live physical commands unaltered. Predict why anticipatory commands would create a physical mismatch here.
- **Wrong intervention controls:** Claim that retimestamping fixes P's physical lag, or advance commands in L as if its physical plant were delayed. Independently reject them on a fresh sequence.

This T3 layer is a **candidate downstream investigation**, not automatically a "new possibility" finding. It earns no Q2 credit merely because the author provided future intervention categories. The model must specify a distinct causal prediction *before* seeing the held-out outcome; an independent checker tests that prediction. If strong-model ordinary deliberation can formulate the same progression with equal resources, attribute no special value to SSL.

**T3 stop rule:** If T2 diagnosis followed by the two obvious textbook repairs is all this case offers, or the supposed new inquiry follows immediately from supplied sensor information with no enabling candidate effect, independent reviewers may reject F1 as too shallow to represent possibility-space change.

## Independent technical judgment (not a human novelty verdict)

A test is *discriminating* only if it names a **non-derived** measurement/intervention and contains at least one predeclared observation for which P and L make different predictions. A full audit records:
- whether the model only identified the visible two-step archive lag (no Q2);
- whether the proposed test is independent rather than a copy of `r`;
- whether the selected sampling instants separate the counterfactuals;
- whether a purported final explanation is based on newly obtained data rather than inferred from `r`;
- whether a new question is meaningfully formulated and can be addressed by an action available under the declared environment.

The assessor can check this against the [key and holdouts](assessor-key-and-holdouts.md). A second **independent semantic reviewer** must determine whether these checks constitute *new meaningful investigability* or merely standard experimental planning. The author's model cannot decide that.

## Threat to construct validity: we designed the new instrument

A researcher who predefines two observationally equivalent worlds and an independent meter has constructed the potential for discrimination. A model that asks for that instrument **does not create the physical affordance**. This case can at most evaluate whether an unselected, remembered *interpretive doubt* causes a later test to be proposed under controlled access. **Reject claims about ontologically new facts, novel science, changed model weights or genuinely new mathematical support.**

**Exit:** F1 cannot pass G0 on equations alone; requires independent reviewers to accept meaningful nontrivial downstream research change, and to specify what a powerful ordinary model plus search would not already trivially accomplish.
