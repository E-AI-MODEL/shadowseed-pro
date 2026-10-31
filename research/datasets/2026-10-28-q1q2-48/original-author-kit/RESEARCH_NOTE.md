# Shadow Seed Learning: de invloed van twee gevonden twijfels

**Verkennende onderzoeksnotitie, 28 oktober 2026**  
**Status:** 48 modelantwoorden gecontroleerd; nog geen onafhankelijke inhoudelijke beoordeling.  
**Onderzoek:** E-AI-MODEL/shadowseed-pro, [GitHub Actions-run 40616375653](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40616375653), [concept-PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260).

## Wat we werkelijk hebben uitgevoerd

De onderzochte vraag is niet of GPT-5 of GPT-6 meer informatie kan opsommen. We onderzoeken of een eerder gevonden maar niet uitgewerkte relatie de richting van later onderzoek kan veranderen. Er zijn twee detectoruitingen gebruikt uit één fictieve casus over een meetboei, op twee verschillende momenten in het gesprek:

- **Horizon, na beurt T2, GPT-5:** ontbrekende of onbruikbare vaste referenties kunnen een voorgestelde homografie- of bewegingsschatting ondermijnen. Deze kandidaat was historisch toegelaten als seed `ss_006`.
- **Batterij, na beurt T3, GPT-6 Luna:** een periode met lagere batterijspanning kan behalve de camera ook de bewegingssensor of tijdregistratie raken. Deze kandidaat was historisch afgewezen met `not_atomic`.

Iedere uitgangssituatie kreeg vier onderzoeksarmen. De gewone arm kreeg dezelfde, expliciete opdracht om een onderscheidende onderzoeksvraag te formuleren. De gerichte zoekarm moest ook naar minder voor de hand liggende verbanden zoeken. De Shadowseed-arm kreeg daarnaast de oorspronkelijke kandidaat te zien als *onbevestigde aantekening met gewicht nul*. De placebo-arm kreeg een qua lengte vergelijkbare detectorkandidaat uit een andere fictieve casus, bijvoorbeeld over materiaal- of slijtagemetingen. Alle armen kregen dezelfde opgeslagen oorspronkelijke hostgeschiedenis binnen hun eigen model en moment.

Per arm zijn drie trajecten gegenereerd, elk met twee nieuwe onderzoeksbeurten. Dit leverde **24 complete trajecten en 48 voltooide API-antwoorden** op. Alle 48 antwoorden hebben een eigen provider-ID en een gecontroleerde inhoudschecksum. Het model rapporteerde in totaal **187.255 input- en outputtokens**. Er zijn **geen** onafhankelijke menselijke kwaliteitsoordelen ingevuld.

De bron is het oorspronkelijke `observed.json` uit Actions-artifact 12754935105, met SHA-256 `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`. Het eerste technische workflowontwerp faalde bij bronophaling zonder modelaanroepen. Een volgende poging deed één niet-afgeronde GPT-5-aanroep onder een te lage outputlimiet. De gecorrigeerde proef voerde daarna **48 van 48** geplande modelaanroepen volledig uit. In totaal waren er dus één onbruikbare technische poging en 48 voltooide antwoorden, niet 49 voltooide experimenten.

## Resultaten die direct in de ruwe tekst zichtbaar zijn

### De horizonrelatie blijkt ook zonder seed bereikbaar

De gewone GPT-5-arm is geen lege of passieve baseline: hij moet zelf een toetsbare vervolgvraag bedenken. In **twee van de drie** gewone trajecten noemt hij in de tweede vervolgbeurt expliciet dat bruikbare vaste referenties (zoals horizon, kustlijn of mast) mogelijk ontbreken of ontoereikend zijn. Een voorbeeld uit het gewone traject is:

> Mogelijk ontbreken in alle frames voldoende vaste referenties (horizon/kustlijn/mast) om skew robuust te meten.

In een ander gewoon traject wordt voldoende statische referentiegeometrie als *voorwaarde* voor homografieschatting genoemd. De Shadowseed-arm neemt deze voorwaarde ook op, maar de relatie is hier niet aantoonbaar exclusief voor die arm. De gerichte zoekarm verkent daarnaast onder andere de koppeling van beeldgeometrie aan automatische belichting en fotometrie. De placebo-arm blijft eveneens met de meetboei bezig en wijst de irrelevante materiaalaantekening af.

**Voorlopige betekenis:** deze kandidaat is geschikt om te onderzoeken *hoe* twijfel wordt gebruikt, maar geen overtuigend voorbeeld van iets wat het model onder een serieuze gewone onderzoeksvraag niet zelf zou kunnen formuleren. De eerdere stelling dat de horizonrelatie ‘buiten gewone generatie’ lag, houdt bij deze uitgebreidere baseline niet stand.

### De batterijkandidaat verandert de gevolgde onderzoeksrichting

In alle **drie** Shadowseed-trajecten onderzoekt GPT-6 Luna expliciet een mogelijke combinatie van voedingsspanning, bewegingssensor en tijdregistratie. In de tweede beurt komen verschillende afgeleide voorwaarden aan bod: elektrische belasting, de mogelijke invloed van de camera op gedeelde voeding, en de vraag of een relatie tussen beweging en geschatte watergrens verandert bij lage spanning.

De gewone GPT-6-trajecten komen ook met toetsbare vragen, maar vooral over beeldkwaliteit, cameraconfiguratie, scènecontrast en licht. De gerichte zoekarm brengt weer andere mogelijkheden naar voren: temperatuur als derde factor, een tijdelijke spanningsdip door belasting, of omgekeerde causaliteit van opnameactiviteit naar lagere spanning.

