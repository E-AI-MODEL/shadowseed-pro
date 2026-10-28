# Shadowseed: de schaduw die meereist | The shadow that travels

**Onderzoeksarchief 27 oktober 2026 · Research archive, 27 October 2026**  
[Nederlands](#nederlands) · [English](#english) · [Bronbestanden en herkomst](#bronbestanden-en-herkomst--source-files-and-provenance)

## Nederlands

### Wat had hier kunnen staan?

Een taalmodel geeft een antwoord. Vaak een goed antwoord, soms een onverwacht goed antwoord. Maar het antwoord dat we lezen, is een keuze uit vele mogelijke vervolgen. Wat geen plaats krijgt in die keuze, verdwijnt meestal uit beeld.

Daar begon Shadow Seed Learning. In de eerste versies onderzochten we vooral wat in een antwoord leek te ontbreken: een voorwaarde, een verband, een andere verklaring. Dat leverde bruikbare kandidaten op. Toch bleef iets wringen. Als je alleen zoekt naar wat er volgens een maatstaf *had moeten staan*, kom je gemakkelijk uit bij een completer antwoord op dezelfde vraag.

In [ons visiedocument van juni 2026](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) schreven we daarom een andere vraag op:

> **Wat had hier kúnnen staan?**

Dat kleine verschil heeft veel veranderd. Een verband hoeft nog nergens bij te horen. Een twijfel hoeft niet meteen te worden opgelost. Een gedachte die nu weinig oplevert, kan in een andere context ineens een interessante voorwaarde of nieuwe vraag worden. Het kan ook nergens toe leiden. We willen beide kunnen waarnemen.

Later hebben we die gedachte verder uitgewerkt. Het onderzoek gaat inmiddels ook over het moment waarop een mogelijke relatie aanleiding geeft tot een volgende mogelijkheid. Niet alleen een ander antwoord, of meer varianten, maar een verandering in wat daarna zinvol onderzocht kan worden. De oorspronkelijke vraag is bewust in het Nederlands bewaard:

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

We veronderstellen daarbij niet dat een taalmodel toegang heeft tot een geheime voorraad ongekozen ideeën. Wat een model niet genereert, kunnen we niet rechtstreeks aflezen. Een detector kan wel een andere relatie of twijfel *formuleren*. Dat geeft ons iets om te onderzoeken, geen bewijs dat we iets uit een verborgen modelgeheugen hebben gehaald.

### Waarom een schaduw?

De naam beschrijft wat we wilden bouwen. Een shadow seed is een mogelijke relatie, vraag of twijfel die in het gesprek kan blijven bestaan zonder het gesprek al te sturen.

Daarom hebben we twee dingen uit elkaar gehaald: *aanwezigheid* en *invloed*. Een geregistreerde seed kan een spoor hebben (`trace > 0`) terwijl de bevoegdheid om een antwoord te sturen ontbreekt (`weight = 0`). De latere context kan opnieuw aanleiding geven om naar een seed te kijken. Soms wordt een vraag concreter. Soms blijkt een vermoeden ongegrond. Soms vervaagt het spoor.

In het [oorspronkelijke visiedocument](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) noemden we dat *de schaduw die meereist*. Het is een beeld voor een technisch onderscheid dat inmiddels in Shadowseed Pro werkt. De Validation Gate en een aparte controle op het moment van gebruik bepalen of een kandidaat ooit invloed mag krijgen. Ook een terugkerende seed krijgt niet vanzelf gelijk.

Het uitstellen van dat oordeel is belangrijk voor het onderzoek. Een kansrijke gedachte kan er bij de eerste formulering rommelig uitzien. Toen we de ruwe modeluitvoer naast de intakebesluiten legden, zagen we hoe sommige kandidaten op hun *vorm* werden afgewezen. Een technisch afwijslabel vertelt ons nog niet of een mogelijkheid later betekenis zou kunnen krijgen. Daarom bewaren we ook de tekst die níét als seed door mocht.

### Hoe we verder zijn gekomen

We hebben onderweg onze eigen onderzoeksmethoden moeten corrigeren. Een ontbrekende verbinding in een vooraf getekende graaf bleek niet hetzelfde als een nieuwe onderzoekbare mogelijkheid. Een antwoord dat anders klinkt, hoeft inhoudelijk geen andere richting te openen. En wanneer het model zonder Shadowseed dezelfde relatie formuleert, moeten we dat serieus nemen.

Daarom kijken we nu naar de hele gang van zaken. Wat antwoordde het model? Wat formuleerde de detector letterlijk? Wat werd vastgelegd of tegengehouden? Welke kandidaten bleven in latere beurten beschikbaar? Werd een kandidaat daadwerkelijk getoond of gebruikt? En welke vervolgvraag ontstond daarna? Die momenten kun je niet allemaal vervangen door één score.

Het resultaat is inmiddels behoorlijk concreet. Shadowseed Pro bevat een werkende geheugen- en validatielaag, onderzoeksinstrumenten en echte meerbeurtentrajecten. We hebben oorspronkelijke antwoorden, kandidatuitspraken, tussenstappen en gedeeltelijke proeven vastgelegd. Juist het terugkijken naar die bronnen heeft ons scherper laten zien wat het systeem doet en wat we er nog niet uit kunnen afleiden.

De vraag of een ongekozen mogelijkheid *zelf* een nieuwe onderzoekbare richting kan laten ontstaan, blijft open. Dat is geen reden om de eerdere stappen klein te maken. Het is de reden om ze zo goed mogelijk te bewaren.

### Waarom dit archief openbaar is

Een groot deel van het werk stond verspreid over repositories, branches en tijdelijke GitHub Actions-artifacts. Voor wie de totstandkoming wil begrijpen, is de volledige geschiedenis relevant. Ook wanneer een proef vroeg stopte, een detector een kandidaat afwees of een model zonder extra hulp al hetzelfde verband vond.

Deze release bevat vier repositorygeschiedenissen en bronmomentopnamen van `shadow-seed-study`, `shadowseed`, `shadowseed-agent-lab` en `shadowseed-pro`, plus **62 oorspronkelijke GitHub Actions-artifactbestanden**. De bestanden zijn ongewijzigd bewaard. De [bestandsinventaris](INVENTORY.json) bevat herkomst, grootte en SHA-256-controlesommen.

De 62 artifacts zijn geen 62 onafhankelijke experimenten. Sommige uitvoeringen zijn onvolledig; al eerder verlopen artifacts zitten niet in deze verzameling. De bronmomentopnamen zijn evenmin een actuele kopie van de code. De afzonderlijke [48-call-proef van 28 oktober](https://github.com/E-AI-MODEL/shadowseed-pro/tree/main/research/datasets/2026-10-28-q1q2-48) is later gepubliceerd en hoort niet bij deze 62 bestanden.

We bewaren deze geschiedenis om het onderzoek bij de oorspronkelijke waarneming te kunnen hervatten. Ook bij een uiting die destijds nergens meer terechtkwam. Misschien gebeurt er later niets mee. Misschien verandert juist zo'n uiting welke vraag we daarna stellen. Dat verschil willen we kunnen onderzoeken.

## English

### What could have been there?

A language model produces an answer. Often a good one, sometimes a remarkably good one. Yet the answer we see is one selected continuation among many. The paths that were not selected usually leave no visible record.

This is where Shadow Seed Learning began. Early versions looked for possible omissions: an unstated condition, a missing connection, an alternative explanation. These were useful things to examine. But measuring what an answer *should have included* kept pulling us back towards a more complete answer to the same question.

In our [June 2026 vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md), we framed the question differently:

> **What could have been there?**

A possible relation does not need an established place in the current answer. A doubt may remain unresolved. Something that seems unpromising today may matter under conditions we have not yet encountered. It may also lead nowhere. Both outcomes belong in the research record.

That idea eventually took us further. We began asking whether a newly considered possibility could make *other* questions or relations available for investigation. A different answer would be interesting, but it would not by itself answer that question. The full research question, first formulated in Dutch, is preserved above. A working translation is:

> Can we use the probability-oriented way a language model works to investigate not only what it knows, does not know or does not generate, but also which relations and possibilities might exist outside its usual generation? And can we investigate how new possibilities emerge that themselves change what becomes thinkable next?

We do not assume that a model can inspect a hidden list of ideas it chose not to express. A detector can formulate another candidate relation, question or doubt. That gives us something observable to follow. It does not establish that the candidate was recovered from some inaccessible internal store.

### The shadow that travels

The name captures an important design choice. A shadow seed is a possible relation, question or doubt that can remain part of a conversation's recorded history without being allowed to steer what comes next.

We separated *presence* from *authority*. A seed can have a trace (`trace > 0`) while its ability to influence an answer remains zero (`weight = 0`). Later context may bring the candidate back into view, sharpen the question or leave the idea behind. A Validation Gate and a separate point-of-use check control any subsequent influence. Recurrence alone is not confirmation.

We called this [“the shadow that travels”](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md). The metaphor expresses an actual separation now implemented in Shadowseed Pro. It also explains why we cannot judge every candidate at birth. A tentative relation may be awkwardly phrased or difficult to reduce to a single neat item. When we revisited the original detector output, we found intake decisions that depended on written form. A rejection at that stage is part of the record, not an independent verdict on what the candidate could have become.

### Following the whole route

The research has changed because the early tests taught us what *not* to confuse. Finding a missing edge in a predefined graph does not show that a new kind of inquiry has become possible. Two different-looking answers are not necessarily two different ideas. And if an ordinary model can reach the same relation without Shadowseed, that belongs in the comparison.

We therefore follow each step separately: the original model response, the detector's literal proposal, the intake decision, the recorded seed, what survives across turns, whether a candidate is actually shown or used, and what happens afterwards. Keeping those distinctions visible matters more than arriving quickly at an attractive percentage.

There is substantial work behind this archive. Shadowseed Pro has a functioning memory and validation engine. We have real model runs, multi-turn records, original candidate text, partial experiments and source-level reconstruction. Returning to those materials has improved both the software and the questions we ask of it.

Whether retaining an unselected possibility can *cause* a new direction of inquiry to become available remains under investigation. We are further along precisely because we can now examine the process rather than rely on a promising story about the outcome.

### Why this archive belongs in public

Earlier work was scattered across repositories, branches and short-lived GitHub Actions artifacts. That history includes decisions that shaped the design, experiments that stopped early and candidates that never reached a later turn. All of it matters if someone wants to understand how the project developed.

This release preserves source snapshots and Git bundles from **four repositories**: `shadow-seed-study`, `shadowseed`, `shadowseed-agent-lab` and `shadowseed-pro`. It also contains **62 original GitHub Actions artifact ZIPs**. The original files are unchanged, and the [inventory](INVENTORY.json) records their provenance, sizes and SHA-256 checksums.

Those 62 artifacts are not 62 independent experiments. Some runs are partial, and the collection cannot restore artifacts that had already expired or were unavailable. The source snapshots describe an earlier point in time. The separately released [48-call study of 28 October](https://github.com/E-AI-MODEL/shadowseed-pro/tree/main/research/datasets/2026-10-28-q1q2-48) is not an additional item in this collection.

We made the archive public so that the work can be read from its original observations. Including the candidates that were set aside. A possibility may fade without changing anything. Another may become relevant much later. The research depends on being able to tell those histories apart.

## Bronbestanden en herkomst / Source files and provenance

**Release:** [Originele onderzoeksarchieven 27 oktober 2026](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27)  
**Exact ZIP:** [shadowseed_alle_raw_artifacts_20261027.zip](https://github.com/E-AI-MODEL/shadowseed-pro/releases/download/research-archive-2026-10-27/shadowseed_alle_raw_artifacts_20261027.zip)  
**Size:** 87,841,733 bytes  
**SHA-256:** `0c2fac002613e88dd74a8d305cb7c8078d6349fbc2c76b11042982cdeaf921d8`  
**Inventory:** [`INVENTORY.json`](INVENTORY.json), reproduced byte-for-byte from the original ZIP, with SHA-256 for all 70 archived members.

The outer ZIP contains 71 entries: four `*-main-source.tar` snapshots, four `*.git.bundle` histories, 62 original Actions artifact ZIPs, and the inventory. The complete original ZIP is retained byte-for-byte. The inventory records repository refs as they existed on 27 October 2026 and explicitly notes that already expired or unavailable Actions artifacts are not included.

For current research context, see the [research entry](../../README.md), the [foundational question](../../possibility-space-thesis.md) and the [dated retrospective evidence map](../../possibility-space/retrospective-evidence-map-2026-10-27.md). These documents have different dates and purposes; they should not be silently read as one final conclusion. Nothing in this README changes historical test outcomes, product Gate rules or earlier research records.
