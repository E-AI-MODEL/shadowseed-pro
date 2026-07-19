# PvA — open taken richting einddoel

> **Levend document.** Doel: de openstaande stappen richting het einddoel —
> *SSL gevalideerd als scenario-onafhankelijk mechanisme* (hoofdclaim op
> gescheiden evidence-lagen A–G, `docs/00_shadow_seed_learning_4_6.md`) — in
> beeld houden en afvinken terwijl we ze doen.
>
> Bijwerken: vink `[x]` af wanneer "klaar wanneer" is gehaald, met de PR/round
> erbij. Voeg nieuwe taken toe onder de juiste sectie. Geen totaalscore —
> houd de laag-status eerlijk gescheiden.
>
> Status-legenda: `[ ]` open · `[~]` bezig · `[x]` klaar · `[!]` geblokkeerd/keuze nodig
>
> Baseline bij start (2026-06-20): stappen ~55% · repo-kwaliteit ~82% ·
> output-kwaliteit ~58% (detectie zwak / payoff sterk).

---

## P0 — Hoogste hefboom: de wild-detectie → payoff-lus sluiten

*Raakt Laag C + E + output-kwaliteit tegelijk. Tot nu zijn payoff-seeds
auteur-ontworpen; dit koppelt "vinden" aan "gebruiken".*

- [x] **W1. Open-set seeds als payoff-input.** Echte open-set-gedetecteerde seeds
  (round 006 batch1, AI-accepted, κ 0.63) door de payoff-pijplijn op gpt-4.1
  (round 015). **Resultaat: grotendeels negatief/directioneel** — een sterk model
  vindt zélf ~82% van de gedetecteerde gaps (echt nieuw: ~2/29 niche). De
  wild-loop loont dus níét op korte, makkelijke teksten. Zie `round_015/`.
- [~] **W3. Eerlijke koppeling detectie↔payoff vastgelegd** (round 015):
  detectie-kwaliteit op makkelijke teksten → lage payoff omdat het model de
  triviale gaps zelf al ziet. Vervolg hieronder (W4–W6).
- [ ] **W4. Harde/dichte teksten**: draai de wild-payoff op de round-007
  wetenschap-batch / lange of technische teksten, waar het model de gap *niet*
  spontaan ziet. *Klaar wanneer:* baseline-coverage van gedetecteerde gaps
  duidelijk < dan op nieuws (detector voegt aantoonbaar toe).
- [x] **W5. Generatieve "kunnen staan"-frames door payoff** (gap 1, v0.4-gen):
  uitgevoerd (round 016). **Convergent negatief**: gpt-4.1 dekt zelf ~88% van de
  generatieve frames (novel 3/24). Kanttekening: baseline was *geprimed* op
  "verklarende invalshoeken" → confound, zie W7. Zie `round_016/`.
- [!] **W7. (gedegradeerd) naïeve single-shot baseline.** Nuttige sanity-check,
  maar niet meer de decider — scope-correctie hieronder: single-shot mist het
  SSL-mechanisme.
- [~] **W9. DE ECHTE DECIDER — cross-turn payoff (gap 5), via de ECHTE pijplijn.**
  Harness gebouwd: `ssl_session_suite.py` draait een multi-turn gesprek door de
  echte `SSLManager` (weight-0 ingest, recurrence-dedup, Validation Gate over
  beurten, TTL-decay, TrTL-reactivatie, constellations); alleen een
  pijplijn-PROMOTED seed geboren in een eerdere beurt mag een later antwoord
  sturen. Pipeline-getrouwe test bewijst het pad (recurrence→Gate→promote→
  cross-turn surface). **Vervangt de losstaande W1/W5/W14-afgeleiden** (die de
  manager NIET gebruikten — nu gemarkeerd als NIET-PIJPLIJN). Eerste gpt-4.1-run
  (round 017): pijplijn liep schoon, **0 cross-turn events** — diagnose:
  max_occurrence=2 < Gate-drempel 3, dus 0 promoties (gesprekken te kort/wisselend
  voor recurrence). Geen bug; mechanisme kreeg geen kans. Zie `round_017/`.
