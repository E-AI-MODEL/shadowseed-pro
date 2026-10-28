# Shadowseed: de mogelijkheden die buiten beeld bleven | The possibilities we did not select

**Onderzoeksarchief van 27 oktober 2026 · Research archive, 27 October 2026**  
[Nederlands](#nederlands) · [English](#english) · [Bronbestanden en herkomst / Source files and provenance](#bronbestanden-en-herkomst--source-files-and-provenance)

## Nederlands

### Waarom we dit onderzoeken

Een taalmodel geeft een antwoord. Soms een uitstekend antwoord. Maar wat we lezen, is altijd een selectie. Andere verbanden, vragen of twijfels verschijnen niet. Misschien waren ze niet relevant. Misschien waren ze onzin. En misschien hadden ze iets kunnen veranderen aan de vraag die we daarna zouden stellen.

Dat laatste interesseert ons. Niet alleen wat het model weet of niet weet, maar wat er nog *zou kunnen* ontstaan wanneer je een niet-gekozen mogelijkheid niet meteen laat verdwijnen. Kan een verband dat nu weinig betekenis lijkt te hebben, later een andere vraag oproepen? En kan die vraag op haar beurt veranderen wat er vervolgens onderzocht kan worden?

De oorspronkelijke onderzoeksvraag luidt:

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Hiermee beweren we niet dat een model verborgen waarheden kan opvragen of precies weet welke gedachten het heeft overgeslagen. Ook gaat het niet om het verzamelen van zo veel mogelijk alternatieven. We onderzoeken wat we daadwerkelijk kunnen waarnemen, bewaren en in latere beurten opnieuw tegenkomen.

### Van een vraag naar iets dat we kunnen onderzoeken

In *Shadow Seed Learning* begonnen we met het observeren van mogelijke ontbrekende relaties. Gaandeweg werd duidelijk dat een detectoruitspraak nog geen waarheid is, en ook geen bewijs dat een verband waardevol of werkelijk nieuw is. Daarom moesten we leren onderscheiden: wat gaf het model zelf als antwoord, wat opperde de detector, wat liet de verwerking door, en wat gebeurde er in een volgende beurt?

Die scheiding zit inmiddels ook in de software. Een kandidaat kan worden vastgelegd zonder dat hij het volgende antwoord mag sturen. `trace > 0` betekent dat er iets is onthouden. `weight = 0` betekent dat het geen bevoegdheid heeft om het antwoord te bepalen. Een afzonderlijke Validation Gate en een controle op het moment van gebruik regelen eventuele latere invloed. Dat is werkende techniek, geen bewijs dat de grote onderzoeksvraag daarmee al beantwoord is.

We hebben vervolgens echte modelantwoorden, detectorkandidaten, meerbeurtentrajecten en vergelijkingen naast elkaar gelegd. Soms ontstond er een nieuwe onderzoeksvraag. Soms noemde een gewoon model dezelfde relatie al zonder Shadowseed. Soms kwam een kandidaat nooit in een later antwoord terecht. We zagen ook dat een vormregel bij de intake een uiting kon tegenhouden, zonder dat daarmee iets over de inhoud was vastgesteld. Juist zulke verschillen zijn interessant. Ze laten zien waar een mogelijkheid verloren gaat, bewaard blijft of opnieuw onderzocht wordt.

De methoden werden daarbij regelmatig bijgesteld. Van vroege experimenten met ontbrekende informatie naar het volgen van kandidaten over meerdere beurten. Van alleen geaccepteerde seeds naar ook de oorspronkelijke afgewezen uitingen. Van een verschil tussen twee antwoorden naar de moeilijkere vraag wat dat verschil eigenlijk betekent. We bewaren eerdere aannames, tussenstappen en mislukte proeven, omdat je anders achteraf niet meer ziet hoe het onderzoek zich heeft ontwikkeld.

### Waarom dit archief bestaat

Deze release bewaart de bronbestanden van **vier repositories** (`shadow-seed-study`, `shadowseed`, `shadowseed-agent-lab` en `shadowseed-pro`), met van elk een bronmomentopname en een Git-bundle. Daarnaast bevat zij **62 oorspronkelijk gedownloade GitHub Actions-artifacts**. Het bestand `INVENTORY.json` vermeldt de afzonderlijke bestanden, grootte, herkomst en SHA-256-controlesommen.

Dat zijn 62 bewaarde artifactbestanden, geen 62 onafhankelijke experimenten en evenmin 62 geslaagde proeven. Sommige resultaten zijn onvolledig of laten zien dat een gekozen meetmethode onze vraag niet goed kon beantwoorden. Beschikbaar betekent ook niet volledig: artifacts die bij de verzameling al ontbraken of verlopen waren, zitten er niet alsnog in. De archiefmomentopnamen zijn geen actuele versies van de vier repositories.

Dit archief geeft onderzoekers de mogelijkheid terug te gaan naar de oorspronkelijke waarnemingen. Niet om er achteraf één succespercentage uit te halen, maar om te kunnen volgen hoe een modeluiting door de verschillende stappen ging, welke keuzes invloed hadden en wat we nog niet kunnen zeggen. De afzonderlijk gepubliceerde [48-call-proef van 28 oktober](https://github.com/E-AI-MODEL/shadowseed-pro/tree/main/research/datasets/2026-10-28-q1q2-48) hoort bij de latere onderzoeksontwikkeling en is geen extra onderdeel van deze 62 artifacts.

Het onderzoek is ver gekomen: er is software die de route zichtbaar maakt, er zijn echte meerbeurtentrajecten en er is bronmateriaal waarmee de oorspronkelijke keuzes opnieuw bekeken kunnen worden. Of het bewaren van een ongekozen mogelijkheid ook werkelijk verandert wat later denkbaar en onderzoekbaar wordt, blijft de vraag die we zorgvuldig willen beantwoorden.

## English

### Why we started asking

A language model produces an answer. Sometimes a very good one. But the answer we read is a selection. Other relations, questions or doubts do not appear. They may have been irrelevant. They may have been nonsense. Or they might have changed the question we would ask next.

That last possibility is what interests us. We want to investigate not only what a model knows or fails to generate, but what *might become possible* when an unselected thought is not immediately discarded. Could a relation that seems unimportant now lead to a different question later? Could that question, in turn, change what can be investigated?

A working English translation of our original Dutch research question is:

> Can we use the probability-oriented way a language model works to investigate not only what it knows, does not know or does not generate, but also which relations and possibilities might exist outside its usual generation? And can we investigate how new possibilities emerge that themselves change what becomes thinkable next?

This is not a claim that a model can reveal hidden truths or accurately report every idea it did not select. Nor are we trying to generate as many alternatives as possible. We want to observe what can actually be recorded, retained and revisited over subsequent turns. The [original Dutch wording](../../possibility-space-thesis.md) remains the reference for the research question.

### Turning the question into research

*Shadow Seed Learning* began by looking for potentially missing relations. We soon had to distinguish a detector's suggestion from evidence, and a plausible hypothesis from a genuinely new possibility. A detector output does not tell us whether a candidate is true, useful or novel. We therefore track the original answer, the detector's raw text, its processing and intake decision, and what happens in later turns as separate events.

This separation is now part of the working software. A candidate can be remembered without acquiring the authority to shape the next answer. `trace > 0` means something remains in memory. `weight = 0` means it has no steering authority. A separate Validation Gate and a point-of-use decision control whether it may influence an answer later. Implementing that distinction is substantial engineering progress. It is not, by itself, proof of our wider hypothesis.

We went on to compare actual model answers, candidate records and multi-turn trajectories. Sometimes a later answer explored a relation that had appeared in a candidate. Sometimes an ordinary model reached the same relation without Shadowseed. Sometimes a candidate was never shown in a later answer. We also saw that an intake rule could reject a candidate because of its written form, without settling anything about the idea itself. Those distinctions matter: they tell us where an option was lost, retained or revisited.

Our approach changed as we learned from the records. Early experiments concentrated on missing information. Later work followed candidates through multiple turns, preserved rejected as well as accepted source text, and separated a different-looking answer from the harder question of whether a new avenue of investigation had become available. We kept the earlier assumptions, failed tests and partial runs. Without them, the research would look much more settled than it was.

### Why we published the archive

This release preserves source snapshots and Git bundles for **four repositories** (`shadow-seed-study`, `shadowseed`, `shadowseed-agent-lab` and `shadowseed-pro`), together with **62 original GitHub Actions artifact ZIPs**. Inside the download, `INVENTORY.json` lists the files, their provenance, sizes and SHA-256 checksums.

Sixty-two preserved artifacts do not mean 62 independent experiments, and a successful workflow is not the same as a validated research result. Some runs were partial; some tested a narrower question than the one we ultimately care about. The collection includes only artifacts that were available for download when it was assembled. The repository snapshots record that date, not the current state of the code.

We publish this material so that someone can return to the original observations and ask better questions about them: what the model actually produced, what the detector proposed, where an item was filtered out, and what could be traced across turns. The separately published [48-call study from 28 October](https://github.com/E-AI-MODEL/shadowseed-pro/tree/main/research/datasets/2026-10-28-q1q2-48) belongs to a later step and is not an additional item among these 62 artifacts.

There is already a working system, real multi-turn material and a substantial source record. What remains open is the question that made us start: can retaining an unselected possibility change what becomes conceivable and investigable afterwards? The archive lets that question remain open without losing the work already done.

## Bronbestanden en herkomst / Source files and provenance

**Release:** [Originele onderzoeksarchieven 27 oktober 2026](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27)  
**Exact ZIP:** [shadowseed_alle_raw_artifacts_20261027.zip](https://github.com/E-AI-MODEL/shadowseed-pro/releases/download/research-archive-2026-10-27/shadowseed_alle_raw_artifacts_20261027.zip)  
**Size:** 87,841,733 bytes  
**SHA-256:** `0c2fac002613e88dd74a8d305cb7c8078d6349fbc2c76b11042982cdeaf921d8`  
**Inventory:** [`INVENTORY.json`](INVENTORY.json), reproduced byte-for-byte from the original ZIP, with SHA-256 for all 70 archived members.

The outer ZIP contains 71 entries: four `*-main-source.tar` snapshots, four `*.git.bundle` histories, 62 original Actions artifact ZIPs, and the inventory. The complete original ZIP is retained byte-for-byte. The inventory records repository refs as they existed on 27 October 2026 and explicitly notes that already expired or unavailable Actions artifacts are not included.

For current research context, see the [research entry](../../README.md), the [foundational question](../../possibility-space-thesis.md) and the [dated retrospective evidence map](../../possibility-space/retrospective-evidence-map-2026-10-27.md). These documents have different dates and purposes; they should not be silently read as one final conclusion. Nothing in this README changes historical test outcomes, product Gate rules or earlier research records.
