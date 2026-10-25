# Echte GPT-5 RF-vraagproef: detector stelde voor, T0-intake weigerde alles

> **25 oktober 2026. Na uitvoering opgesteld.** [GitHub Action #40220605205](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40220605205), broncommit `b074a36c6c26c328a22d0970127d006a95218d96`. Ruwe `observed.json` in artifact `real-seed-rf-inquiry-40220605205`. **G0 NOT PASSED. Geen Q1-/Q2-effect aangetoond.**

## Uitvoering en echte uitkomst

- Alle offline tests geslaagd, inclusief canonieke meerturn-Engine, no-network-API-test en `NONE`/geen-seed-stopregel.
- **9 echte GPT-5 Responses-aanroepen**, provideridentiteit `gpt-5-2025-08-07`; **6 embeddings**; **19.787 providergerapporteerde tokens**. Alle modelresponsstatussen waren `completed`; geen API-retries of incomplete outputs.
- Eén door een onderzoeker geschreven, publieke fictieve meetcasus. Drie echte opeenvolgende host-/detectiebeurten in één `ShadowseedEngine`. Elk gewoon hostantwoord bleef vrij van seedcontext. De tweede expliciet lege detector-Engine kreeg dezelfde hostantwoorden.
- De detector gaf **drie voorstellen per beurt**, de parser herkende alle negen. De **bestaande** intake accepteerde op T0 **nul** voorstellen, op T1 **twee** en op T2 **één**. Alle zes afwijzingen kregen de bestaande registratie `not_atomic`. De T1/T2-seeds zijn werkelijk geboren en traceerbaar, maar **niet vooraf geselecteerd als D-kandidaat**.

| Meetpunt | T0 | T1 | T2 |
| --- | ---: | ---: | ---: |
| Echte detectorvoorstellen | 3 | 3 | 3 |
| Via canonical intake geaccepteerd | **0** | 2 | 1 |
| Intake `not_atomic` | **3** | 1 | 2 |
| `seeds_born_weightless` | 0 | 2 | 1 |
| A/B/C/D/E-modelonderzoeksvragen | **0** | **0** | **0** |

**De vooraf bepaalde proefregel was dat de eerste canoniek geaccepteerde T0-seed in de echte Engine moest ontstaan.** Zo'n seed ontbrak. Daarom stopte de latere vijfarmige onderzoeksvraagvergelijking correct als `completed_no_seed_no_q2_opportunity`. De latere T1/T2-seeds achteraf aanwijzen als de gewenste T0-kandidaat zou selectie op de uitkomst zijn en is **niet** gebeurd. Een no-opportunity-status is geen `NONE`-antwoord van het model: de detector had wel negen kandidaten opgesteld.

## Lezing van de drie T0-afwijzingen

De inhoud van de T0-items is in het originele artifact behouden. De volgende analyse gaat over de **bestaande lexicale toelatingsregels**, niet over semantische kwaliteit.

1. De eerste kandidaat noemt een mogelijk verschil tussen interne sensormeting en logging, dat pieken in slechts één kanaal kan **veroorzaken**. De Nederlandse `is_atomic_seed`-filter uit `src/shadowseed/intake.py` zoekt via `term in lowered` onder meer de brede term `oorzaken`. Die tekenreeks komt letterlijk voor **binnen het werkwoord `veroorzaken`**. Dat is een concrete vormafhankelijke reden voor afwijzing, zonder dat de kandidaat aantoonbaar meer dan één onderzoeksrichting heeft.
2. De tweede kandidaat noemt verschillende manieren waarop kanaaltoewijzing of data-integriteit een schijnverschil kan creëren. Een komma en ` of ` voldoen samen aan de historische `has_many_separators`-afwijzing, ongeacht of de varianten bij één overkoepelende onderzoeksrichting horen.
3. De derde kandidaat wijst op ontbrekende statuslogs om uitschieters aan regelkastgebeurtenissen te kunnen koppelen. Een komma en ` of ` bij `schakel- of bedrijfsstates` veroorzaken dezelfde structurele afwijzing. Ook dit kan inhoudelijk één onderzoeksrichting zijn.

De drie feitelijke afwijzingen zijn **geen onafhankelijke beoordeling van atomiciteit**. Evenmin bewijzen deze voorbeelden dat alle drie inhoudelijk goede seeds zijn. De eerste logische vervolgstap is een **geblindeerde beoordeling van ruwe T0-kandidaten vóór én na intake**, naast negatieve voorbeelden en echte samengestelde onderzoeksvragen. Pas dan kan een mogelijke aanpassing van de filter overwogen worden.

De opvallende observatie is dat **de LLM wel relaties formuleerde**, terwijl een externe structuurfilter geen T0-onderzoekskandidaat toeliet. De mislukte Q2-proef mag dus niet als bewijs voor een onvermogen van het model worden gepresenteerd.

## Waar dit de oorspronkelijke these raakt

Q1 (niet-gekozen maar bereikbare relaties): er is zichtbaar gedrag, geen directe meting van interne representaties of kansen. Er waren twee gewone T0-samples vóór detectie; te weinig om afwezigheid of zeldzaamheid te schatten. De inhoudelijke betekenis van de drie voorstellen moet onafhankelijk getoetst worden.

Q2 (ontstaan van latere onderzoekbaarheid): **niet getest**. De code heeft correct geen vijf onderzoekscondities geactiveerd, geen vragen laten ontstaan en geen onderzoekshandelingen uitgevoerd. Een later geboren T1- of T2-seed toont alleen het bestaande registratiepad, niet eigen invloed op nieuw onderzoek.

## Wat niet stilzwijgend aangepast wordt

Geen promptverlenging om een gewenste kandidaat te forceren, geen heretikettering van T1 als T0, geen second-chance-seedgeboorte, geen verzwakte Gate, geen nieuwe manager, geen gewichts-, TTL- of TrTL-wijziging, en geen productfix die als experimenteel bewijs wordt verkocht.

**Afzonderlijk opvolgbesluit:** lees alle ruwe T0-voorstellen blind met een expliciete atomiciteitsrubric (één toetsbare vraag versus verschillende zelfstandige vragen). Bepaal daarna prospectief een nieuwe onderzoeksopzet die ook een T1-eerste geboorte kan meenemen, mits minstens twee **latere** echte beurten beschikbaar zijn. Het feit dat T1 in deze openbare case wél twee seeds opleverde is een **ontwikkelbeperking**, geen held-out effectbewijs en geen reden om de oude run opnieuw te labelen.