- [x] **W9b. Recurrence een eerlijke kans geven (langere gesprekken).** Gedaan
  (round 018): 3 gesprekken, 22 beurten, **110 gaps** — maar `max_occurrence` nog
  steeds **2**, 0 promoties. Bottleneck precies gelokaliseerd: **dedup (0.85) merge
  paraphrastische LLM-gaps niet**, dus recurrence accumuleert nooit. Niet "te
  kort"; het is de dedup/recurrence-parametrisering. Zie `round_018/`.
- [x] **W9c. Bottleneck deblokkeren — GELUKT, eerste positief (round 019).** Met
  dedup 0.6 + min_occ 2: max_occurrence 2→**10**, **11 promoties**, **10 cross-turn
  events**. Gelezen (CONV_CITY t5–t8): vroeg-gezaaide frames (historische
  gelaagdheid, informele netwerken, klimaatadaptatie) reizen mee en maken latere
  antwoorden rijker/onderscheidender → eerste positieve signaal voor SSL's eigen
  mechanisme (gap 5). Grenzen: nodig had het **onder-doctrine drempels** (default
  0.85/3 vuurt niet, round 018), SSL-antwoorden zijn langer (confound), AI-
  geoordeeld, n=10, auteur-gekozen terugkerende thema's. Signaal, geen validatie.
  Zie `round_019/`.
