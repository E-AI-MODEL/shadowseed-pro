# W9f blind-review artifact contract

> Status: current
> Date: 2026-06-30
> Evidence layer: W9f cross-turn payoff / blind review
> Current source: yes

## Doel

Dit document legt vast welke artifacts horen bij een `ssl-session` run (W9 én W10-transfer) en hoe ze gebruikt moeten worden. Het is de leesbare begeleider; de **canonieke, machine-gecheckte** contractdefinitie (neutrale prefix `ssl_session_blind_ab`, `source_artifact_sha256`, `answer_key_sha256`, `answer_key_is_canonical`, truncation-flags, gebalanceerde shuffle) leeft sinds de artifact-contract-fix in `scripts/make_blind_ab_review.py` + `tests/test_make_blind_ab_review.py`, met het live voorbeeld in `benchmarks/open_review/rounds/round_024/README.md`.

De artifact-set is bedoeld voor kwaliteitscontrole op door SSL geopende antwoordruimte. Het is geen klassieke model-vs-model benchmark waarin SSL alleen waarde heeft wanneer het elk baselineantwoord verslaat.

## Workflow

Workflow:

```text
.github/workflows/openai-benefit.yml
```

Handmatige inputs (ssl-session):

```text
experiment: ssl-session
model_id: gpt-4.1
recurrence_mode: cluster
max_new_tokens: 1000          # ruim, niet de default 400 (afkap-confound)
input_path: leeg = default fixtureset; W10 = src/shadowseed/data/ssl_session_transfer_suite.json
dedup_threshold: leeg / default
min_occurrences: leeg / default
```

De workflow draait:

```text
python -m shadowseed.cli run-ssl-session \
  --backend openai \
  --model-id <model_id> \
  --max-new-tokens 1000 \
  --embedding-backend openai \
  --recurrence-mode cluster \
  --output results/ssl_session_suite.json
```

Daarna genereert hij het blind-reviewpack (de workflow doet dit automatisch met de neutrale prefix):

```text
python scripts/make_blind_ab_review.py \
  --input results/ssl_session_suite.json \
  --output-dir results/blind_ab_review \
  --seed 45 \
  --prefix ssl_session_blind_ab \
  --title "SSL session blind A/B review"
```

## Artifactnaam

De GitHub Actions artifactnaam volgt:

```text
ssl-openai-ssl-session-<safe_model_id>
```

Voor `gpt-4.1`:

```text
ssl-openai-ssl-session-gpt-4.1
```

## Bestanden

| Pad | Type | Voor wie | Gebruik |
|---|---|---|---|
| `results/ssl_session_suite.json` | raw output | maintainer / analyse | volledige run, conversations, turns, seeds, answers |
| `results/blind_ab_review/ssl_session_blind_ab_review_items.json` | blinded review input | reviewer of script | bevat A/B-antwoorden zonder key |
| `results/blind_ab_review/ssl_session_blind_ab_review_form.md` | menselijk reviewformulier | reviewer | primaire mail-/reviewbijlage |
| `results/blind_ab_review/ssl_session_blind_ab_scoring_template.csv` | scoretemplate | reviewer / spreadsheet | gestructureerd invullen |
| `results/blind_ab_review/ssl_session_blind_ab_answer_key.json` | hidden key | maintainer pas na review | onthult welke kant SSL/baseline was |
| `results/blind_ab_review/ssl_session_blind_ab_summary.json` | summary | maintainer | telt items en A/B-distributie |

## Wat reviewers mogen krijgen

Wel meesturen vóór review:

```text
ssl_session_blind_ab_review_form.md
ssl_session_blind_ab_scoring_template.csv
```

Optioneel voor technische reviewers:

```text
ssl_session_blind_ab_review_items.json
```

Niet meesturen vóór review:

```text
ssl_session_blind_ab_answer_key.json
ssl_session_suite.json
ssl_session_blind_ab_summary.json
```

Reden: deze bestanden kunnen onthullen welke variant SSL was of de reviewer beïnvloeden met runcontext.

## Randomisatie

Het script gebruikt een gebalanceerde shuffle in plaats van losse random bits.

Daarom geldt voor kleine reviewpacks:

- bij even aantal items: SSL staat exact even vaak op A als op B;
- bij oneven aantal items: het verschil tussen A en B is maximaal 1.

Dit voorkomt dat een seed zoals `45` per ongeluk alle SSL-antwoorden aan dezelfde kant zet.

## Interpretatie

Een reviewer kiest A, B of gelijk.

Na unblinding wordt per item bepaald of de keuze SSL of baseline bevoordeelde.

Belangrijk:

- SSL-winst betekent dat de door SSL geopende antwoordruimte nuttig was;
- baseline-winst betekent niet automatisch dat SSL waardeloos was;
- seed-ruis of seed-vernauwing is een foutklasse voor gebruiksdiscipline;
- de review meet kwaliteit van surfaced context, niet het bestaan van de lifecycle.

## Beslisregel na W9f

W9f is niet afhankelijk van een harde regel zoals "SSL moet elk item winnen".

Na de W9f-review is het besluit:

- het W9f cross-turn mechanisme staat op veilige drempels; de payoff-kwaliteit is een baseline-kandidaat (round 022 kwam gespleten terug, twee reviewers oneens op 7/8);
- blind A/B blijft een kwaliteitsinstrument, geen pass/fail-benchmark — maar de reframing verandert de lat, ze verwijdert hem niet;
- de volgende laag is use-time seed-discipline (potentieel-vs-must) plus W10 doctrine-transfer;
- nieuwe reviews moeten vooral seed-effect, ruis/vernauwing en transfer meten, met ≥2 reviewers en de answer key.
