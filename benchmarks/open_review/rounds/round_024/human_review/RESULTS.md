# Round 024 — blinde review van het canonieke W10 transfer-pack

> **Status: review afgerond en geünblind. Uitkomst op de geldige items:
> baseline 2 / SSL 1 — maar n=3, want 6 van 9 items zijn uitgesloten door
> afkap. Het transfer-kwaliteitsverdict is daarmee ONBESLIST; de afkap
> domineert de meting.** Reviewdata: maintainer-aangeleverde scoring van het
> canonieke pack (run 28519306334, artifact 8010902341).

## Het ruwe reviewresultaat (blind, vóór unblinding)

| Item | Winnaar | Geldig voor win-rate |
|---|:--:|:--:|
| CONV_EDU-t04-01 | B | ja |
| CONV_EDU-t05-02 | B | ja |
| CONV_EDU-t06-03 | B | ja |
| CONV_HEALTH-t04-04 | — | nee (afkap) |
| CONV_HEALTH-t05-05 | — | nee (afkap) |
| CONV_HEALTH-t06-06 | — | nee (afkap) |
| CONV_POLICY-t04-07 | Gelijk | nee (beide kanten afgekapt) |
| CONV_POLICY-t05-08 | — | nee (afkap) |
| CONV_POLICY-t06-09 | — | nee (afkap) |

De reviewers begonnen vóór de afkap-waarschuwing in het round-README, maar
sloten afgekapte items **zelfstandig** uit (`exclude_from_winrate = TRUE`) —
het protocol werkte dus op eigen kracht.

**Onafhankelijke kruisvalidatie:** de 6 uitgesloten items zijn exact de 6
items waarvoor de agent-lezing van de joblog afkap vond (HEALTH t4/t5/t6,
POLICY t4/t5/t6; EDU t4–t6 volledig schoon), en het enige item dat de
reviewers als "beide kanten afgekapt" markeerden (POLICY-t04-07) is exact het
enige item waar de log-analyse beide kanten afgekapt vond. Twee onafhankelijke
metingen, één-op-één gelijk.

## Unblinding

De answer key is deterministisch reproduceerbaar uit
`scripts/make_blind_ab_review.py` (`_balanced_ssl_a_assignments`, seed 45,
9 items in suite-volgorde). Gereproduceerde toewijzing:

| Item | A | B |
|---|---|---|
| CONV_EDU-t04-01 | ssl | baseline |
| CONV_EDU-t05-02 | ssl | baseline |
| CONV_EDU-t06-03 | baseline | ssl |
| CONV_HEALTH-t04-04 | ssl | baseline |
| CONV_HEALTH-t05-05 | baseline | ssl |
| CONV_HEALTH-t06-06 | ssl | baseline |
| CONV_POLICY-t04-07 | ssl | baseline |
| CONV_POLICY-t05-08 | baseline | ssl |
| CONV_POLICY-t06-09 | baseline | ssl |

Verificatie van de reproductie: (a) de itemvolgorde/ids matchen het pack
(`CONV_POLICY-t04-07` = global index 7); (b) key + afkapanalyse voorspellen
per item welke kant afgekapt is, en dat klopt met de reviewer-notities
(o.a. t04-07 beide kanten). De reproductie is dus betrouwbaar; de canonieke
`ssl_session_blind_ab_answer_key.json` in het artifact blijft de formele bron.

## Geünblinde uitkomst (geldige items, n=3)

| Item | Winnaar (blind) | = | Agent-lezing vooraf |
|---|:--:|---|---|
| CONV_EDU-t04-01 | B | **baseline** | "echte aanscherping, maar laat extern-partnerspunt vallen" (close) |
| CONV_EDU-t05-02 | B | **baseline** | "ruwweg gelijkwaardig" |
| CONV_EDU-t06-03 | B | **ssl** | "SSL voegt twee onderscheidende faalwijzen toe" (sterkste EDU-item) |

**Baseline 2 / SSL 1.** Let op: "B won 3×" betekent dus níét "SSL won 3×" —
de gebalanceerde shuffle legt SSL afwisselend op A en B (5/4 over 9 items).
Elke lezing van B als één vaste kant is een unblinding-fout.

De richting is consistent met de niet-blinde agent-lezing: de reviewer koos
baseline op de twee items die de agent als close/licht-vernauwend las, en SSL
op het item waar de seed onderscheidende inhoud toevoegde.

## Conclusie

1. **Kwaliteitsverdict transfer: onbeslist.** n=3 geldige items (alleen EDU;
   HEALTH en POLICY volledig weggevallen — juist het domein met de sterkste
   weave, POLICY, is niet gemeten). Baseline 2 / SSL 1 op n=3 draagt geen
   uitspraak.
2. **De afkap domineert de meting.** 6/9 items ongeldig bij
   `max_new_tokens=1000`. De volgende run moet dit oplossen — ruimer budget
   (~1500+) en/of een prompt die om compacte, afgeronde antwoorden vraagt —
   anders blijft elke win-rate onmeetbaar.
3. **Wat wél staat:** het protocol werkt (reviewers filterden afkap
   zelfstandig; exclusies matchen de log-analyse 1:1), het mechanisme vuurt in
   alle drie de nieuwe domeinen, de weave is coherent en ruisvrij (geen
   round-022-patroon), en de reviewer-uitkomst spoort met de vooraf vastgelegde
   agent-lezing.

## Grenzen

- Aantal onafhankelijke reviewers in deze scoring: door de maintainer
  aangeleverd als één ingevulde scoring-set; ≥2 reviewers blijft de lat.
- De agent-lezing was niet blind (kende de key) — secundair bewijs.
- Eén model, auteur-gekozen thema's; n=3 geldig. Signaal, geen verdict.

## Volgende stap

Her-draai de transfer-set met een afkap-vrije configuratie (ruimer
`max_new_tokens`, en overweeg een expliciete compactheidsinstructie in de
antwoordprompt), genereer een vers canoniek pack en review dat — pas dan is een
per-domein transfer-uitspraak mogelijk.