- [x] **W9d. Blinde human-review** van de 10 cross-turn paren — GEDAAN
  (`round_019/human_review/RESULTS.md`): **2 onafhankelijke reviewers, 92% en 98%
  eens met de AI** (AI-lean 8 ssl / 2 tie). Verankert R019 menselijk: cross-turn
  SSL-antwoorden worden door onafhankelijke mensen rijker bevonden; geen
  AI-bias/lengte-artefact (reviewers expliciet verteld dat substantiële lengte
  mag). AI-jury nu tweemaal gevalideerd (ook round 013). Grenzen onveranderd
  (onder-doctrine drempels, n=10, gekozen thema's).
- [x] **Per-topic instelbare drempels** (maintainer-eis): hoeveel tegengehouden
  vs doorgelaten verschilt per onderwerp → `ssl_session_suite` accepteert nu
  per-conversatie overrides van `dedup_threshold`/`min_occurrences`/
  `promotion_threshold` (winnen over run-level; globale doctrine-defaults intact).
  Vastgelegd als ontwerpprincipe; W9e maakt dit adaptief.
- [x] **W9e. Recurrence-model gefixt — WERKT op veilige drempels (round 020).**
  Cluster-based recurrence: identiteit/opslag blijft strikt (0.85 dedup), maar
  recurrence wordt semantisch geteld (cluster). Op **veilige defaults** (dedup
  0.85, Gate-bar 3) vuurt nu max_occurrence **29**, **49 promoties**, **10
  cross-turn events** — vs R018 (zelfde veilige drempels, pairwise) = 0. Verzoent
  round-014-veiligheid met round-019-payoff. Restpunten: cluster promoot nu álle
  leden (49) i.p.v. een representant (verfijnen); kwaliteit op deze run nog niet
  apart human-gereviewd (rust op R019 92/98%). Zie `round_020/`.
- [~] **W9f. Cluster-representant** promoten i.p.v. alle leden (49→clusteraantal),
  daarna her-draaien + verse human-review op veilige drempels. **Code geland**
  (round 021): cluster-recurrence crediteert nu alleen de vroegst-geboren
  representant per cluster; identiteit (0.85 dedup) en Gate-bar (3) onveranderd;
  cross-turn surfacing is relevance-gated dus events blijven. Deterministische
  test bewijst: 6 parafrasen blijven distinct, recurrence haalt de veilige bar,
  maar exact 1 promoot. *Klaar wanneer:* live her-draai op gpt-4.1 + verse blinde
  human-review op veilige drempels (pending, secrets-gated). Zie `round_021/`.
- [~] **W9c (oud). Bottleneck deblokkeren (per-run knob, defaults intact).** Expose
  `dedup_threshold`/`min_occurrences` als run-parameter; her-draai met lossere
  dedup (~0.6) zodat paraphrastische recurrence kan mergen — puur om te testen:
  *als promotie WEL kan vuren, surfacet een cross-turn schaduw dan waarde?*
  *Klaar wanneer:* ≥1 promotie + cross-turn event, of een schoon negatief mét
  werkende machinerie. Doctrine-defaults blijven ongewijzigd (round-014-veiligheid
  blijft staan).
- [!] **Doctrine-keuze (alleen als W9b ook leeg blijft):** promotie-drempel
  verlagen botst met de Gate-strengte die round 014 valideerde; alleen met
  TTL/EXPIRED als vangnet en als expliciete doctrine-wijziging. Multi-turn gesprek
  waarin een weight-0 seed die vroeg gedetecteerd is meereist (TTL/TrTL) en pas
  later, als de context verschuift, alsnog in het antwoord kan landen. Baseline =
  normale chatbot met dezelfde gespreksgeschiedenis maar zónder shadow-memory.
  *Klaar wanneer:* gemeten is of de meegereisde seed in een latere beurt waarde
  toevoegt die het model niet zelf uit de historie afleidt. Mag falen (sterk
  model leidt zelf af); per het residu-argument telt zelfs een kleine
  betrouwbare winst. **Scope-correctie (2026-06-21):** W1/W5 maten single-shot;
  SSL's eigenlijke claim is dit cross-turn-mechanisme + dat het 3–10%-residu dat
  zelfs een frontier-model mist betrouwbaar/persistent/gratis wordt gevangen — een
  grote LLM-stap, geen marginale. Zie `round_016/`.
- [ ] **W6. Blinde human-review** alleen op een variant die toegevoegde waarde
  laat zien (W4/W7), niet op de redundante sets. *Klaar wanneer:* win-rate + κ.
- [ ] **W8. Andere claim-richtingen** indien W7 ook negatief: (a) zwakker model
  dat SSL-lift krijgt, (b) cross-turn accumulatie (gap 5), (c) Niveau 2. Elk is
  een *andere* claim dan "externe detector verslaat frontier-model".

## P1 — Laag C: open-set seedkwaliteit naar criterium (≥ 0.60)

*De make-or-break detectie-claim; plateaut nu op "relevant maar triviaal".*

- [ ] **C1. Substantie-probleem aanpakken**: de generatieve "kunnen staan"-variant
  (gap 1, v0.4-gen) echt A/B draaien vs de absence-detector op verse items.
  *Klaar wanneer:* round 009 uitgevoerd (niet alleen gepland) met acceptance per
  variant.
- [ ] **C2. Tweede onafhankelijke human-reviewer** op een verse batch.
  *Klaar wanneer:* κ op n≥50 met ≥2 reviewers, los van AI-review.
- [ ] **C3. Acceptance ≥ 0.60 op een verse, geblindeerde batch** of een eerlijke
  conclusie waaróm dat (nog) niet haalbaar is. *Klaar wanneer:* criterium gehaald
  óf gefundeerd afgeschreven.

## P1 — Laag F: domeintransfer

- [ ] **F1. Minder afhankelijkheid van domein-priors**: de model-benefit-detectie
  draait nu op `DOMAIN_PRIORS`. Test op domeinen zónder priors. *Klaar wanneer:*
  een transfer-run op holdout-domeinen met eerlijke uitkomst.
- [ ] **F2. Driver van de out-of-sample-daling** (round 007, |r|<0.25 voor
  dichtheid) verder onderzoeken of expliciet open laten. *Klaar wanneer:*
  kandidaat-verklaring getoetst of gemarkeerd als onbeslist.

## P2 — Laag E: probe utility verdiepen

- [ ] **E1. Behavioral metric "betere vervolgvraag/retrieval-query"** verder dan
  smoke. *Klaar wanneer:* een meetbare vergelijking promoted-vs-niet op
  probe-kwaliteit.

## P2 — Repo-kwaliteit (warts opruimen)

- [ ] **Q1. Semantische coverage overal** waar nu nog lexicale `coverage()` de
  primaire maat is (niet alleen model-benefit). *Klaar wanneer:* lexicaal is
  gedegradeerd tot secundaire/echo-indicator.
- [ ] **Q2. Falsehood-flag met negatie-detectie** (round 014 gaf 2/3
  vals-positief). *Klaar wanneer:* de flag een correctie niet meer als bewering
  telt.
- [ ] **Q3. Doc-code-drift sweep**: controleer dat docs/00, manager-design en de
  wiki de huidige lifecycle (TTL/TrTL/EXPIRED) consistent beschrijven.
- [ ] **Q4. Coverage-metric blind spot in de suite-interpretatie** documenteren
  waar resultaten nog de oude lexicale +0.35 noemen.

## P3 — Visie-gaten (gap 4 & 5) en Laag G

- [x] **V1. Gap 5 — levende cross-turn shadow-laag**: de seed die echt meereist
  over beurten (nu lifecycle-mechaniek aanwezig, maar geen multi-turn demo).
  *Klaar wanneer:* een demo waarin een seed over meerdere beurten leeft, decayt
  of via TrTL herleeft in een echt gesprek. *Gedaan (2026-07-02):*
  `shadowseed chat` (PR #164) — applicatiedemo, geen bewijslaag; plus de
  SSL→RAG-brug live via `--probe-corpus` (PR #166).
- [x] **V2. Gap 4 / Laag G — modelinterne (H-neuron) verkenning**: blijft
  research; alleen oppakken als P0–P2 staan. *Klaar wanneer:* een scoping-notitie
  of eerste sonde. *Gedaan (2026-07-02):* scoping-notitie
  (`docs/research/laag-g-scoping.md`) én eerste sonde
  (`run-dialectic-falsification`, spoor 1: WEERLEGD → Gate-contradictie,
  HOUDT_STAND → bounded feedback, promoveert nooit). Spoor 2
  (activatie-sonde op een klein HF-model) is de vervolgstap.

## Doorlopend

- [ ] **D1. Round-notes + status-doc** bijwerken bij elke afgeronde taak.
- [ ] **D2. Deze PvA bijhouden** (afvinken, nieuwe taken toevoegen).

---

## Changelog

- 2026-06-20 — PvA aangemaakt na merge van PR #142 (rounds 010–014 + lifecycle
  TTL/TrTL). Eerstvolgende focus: P0 (wild-lus).
- 2026-06-21 — W1 gedaan (round 015): wild-loop op nieuws is grotendeels redundant
  (model vindt ~82% zelf). W-taken bijgesteld naar harde teksten (W4) +
  generatieve frames (W5), human-review (W6) pas op de winnende variant.
- 2026-06-29 — W9f code geland (round 021): cluster-recurrence promoot nu één
  representant per cluster i.p.v. alle leden; deterministische test + volledige
  suite groen. Live her-draai + verse human-review op veilige drempels is de
  pending vervolgstap.
- 2026-07-02 — Pivot van bewijsrondes naar bouwen: `shadowseed chat` (V1, PR
  #164), SSL→RAG-brug live (PR #166), positioneringsbesluit doorgevoerd (issue
  #46, PR #165/#167) en Laag G geopend met scoping-notitie + dialectische
  falsificatie-sonde (V2). Round-025 blinde review blijft de pending
  bewijsstap.
- 2026-07-02 (avond) — W10 doctrine-transfer AFGEROND met een eerste
  voorzichtig positief blind verdict (round 025, 2 protocol-conforme blinde
  reviewers): consensus-SSL 4/7, waaronder álle t6-valkuilvragen (blind 6/6
  stemmen); consensus-baseline 1/7; 2 gespleten; ruis 0; overeenstemming
  ~0.71. R3 was seed-bewust en telt apart (convergent, 7/7). Grenzen: n=7,
  één model. Het round-023-patroon (sturen bij aanscherping) repliceert
  cross-domein.
- 2026-07-04 — Laag G eerste iteratie doorlopen (rounds 026–028): dialectische
  falsificatie (spoor 1) + activatie-sonde met token-scoped pooling en
  permutatie-controle (spoor 2). Met **fixture-labels** gemeten op
  distilgpt2/pythia-14m/-31m (rounds 026–027); met **gpt-4.1 als echte
  oordeelbron** op distilgpt2 + de pythia-14m-reproductie (round 028;
  pythia-31m draaide níet met gpt-4.1-labels). Schoon nulresultaat — geen
  interne steun aangetoond op kleine Engelse modellen (het correcte antwoord);
  een positieve uitspraak vraagt een NL-capabel/groter model. Coherentie-pass:
  README,
  current-status, evaluation-matrix, laag-g-scoping en visiedoc gelijkgetrokken
  met deze stand. Volgende bewijsstap indien gewenst: W10-replicatie op een
  tweede model (round 025 was voorzichtig positief, n=7).
