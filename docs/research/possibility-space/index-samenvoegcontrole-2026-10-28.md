# Samenvoegcontrole onderzoeksindex — 28 oktober 2026

> **Controleverslag, geen merge of onderzoeksconclusie.** Dit verslag vergelijkt de afzonderlijke documentwijzigingen van concept-PR [#259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259), [#260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) en [#264](https://github.com/E-AI-MODEL/shadowseed-pro/pull/264). Er zijn geen bestaande onderzoeksgegevens, verslagen, PR-bases, branches, Gate-regels of modelresultaten aangepast.

## Bronnen voor deze vergelijking

Alle onderstaande SHA's zijn **Git blob-SHA's van de onderzoeksindex** zoals deze tijdens de vergelijking in de desbetreffende branch stond. Het zijn geen hoofdcommit-SHA's en ze blijven momentopnamen.

| Indexversie | GitHub-branch | Blob-SHA | Toevoeging aan deze index |
| --- | --- | --- | --- |
| Uitgangstekst | `main` | `91b525c431ead402b88230b11e97ffd78122eca1` | Oorspronkelijke tekst van de onderzoeksindex |
| [PR #259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259) | `docs/research-archive-map-20261027` | `773e136474326a12c05bdd097c7f94f21b7741cc` | Sectie **Retrospective research inventory (27 October 2026)** met drie verwijzingen |
| [PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) | `research/q1q2-two-point-48-20261028` | `7bf2144bc2e7850f6cce0bec37f03d283e05b11b` | Sectie **New exploratory two-checkpoint inquiry pilot (28 October 2026)** met bronverslag en protocol |
| PR #264, vóór deze controle | `docs/observation-first-readme-20261028` | `1dc8b8ab17ac7bb8c62260747564b2ffa5653b87` | Datering en verwijzing naar de actuele onderzoeksingang bovenin |

Bij de controle zijn de volledige tekstbestanden opgehaald, niet alleen PR-samenvattingen. De drie aanpassingen zijn **toevoegingen** aan de originele 25-oktobertekst. #259 en #260 plaatsen hun nieuwe sectie op **hetzelfde invoegpunt**, na het blok over stap 1 en vóór `## Current reading order (start here)`. Dat kan bij een echte Git-merge een tekstconflict geven, ook al spreken de inhoud en de dateringen elkaar niet tegen. De datumverwijzing van #264 staat boven de historische tekst en raakt een ander invoegpunt.

## Tekstuele samenvoegproef

Met de complete opgehaalde bestandsteksten is een **tijdelijke, niet-gecommitteerde samengestelde versie** gemaakt. Beide invoegingen zijn letterlijk overgenomen, in deze volgorde:

```text
# Shadowseed possibility-space research ...
> Oorspronkelijke indexstand: 25 oktober 2026 [PR #264]
## Stap 1: ...
[alle bestaande stap-1-verwijzingen ongewijzigd]
## Retrospective research inventory (27 October 2026) [PR #259]
[letterlijk de drie archiefverwijzingen en toelichting van #259]
## New exploratory two-checkpoint inquiry pilot (28 October 2026) [PR #260]
[letterlijk de twee bronverwijzingen en toelichting van #260]
## Current reading order (start here)
[de volledige resterende oorspronkelijke index ongewijzigd]
```

De toegevoegde sectie uit #259 bevat **783 tekens** en die uit #260 **621 tekens**, inclusief de gedeelde Markdown-scheidingsopmaak. De simulatie behield de oorspronkelijke tekst na `Current reading order` exact. Bij terugverwijderen van de twee letterlijk toegevoegde secties ontstond weer precies de #264-variant. **Dit controleert tekstbehoud, niet een echte Git-merge, CI of de wetenschappelijke inhoud.**

### Waar de bijbehorende bestanden staan

De drie documenten waarnaar #259 relatief verwijst, staan uitsluitend in de #259-branch zolang deze PR niet is gemerged:

- [Bron-resultatenkaart, 27 oktober](https://github.com/E-AI-MODEL/shadowseed-pro/blob/docs/research-archive-map-20261027/docs/research/possibility-space/retrospective-evidence-map-2026-10-27.md)
- [Historische PR-kaart, 27 oktober](https://github.com/E-AI-MODEL/shadowseed-pro/blob/docs/research-archive-map-20261027/docs/research/possibility-space/research-branch-map-2026-10-27.md)
- [Publicatie- en reviewstatus, 27 oktober](https://github.com/E-AI-MODEL/shadowseed-pro/blob/docs/research-archive-map-20261027/docs/research/possibility-space/publication-readiness-2026-10-27.md)

Het protocol en verslag van #260 staan in de afzonderlijke onderzoeksbranch:

- [48-call-verslag](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/q1q2-two-point-48-20261028/research/experiments/20261028/RESULTS_STATUS.md)
- [48-call-protocol](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/q1q2-two-point-48-20261028/research/protocols/q1q2-two-point-48-20261028.md)

**Linkcontrole:** alle vijf bronnen bestaan op hun bronbranch. Geen van de vijf bestaat momenteel op de #264-branch. Daarom zijn de twee secties **niet** alvast aan #264 toegevoegd: dat zou in deze branch vijf niet-werkende relatieve verwijzingen veroorzaken en het onderzoeksmateriaal in andere PR's vooruitlopen.

## Inhoudelijk naast elkaar, zonder gegevens samen te voegen

- **#259** beschrijft een archiveer- en herkomstoverzicht van 27 oktober, waaronder 62 oorspronkelijke Actions-ZIP's, een fixed22-reeks met 196 kandidaatvoorkomens, een dual-modelreeks met 94 voorkomens, en eerder vastgelegde reviewlabels. Registraties met verschillende modellen, meeteenheden en herkomst zijn niet als onafhankelijke, optelbare onderzoeksresultaten behandeld.
- **#260** beschrijft één nieuwe afzonderlijke fictieve boeicasus, onderzocht op twee modelafhankelijke meetmomenten. De gecorrigeerde uitvoering bevat 48 volledig afgeronde providerantwoorden verdeeld over 24 tweeturntrajecten. Er zijn nul afgeronde onafhankelijke menselijke semantische beoordelingen. De kandidaat werd in een **onderzoeksnotitie** aangeboden, niet via de normale Pro-Gate gepromoveerd.
- **#264** geeft deze historische datasets een actuele onderzoeksingang en inventariseert de 166 remote branches. De huidige interpretatie staat apart van de ruwe detectorregistraties, oude intakebesluiten, historische beoordelingslabels en uitgevoerde modelantwoorden.
- De 48 modelantwoorden uit #260 mogen niet automatisch bij de 94 kandidaatvoorkomens of de 220 beurten van de latere, afgeleide reconstructie worden opgeteld. De noemers en de herkomst zijn niet identiek vastgesteld.

De index mag alle drie de onderdelen tonen. Hij mag hun historische inhoud niet stilzwijgend omzetten in één nieuw effectcijfer, één kwaliteitslabel of een terugwerkende architectuurkeuze.

## Veilige volgorde bij integratie

1. **#264 afzonderlijk beoordelen.** Deze PR bevat de actuele onderzoeksingang, de behouden oorspronkelijke index en het branchregister. Geen onderzoekscode of private ruwe data.
2. **#259 apart beoordelen en daarna eventueel samenvoegen.** Controleer of de drie meegeleverde documenten en de invoeging in de index samen landen. De bronkaart blijft expliciet gedateerd op 27 oktober, ook als hij later in `main` verschijnt.
3. **#260 niet als louter indexwijziging behandelen.** Naast zijn indexsectie bevat deze PR onderzoekssoftware, tests, een inactief gearchiveerde eenmalige workflow, het protocol, het resultaatverslag en een **publieke** encryptiesleutel. Controleer privacy, workflows, CI, bron-SHA's en de afbakening tegenover de gewone Pro-runtime vóór een mergebesluit. Kopieer de relatieve links niet zonder die bestanden.
4. **Bij tekstconflict alleen de index oplossen:** behoud eerst het bovenste datumblok van #264, daarna de volledige sectie van #259, daarna die van #260 en pas daarna `Current reading order`. Bewaar alle oorspronkelijke regels van de index; geen automatische voorkeur voor de laatste ingevoegde sectie.
5. **Na ieder echt mergebesluit opnieuw controleren:** actuele `main`-SHA, alle vijf relatieve bestanden, koppen precies eenmaal, geen verwijdering uit de historische index, geen onbedoelde PR-basewijziging en normale GitHub-controles. Deze samenvoegproef geeft geen garantie dat de actuele repo dan nog dezelfde stand heeft.

**Nog niet uitgevoerd:** daadwerkelijke Git-merge of rebase, een werkelijke Git-conflictresolutie, runtime- of testuitvoering, semantische beoordeling of wijziging/verwijdering van een historische branch. Deze controle verandert alleen de documentatie in concept-PR #264.
