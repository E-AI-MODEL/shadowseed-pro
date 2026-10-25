# Gewichtloze seed over meerdere beurten: read-only checkpoints

> 25 oktober 2026. Alleen mechanische onderzoekscontrole met de **bestaande** `ShadowseedEngine`. Geen modelaanroepen, nieuwe productpipeline, semantische groeiclassifier of nieuw modelprompt. **G0 NOT PASSED, Q1/Q2 niet gemeten.**

## Aanleiding

Na gemergede PRs [#246](https://github.com/E-AI-MODEL/shadowseed-pro/pull/246), [#248](https://github.com/E-AI-MODEL/shadowseed-pro/pull/248) en [#247](https://github.com/E-AI-MODEL/shadowseed-pro/pull/247) is een echte eerste seedgeboorte mechanisch traceerbaar van precies één ruwe detectorwaarneming via intake naar een `created`-event. De `freeze_canonical_weightless_birth` bevriest dat bewijs alleen direct na de eerste beurt. Later ontstaat een ander bewijsprobleem: de actuele eindtoestand toont niet wat de seed na **elke** tussenliggende beurt deed.

## Kleine aanvulling, geen productwijziging

`research/src/shadowseed_research/benchmark/weightless_longitudinal_handoff.py` biedt `freeze_weightless_followup(engine, birth, previous=None)`. De caller bewaart de oorspronkelijke birth-snapshot en maakt direct na **iedere afzonderlijke, afgeronde** `prepare_turn / observe_turn` een nieuw checkpoint. Er wordt niets opnieuw berekend over een overgeslagen tussenbeurt.

Elke checkpoint bevat alleen hashes/IDs, de bestaande toestand van precies dezelfde seed en feitelijke auditinformatie:
- immutabele koppeling aan het oorspronkelijke raw detector-item, normalisatie, observatie-ID en `created`-event;
- opeenvolgende turnindex en report-hash plus de hash van de volledige tot dan opgeslagen productgeschiedenis;
- keten van vorige checkpoint, eventlogprefix en Gate-ledgerprefix;
- trace, status, dormant-aantal, occurrence_count, en afzonderlijke herkenning van **echte herdetectie** en **TrTL-heractivering**;
- gewicht, evidence en authority_version blijven 0; bestaande `blocked` of `no_change` Gate-events worden **wel** als werkelijke weigering gerapporteerd;
- geen toegestane seedcontext of same-turn wijziging van het gewone antwoord gedurende het onderzoek.

Deze schaduwhistorie is niet hetzelfde als inhoudelijke groei. Herhaling, `DORMANT`, `NEW`, een geblokkeerde Gate-aanvraag of een opnieuw aangeraakte seed is geen bewijs van een later bedachte nieuwe vraag.

## Expliciete grenzen

1. De tests gebruiken onderzoeker-geschreven hostantwoorden en detectoruitvoer, niet een echt LLM. Hashes bevestigen alleen consistentie van **aangeleverde records**. Wie het hostantwoord werkelijk schreef, blijft extern te bewijzen.
2. Alleen-lezen registratie kan geen semantisch oordeel leveren, ook niet over het ontstaan van een nieuwe mogelijkheid.
3. Ontbrekende of gewijzigde lineage, een overgeslagen checkpoint, achteraf aangepaste bron-/eventhistorie of positieve autoriteit wordt geweigerd. Een hashketen in dezelfde onbeschermde opslag is niet bestand tegen een aanvaller die alle records kan herschrijven; onafhankelijke opslag of handtekening is een **aparte** onderzoeksvoorziening.
4. Het gate/SSOT-probleem uit [issue #241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241) blijft onafhankelijk en wordt door deze registratie **niet** gerepareerd. Draft PRs #243/#244 moeten hun eigen review doorlopen.
5. De chronologie van productrecords bewijst nog niet dat **de kandidaat zelf** een eigen, later voorgestelde vraag veroorzaakte. Daarvoor is de vooraf goedgekeurde, geblindeerde Q1/Q2-proef nodig, inclusief gelijkwaardige baselines, echte sterke modellen, RF/RI-scheiding en onafhankelijke semantische toets.

## Uitvoerbaar controlepunt

`research/tests/test_weightless_longitudinal_handoff.py` gebruikt een echte blijvende Engine en test opeenvolgende beurten tegenover een NONE-controlearme, legitieme herdetectie, Gate-weigering zonder gewichtsverandering, echt dormant worden en TrTL-reactivatie, ontbrekende turn, openstaande turn en vervalste records, historie en autoriteit. **Testcode is geen testresultaat**: tel alleen groen op een concrete GitHub-run als uitgevoerd.

**Stopgrens:** geen automatische modelcalls, geen levende Q1/Q2-proef, geen tweede Gate en geen wijziging van TTL, TrTL, weight, seedidentiteit of normale antwoordprompt. G0 blijft NOT PASSED.
