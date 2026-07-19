# Start hier

Deze pagina is de eenvoudige ingang voor nieuwe bezoekers van Shadow Seed Learning 4.5.

## Het idee in een paar regels

Een modelantwoord kan goed klinken en toch iets belangrijks missen.
SSL probeert dat gemis zichtbaar te maken.

Voorbeeld:

```text
Vraag: wat moet je juridisch meenemen bij een Nederlandse consument en een Amerikaanse webwinkel?

Mogelijke gemiste punten:
- rechtsbevoegdheid
- toepasselijk recht
- afdwingbaarheid van EU-consumentenrecht
```

SSL noemt zo'n gemist punt een seed.
Die seed krijgt niet meteen macht. Eerst blijft hij gewichtloos.

## Waarom dat belangrijk is

Een systeem dat elk gemis direct als waarheid gebruikt, wordt snel onbetrouwbaar.
Daarom gebruikt SSL twee aparte signalen:

- `trace`: iets lijkt terug te keren
- `weight`: het punt heeft genoeg validatie om echt mee te tellen

Pas na validatie via de Validation Gate kan een seed promoted worden.

## Wat je hier vandaag kunt zien

De repo laat nu vooral vier dingen zien:

1. de mechanische kern werkt
2. de standaard meetketen werkt
3. kleine benchmarklagen geven bruikbare signalen
4. aanvullende evidencelagen maken zichtbaar of de repo verder gaat dan alleen fixture- en scenario-smokes

## Welke resultaten zijn het belangrijkst?

Begin met:

1. [Latest Test Results](Latest-Test-Results)
2. [SSL 4.5 Analysis](SSL-45-Analysis)
3. [Benchmarks](Benchmarks)

## Hoe je resultaten moet lezen

Niet elke test zegt hetzelfde.

| Bewijssoort | Wat het zegt |
|---|---|
| regressie | de basis werkt nog |
| technische smoke | een route werkt technisch |
| methodologische smoke | de meetmethode blijft eerlijk |
| kleine benchmark | er is winst op een kleine vaste set |
| aanvullende evidencelaag | er is extra inhoudelijk bewijs buiten de kleinste basislaag |

## Wat je wel voorzichtig kunt concluderen

- SSL is meer dan een idee; de keten bestaat echt.
- De repo kan bekende gaps vinden en meten.
- De repo kan false positives proberen te blokkeren.
- De repo kan aanvullende bewijssoorten publiceren zonder alles op een hoop te gooien.

## Wat je nog niet te groot moet maken

- dit is nog geen brede algemene claim over alle modellen;
- dit is nog geen volledige open-set validatie;
- dit is nog geen bewijs van domeintransfer of modelinterne validatie.

## Samenvatting in een zin

SSL onderzoekt of een model beter kan worden door kleine, toetsbare afwezigheden veilig vast te leggen, pas na validatie mee te laten wegen, en daarna te meten of dat echt helpt.
