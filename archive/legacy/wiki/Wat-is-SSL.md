# Wat is SSL

> Status: actueel (4.6). Canonieke bron: `docs/00_shadow_seed_learning_4_6.md`.

## In één zin

Shadow Seed Learning is een mechanisme waarmee een taalmodel kleine
structurele afwezigheden in een antwoord detecteert, die opslaat als
gewichtloze shadow seeds, en alleen gevalideerde seeds gebruikt om
vervolgvraag, retrieval of falsificatie gerichter te maken.

## Wat het niet is

- geen nieuw foundation model en geen modeltraining
- geen poging om "meer context" toe te voegen

Het is een evaluatie- en navigatielaag bovenop een bestaand model.

## De mechanische kern

1. **Atomische seed** — precies één klein, toetsbaar, ontbrekend punt. Brede
   of vage "categorieën" worden geweigerd of gesplitst (zie
   `docs/02_atomic_seeds.md`).
2. **Twee velden** — `trace` meet aanwezigheid (start 2.0, vervalt),
   `weight` meet invloed (start 0.0).
3. **Levenscyclus** — NEW → ACTIVE → DECAYING → DORMANT → PROMOTED of EXPIRED.
4. **Validation Gate** — promotie vereist herhaalde herkenning, externe
   evidence én afwezigheid van contradictie. Pas daarna stijgt `weight`.
5. **Probes** — een gepromoveerde seed kan een betere vervolgvraag, een
   gerichtere retrieval-query of een falsificatiepoging sturen.

## Waarom dit niet naïef is

`weight = 0` betekent: de seed stuurt nog niets. Een seed moet zich eerst
bewijzen via de Gate voordat hij het antwoord mag beïnvloeden. Dat scheidt
"iets opmerken" van "er iets mee doen" — precies wat een naïeve
"voeg-meer-toe" aanpak mist.

## Verder lezen

- [Huidige Evidence-Status](Huidige-Evidence-Status) — wat hiervan vandaag bewezen is
- [Reproduceren](Quick-Start) — zelf draaien
- Achtergrond en eerdere uitwerkingen: [Archief](Archief)