De oorspronkelijke verhouding *spanning → sensor/klok* is dus geen exclusieve technische mogelijkheid van Shadowseed. Andere modellen en onderzoeksprompts kunnen vergelijkbare verbanden vormen. **Wat deze proef rechtstreeks laat zien, is dat het tonen van de kandidaat de aandacht van het model gericht op dat verband houdt**. Het onderscheid tussen zo'n gerichte invloed en het ontstaan van een echt andere onderzoekbaarheid is nog niet door onafhankelijke lezers beoordeeld.

### De irrelevante placebo wordt geregeld terecht afgewezen

De placebo bij de batterijcasus betreft slijtage- of slijtvastheidsmetingen die nergens in de meetboeicasus worden vermeld. In meerdere placebo-antwoorden zegt het model expliciet dat deze aantekening geen onderbouwde nieuwe vraag voor deze situatie oplevert. Eén antwoord concludeert:

> Er volgt geen onderbouwde, andere afhankelijkheid of voorwaarde uit de nieuwe aantekening.

Dit is geen ‘slechtere’ uitkomst omdat het model minder nieuwe vragen maakt. Een systeem dat weerstand biedt aan een irrelevante suggestie kan juist beter handelen dan een systeem dat koste wat kost een relatie fabriceert. De beoordeling moet dit kunnen herkennen.

## Controleerbare cijfers, zonder inhoudelijke scores

| Onderzoeksmoment | Arm | Volledige trajecten | Modelcalls | Gerapporteerde tokens |
|---|---|---:|---:|---:|
| Horizon, GPT-5 | Gewoon onderzoeken | 3 | 6 | 31.219 |
| Horizon, GPT-5 | Gericht diep zoeken | 3 | 6 | 36.837 |
| Horizon, GPT-5 | Gewichtloze kandidaat | 3 | 6 | 31.294 |
| Horizon, GPT-5 | Irrelevante placebo | 3 | 6 | 30.201 |
| Batterij, GPT-6 | Gewoon onderzoeken | 3 | 6 | 13.875 |
| Batterij, GPT-6 | Gericht diep zoeken | 3 | 6 | 15.381 |
| Batterij, GPT-6 | Gewichtloze kandidaat | 3 | 6 | 14.253 |
| Batterij, GPT-6 | Irrelevante placebo | 3 | 6 | 14.195 |
| **Totaal** | | **24** | **48** | **187.255** |

De grote verschillen in antwoordlengte tussen GPT-5 en GPT-6 maken samenvoegen tot één kwaliteitsscore onverantwoord. Zelfs binnen één model geeft de gerichte zoekarm vaak meer tekst. Het aantal vragen, woorden of gebruikte seedtermen is geen maat voor het ontstaan van nieuwe mogelijkheden.

## Wat dit wel en niet betekent voor de oorspronkelijke these

Een kandidaat met gewicht nul kan duidelijk beïnvloeden waar een model vervolgens naar kijkt. De batterijkandidaat laat dat in deze proef zien. Maar een *andere richting* is nog niet hetzelfde als een *voorheen onbereikbare relatie*. De horizoncontrole laat juist zien dat een sterke gewone onderzoeksarm zelf op de beperking kan stuiten. De placebo laat zien dat het afwijzen van een ongefundeerd verband ook een goede uitkomst kan zijn.

**Niet aangetoond:** dat het model deze relaties onmogelijk zelfstandig had kunnen genereren; dat een verschuiving in de volgende antwoorden een structurele verandering van de mogelijkhedenruimte is; dat een originele weight-zero seed via TrTL of de Validation Gate is gepromoveerd; dat er echte technische oorzaken bij een bestaande meetboei zijn ontdekt. De fictieve casus bevat geen echte spanningsmetingen of opgeslagen beelden waarmee die oorzaken geverifieerd kunnen worden.

**Wat verder onderzocht moet worden:** of twee onafhankelijke, geblindeerde lezers binnen de tweede vervolgbeurten *inhoudelijk andere en weerlegbare* relaties vinden die de andere armen niet op gelijkwaardig niveau formuleren, zonder dat de seed simpelweg wordt herhaald. De twee beoordelingspakketten en hun gescheiden sleutel zijn hiervoor gemaakt. Tot die beoordelingen binnen zijn is deze tekst een niet-geblindeerde, beschrijvende analyse. Voor generalisatie buiten deze meetboeicasus zijn later meer onafhankelijke situaties nodig.

## Over de twee reviewpakketten

Iedere beoordelaar krijgt dezelfde oorspronkelijke hostgeschiedenis, drie herhalingen per onderzoeksmoment en de twee vervolgantwoorden per track, maar **geen** modelarm, acceptatiestatus of ontblindingssleutel. De beoordelingsvragen gaan over een nieuwe toetsbare relatie, herhaling, een ongerechtvaardigde aanname en aanwezigheid in de gewone voorgeschiedenis. De twee beoordelingen moeten afzonderlijk en vóór ontblinding worden ingevuld. Er staan nu nul ingevulde oordelen in.

## Openbare bron versus auteursarchief

De publieke [concept-PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) bevat de experimentcode, offline tests, de oorspronkelijke onderzoeksvraag als verwijzing, het protocol, een openbare bronsamenvatting en het archief van de uitgevoerde workflow. De tijdelijke actieve startworkflows zijn na de succesvolle run verwijderd. De 48 volledige modelantwoorden, de bronarchieven en de RSA-privésleutel blijven buiten de openbare repository. Het versleutelde Actions-artifact verloopt op **4 november 2026**; een auteursexemplaar is daarom afzonderlijk bewaard.

*Deze notitie vervangt de bestaande preprint niet. De bevindingen kunnen na onafhankelijke beoordeling als afzonderlijke, afgebakende pilot worden opgenomen.*
