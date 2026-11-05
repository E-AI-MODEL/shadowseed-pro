# Gewone notitie tegenover weightless seed, met exact gelijke kandidaatinhoud

**Live uitgevoerde proef, 5 november 2026.**

Bron: [GitHub Actions 41982542768](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41982542768). De onveranderde provideruitvoer, volledige prompts, factureringsgebruik, respons-ID's, echte compaction-objecten en checksums staan in [het bronarchief](../sources/paired-memory-vs-seed-20261105/). De onderzoeksopzet is [vooraf vastgelegd](paired-memory-vs-seed-plan-2026-11-05.md).

## Wat echt gebeurde

Vier fictieve, **onderling gescheiden** gesprekken: koeltransport, museumcommunicatie, regenwatermetingen, leesclub. Ieder gesprek had drie GPT-6.1 Sol-beurten en een eigen canonieke `ShadowseedEngine`. De GPT-4.1 `current_pair`-detector maakte zelf de kandidaten. In totaal ontstonden **24 seeds** (4, 8, 5, 7). Alle seeds behielden **weight = 0** en **evidence_count = 0**. De drie eerdere hostantwoorden bevatten geen toegelaten ShadowSeed-invloed.

De vooraf vastgelegde selectie nam uit het **eerste** antwoord deterministisch maximaal drie seeds. In werkelijkheid waren er per casus **2, 2, 1, 1** geselecteerd (totaal zes). Dat is minder dan de vooraf toegestane bovengrens; we hebben ze achteraf niet aangevuld.

Na de oorspronkelijke gesprekshistorie maakte OpenAI per casus één echt, grotendeels onleesbaar `responses.compact`-object. Alle vervolgcondities kregen hetzelfde volledige of hetzelfde gecomprimeerde bronverleden.

Per context volgden vier onafhankelijke API-calls: **regulier**, **reflectie**, **gewone notitie**, **weightless-herbeoordeling**. Het laatste paar kreeg **letterlijk dezelfde geselecteerde seedteksten**, dezelfde instructies en dezelfde maximale uitvoerlengte. Alleen de kop erboven verschilde: `Gewone notities (onbewezen):` tegenover `Gewichtloze seeds (onbewezen):`.

Totaal **108 echte API-aanroepen inclusief embeddings**, **32 vervolgantwoorden**, geraamde kosten **$0,245268** binnen de ingestelde limiet van $0,50. Geen automatische herhalingen. De oorspronkelijke resultaten zijn niet herschreven.

## De invoer was werkelijk even groot

| Casus | Volledig: notitie / seed | Gecomprimeerd: notitie / seed | Nieuwe seeds gebruikt |
|---|---:|---:|---:|
| Koeltransport | 1.668 / 1.668 | 860 / 860 | 2 |
| Museum | 879 / 879 | 868 / 868 | 2 |
| Regenwater | 1.379 / 1.379 | 913 / 913 | 1 |
| Leesclub | 852 / 852 | 764 / 764 | 1 |

Het was dus **acht keer exact hetzelfde aantal invoertokens**, met een gedeeld outputlimiet van 600 tokens. De promptbytes verschillen wel: het statuslabel is de onderzochte ingreep.

Bij de reguliere conditie daalde de invoer door providercompressie met **52,0%** (koeltransport), **1,4%** (museum), **35,7%** (regenwater) en **11,3%** (leesclub). Dit bewijst niet dat specifieke ideeën intern verloren gingen.

## Inhoudelijk gelezen, nog niet onafhankelijk blind beoordeeld

**Koeltransport:** alle voorwaarden kozen een meetopzet met gesynchroniseerde registraties en een onafhankelijke temperatuursensor. Het bewaren van de twee vroeg geboren seeds gaf geen zichtbaar exclusief experiment. De herbeoordeling benoemde meetketen en definities van dagrapporten; reguliere en reflecterende antwoorden deden dat grotendeels ook.

**Museum:** alle versies vroegen de lezer om anders te luisteren naar alledaagse stadsgeluiden. De stijl verschilde per antwoord, maar de gewone notitie en weightless seed boden geen aantoonbaar andere inhoudelijke mogelijkheid. Reguliere en reflecterende versies waren eveneens aansprekend.

**Regenwater:** alle acht antwoorden kozen een onafhankelijke peilstokmeting om een meetprobleem van werkelijk waterstandsverschil te scheiden. De gewone notitie en weightless seed noemden beiden de betrouwbaarheid van weekgemiddelden. Een unieke vondst van ShadowSeed is niet zichtbaar.

**Leesclub:** alle acht uitnodigingen bleven vriendelijk maar betrekkelijk formeel. De gewichtloze kandidaat over plaats/tijd maakte de tekst niet wezenlijk creatiever dan een gewone notitie.

De ruwe teksten verschillen aanzienlijk op woordniveau, maar die verschillen bewijzen geen betekenisvolle verbetering. Een tekstvergelijkingsgetal zoals SequenceMatcher meet overlap, geen kwaliteit of originaliteit.

## Belangrijke grenzen

**Technisch:** de vergelijking van kandidaatinhoud, invoertokens, modelversie, maximumuitvoer en gevalssituatie is beter gecontroleerd dan in de eerdere pilots. Alle vier gespreksgeschiedenissen waren onafhankelijk opgebouwd. Binnen ieder geval waren de acht antwoorden gekoppelde voortzettingen van dezelfde geschiedenis; ze zijn dus geen acht onafhankelijke herhalingen.

**Inhoudelijk:** de gewone notitie kreeg bewust **dezelfde door ShadowSeed gevonden seeds**. Daardoor isoleert deze proef het effect van het **statuslabel**, niet het effect van het verschil tussen een gewone memory-summarizer en de ShadowSeed-engine. De verschillen die overblijven kunnen ook uit gewone generatievariatie komen. Eén vervolgcall per conditie en vier casussen zonder onafhankelijke blindering rechtvaardigen geen effectschatting.

**Context:** echte providercompressie is aangetoond, maar de inhoud van de opaque compaction-toestand is niet inspecteerbaar. Een verschil tussen volledige en gecomprimeerde context is dus niet automatisch bewijs van vergeten ideeën. Modelgewichten veranderen hierbij niet.

**Bevoegdheid:** het weightless-record werd alleen gebruikt in een *afgebakende onderzoeksquery*, niet als productautorisatie voor een antwoord. De product-Gate heeft geen promotie uitgevoerd.

## Voorlopige uitkomst

**Geen duidelijk voordeel voor het weightless-statuslabel ten opzichte van dezelfde tekst als gewone notitie.** In deze vier gevallen kwamen beide vormen vrijwel steeds tot vergelijkbare onderzoekskeuzes of schrijfstijl. De technische vergelijking is geslaagd; een afwijkende, betere onderzoeksfunctie is nog niet aangetoond.

Vervolgonderzoek moet het **verschil in wat werkelijk wordt bewaard** meten: een gewone geheugencompressor die zelf notities kiest versus de canonieke ShadowSeed-detector die onbewezen mogelijkheden bewaart. Pas daarna kunnen we onderzoeken of een passend bewaard, later opnieuw bekeken idee op langere termijn een inhoudelijk beter nieuw onderzoekspad oplevert. Houd beoordelingsopdracht, begroting en casussen vooraf gelijk.
