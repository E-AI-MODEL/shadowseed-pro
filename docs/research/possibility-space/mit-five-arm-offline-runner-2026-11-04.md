# Uitvoerbare vijfarmige RF-kalibratie

**4 november 2026. De synthetische proef draait; er is nog geen live-modelonderzoek uitgevoerd.**

De bestaande [MIT-preflight](mit-next-matched-pilot-2026-11-04.md) controleerde alleen het manifest. `research/scripts/mit_matched_runner.py` voert nu op een afzonderlijke synthetische casus daadwerkelijk T1 en T3 uit voor de vijf onderzoeksarmen A, B, C, D en E. Het programma gebruikt uitsluitend `FakeProvider`. Het accepteert **geen live provider** en heeft geen API- of netwerkfunctie.

## Wat er daadwerkelijk gebeurt

De runner leest `research/fixtures/mit_matched_runner_synthetic_v1.json` en controleert vóór de eerste aanroep de teksthashes van de gedeelde historie, beginvraag, latere waarneming en de bevroren kandidaat. Hij controleert ook of de vervangende notitie in E anders is, precies hetzelfde aantal synthetische woord-eenheden telt en niet in de gedeelde teksten voorkomt. De preflight controleert daarnaast de vastgelegde modelidentiteit, het tijdstip van kandidaat-geboorte, gelijke maximale model- en toolbudgetten, nul kandidaatgewicht en geen productbevoegdheid.

De vijf condities krijgen hun **eigen prompts**. In A staat alleen de gewone historie. B krijgt een expliciete aanwijzing om tegenverklaringen te zoeken. C krijgt normale onderzoeksnotities. D krijgt de onzekere bewaarde kandidaat en E een andere, even lange schijnnotitie. De latere RF-waarneming wordt pas na de eerste, geslaagde modelbeurt toegevoegd. Iedere arm gebruikt zijn eigen T1-antwoord bij T3. De uitvoervolgorde wordt per casus reproduceerbaar gehusseld.

Per aanroep legt de runner vast: het exacte promptbericht, de prompt-hash, de inhoud van het antwoord, parseerstatus, gebruikte synthetische woord-eenheden, gereserveerd budget en eventuele fout of afbreking. Technische fouten tellen **niet** als een inhoudelijk negatief oordeel. Er worden geen automatische retries verborgen. De artefacten zijn alleen voor de onderzoekseigenaar en worden als nieuwe bestanden met mode `0600` aangemaakt. De CLI weigert bestaande uitvoermappen te overschrijven.

Het synthetische model geeft voor alle armen dezelfde vaste reactie. Een verschil tussen armen wordt dus bewust **niet** nagebootst of als wetenschappelijk resultaat gepresenteerd.

## Reproduceerbare lokale controle

```bash
python3 -m pytest -q \
  research/tests/test_mit_matched_runner.py \
  research/tests/test_mit_matched_preflight.py

python3 research/scripts/mit_matched_runner.py \
  --input research/fixtures/mit_matched_runner_synthetic_v1.json \
  --output-dir /tmp/shadowseed-offline-$(date +%s)
```

In de lokale werkcontainer zijn **32 tests geslaagd**: 17 voor de uitvoerbare runner en 15 voor de bestaande preflight. Het demonstratieprogramma heeft vijf armen en per arm twee stappen volledig uitgevoerd, met **nul modelnetwerkcalls**. GitHub CI op de huidige commit moet apart worden gecontroleerd; een geslaagde lokale run bewijst niet dat alle bestaande repositorytests slagen.

## Grenzen die we bewust behouden

- Dit is **RF**, waarbij alle armen een identieke externe vervolgwaarneming ontvangen. Het is nog **geen RI-proef** waarin iedere arm zelf een instrument kiest en het echte gevolg terugkrijgt.
- De tijdschriften, kandidaattekst, bronherkomst en evaluatie zijn **synthetisch**. Er is geen bewijs dat de kandidaat daadwerkelijk door een ShadowSeed-detector is geboren of over meerdere echte modelbeurten is behouden.
- Synthetische **woord-eenheden zijn geen echte modeltokens**. Werkelijke budgetpariteit vereist een gemeten tokenizer en echte provider-usage.
- De controle op gelijk gewicht tussen D en E betreft lengte en gedeelde voorgeschiedenis, niet zelfstandig bewezen semantische gelijkwaardigheid van de schijnnotitie.
- Een echte runner heeft later een afzonderlijk geteste provideradapter, een bevroren modelversie, werkelijke resource accounting, een afgeschermde holdout en twee onafhankelijke G0-v3 ontwerpbeoordelingen nodig. Niet toevoegen via een stille fallback van deze kalibratie.

**G0: `NOT_PASSED`. Geen nieuw productgedrag, geen Gate-authorisatie, geen bewijs voor Q1/Q2 en geen automatische of betaalde proef.**