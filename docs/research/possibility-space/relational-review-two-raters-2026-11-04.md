# Twee beoordelingen van 14 geblindeerde notitieparen

**4 november 2026. Onderzoeksnotitie, geen effectmeting of ontblinding.**

De oorspronkelijke 14 notitieparen zijn teruggevonden in het eerder aangeleverde beoordelaarspakket `shadowseed_mit_blind_review_for_reviewer.zip`. De bron bevat R01-R14 en geen toegang tot de verborgen methode-indeling in het beoordelaarsdeel. De verborgen toewijzing van kandidaatparen en controleparen is niet bekeken.

De eerste beoordelaar was `claude-sonnet-5-5 (blind, single pass)`. De gebruiker leverde daarna een verkorte tweede ronde aan, gevolgd door een **volledig ingevulde** zevenkoloms-CSV met `reviewer_id=blinded_reviewer_1`, motivering en tekstbewijs per rij. Die laatste versie vervangt voor de vergelijking de verkorte tweede ronde, maar blijft als correctie herkenbaar. De onderzoeksverantwoordelijke heeft de tweede beoordelaar persoonlijk gesproken en bevestigt dat deze **zonder voorkennis** heeft beoordeeld: geen inzage in de eerste beoordeling of de verborgen casusindeling. De beoordelaar wil anoniem blijven en wordt uitsluitend aangeduid als `blinded_reviewer_1`. Dit is een door de onderzoeksverantwoordelijke bevestigde onafhankelijke beoordeling; er is geen aanleiding zijn naam openbaar te maken.

Controleerbare SHA-256 van de afzonderlijke, hier niet meegestuurde bronbestanden:
- Eerste CSV: `11fcee0e85a93cbedd50670a8816867b906ec738fcf36e0efe07cf73adda2b44`.
- Volledig tweede CSV, letterlijk uit het gebruikersbericht: `166624be1caf438db901d3e7649db0d6f1eee0ed81fd3f00fb285a5fd8b7c220`.

## Verschillen per beoordelingsdimensie

| Veld | Eerste beoordeling | Volledige tweede beoordeling |
| --- | ---: | ---: |
| SAME_CLAIM | 1 | 1 |
| BROAD_ONLY | 4 | 1 |
| RELATED_DISTINCT | 9 | 12 |
| Bruikbaarheid 0 / 1 / 2 / 3 | 1 / 7 / 6 / 0 | 1 / 2 / 9 / 2 |
| Expliciete voorstellen voor een nieuwe test | 3 | 11 |

- Relaties gelijk bij **11/14**. Verschillen: **R02, R04, R13**.
- Bruikbaarheid gelijk bij **7/14**. Verschillen: **R02, R07, R08, R10, R12, R13, R14**.
- Wel/geen testvoorstel gelijk bij **6/14**. Verschillen: **R02, R03, R06, R07, R08, R12, R13, R14**.
- Alle drie gelijk bij **4/14**: **R01, R05, R09 en R11**.
- Beide beoordelaars noemen **R05, R10 en R11** een nieuw testvoorstel.

De expliciete waarde `none` in het tweede formulier betekent **geen nieuwe test**, niet een test genaamd "none". De onderzoeks-CLI heeft hiervoor een correctie en regressietest gekregen. Het eerdere rapport op basis van de verkorte tabel telde R09 als relatieverschil; in het volledige formulier staat R09 terecht als `BROAD_ONLY`. Dit is geen bevestiging van een wetenschappelijke uitkomst.

## Wat de verschillen betekenen

**R02 en R13:** de tweede beoordeling stelt voor bestaande methoden (disjuncte validatieset respectievelijk aandachtsdiagnostiek) op een latere claim toe te passen. Het eerdere bewijs laat niet zien dat deze nieuwe test al is uitgevoerd. Een methodische koppeling is nog geen extra causaal resultaat.

**R04:** de tweede beoordelaar ziet een specifiek methodisch verband rond het reconstrueren van de beste ingreep en het later geteste bevroren resultaat. Claude kwalificeerde die relatie als breed omdat de tekst de identiteit van beide ingrepen niet vastlegt.

**R08 en R10:** de tweede beoordeling geeft score 3 door concrete interventievergelijkingen, maar een meetbare uitkomst is niet hetzelfde als een reeds gemeten effect. De scorer moet de vergelijking en identieke experimentele condities expliciet vastleggen.

**R11:** beide formulieren suggereren een controle voor een ingreep op 64 neuronen. Norm-matched random richtingsverwijdering en random neuronselectie zijn niet vanzelf hetzelfde. Controleer de werkelijk toegepaste ingreep alvorens uit een controlegroep conclusies te trekken.

**R05 en R12:** vergelijk uitkomsten slechts als taakverzameling, model, versie, interventie en protocollen daadwerkelijk overeenkomen. Bij R05 is nog niet aangetoond dat de vroege 85/96-truncatiemeting en latere foutcategorieën dezelfde conditie beschrijven.

## Grenzen van de conclusie

Deze twee **ingevulde** formulieren zijn correct vergelijkbaar als annotaties. De oorspronkelijke paarteksten zijn beschikbaar en kunnen gecontroleerd worden, maar de onderzoeks-CLI voert geen semantisch expert-oordeel over die teksten uit. De onderzoeksverantwoordelijke bevestigt persoonlijk contact en beoordeling zonder voorkennis door `blinded_reviewer_1`. Een aanvullende identiteitsvraag is niet nodig. De publieke stukken tonen de beoordelingen en herkomstverklaring, maar bevatten bewust geen persoonsgegevens of externe identiteitscontrole. Meningsverschillen tussen beoordelaars zijn informatie over de beoordeling, geen score van ShadowSeed.

De formulieren meten niet of ShadowSeed de voorgestelde verbanden zelf heeft gevonden of beter presteert dan een model met gewone notities. De tweede beoordeling voldoet volgens de onderzoeksverantwoordelijke aan de voorwaarde van onafhankelijkheid en blinding. De volgende stap is de vooraf vastgelegde beoordelingsregels toepassen en de verborgen toewijzing alleen via de bevoegde onderzoeksbeheerder gecontroleerd openen. Voor een effectclaim blijft daarnaast een prospectieve vergelijking met gewone notities en een gerichte kandidaat-ablatie nodig.

**G0 blijft NOT_PASSED.** Geen extra autoriteit, nieuwe Gate of productwijziging.
