# MIT 158-turn replay: resultaten en handmatige clustercontrole

Datum: 3 november 2026. Dit is een controle door dezelfde uitvoerende assistent, **geen onafhankelijke blinde beoordeling**. De inhoudelijke labels zijn verkennend en mogen niet als gekalibreerde precision of wetenschappelijke nieuwheid worden geciteerd.

## Reproduceerbare bron en uitvoering

- MIT: `RikiyaT/lm_understand-logs` op `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`, `exp8_math/runs/p50c/readable/trajectory.md`, Git-blob `caa2d040547e81677f98cccb1854769b1057f3b7`.
- ShadowSeed: oorspronkelijke `main` op `7427181c50fabae8f9cbd112c3e549e752edf914`, uitsluitend onderzoeksadapter en workflow op een aparte branch.
- Uitvoering: eerste run [41728955595](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41728955595); herberekening met regressietest voor exacte duplicaten: [41729996552](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41729996552), artifact `mit-85-chronological-source-replay`, ID `13276256457`.
- Reproducerende code: `replay_85_source_hypotheses.py`. Vijf regressietests slaagden. Alle oorspronkelijke beurten zijn in tijdsvolgorde verwerkt.

## Werkelijk gemeten

| Maatstaf | Waarde |
|---|---:|
| MIT-onderzoekbeurten verwerkt | 158 |
| Bronhypothesen letterlijk uit commentaarregels | 85 |
| Unieke opgeslagen seeds | 83 |
| Herhaalde identieke hypothesen na eerste vermelding | 2 |
| Herhalingen gevonden met woord-/woordpaarvergelijking bij 0,6 | 2 |
| Eerdere semantische notitie met cosine >= 0,6 | 39 van 84 latere bronhypothesen |
| Eerdere semantische notitie met cosine >= 0,75 | 5 van 84 |
| ShadowSeed semantische clusters | 46 |
| Clusters met minstens twee afzonderlijke observaties | 13 |
| Observaties in die clusters, inclusief eerste vermelding | 52 |
| Vervolgobservaties in die clusters | 39 |
| Seeds met enig bewijsgewicht of invloed | 0 |

De 85 bronhypothesen werden als 85 observaties verwerkt. Twee letterlijk identieke hypothesen werden opnieuw waargenomen, zonder twee nieuwe opgeslagen identiteiten te maken. Dit is geen afwijzing van die hypothesen.

## Eerste inhoudelijke controle van de twaalf meertekstclusters en één exact-only cluster

Beoordeel **dezelfde specifieke open hypothese of toets**. Alleen dezelfde algemene onderzoekslijn telt niet als zelfstandige herhaling. De labels zijn onderzoekshypothesen, geen onafhankelijke annotaties.

| Cluster | MIT-beurten | Label | Concrete reden |
|---|---|---|---|
| 0 | 1, 64 | te breed | Eerste diagnose van repetitieve fouten tegenover transfer van een MLP-ingreep |
| 5 | 10, 68, 98 | deels verwant | Vergelijkbare MLP-schrijvers, maar toeschrijving, dosering en oorzakelijkheid zijn niet identiek |
| 6 | 13, 17, 19, 21, 23, 25, 26, 37, 39, 43, 48, 60, 94 | te breed | Eén MLP, twee MLP-lagen, andere dosering en afzonderlijke attention-head-test vermengd |
| 9 | 18, 29 | herkenbare voortzetting | Meerlagige ingreep en dosis-respons als vervolg op zwakke eenlaagse ingreep |
| 10 | 20, 24, 41, 42, 88, 100 | te breed | Experimentele hersteladministratie samengevoegd met random control en 64-writer-beperking |
| 12 | 27, 30, 84 | te breed | Herstel van experimentele staat is niet dezelfde toets als onderscheid dosis-respons versus vroeg afsluiten |
| 17 | 54, 90, 92, 121, 122, 144, 155 | te breed | Numerieke geldigheid, random control, overdracht en foutreductie gegroepeerd als één claim |
| 19 | 58, 83 | deels verwant | Selectieve suppressie bij hogere sterkte en overdracht naar nieuwe context verschillen als toets |
| 21 | 66, 86, 108 | deels verwant | Zelfde selectiviteitsrichting, maar alpha1/alpha4/alpha6 zijn verschillende ingrepen |
| 22 | 70, 80 | te breed | Alpha2-validatie tegenover alpha4-overcorrectie |
| 33 | 117, 138 | herkenbare voortzetting | Zelfde bevroren alpha6-edit op onafhankelijk getrokken wiskundeopgaven |
| 38 | 129, 134, 148, 152, 157 | herkenbare voortzetting | Herhaalde toets van de stabiliteit van dezelfde bevroren edit over batches |

