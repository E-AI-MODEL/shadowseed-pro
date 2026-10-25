# SSOT-relatiecontrole: een voorstel vóór de bestaande Gate

> 25 oktober 2026 | Onderzoeksvoorstel, géén productreparatie. Issue [#241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241). G0 **NOT PASSED**. Geen betaalde modelaanroepen, geen onafhankelijke menselijke beoordeling, geen gewijzigde productautoriteit.

## Wat de bestaande proef daadwerkelijk liet zien

De reproduceerbare modelvrije proef uit [PR #240](https://github.com/E-AI-MODEL/shadowseed-pro/pull/240) gebruikte de **bestaande** `SSOTManager`, `SSLManager` en Gate. Onder kunstmatig aangebrachte `verified`-metadata leverden zowel expliciet ondersteunende als ontkennende documenten dezelfde SSOT-`SUPPORT`-signalen op. De twee proefarmen bereikten gewicht 0,6 en `PROMOTED`. Niet-geverifieerde modelvoorstellen leverden geen SSOT-bewijs op. Dat is een echte software-observatie op **fictieve, door de onderzoeker geschreven bronnen**, geen onafhankelijke waarheidstoets.

De fout zit vóór de Gate: vectorovereenkomst wordt als inhoudelijke steun aangeboden. ADR-002 en ADR-004 laten dat niet toe. Een onderzoeksvraag of what-if kan ook door ontkennend materiaal geholpen worden bij het *onderzoek*, zonder daardoor bevestigd of gefalsifieerd te zijn.

## Wat deze branch toevoegt

`research/src/shadowseed_research/ssot_relation_preflight.py` legt een **voorlopig, strikt read-only** contract vast. Het gebruikt geen tweede Gate, geheugen, modelprompt of detector. Het schrijft geen gewicht, trace, status, bewijs, TTL of TrTL. De bestaande runtime onder `src/shadowseed/` blijft intact.

Een zoekresultaat en een relatieverklaring blijven gescheiden:

| Gegeven | Betekenis |
| --- | --- |
| Zoekscore en chunktekst | Een bron is gevonden; dit zegt niets over de richting van het bewijs |
| `status=verified` | Bestaande bronmetadata, géén zelfstandig bewijs dat deze bron de betreffende seed ondersteunt |
| Seed-ID en SHA-256 van de exacte seedtekst | De relatieverklaring hoort bij déze kandidaat in déze versie |
| Document- en chunk-ID plus SHA-256 van de exacte chunktekst | De relatieverklaring hoort bij déze bronpassage; gewijzigde tekst maakt de verklaring ongeldig |
| `source_unit_id` | Door een actor geclaimde herkomst-eenheid; meerdere chunks kunnen tot dezelfde bron behoren |
| `relation` | **Apart verklaard**, niet automatisch afgeleid: `supports`, `opposes`, `topical`, `undetermined` of `not_testable` |
| Verifier-IDs, tijdstip en motivatie | Traceerbare *verklaringen*, geen cryptografisch of onafhankelijk bewijs van de echte menselijke identiteit |

**Elke uitkomst heeft `gate_authorized=False`.** Ook `supports` is hooguit een kandidaat voor een *nog uit te voeren externe beoordeling*, geen autorisatie of bewijs. Ontbrekende, afwijkende of verouderde relatieverklaringen leiden tot geen mogelijke ondersteuning. Hetzelfde geldt voor alleen topicale, onbesliste en niet-toetsbare relaties en voor bronnen met niet-geverifieerde status. Een expliciete `opposes`-verklaring maakt **geen** automatische contradictie aan.

Bij conflicterende verklaringen over dezelfde geclaimde bewijs-eenheid voor **dezelfde seed** wordt de gehele eenheid voor ondersteuning stilgezet. Verschillende chunks van één bron worden niet als meerdere zelfstandige studies geteld. Verschillende seeds mogen uiteraard verschillende relaties met dezelfde bron hebben.

## Uitvoerbare controle, maar geen zelfstandig oordeel

`research/tests/test_ssot_relation_preflight.py` controleert ontbrekende en verlopen verklaringen, verplichte versiehashes, timezone, bronstatus, alle vijf relaties, identieke evidence-eenheden, conflicten en seedgebonden identiteit. Eén test haalt hits rechtstreeks uit de **echte SSOTManager**, met een **echte gewichtloze seed**, maar roept de Gate bewust niet aan. Daarmee is deze implementatie niet slechts een zelfgemaakt retrieval-algoritme.

Een bewuste negatieve test voert een **onwaarachtig als SUPPORT gelabelde ontkenning** in. De preflight kan die inhoudelijke leugen niet herkennen en geeft *voorlopig ter externe beoordeling* terug. Ze geeft **nooit** Gate-autorisatie. Dit toont wat de module **niet** doet: ze classificeert geen betekenis, kent geen bronwaarheid en bewijst geen onafhankelijkheid. Een LLM-oordeel, trefwoordenfilter of twee ingevulde namen zou deze grens niet opheffen.

## Nog te besluiten voor een echte reparatie

- **Betrouwbare attestatie:** wie mag de bron en de precieze seed-relatie beoordelen? Hoe wordt identiteit, bronauthenticiteit, onafhankelijkheid en herbeoordeling aangetoond?
- **Versiebeheer:** het prototype bindt seedtekst en chunktekst cryptografisch. Volledige documentversie, bewerking en migratie van bestaande `user_verified`-metadata zijn nog niet opgelost.
- **Bestaande API:** `validate_open_seeds_against_ssot` verhoogt nu in bepaalde omstandigheden autoriteit zonder zo'n relatieverklaring. Een omschakeling kan bestaande tests, productgebruik en opgeslagen data raken. Er is **geen stille omschakeling** doorgevoerd.
- **Semantische uitzonderingen:** een ontkennende bron kan relevant zijn voor een open vraag; de begrippen steun en tegenspraak vereisen een expliciete relatie tot de *oorspronkelijke epistemische kandidaat*. Bij conflict telt niet automatisch de meerderheid.
- **Bestaande Gate:** pas ná review mag een expliciet beoordeelde steunrelatie eventueel als getypeerd SSOT-signaal worden aangeboden. De Gate, bron-deduplicatie, autoriteitsregels en historische logboeken blijven hun bestaande eigenaar en contract behouden.

Een productfix vraagt een afzonderlijk besluit over migratie en regressies volgens [issue #241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241). De grotere onderzoeksvraag over nieuwe latere onderzoeksmogelijkheden, modelgedrag en Q1/Q2 is hiermee **niet** getest. Onafhankelijke beoordeling voor G0 blijft open in [#228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228), [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235).

## Herhaalbaarheid

Gebruik de huidige `main` en deze onderzoeksbranch in dezelfde omgeving. De nieuwe tests staan binnen de bestaande research-package-testset:

```bash
uv sync --frozen --extra test --extra build
uv pip install --python .venv/bin/python --no-deps -e ./research
uv run --no-sync python -m pytest -q research/tests/test_ssot_relation_preflight.py
```

De GitHub Actions-run na het openen van de PR moet werkelijk groen worden voordat de testuitvoering als gecontroleerd mag worden gemeld.
