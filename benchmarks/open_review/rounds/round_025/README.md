# Round 025 — W10 transfer, afkap-vrije her-draai (opzet)

> **Status: AFGEROND — de blinde review is binnen en het transfer-verdict is
> voorzichtig positief, met grenzen (zie `human_review/RESULTS.md`): blinde
> consensus (R1+R2) voor SSL op 4/7 — waaronder álle t6-valkuilvragen —,
> consensus-baseline 1/7, 2 gespleten; ruis 0; overeenstemming ~0.71. R3 was
> seed-bewust en telt apart.** Round 024 leverde een onbeslist transfer-verdict op omdat afkap 6/9
> review-items ongeldig maakte (bij `max_new_tokens=1000`); alleen EDU was
> meetbaar (baseline 2 / SSL 1, n=3). Deze ronde herhaalt de transfer-meting
> zonder dat de afkap de meting domineert.

## Wat er verandert t.o.v. round 024

1. **Compactheidsinstructie in de antwoordprompt** (`build_chat_prompt`), in
   **beide armen** zodat het de A/B-vergelijking niet kan biassen: max ~450
   woorden, expliciet afronden met een slotalinea, "midden in een zin stoppen is
   fout". Dit pakt de oorzaak aan (antwoorden gedimensioneerd op het budget)
   i.p.v. alleen het budget te verhogen.
2. **Meta-lek verboden in de weave-prompt**: het antwoord mag nergens
   rechtvaardigen waarom een invalshoek wordt betrokken of weggelaten (round-024
   lek: *"(Deze invalshoek versterkt het antwoord, omdat …)"* kon een item
   de-blinderen).
3. **Ruimer tokenbudget als vangnet**: run met `max_new_tokens: 1600` — de
   compacte instructie hoort het werk te doen; het budget vangt uitschieters.
4. **Quarantaine-regel actief** (uit round 024): key-bewuste diagnostiek wordt
   pas gepubliceerd ná afronding van de scoring, of in een apart
   niet-reviewer-artifact.

## Run-recept

```text
workflow: Research · SSL Benefit (OpenAI)
experiment: ssl-session
model_id: gpt-4.1
recurrence_mode: cluster
input_path: src/shadowseed/data/ssl_session_transfer_suite.json
max_new_tokens: 1600
```

Zelfde transfer-set, zelfde veilige drempels, zelfde use-time discipline
(`surface_top_k=2`, potentieel-niet-must). Het blind A/B-pack
(`ssl_session_blind_ab_*`) wordt automatisch gegenereerd; controleer in de
summary dat `truncation.items_with_likely_truncated_answer` (vrijwel) leeg is
vóór de review start — anders eerst opnieuw draaien.

## Live run (binnen) — 2026-07-02

```text
run_id: 28573062737
branch: main
commit: 8a7230c94e9693c64c389fec05f98ad54045337c   # incl. #161 compacte prompt
artifact: ssl-openai-ssl-session-gpt-4.1 (id 8031850899)
artifact_digest: sha256:c6867a23a056b2bba7b07a51e74141ecdfb212abe67bee67ea9496dd15da4e68
```

Verificatie van de round-025 fixes (log-analyse van alle antwoorden):

- **Afkap: 0 van 14 antwoorden** — elk antwoord eindigt op een volwaardige
  slotzin/slotalinea (round 024: 7/18 afgekapt). Het done-criterium "≤1
  afkap-item" is ruim gehaald; de compactheidsinstructie werkt.
- **Meta-lek: 0 treffers** op de verboden zelfrechtvaardiging ("versterkt het
  antwoord") in de hele log.
- Runcijfers: 3 conversaties, **7 cross-turn events** (EDU t4–t6; HEALTH t5–t6;
  POLICY t5–t6 — twee t4-events uit round 024 vuurden dit keer niet:
  run-to-run-variantie van de LLM-detector), 7 promoties,
  `max_occurrence_count` 28; pack is compact (62 KB vs 119 KB in round 024).

Key-bewuste per-item diagnostiek is conform de quarantaine-regel (round 024)
**niet** opgenomen; die volgt pas na afronding van de blinde scoring.

**Dit pack is review-klaar.** Reviewers: gebruik
`ssl_session_blind_ab_review_form.md` + `ssl_session_blind_ab_scoring_template.csv`
uit het artifact; answer key pas ná scoren openen.

## Klaar wanneer

- een run waarvan ≤1 review-item afkap-gemarkeerd is;
- verse blinde review (≥2 reviewers, per domein, met seed-effect en
  ruis/vernauwing-labels), unblinding via de canonieke answer key;
- per-domein rapportage (EDU / HEALTH / POLICY), geen totaalscore.

Pas dán is een per-domein transfer-uitspraak mogelijk. Round-024-uitkomst blijft
staan als context: mechanisme vuurt in alle drie domeinen, weave coherent en
ruisvrij; kwaliteitsverdict nog open.
