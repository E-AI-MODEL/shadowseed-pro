# Oorspronkelijke CSV-werkbestanden van de analyse

De bestanden in deze map zijn byte-identiek aan de drie op 4 november 2026 gemaakte onderzoeks-CSV's. Ze bevatten *afgeleide onderzoeksgegevens*, niet de ruwe modelantwoorden.

| Bestand | SHA-256 |
| --- | --- |
| `34_bevindingen_bronafhankelijkheid_2026-11-04.csv` | `b7c69246f5f7b3799db838506eba50ec96028fa9660a315d6f2e2caed4e56014` |
| `verbindingskaart_tussen_34_bevindingen_2026-11-04.csv` | `b3f7610a3862790da96041ef601c2fb58ea0bb5b070508198a5f9a564cdbe87d` |
| `24_trajecten_vergelijkingsmatrix_2026-11-04.csv` | `f5dec37fb3a878a5a381f24f49e39f0f1d35db624c93431b6df1a7f1ab78a50c` |

Het oorspronkelijke [48-call-archief](../../datasets/2026-10-28-q1q2-48/README.md) en de oudere [Git- en Actions-archieven](../../../docs/research/archives/2026-10-27/README.md) blijven ongewijzigd. Wijzig deze historische werkbestanden niet achteraf. Nieuwe inzichten krijgen een nieuwe gedateerde versie.

## Onderliggende trajectbeoordeling

De kruistabel met acht groepen is gebaseerd op twee aanvullende, ongewijzigd bewaarde werkbestanden:

| Bestand | SHA-256 |
| --- | --- |
| [T1/T2-teksten van 24 trajecten](24_trajecten_T1_T2_originele_teksten_2026-11-04.md) | `6c8a81c15b9267885cdd3d66a12c206e772c5f591a0d450b69654e4d99475dd3` |
| [Niet-blinde codering van de 24 T2-antwoorden](24_trajecten_T2_beoordeling_2026-11-04.csv) | `5fca4d676bb3b79022b420e399d976ef1de96a245f05115969146a78c9a4e42b` |

Het leesdossier neemt de 48 modelantwoorden over uit het eerder gepubliceerde bronarchief. De interpretaties en `delta_code`-labels zijn achteraf door de analyserende assistent toegekend. Dit is **geen** onafhankelijke of blinde beoordeling. De regressietests vergelijken de dossier-hashes met de 24 gecodeerde trajecten en tellen de acht aggregaten terug.
