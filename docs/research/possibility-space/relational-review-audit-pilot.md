# Blinde beoordeling van verbanden tussen onderzoeksnotities

**Status: hulpmiddel voor gegevenscontrole, geen bewijs van effect.**

Een beoordelaar kan vastleggen of twee notities dezelfde bewering bevatten, alleen over hetzelfde onderwerp gaan of inhoudelijk verschillen maar samen een nuttige volgende vraag oproepen. Dat zegt op zichzelf nog niet dat ShadowSeed een nieuwe onderzoeksmogelijkheid heeft geopend.

## Waarom deze stap?

`src/shadowseed/recurrence_recognition.py` herkent terugkerende open vragen. Het bestaande G0-instrument `research/scripts/g0_blind_later_inquiry_review.py` kan latere onderzoeksvragen armgeblindeerd voorleggen. Daartussen ontbreekt een eenvoudige controle op volledig ingevulde, afzonderlijke *paarbeoordelingen* en op verschillen tussen twee beoordelaars. Dit script controleert alleen dat artefact. Het maakt geen eigen oordeel over de betekenis van de notities.

## Invoer en gebruik

Het script gebruikt de velden `case_id`, `relation`, `usefulness_0_to_3`, `specific_new_test_if_any`, `evidence_for_relation`, `reason_for_rating` en `reviewer_id`. Geldige relaties: `SAME_CLAIM`, `RELATED_DISTINCT`, `BROAD_ONLY` en `UNCERTAIN`. De beoordeling blijft leesbaar in het oorspronkelijke CSV-bestand. Het rapport bevat alleen tellingen, bestandsvingerafdrukken en eventuele meningsverschillen.

```bash
python research/scripts/audit_relational_reviews.py \
  --review /secure/blinded_review_form_completed.csv \
  --output /secure/review-audit.json

# Alleen na een werkelijk afzonderlijk ingevulde tweede beoordeling:
python research/scripts/audit_relational_reviews.py \
  --review /secure/reviewer-a.csv \
  --second-review /secure/reviewer-b.csv \
  --output /secure/comparison.json
```

Het programma gebruikt geen API, model, onderzoeksgeheugen of product-Gate. Het schrijft geen herleidbare notitieteksten naar de rapportuitvoer. Bestanden worden niet overschreven.

## Eerste waarneming, 4 november 2026

Op het aangeleverde CSV-bestand (SHA-256 `11fcee0e85a93cbedd50670a8816867b906ec738fcf36e0efe07cf73adda2b44`) zijn 14 beoordelaarsregels aangetroffen, allemaal van `claude-sonnet-5-5 (blind, single pass)`. Het bestand bevat één `SAME_CLAIM`, vier `BROAD_ONLY` en negen `RELATED_DISTINCT` beoordelingen. De bruikbaarheidsscores zijn respectievelijk 1 bij score 0, 7 bij score 1, 6 bij score 2 en 0 bij score 3. Er staan testvoorstellen bij R05, R10 en R11.

Dit zijn door een model ingevulde oordelen, geen onafhankelijke menselijke beoordeling of meting van een nieuwe latere onderzoeksmogelijkheid. Het oorspronkelijke geblindeerde paarpakket en de privé-mapping zaten niet bij deze CSV. **De inhoudelijke juistheid van de 14 koppelingen is hier niet gecontroleerd.**

## Nog nodig vóór een effectclaim

1. Leg de originele paarteksten, de geblindeerde presentatie en de privé-mapping veilig en gescheiden vast. Laat de blinde beoordeling onafhankelijk herhalen voordat de mapping zichtbaar wordt.
2. Controleer de drie voorgestelde tests op uitvoerbaarheid en vergelijking. R05 vereist aantoonbaar hetzelfde probleemmateriaal. R10 vereist per arm dezelfde meetmaat, dataselectie en budgetten. R11 vereist een controle die de *werkelijk uitgevoerde ingreep* spiegelt; een willekeurige richting is niet vanzelf hetzelfde als een willekeurige set neuronen.
3. Voer een prospectieve vergelijking uit met dezelfde modelversie en gelijke informatie: normaal antwoord, bewust verder zoeken, gewone notities, ShadowSeed-kandidaten en een exacte kandidaat-ablatie. Houd alle mislukkingen en onbesliste gevallen zichtbaar. Meet afzonderlijk de latere onderzoeksvraag en de feitelijk toetsbare vervolgstap.

Deze registratie mag de bestaande G0-veto's niet overschrijven. Het wordt geen tweede Validation Gate, geen bewijsgewicht en geen nieuw productiepad. Een nulresultaat of een even goede gewone-notitiesarm is een geldige uitkomst.

**Stopcriterium:** geen koppeling met originele paarteksten, gebroken blinding of ontbrekende gelijke controlemiddelen betekent geen interpretatie als effectbewijs. Eerst de meetopzet herstellen.
