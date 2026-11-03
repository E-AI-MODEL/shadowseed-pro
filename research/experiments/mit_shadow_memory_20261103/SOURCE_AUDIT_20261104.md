# MIT x ShadowSeed: broncontrole van de vijf checkpoints

**Status:** uitgevoerd op 4 november 2026. Dit is een eigen, niet-blinde broncontrole. Er heeft nog geen onafhankelijke blinde beoordeling plaatsgevonden.

## Uitkomst

Uit [GitHub-run 41733092646](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41733092646) kwamen vijf historische checkpoints en acht daadwerkelijk geselecteerde koppelingen tussen een huidige en een eerdere MIT-hypothese. Ik heb alle acht koppelingen opnieuw getoetst aan de [MIT-hypotheselog](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/readable/trajectory.md), de [experimentgeschiedenis](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/work_notes/experiment_history.md) en het [eindrapport](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/work_notes/final_report.md).

| Checkpoint | Eerder | Methode | Eigen oordeel | Wat MIT al wist of later zelf testte |
| ---: | ---: | --- | --- | --- |
| 26 | 13 | ShadowSeed | Verwant, verschillende ingreep | Een versus twee MLP-lagen; tweelaagse proef later uitgevoerd |
| 26 | 19 | Qwen | Verwant, verschillende ingreep | Eerder effect van enkele laag tegenover later voorstel voor twee lagen |
| 60 | 13 | ShadowSeed | Verwant, ander mechanisme | MLP tegenover attention-heads; head-attenuatie in t62/t63 getest, minder selectief |
| 100 | 20 | ShadowSeed | Verwant, verschillende ingreep | Vergelijking brede L19-ingreep met sparse top64-proef |
| 100 | 21 | Qwen | Verwant, verschillende ingreep | De current note stelt top64 al zelf voor; later verder getest |
| 121 | 54 | ShadowSeed | Alleen breed verband | Numerieke/attentioncontrole zegt weinig rechtstreeks over generalisatie |
| 121 | 48 | Qwen | Verwant, andere uitkomst | Dosis-effect tegenover bevestiging op onafhankelijke opgaven |
| 142 | 21 | Qwen | Verwant, andere foutcategorie | Minder looping tegenover overblijvende formatterings- en no-answer-fouten, al door MIT onderzocht |

**Mijn beoordeling:** 7 specifieke maar verschillende onderzoeksverbanden en 1 algemeen verband. Geen van de 8 koppelingen heeft aantoonbaar een nieuwe, nog niet door MIT onderkende proef opgeleverd. Dit is geen uitspraak over alle mogelijke vervolgexperimenten.

Opvallend zijn het verband van eenlaags naar tweelaags MLP-editing (t13/t26) en de overgang van MLP naar aandachtshoofden (t13/t60). Die verbanden zijn inhoudelijk nuttig. MIT heeft de betreffende vergelijking later daadwerkelijk onderzocht. Het identificeert een reeds zichtbaar spoor, geen nieuwe ontdekking die aan ShadowSeed kan worden toegeschreven.

## Blinde beoordeling voorbereid, nog niet uitgevoerd

Een apart reviewer-pakket bevat 14 geanonimiseerde paren: 8 modelgekozen koppelingen en 6 controles. De beoordelaar ziet alleen de oorspronkelijke teksten en scoort (a) zelfde claim, (b) verwant maar verschillend, (c) alleen breed onderwerp, (d) onvoldoende bewijs. De herkomstsleutel blijft buiten het pakket. Er is nog geen onafhankelijke beoordeling ontvangen en er is geen onafhankelijke accuratesse gemeten.

De lokale generator, broncontrole en anonimisering zijn met **6 geslaagde pytest-regressies** gecontroleerd. Die tests bewijzen de bestandsinhoud, chronologie en scheiding van labels, niet de kwaliteit van de relatieoordelen. De reproduceerbare pakketten zijn afzonderlijk als download in het oorspronkelijke gesprek beschikbaar.

## Gevolg voor ShadowSeed

Behoud de bestaande semantische clustering en Gate-beperkingen. Een inhoudelijk verband tussen verschillende hypotheses is niet per definitie een false positive. Bewaren, herhaling, onafhankelijke bevestiging en toegestaan gebruik blijven onderscheiden. Test pas een nieuwe model-gewichtsingreep nadat een onafhankelijke beoordelaar een concrete, niet eerder uitgevoerde vraag heeft aangewezen. Geen wijzigingen in de productcode en geen merge naar `main`.

MIT-broncommit `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`. Gebruikte ShadowSeed-hoofdversie `7427181c50fabae8f9cbd112c3e549e752edf914`.
