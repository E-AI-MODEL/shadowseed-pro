# V2-contextgelijkheid: uitvoeringspoging, geen vergelijkingsresultaat

> 25 oktober 2026. Dit verslag is geschreven na de tweede poging. G0: **NOT PASSED**. Het is nadrukkelijk geen effectmeting of semantische beoordeling.

## Herleidbare status

- Eerste proef met de oorspronkelijke onderzoeksadapter: [run #40215854335](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40215854335) is **geslaagd**; 20 echte GPT-5-responses, 19 embeddings, 36.998 geregistreerde tokens. De ruwe data staan in het artifact `real-model-stage1-exploratory-40215854335`. [Analyse en geconstateerde contextasymmetrie](real-model-stage1-observations-2026-10-25.md).
- Eerste v2-Action-opstart: [run #40216656716](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40216656716), **mislukt vóór de API-modelaanroepen**. De workflow gebruikte per vergissing het v1-fixturepad, terwijl de runner het v2-schema vereiste. Daarom geen v2-modelobservaties.
- Gecorrigeerde v2-Action: [run #40216755879](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40216755879), commit `66c89e606cc67c66f46606fd3d27a424e144a528`. **Offline-preflight geslaagd.** De live-run stopte na **drie echte GPT-5-responses**, totaal **5.079 providergerapporteerde tokens**, zonder embeddings of detectoruitvoer.
- De twee gewone T0-voorbeelden op de meetcasus waren `completed`; het daaropvolgende **hostantwoord T0** kreeg `status=incomplete`. De runner was ingesteld op `max_output_tokens=1600`. De API-status alleen bewijst niet waardoor de output onvoldoende werd; beschikbare redenen zijn onvoldoende zichtbaar in het bewaarde foutmanifest. De runner stopte zonder verborgen retry zoals bedoeld.
- Het foutartifact `real-model-stage1-v2-context-parity-40216755879` registreert alleen een beperkte foutstatus en tellers, geen afgeronde turns. De nageschakelde effect-/autoriteitschecks zijn overgeslagen omdat de run geen volledig resultaat opleverde.

**Geen v2-vergelijking mogelijk.** De vraag of contextgelijkheid het aantal schijnbaar ontbrekende kandidaten verlaagt, staat nog open. De gebruiker, onderzoeker of rapportage mag uit de gestopte run geen 'minder seeds' afleiden: de detector heeft nul beurten *bereikt*, niet nul kandidaten *gevonden*.

## Welke reparatie is nodig voordat v2 opnieuw zinvol is?

Voeg in een afzonderlijk versiegebonden voorstel een iets ruimere outputlimiet of robuuste behandeling van onvoltooide outputs toe, met een nieuwe no-networktest waarin `status=incomplete` expliciet voorkomt. Houd hetzelfde kostenplafond en nooit een automatische of onzichtbare retry aan. Maak de volledige responsstatus, gebruikte tokenbudget en stopreden zichtbaar in **een vertrouwelijk auditrecord** zonder secrets. Een nieuwe betaalde proef vraagt een nieuwe expliciete one-shot begrenzing; hergebruik de bestaande workflow niet stilzwijgend.

Het oorspronkelijke v1-onderzoek blijft onafhankelijk controleerbaar en laat zien dat de echte, gewichtloze pijplijn technisch over meerdere turns werkt. V2 heeft de eerdere inhoudelijke meetfout **nog niet getest**. Q1/Q2, G0-v3 en onafhankelijke review blijven open.
