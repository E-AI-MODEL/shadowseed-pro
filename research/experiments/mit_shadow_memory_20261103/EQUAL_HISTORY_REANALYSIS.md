# Gelijke MIT-voorgeschiedenis: gecorrigeerde meetuitkomst

De GitHub Actions-proef [41733092646](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41733092646) is technisch geslaagd. De oorspronkelijke score voor het gewone model was **onjuist** door een parserfout. De bewaarde ruwe uitvoer uit artifact [13278407931](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41733092646/artifacts/13278407931) is opnieuw beoordeeld zonder de modellen nogmaals te draaien. Ook de 85 originele MIT-hypotheses uit de eerdere replay zijn gebruikt om de gekozen historische beurt te controleren.

| MIT-checkpoint | ShadowSeed kiest uit vroegere clusters | Gewone Qwen kiest | Qwen benoemt het verband |
| ---: | ---: | ---: | --- |
| 26 | 13 | 19 | SAME_CLAIM |
| 60 | 13 | geen geldig oordeel (alleen `NONE`) | niet beschikbaar |
| 100 | 20 | 21 | SAME_CLAIM |
| 121 | 54 | 48 | SAME_CLAIM |
| 142 | geen kandidaat boven drempel | 21 | SAME_CLAIM |

**Gecorrigeerde aantallen:** 5 checkpoints, ShadowSeed 4 met een kandidaat, Qwen 4 geldige verwijzingen, 1 ongestructureerde onthouding, 0 dezelfde eerste eerdere beurt. De eerdere bewering dat Qwen 0/5 geldige antwoorden had, vervalt.

**Wat de ruwe antwoorden vertellen:** Qwen gebruikt `PICK: t019` in plaats van `PICK: 19`; de oorspronkelijke parser weigerde het voorvoegsel `t`. De andere drie verwijzingen hebben dezelfde vorm. De parser op de onderzoeksbranch is aangepast zodat `tNNN` wordt geaccepteerd. Een los `NONE` blijft *ongestructureerd*: er is geen relatiecategorie of toelichting, dus dat wordt niet als geldig negatief oordeel bijgeteld. De offline-heranalyse is getest met vier geslaagde regressietests in de werkcontainer. Dit is **geen nieuwe GitHub-modelrun**.

**Inhoudelijke grens:** de gewone AI kiest herhaaldelijk `SAME_CLAIM` waar verschillende ingrepen, doses of uitkomsten worden besproken. De beschikbare teksten ondersteunen dan eerder 'verwant, maar verschillend'. Dat is een brongebonden zelfbeoordeling, geen onafhankelijke, blinde annotatie. Een ShadowSeed-cluster signaleert semantische samenhang, maar bewijst evenmin identieke causale hypotheses of onafhankelijke bevestiging.

**Onderzoeksgrens:** beide methoden zagen alleen voorafgaande bronhypotheses; hun werkwijze verschilt wel. ShadowSeed zoekt in semantisch opgeslagen clusters en Qwen kiest uit een uitgeschreven lijst. Deze vijf retrospectief gekozen checkpoints zijn niet voldoende om te bepalen welke methode beter onderzoek mogelijk maakt. Er is geen nieuwe MIT-gewichtsproef uitgevoerd en geen wetenschappelijke nieuwheid aangetoond.

**Besluit:** behoud de werkende ShadowSeed-clustering en de huidige Gate. Meet bij een vervolg apart: vindbaarheid van een verband, type relatie, bronherkomst en of de verbinding een nog niet uitgevoerde toets oplevert. Laat de beoordeling blind en onafhankelijk uitvoeren. Geen merge van deze onderzoeksbranch naar `main`.

Bronversies: MIT `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`; ShadowSeed product-`main` `7427181c50fabae8f9cbd112c3e549e752edf914`.