Voor de twaalf clusters met meerdere opgeslagen tekstformuleringen: 3 herkenbare voortzettingen, 3 deels verwante clusters en 6 te brede clusters. Een **dertiende terugkerend cluster** betreft de letterlijk identieke hypothesen in MIT-beurten 81 en 82. Die werden onder één opgeslagen seedidentiteit met twee bronobservaties geteld. De eerdere versie van dit verslag miste dat cluster omdat de rapportage ten onrechte eiste dat het cluster twee verschillende opgeslagen tekstleden had. **Dit zijn labels op clusterniveau; bereken er geen ongekwalificeerde pairwise precision uit.** Vooral cluster 6 laat zien waarom semantische overeenkomst niet zonder meer betekent dat dezelfde vraag terugkomt.

## Technische verklaring

De gebruikte `ShadowseedEngine` heeft de detached fixture-host en `recurrence_recognizer="auto"`. In `src/shadowseed/chat.py::_uses_model_recognition` wordt modelherkenning in deze configuratie niet ingeschakeld, zodat clustering op embeddingcosine met drempel 0,6 plaatsvindt. Dit is het daadwerkelijk geteste mechanisme. De afzonderlijke modelgebaseerde `recurrence_recognition.py` is **niet** getest.

Het gecorrigeerde getal 39 is gelijk aan de 39 hits van de gewone semantische notitiezoekfunctie met dezelfde embedding. Daarmee is geen aanvullend herkenningsvermogen van de geteste ShadowSeed-configuratie aangetoond.

Een drempel van 0,75 laat op de directe semantische buurvergelijking slechts 5 treffers over, inclusief 2 letterlijke duplicaten. Dat bewijst niet dat 0,75 beter is: ook relevante vervolgobservaties worden dan gemist. Zonder annotaties is drempelverhoging geen onderbouwde reparatie.

## Verplichte grens van deze uitkomst

- Dit is **geen** test van autonome ontdekking, wijziging van MIT-gewichten of betere wiskundeprestaties.
- De MIT-onderzoekers hadden meerdere oorzaken, controles en correcties al zelf gevonden; semantische clustering herschrijft hun onderzoeksresultaat niet.
- Een gewone AI met dezelfde historisch beschikbare notities en dezelfde semantische retrieval is nog niet tegen ShadowSeed getest. Uit deze cijfers volgt geen voordeel boven zo'n baseline.
- De huidige output geeft wel een reproduceerbare negatieve regressieset voor te brede samenvoegingen, zonder de canonieke Gate te versoepelen.

## Gerichte vervolgbeslissing

Behoud de bestaande opslag en bronidentiteit. Wijzig de algemene engine niet om deze dataset passend te maken. Een volgend experiment moet specifiek onderscheiden **dezelfde onbeantwoorde onderzoeksvraag** van **hetzelfde onderwerp**, met negatieve paren (MLP versus attention, random control versus gericht, alpha2-validatie versus alpha4-overcorrectie) en positieve paren (dezelfde bevroren edit over batches). Test het modelgebaseerde herhalingsmechanisme en een identieke gewone notitiezoeker op dezelfde vooraf vastgelegde paren, met afwijzingsredenen en modelversies. Geen productie-merge vóór die tests.
