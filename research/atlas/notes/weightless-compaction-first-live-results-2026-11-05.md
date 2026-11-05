# Eerste echte ShadowSeed-proef bij OpenAI-contextcompressie

**Uitgevoerd 5 november 2026.** [GitHub Actions #41981167823](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41981167823), artifacts `weightless-compaction-live-20261105` (ID `13394475903`). Deze analyse is na de run geschreven. Geen blinde onafhankelijke beoordeling.

## Wat daadwerkelijk is uitgevoerd

GPT-6.1 Sol genereerde per casus drie hostantwoorden. De echte product-API `ShadowseedEngine.prepare_turn / observe_turn` zag elk van die antwoorden. De canonieke `current_pair`-detector en parser werkten met GPT-4.1; de engine gebruikte `text-embedding-3-small`, de bestaande `evidence_backed`-Gate en de gewone seed-intake. De engine gaf **geen seed aan het hostmodel** mee en de seeds bleven zonder bewijs en met gewicht 0.

Daarna vond per casus één echte `client.responses.compact`-aanroep plaats. De provider leverde een opaque `compaction`-item, naast drie berichtitems. Alle vervolgvarianten kregen dezelfde oorspronkelijke geschiedenis in hun `full`-groep, of hetzelfde ongewijzigde provider-compaction-object in hun `provider_compacted`-groep.

Er volgden drie condities in elke contextgroep, ieder als eigen stateless Responses-aanroep: `regular`, `reflect` en `weightless_review`. Alleen de derde kreeg bij een **afzonderlijke fictieve onderzoeksvraag** de weightless kandidaatteksten te lezen. Die kandidaatteksten kregen geen productbevoegdheid.

## Meetresultaten

| | PANELEN | BIBLIOTHEEK |
|---|---:|---:|
| Onafhankelijke gevalscontexten | 1 | 1 |
| Hostbeurten | 3 | 3 |
| Zelfstandig gevonden, bewaarde seeds | **8** | **7** |
| Gewicht / extern bewijs bij alle seeds | **0 / 0** | **0 / 0** |
| Werkelijke provider-compactions | **1** | **1** |
| Vervolgaanroepen | **6** | **6** |
| Reguliere voortzetting met volledige context: inputtokens | 1.633 | 1.086 |
| Dezelfde met provider-compaction: inputtokens | **1.127** | **826** |
| Invoerafname bij reguliere vervolgvraag | **31,0%** | **23,9%** |

Totaal: **54 echte API-aanroepen** (6 host, 6 detector, 28 embedding, 2 compaction, 12 vervolg), geraamde kosten **$0,119797** binnen de vooraf ingestelde grens van $0,50. Bij beide compactions waren de uitvoertypen `message, message, message, compaction`. De originele providerontvangstbewijzen en checksums staan in het artifact.

## Inhoudelijk: zonnepanelen

De gewone voortzetting (volledige en gecomprimeerde context) stelde een gecontroleerde vergelijking voor tussen omvormers met verschillende firmwarestatus en schaduwblootstelling. De reflectiecontrole kwam grotendeels met dezelfde aanpak en wees daarnaast op de mogelijkheid dat firmware **registratie** beïnvloedt zonder dat de opbrengst verandert.

De `full/weightless_review`-conditie stelde als eerste toets een **onafhankelijke energiemeter** voor om registratieverschillen van werkelijk productieverlies te scheiden. Dat is een afwijkende, uitvoerbare onderzoeksrichting. De `provider_compacted/weightless_review`-conditie bleef dichter bij de firmware-versus-schaduwvergelijking, maar vroeg waar mogelijk ook om firmware-onafhankelijke energiemeting.

Een interessante waarneming, maar geen aangetoonde unieke ontdekking. Registratieproblemen waren ook door de gewone reflectiecontrole herkend, en de afzonderlijke kandidaatprompt had meer inhoud. Bovendien kwam de scherpste afwijking uit de **volledige** context, niet uit de gecomprimeerde. Deze twee outputs bewijzen dus geen herstel van verloren context door compressie.

## Inhoudelijk: bibliotheek

De detector bewaarde onder andere vragen over bereik van nooit-bezoekers, zakelijke toon versus nieuwsgierigheid, en leesbaarheid. Toch bleven alle zes openingsteksten grotendeels zakelijk en informerend. Er ontstond geen verhalende, uitgesproken unieke tekst in de weightless-conditie. De varianten verschillen wat in formulering, maar er is geen overtuigend nieuw stijleffect aangetoond.

## Betekenis en grenzen

**Uitvoering: geslaagd.** Dit is voor het eerst binnen deze reeks een end-to-end combinatie van echte productseedgeboorte, gewichtloos bewaren, een échte OpenAI-compaction en gepaarde modelvervolgen.

**Inhoudelijk effect: open.** Eén onderscheidende onderzoekstoets in één conditie is geen bewijs van verbetering. De reflectiecontrole vond al een verwant probleem. Het experiment bevat slechts twee oorspronkelijke casussen, één traject per conditie en geen onafhankelijke beoordelaars.

**A/B-kwaliteit:** De calls waren afzonderlijk, stateless en kwamen per geval uit dezelfde vastgelegde geschiedenis. Toch verschillen `reflect` en `weightless_review` bewust in instructies en informatieomvang. Dit meet het effect van **extra geheugeninformatie in een onderzoeksprompt**, niet geïsoleerd de softwarematige seedstatus en niet onafhankelijk van extra tokens. De zes antwoorden per casus zijn geen zes onafhankelijke gevallen.

**Wat we niet kunnen zien:** Het compaction-object is versleutelde/opaque providerstate. De kleinere inputtokentelling is concreet, maar zegt niet welke gedachte de provider intern heeft weggelaten, behouden of herwogen. Modelparameters veranderden niet. De detector zag zichtbare tekst, geen verborgen redeneringsverdeling.

**Aanscherping voor volgende proef:** herhaal met méér onafhankelijke gesprekken en een geblindeerde, inhoudelijke beoordeling. Voeg een gewone-notitieconditie toe met **dezelfde kandidaattekst en hetzelfde tokenbudget** als de weightless-conditie, zodat het verschil tussen bewaren als record en tonen als gewone herinnering wordt getoetst. Laat de onderzoeksrol apart, zodat een gewichtloze hypothese geen gewone antwoordautoriteit krijgt. Gebruik langere gesprekken waarin een beperkt contextbudget plausibel relevante informatie verdringt.

De ruwe sourcefiles mogen niet worden herschreven om het resultaat achteraf mooier te maken.
