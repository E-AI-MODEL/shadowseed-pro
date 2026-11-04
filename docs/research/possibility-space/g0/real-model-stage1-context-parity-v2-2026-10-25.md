# V2-correctie vóór de volgende GPT-5-verkenning

> 25 oktober 2026. **Opgesteld na inzage van v1-resultaten.** Dit is een aparte, post-hoc **verkennende** methodecorrectie, niet een preregistratie die achteraf als vooraf vastgesteld wordt voorgesteld. G0 blijft **NOT PASSED**. V1 ([run #40215854335](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40215854335), exact commit `89d8a0f3e3817618b07b2bbc58e53028112c0150`) wordt ongewijzigd bewaard.

## Gerechtvaardigde reparatie

De v1-host ontving de complete fictieve startcasus op T0. De bestaande detector kreeg alleen het losse vraagzinnetje en het zichtbare hostantwoord. Hij kon dus iets als ontbrekend markeren terwijl het in de voor het hostmodel beschikbare casus wél stond. Bij de administratieve controle gebeurde dat aantoonbaar met het getal twintig.

Voor **v2** krijgt de *bestaande* `ShadowseedEngine.prepare_turn` op **T0** ook de volledige oorspronkelijke casusbeschrijving en de vraag als één feitelijke gebruikersinvoer. De bestaande `OpenAIDetectorBackend(current_pair)` krijgt daardoor dezelfde casuscontext als de host. Voor latere beurten gelden nog steeds de bestaande maximale schone gesprekscontext en de nieuwe waarnemingen per beurt. Dit maakt T0 gelijkwaardiger, niet de hele context over alle turns identiek.

Geen nieuw geheugen, geen extra detectorrol, geen gewijzigd promptcontract, geen ingreep in normalization, Gate, SSOT, TTL/TrTL, weight of point-of-use.

## Wat gelijk blijft

- Twee **publieke**, door onderzoekers geschreven fictieve casussen, vier echte Engine-beurten, eerste echte geboorteregistratie, latere gewichtloze checkpoints en zelfstandige NONE-control Engine.
- GPT-5-host, GPT-5-detector met de bestaande `current_pair`-prompt, `text-embedding-3-small`; alle ruwe tekstrecords en werkelijk voorkomende afwijzingen behouden.
- 20 geplande modelverzoeken, harde bovengrens 24, maximaal 48 embeddingverzoeken en 85.000 geregistreerde tokens; geen automatische retries.
- Vragen en externe waarnemingen blijven inhoudelijk identiek aan v1. Ook het minder geschikte administratieve negatieve geval, inclusief de vraag naar wat nog onbekend is, blijft staan zodat er niet stiekem naar een gewenste uitkomst wordt herschreven.

V2 zal verschillen door nieuwe generatie-uitkomsten en de andere contextinformatie voor de detector. Zelfs bij een lager aantal valse voorstellen kun je dat **niet causaal aan alleen de contextwijziging** toeschrijven zonder een gecontroleerde replay van dezelfde hostantwoorden en sampling.

## Wat de vergelijking wel kan leren

De onafhankelijke registratie maakt zichtbaar: API-modelrespons, detectorvoorstel, NONE/afwijzing, eerste echte seedgeboorte, ongewijzigde candidate-identiteit, het verloop over aparte turns en eventuele geblokkeerde Gate-besluiten. Het is toegestaan dat ook de administratieve casus seeds produceert. De telling is geen effectmaat voor Q1 of Q2.

Nog steeds **niet** onderzocht: interne niet-gekozen representaties, kandidaat-specifieke latere onderzoeksrichtingen, onafhankelijke betekenisbeoordeling, sterke kosten-gelijke controlearms en een algemene tweede-orde onderzoekstoets.

**Stopcriterium:** geen gepubliceerd G0-PASS, geen late 'novelty' uit voorgescripte vragen, geen positieve seedautoriteit of gewone antwoordinvloed. De eerdere v1-fout blijft zichtbaar en telt als methodische les, niet als weggepoetste mislukking.
