# Legacy SSOT: inspectiedossier vóór een eventuele herkwalificatie

> 25 oktober 2026 | Concept, opvolger van [PR #243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243). Geen productie-migratie, geen vrijgave van oude seeds en geen bewijs voor G0, Q1 of Q2.

## Waarom niet simpelweg opnieuw verifiëren?

De oorspronkelijke SSOT-route gebruikte vectorovereenkomst en een bronlabel `verified` om **SSOT SUPPORT** naar de bestaande Gate te sturen. Zo kon een fictieve, ontkennende bron een onbewezen seed helpen promoveren. [De oorspronkelijke run #40176388209](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209) laat dit als daadwerkelijk softwaregedrag zien.

PR #243 houdt de bekende automatische route nu voor **nieuw point-of-use-gebruik** tegen. Die blokkering heeft bewust geen terugwerkende kracht. Het oude gewicht blijft in de geschiedenis staan. Een nieuwe `supports`-beoordeling bovenop dat gewicht maakt de vorige bewijsbasis niet alsnog betrouwbaar.

Een losse tekst `reviewer="mens"`, een nieuwe bron-URL, een hogere similariteit of vier gekopieerde bronnen zijn geen herstelbesluit. Ook een gewone `evidence.verify`-indiening kan op zichzelf geen historische basis ongeldig maken. Autorisatie van een operator is iets anders dan de inhoudelijke juistheid of onafhankelijkheid van bewijs.

## Wat dit voorstel toevoegt

Er komt één **deterministisch, alleen-leesbaar inspectiedossier** per seed, gebaseerd op de al opgeslagen seed-snapshot, Gate-events en point-of-use-records.

`build_legacy_ssot_review_dossier(seed, gate_events, influence_records)`:

- Gebruikt dezelfde herkenning van de **bekende foutieve automatische SSOT-producer** als `AgentSafetyContract`. Die herkenning ziet `verified SSOT chunk ...`, `::chunk_...` en de onveilige `relation-attested:ssot:...`-tussenvorm. Dit zijn historische *herkomstsignaturen*, geen bewijs dat alle overige SSOT-signalen authentiek zijn.
- Bewaart de oorspronkelijke volgorde, Gate-event-ID's, policies, beslissingen, versies, geregistreerde gewichten en SHA-256 van de aangeleverde eventgegevens. Een gewichtsverschil binnen één Gate-event mag **niet** uitsluitend aan één SSOT-signaal worden toegeschreven als dat event meerdere signalen bevat.
- Toont de geclaimde verificatie en onafhankelijkheid van de oude signalen, nadrukkelijk als **geclaimde vlaggen**. Zonder terugvinden en inhoudelijk beoordelen van de bron wordt geen van die vlaggen als betrouwbaar verklaard.
- Telt eerder opgeslagen gebruiksbesluiten, inclusief vroeger `allowed=True`, zonder die besluiten achteraf te herschrijven. Een oud toegestaan antwoord blijft historisch geregistreerd; dat is geen toestemming voor een nieuw antwoord.
- Gebruikt standaard alleen digests voor bronnamen en vrije toelichtingen. Een vertrouwde lokale beoordelaar kan `include_source_refs=True` gebruiken om de originele bronverwijzingen op te zoeken. Dit is geen nieuwe publieke autorisatie-interface.
- Geeft altijd `review_state=not_requalified`, `requalification_performed=False`, `source_to_seed_truth_checked=False`, `actor_identity_checked=False` en `independence_verified=False` terug. De functie geeft **geen** `allowed` of `authorized` resultaat.
- Verandert geen seed, Gate-event, weight, trace, TTL, TrTL, bronrecord, logboek of point-of-use-beleid. De dossierhash is een **ongekeyde inhoudshash**, geen handtekening en geen onafhankelijk bewijs dat opgeslagen data waar of ongewijzigd zijn.

De lokale toegang loopt via `InspectionService.legacy_ssot_review_dossier` en `WorkbenchController.legacy_ssot_review_dossier`. Die methoden inspecteren bestaande sessiegegevens en sturen niets naar de Gate.

## Voorgestelde vervolgstappen voor een echte herkwalificatie

Dit is een **ontwerpkader, geen geïmplementeerde vrijgave**:

1. **Identificeer de oude bron.** Haal de historische `source_ref`, exacte bronversie en het bewijs achter de verwijzing op. Een hash bewijst alleen dat gegevens overeenkomen met een vastgelegd fragment, niet dat het fragment uit de gestelde bron afkomstig is.
2. **Beoordeel de precieze seed.** Leg vast of de bron werkelijk *de specifieke open vraag, hypothese of what-if* ondersteunt, tegenspreekt, alleen raakt of niet kan toetsen. Zonder die relatie is er geen SSOT SUPPORT. Beoordeel ook eventuele tegenpassages, gewijzigde documenten en bronafhankelijkheden.
3. **Controleer de beoordelaar.** Gebruik de bestaande productafgeleide `ActorContext` met passende workspace-scope en `evidence.verify`. Een vrij tekstveld is geen geauthenticeerde actor. Het productieledger moet de latere beslissing, basis, bronversie en aanvraag-identiteit atomair vastleggen.
4. **Houd nieuw bewijs los van oud gewicht.** Een historische promotie blijft in quarantaine. Er is nog geen geaccepteerde Gate-migratie die besmette gewichtsopbouw kan vervangen zonder de geschiedenis te wijzigen. Gebruik geen `unsafe_set_authority`, metadatavlag, exception of nieuw `supports`-label als vrijgaveschakelaar.
5. **Beslis over een versiegebonden, toetsbare migratieroute.** Voordat invloed mogelijk wordt, moet expliciet vaststaan hoe een nieuwe, zelfstandige bewijsbasis wordt aangelegd en hoe de eerdere Gate-autoriteit daarvan is afgescheiden. Een **nieuwe, weightless seed-identiteit met gedocumenteerde herkomst** kan een onderzoekbare optie zijn, maar mag geen stilzwijgende kopie van oud gewicht of bewijs worden. Dit is nog geen gekozen productimplementatie.
6. **Test tegen oneigenlijk herstel.** Herhaal dezelfde bron in verschillende kanalen, verander tekst of digest na beoordeling, gebruik een verkeerde workspace-scope, herhaal dezelfde request-ID en laat een reviewer een vals `supports`-label aanbieden. Niets daarvan mag de oude quarantaine automatisch opheffen.

De bestaande [actor-autorisatie](../../../architecture/production-actor-authorization.md), [migratieregels](../../../architecture/production-migration-policy.md) en [ADR-004](../../../architecture/adr/ADR-004-evidence-identity-and-independence.md) blijven leidend. Een latere autorisatie- of migratiewijziging moet een **eigen ontwerpbesluit, testset en releasecontrole** krijgen.

## Wat de tests wel en niet bewijzen

De nieuwe modelvrije tests toetsen: echte Gate-historie, dezelfde diagnose uit objecten en JSON, oude toegestane gebruiksrecords, afscherming van bronidentificaties, een wijzigende inhoudshash bij gewijzigde eventgegevens, een herkenbaar oud tussensignaal, afzonderlijke onderzoeksbronnen, ongeldige historische invoer en Workbench-toegang zonder mutatie.

De tests leveren **geen** onafhankelijke bronbeoordeling, geen herstelbare productie-migratie, geen verdedigbare wetenschappelijke autoriteitsmaat en geen Q1/Q2-uitkomst. De bestaande meerturns-shadowroute blijft ongewijzigd. Ook wordt geen extra model, tweede Gate, nieuwe toolautorisatie, sleutel of netwerkdienst toegevoegd.

**Mergegrens:** deze inspectie kan los worden beoordeeld op correcte read-only werking. Een herstelknop of automatisch wissen van `legacy_ssot_requires_review` hoort er nadrukkelijk niet bij.
