# Conceptueel overzicht

> Status: achtergrondmateriaal. Gebruik voor de actuele repo-status eerst [Home](Home), [Latest Test Results](Latest-Test-Results), [SSL 4.5 Analysis](SSL-45-Analysis) en [Dashboard](Dashboard). Deze pagina legt het basisidee uit, maar is niet de primaire statusbron.

Shadow Seed Learning 4.5 gebruikt ontbrekende structurele elementen als signaal.

Een modelantwoord kan correct klinken en toch een belangrijke relatie missen. SSL noemt zo'n ontbrekend element een **gap**. Als die gap klein, specifiek en toetsbaar is, kan hij worden opgeslagen als **shadow seed**.

## Shadow seed

Een shadow seed bevat precies één gap.

Voorbeeld:

```text
Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.
```

Niet goed:

```text
De tekst mist economische, sociale en koloniale context.
```

Dat is te breed en bevat meerdere gaps.

## Trace en weight

SSL scheidt aanwezigheid en invloed.

| Veld | Betekenis |
|---|---|
| `trace` | hoe sterk een seed aanwezig of opnieuw herkend is |
| `weight` | hoeveel invloed een seed mag hebben |

Een seed start met:

```text
trace = 2.0
weight = 0.0
```

Dat betekent: de seed is aanwezig, maar stuurt nog niets.

## Validation Gate

Een seed krijgt pas gewicht als hij gevalideerd is.

Minimale voorwaarden:

```text
occurrence_count >= 3
evidence_count >= 2
geen contradictie
```

Pas daarna stijgt `weight`.

## Promotie

Een seed wordt `PROMOTED` als:

```text
weight >= 0.5
```

In de huidige implementatie stijgt weight per geldige Gate-pass met `0.2`. Na drie geldige passes komt een seed dus op `0.6` en wordt promoted.

## Wat SSL niet is

SSL is niet:

- een nieuw foundation model
- training van modelgewichten
- simpelweg meer context toevoegen
- blind retrieval
- automatische waarheid

SSL is een toetsbare laag die afwezigheden volgt, valideert en pas daarna laat meewegen.
