# Shadow Seed Learning — het verhaal, de wetenschap en het pad vooruit

> Status: current · Datum: 2026-07-07
> Dit document vertelt het hele verhaal van SSL voor een breed, tech-geïnteresseerd
> publiek: waar het vandaan komt, wat het is, wat er bewezen is en waar het heen
> gaat. Elke claim hierin is gedekt door de repo — de bronnen staan onderaan en
> de meetdossiers zijn openbaar. Voor de canonieke theorie:
> `docs/00_shadow_seed_learning_4_6.md`; voor de volledige bewijsweging:
> `docs/research/ssl-integrale-evaluatie.md`.

---

## 1. De vraag die bijna niemand aan een AI stelt

Vraag een taalmodel wat er in een tekst staat, en het antwoordt indrukwekkend
goed. Vraag het wat er **ontbreekt**, en het valt door de mand.

Dat is geen mening — het is gemeten. De AbsenceBench-studie (Fu et al., 2025)
gaf de sterkste modellen ter wereld een origineel document én een versie
waaruit bewust stukken waren geknipt, en vroeg: wat mist er? Zelfs
frontier-modellen haalden rond de 70% F1 op contexten van slechts 5.000
tokens. De verklaring zit diep in de architectuur: het attention-mechanisme
van een transformer kan aandacht geven aan wat er stáát, maar er bestaat geen
token voor een gat. **Een model kan niet kijken naar wat er niet is.**

Tegelijk is precies dát de vaardigheid die experts onderscheidt. De arts die
opmerkt welke vraag de patiënt níet beantwoordde. De beleidsadviseur die ziet
welk belang niet aan tafel zit. De docent die hoort welk begrip een leerling
overslaat. De waardevolste informatie in professioneel werk is vaak de
afwezige.

Shadow Seed Learning (SSL) is een Nederlandse onderzoekslijn (H. Visser,
EAI) die uit deze observatie is geboren, met één kernvraag:

> Kan een AI-systeem beter verder werken als het niet alleen kijkt naar wat
> er staat, maar ook systematisch vastlegt wat er structureel ontbreekt —
> zónder dat die vermoedens ongecontroleerd het antwoord gaan sturen?

De tweede helft van die zin is net zo belangrijk als de eerste. Daarover gaat
dit hele verhaal.

En SSL draait daarbij een aanname om die in de meeste literatuur impliciet
blijft. Vrijwel overal wordt een gap behandeld als een *probleem* — iets dat
weggewerkt moet worden. SSL leest hem als een **signaal van het model over
zichzelf**: hier had, op basis van alles wat dit model over de wereld weet,
iets moeten staan. Dat signaal is geen afval. Het is brandstof — de kortste
formulering van het hele programma:

> SSL gebruikt wat een model mist als startpunt voor gericht verder zoeken.

### Van 4.5 naar 4.6: hoe dit programma volwassen werd

Het verhaal heeft ook een eigen geschiedenis, en die is tekenend. De
4.5-specificatie legde de volledige mechaniek vast — twee-veld-architectuur,
levenscyclus, Validation Gate, probes — én formuleerde vooraf **twaalf
falsifieerbare hypotheses** (H1–H12): van "gewichtloze seeds verstoren de
basisprestatie niet" tot "de Gate halveert minstens de valse promoties
tegenover puur herhalingsgestuurde promotie". Geen visiedocument dat naar
succes toe schrijft, maar een programma dat vooraf opschreef waarop het
afgerekend wil worden.

De 4.6-canon veranderde vervolgens niets aan die mechaniek — hij verscherpte
de *epistemische positie*: vaste testscenario's tellen voortaan alleen als
regressielaag, en de hoofdclaim moet gedragen worden door open-set-kwaliteit,
adversariële controle, gemeten nut en domeintransfer. In de eigen woorden van
de canon: *4.5 beschreef vooral de mechaniek; 4.6 beschrijft dezelfde
mechaniek plus de evaluatiekoers die nodig is om geloofwaardig te worden.*
De secties hierna laten zien hoe die koers is uitgevoerd — meting voor
meting, inclusief de uitkomsten die tegenvielen.

## 2. Het idee in één beeld

Stel je een onderzoeksjournalist voor met een muur vol post-its. Elke post-it
is een vermoeden: *"niemand heeft de financiering gecheckt"*, *"de
tegenpartij is nooit gehoord"*. Die muur is goud waard — maar geen enkel
vermoeden mag de voorpagina halen voordat het geverifieerd is. Het verschil
tussen een goede journalist en een roekeloze zit niet in de muur; het zit in
de discipline tussen muur en voorpagina.

SSL bouwt die muur — en die discipline — in software:

- Een **shadow seed** is één klein, toetsbaar ontbrekend punt, opgemerkt
  tijdens het werk. De atomiciteitseis is hard, en het verschil is meteen
  voelbaar. Niet goed: *"security, privacy en schaalbaarheid ontbreken"* —
  dat is een analyseplan, geen seed. Wél goed: *"AVG-compliance bij de
  verwerking van medische hartslagdata."* Klein, specifiek, controleerbaar —
  een beoordelaar kan zeggen: klopt, klopt deels, of klopt niet. Brede
  detecties worden gesplitst of geweigerd vóór ze de schaduw in mogen.
- Elke seed heeft twee strikt gescheiden velden. **Trace** is aanwezigheid:
  hij vervalt met de tijd (TTL) en leeft op wanneer het gesprek het thema
  weer raakt (TrTL) — zoals een menselijke herinnering. **Weight** is
  invloed: die start op exact **0.0** en kan maar op één manier stijgen —
  door een expliciete validatietoets, de **Validation Gate**, te doorstaan.
- Een seed die de Gate passeert mag **gerichte vervolgactie** sturen — als
  potentieel, nooit als verplichting. De theorie kent daar drie vormen voor:
  de **Socratische probe** (een betere vraag stellen), de **retrieval-probe**
  (een smallere, scherpere zoekactie) en de **dialectische probe** (de eigen
  aanname proberen te weerleggen). Alle drie bestaan in de repo. Een seed
  die de Gate niet haalt, stuurt nooit iets.

Drie woorden vatten de doctrine samen, en ze zijn de harde kern van alles wat
volgt:

> **Gevonden ≠ waar ≠ sturend.**

Iets opmerken maakt het niet waar. En zelfs iets dat waar is, mag pas
meesturen als het die rol verdiend heeft én op het moment van gebruik opnieuw
gecheckt is.

## 3. Waarom de voorzichtigheid geen rem is, maar het product

Wie de SSL-repo doorleest, ziet een pipeline die zichzelf op elk punt
wantrouwt: gewichten die op nul beginnen, een Gate die promotie kan weigeren,
een contract dat op het gebruiksmoment nógmaals controleert, een audit-trail
die hard faalt wanneer een gewichtloze seed toch invloed blijkt te hebben,
en falsificatie als ingebouwde operatie — er is letterlijk een commando om
een gevalideerde seed alsnog te laten wegargumenteren.

Dat is geen overdreven voorzichtigheid. Dat is het product.

We leven in het tijdperk van AI-agents met geheugen. En geheugen dat
ongecontroleerd meestuurt is precies het mechanisme achter de pijnlijkste
faalwijzen van dit moment: een verkeerde aanname die blijft plakken, een
hallucinatie die in een notitie belandt en drie gesprekken later als feit
terugkeert. De meeste geheugensystemen voor agents kennen maar twee standen:
niets onthouden, of alles laten meewegen. SSL bouwt de derde stand — en dat
is de stand die schaalbaar vertrouwen mogelijk maakt:

> **Geheugen dat zijn invloed moet verdienen, en die invloed op elk moment
> kan verliezen — controleerbaar, replaybaar, falsifieerbaar.**

Wetenschappelijk rust dit op drie expliciete pijlers, plus een biologische
spiegel:

1. **Epistemische onzekerheid** (Kendall & Gal, 2017). De Bayesiaanse
   literatuur onderscheidt ruis die je niet kunt wegnemen (aleatorisch) van
   onzekerheid door gebrek aan kennis (epistemisch) — en alleen die tweede
   is reduceerbaar. SSL richt zich uitsluitend daarop, met een precieze
   draai: niet *"ik weet niet zeker of dit klopt"*, maar *"ik merk dat hier
   iets zou moeten staan dat er niet staat."* SSL is dan ook géén
   kalibratiesysteem en geen hallucinatiefilter — het is **epistemische
   zelfrapportage over structurele afwezigheid**.
2. **Computationele nieuwsgierigheid** (Schmidhuber, 2011). Nieuwsgierigheid
   is formeel de drang om de onzekerheid in de eigen kennisrepresentatie te
   verlagen. SSL implementeert daar een gedisciplineerde variant van: welke
   afwezigheid is het vaakst herkend, het sterkst bevestigd én het meest
   resistent tegen falsificatie? Díe verdient de vervolgactie.
3. **Active learning** (Settles, 2009). Een lerend systeem dat zelf bepaalt
   welke informatie het meest waard is om op te halen. In die taal: de seeds
   zijn de onzekerheidsrepresentaties, de probes zijn de queries, en SSL is
   de learner met een eigen query-strategie — op interactieniveau in plaats
   van trainingsniveau.

De biologische spiegel is het engram-onderzoek naar geheugenconsolidatie
(Josselyn & Tonegawa, 2020). Een verse herinnering is een fragiel spoor dat
alleen overleeft door reactivatie — precies de trace/TTL/TrTL-dynamiek. En de
neurowetenschap kent **reconsolidatie**: elke keer dat een herinnering wordt
opgehaald, wordt ze even kwetsbaar en moet ze opnieuw gestabiliseerd — wordt
ze weersproken, dan wordt ze bijgesteld. Dat is exact wat de contradictie-
check van de Gate doet. De claim is nadrukkelijk geen neurologische
gelijkwaardigheid; de claim is dat *fragiele kandidaat-representaties die via
validatie consolideren en daarna actief nieuw begrip sturen* een biologisch
beproefd ontwerp is.

De falsificatie-reflex is tot slot regelrecht Popperiaans: een claim telt pas
als hij een serieuze poging tot weerlegging heeft overleefd. En de
detectiekant bouwt voort op de gap-literatuur rond retrieval en
multi-hop-redeneren (Khot et al., 2019; Lewis et al., 2020) — met
AbsenceBench als het bewijs dat dit voor moderne LLM's een écht, onopgelost
probleem is.

### Hoe SSL zich verhoudt tot RAG, Reflexion en verwanten

De eerste vraag van elke technische lezer: *"is dit niet gewoon RAG?"* Nee —
en het vervangt RAG ook niet. SSL voegt een laag toe die geen van de
bekende systemen heeft: bijhouden welke kleine afwezigheden over meerdere
interacties relevant blijven, en daar pas na validatie op navigeren.

| Systeem | Wat het doet | Wat SSL anders doet |
|---|---|---|
| **RAG** (Lewis, 2020) | vraag → zoeken → antwoord | SSL detecteert wat de zoekactie *niet* activeerde |
| **Self-RAG** (Asai, 2023) | reflectie binnen één beurt | SSL werkt tussen beurten, met een levenscyclus |
| **FLARE** (Jiang, 2023) | lage zekerheid → bijzoeken | SSL detecteert structurele afwezigheid, geen lage confidence |
| **CRAG** (Yan, 2024) | zoekresultaten corrigeren | SSL zoekt exploratief, niet correctief |
| **S2G-RAG** (Li, 2026) | gap → direct vullen | SSL laat gaps bewust bestaan als gewichtloze plekhouders en valideert over beurten |
| **Reflexion** (Shinn, 2023) | reflecties sturen direct | SSL houdt observaties gewichtloos tot de Gate ze promoveert |
| **GapQA** (Khot, 2019) | ontbrekende kennis per vraag | SSL werkt niet vraag-specifiek maar over interacties heen |

Even belangrijk is wat SSL **niet** is: geen nieuw foundation-model, geen
permanent geheugen (alles is consolidatie, verval of falsificatie), geen
waarheidsmachine (seeds zijn hypotheses, promotie is omkeerbaar) en geen
prompt-trucje — het is een architecturale laag óp de bestaande
modelcapaciteit.

## 4. Het leven van één seed — het golden path

Dit is geen diagram op een whiteboard; het draait vandaag, in
`shadowseed chat`. Volg één seed door het systeem:

1. **Geboorte (gewichtloos).** In beurt vier van een gesprek over een
   gezondheidscampagne merkt de detectielaag op dat niemand het over de
   psychologische drijfveren van de doelgroep heeft. Er ontstaat een seed:
   klein, toetsbaar, `weight = 0.0`. Het antwoord van dat moment verandert
   er **niet** door.
2. **De schaduw.** De seed reist mee door een expliciete statusketen
   (`NEW → ACTIVE → DECAYING → DORMANT → PROMOTED of EXPIRED`), gedreven
   door twee spiegelbeeldige mechanismen: herkenning houdt hem in leven
   (TrTL), uitblijvende herkenning laat hem verdwijnen (TTL). Wordt hij
   nooit meer relevant, dan verloopt hij stil — en EXPIRED is terminaal:
   een afgeschreven seed komt niet terug. Aanwezigheid kost niets en stuurt
   niets.
3. **De poort.** Het gesprek komt terug op de doelgroep. De seed wordt
   aangeboden aan de Validation Gate: is dit punt houdbaar, relevant, niet
   strijdig met wat bekend is? Alleen bij een positief oordeel stijgt het
   gewicht. Dit is de enige route — er bestaat geen tweede manier om invloed
   te krijgen.
4. **De tweede sleutel.** Gevalideerd zijn is niet genoeg. Op het moment dat
   de seed een antwoord wíl meesturen, controleert het agent-contract
   opnieuw: gewicht > 0? Status PROMOTED? Promotie gelogd? Geen contradictie
   sindsdien? Elke poging tot invloed — geslaagd of geweigerd — staat in de
   audit-trail, en die trail is replaybaar: gewichtloze invloed laat hem
   hard falen.
5. **De bijdrage.** Nu pas weeft het model het punt in: het latere antwoord
   noemt de psychologische drijfveren die anders buiten beeld waren
   gebleven. Niet omdat een prompt het afdwong, maar omdat een gevalideerd,
   gecontroleerd geheugenspoor het aandroeg. In de blinde review van precies
   dit domein (round 029) kozen reviewers deze kant **3 van de 3 keer**, met
   het label "helpt duidelijk".
6. **De aanval achteraf.** Op elk moment kan `/falsify` de seed opnieuw voor
   het gerecht slepen: een model probeert hem actief weg te argumenteren
   tegen de bron. Wordt hij weerlegd, dan daalt het gewicht via de Gate en
   blokkeert het contract hem — zichtbaar in de audit.

Dat is het golden path: **van waarneming naar verdiende, verantwoorde,
herroepbare invloed.** Elke stap bestaat in code, is getest (354 tests in
CI) en is na te spelen.

## 5. De toetsing: zo streng als we hem konden maken

Een mooi mechanisme is nog geen bewijs. SSL hanteert daarom een
bewijsladder van zeven lagen (A t/m G), waarin elke laag een eigen vraag
beantwoordt en een sterke laag een zwakke nooit compenseert — er bestaat
bewust géén totaalscore. De lat per laag:

| Laag | Vraag | Stand |
|---|---|---|
| **A** Regressie | Blijft de kern mechanisch correct? | Sterk — CI-bewaakt, 354 tests |
| **B** Kleine benchmark | Werkt het op controleerbare casussen? | Bruikbaar, bewust smal |
| **C** Open-set kwaliteit | Zijn gevonden seeds goed op ónbekende tekst? | Echt maar gemengd — relevant, soms triviaal |
| **D** Adversarial | Weert de Gate misleidende seeds? | Eerste echte evidence — de Gate verslaat zwakkere baselines |
| **E** Payoff | Maken gevalideerde seeds vervolgwerk beter? | Mechanisme bevestigd; twee-assen-lezing hieronder |
| **F** Transfer | Werkt het buiten de bekende domeinen? | Voorzichtig positief over twee modellen |
| **G** Modelintern | Is er steun in de interne activaties? | Instrument gebouwd; drie eerlijke nulls t/m een NL-model (round 030) — vraag door naar grotere modellen |

Die ladder is bovendien geen achteraf bedachte ordening: hij toetst de
hypotheses die het programma vooraf formuleerde. Laag D meet letterlijk H11
("de Gate vermindert valse promoties tegenover puur herhalingsgestuurde
promotie") — bevestigd. Het "do no harm"-ontwerp van de payoff-metingen is
H2 ("gewichtloze seeds verstoren de basisprestatie niet"). En de hele
payoff-lijn toetst H6: iets meer werk in de vroege beurten, rijkere
antwoorden daarna. Vooraf opgeschreven, daarna gemeten.

De toetsmethode is zo streng als we hem konden maken:

- **Blinde A/B-reviews.** Reviewers zien twee antwoorden — met en zonder
  SSL — zonder te weten welke welke is. De antwoordsleutel zit in
  quarantaine tot ná de scoring, en de unblinding wordt onafhankelijk
  geverifieerd tegen de inhoud van de motivaties.
- **Adversarial druk.** De Gate wordt aangevallen met bewust misleidende
  lokaas-seeds (laag D).
- **Statistische controle.** De interne sonde (laag G) rapporteert nooit een
  scheiding zonder permutatietoets: klopt het "signaal" ook als je de labels
  husselt? Twee keer heeft dat instrument een veelbelovend ogend resultaat
  van ons eigen team afgeschoten. Dat is geen zwakte — dat is een instrument
  dat wérkt.
- **Falsificatie als feature.** De dialectische toets probeert gevalideerde
  seeds actief weg te argumenteren; bij twijfel valt het oordeel altijd
  terug op neutraal.

En het traject laat zien dat deze aanpak loont. De eerste blinde review op
veilige instellingen (round 022) kwam gespleten terug: reviewers waren het
op 7 van de 8 items oneens, en er zat ruis in gevalideerde seeds. In plaats
van dat weg te poetsen hebben we er een disciplinevraag van gemaakt —
wanneer mag een gevalideerde seed het antwoord sturen? Eén gerichte ingreep
later (maximaal twee seeds tegelijk, altijd als potentieel, nooit als
verplichting) steeg de reviewer-overeenstemming van **0.125 naar ~0.67**,
en in de transferronde daarna naar **~0.71** — terwijl de ruis vrijwel naar
nul ging. Dat patroon, zichtbaar leren van elke meting, ís de methode.

## 6. Wat de cijfers zeggen — en waarom je twee assen nodig hebt

Een blinde A/B-review dwingt een keuze af: antwoord A of antwoord B. Daar
rolt vanzelf een "win-rate" uit. Maar bedenk wat er vergeleken wordt: SSL
staat niet tegenover een zwak model — het staat tegenover **hetzelfde
frontier-model op z'n best**. Een 50/50-uitslag betekent daar niet "het
werkt niet"; het betekent "even goed, en soms opent het iets dat er anders
niet was". De vraag van de repo is dan ook nooit "wint SSL het gevecht?"
maar "**helpt SSL naar een beter antwoord?**" — en dáárvoor labelen de
reviewers elk item apart op seed-effect. Daarbij geldt: de seed hoeft niet
te winnen. Soms is het niks, soms ondersteunend, soms winnend — drie goede
standen. Alleen *hinderen* is fout, en dát is de metriek die omlaag moet.

Alle gecommitteerde blinde beoordelingen samen (rounds 022–031, 83 oordelen):

| As | Uitslag |
|---|---|
| Seed-effect: "helpt de seed naar een beter antwoord?" | **57 van 83 (~69%) "helpt"** |
| Waarvan expliciet "helpt duidelijk" | 33 van 83 |
| "Maakt geen verschil" | 13 van 83 |
| "Veroorzaakt ruis" of "vernauwt" | 13 van 83 — gelokaliseerd, zie onder |
| Head-to-head win-rate | ≤ 0.5 — tegen hetzelfde model op z'n best |

De ruis is niet willekeurig maar gelokaliseerd: drie gevallen vóórdat de
gebruiksdiscipline bestond (ronde 022), twee op vroege gespreksbeurten
(ronde 029), en acht in de discipline-hertest (ronde 031) — daar verdween
de vroege ruis, maar bleef één matig passende seed op latere beurten
herhaald terugduwen. Dat is de huidige, precies omschreven werklijst-post.
Nergens verzon een seed feiten: elke ruis-toelichting van reviewers
beschrijft afleiding of vernauwing, nooit fabricage.

De sterkste resultaten zijn bovendien geen toevalstreffers, maar een
patroon:

- **Op valkuil- en aanscherpingsvragen** — vragen waar een standaardantwoord
  te makkelijk is — koos de blinde consensus in de transferronde (round 025)
  **álle** keren voor de SSL-kant, en labelden beide reviewers het
  seed-effect **14 van de 14 keer** als "helpt".
- **Cross-domein en cross-model.** Hetzelfde patroon dat in de eerste
  domeinen werd gevonden, repliceerde blind in drie nieuwe domeinen
  (onderwijs, gezondheid, beleid) op gpt-4.1, en de kern ervan opnieuw op
  gpt-4o — waar het gezondheidsdomein 3/3 scoorde.

Eén zin, gedekt door alle data:

> **De seed helpt vaker dan hij de wedstrijd wint: in ~69% van alle blinde
> beoordelingen maakte hij het antwoord beter, hij verzon nooit iets, en bij
> sterke fit — de vraagtypes die om diepgang vragen — was hij unaniem de
> betere. Matig passende seeds die blijven terugduwen zijn de gemeten,
> gelokaliseerde zwakte waar nu aan gewerkt wordt.**

## 7. Waar we nu staan

- **De kern staat.** Lifecycle, Gate, contract, audit en falsificatie zijn
  gebouwd, getest en CI-bewaakt. De levende schaduwlaag is een werkende
  demo (`shadowseed chat`), inclusief brug naar retrieval (SSL→RAG): een
  gevalideerde seed kan een documentcorpus proben, waarbij "gevonden"
  expliciet aanwezigheid blijft en nooit vanzelf sturing wordt.
- **De payoff is gemeten, blind, over twee modellen en vier rondes** — de
  cijfers hierboven.
- **De modelinterne verkenning is een instrument geworden.** Zes iteraties
  in vijf dagen: van naïeve meting, via token-gerichte pooling en
  permutatiecontrole, naar een keten waarin gpt-4.1 houdbaarheidsoordelen
  velt en een klein model op die labels wordt gesondeerd — inmiddels ook
  gedraaid op een **Nederlands getraind model** met een 24-case set en een
  statistische vloer van 0.002 (round 030). De eerlijke uitkomst, drie
  runs op rij: kleine modellen (≤124M) coderen dat oordeel niet lineair —
  drie correcte nulresultaten die het instrument valideren en de vraag
  scherp doorgeven aan grotere modellen. Een team dat zijn eigen
  aantrekkelijkste hypothese drie keer durft af te wijzen, is een team
  waarvan je de positieve resultaten kunt geloven.

## 8. Het pad vooruit

**Nu direct (weken):**

1. **De vroege-beurt-discipline.** De laatste bekende ruisbron (seed-sturing
   op de openingsbeurt) dichten en blind hertesten — de aanpak die eerder de
   overeenstemming vervijfvoudigde, toegepast op het laatste gat.
2. **Derde model, meer items** voor de transferlaag, zodat "voorzichtig
   positief" kan doorgroeien naar "gerepliceerd, robuust".

**Daarna (maanden):**

3. **Generatieve seeds.** Van "dit ontbreekt" naar "dit zou er kunnen
   staan" — speculatieve seeds die per constructie door dialectische
   falsificatie moeten voordat ze ook maar in de schaduw mogen hangen.
4. **Interne steun (het H-neuron-spoor).** Recent werk identificeerde
   hallucinatie-geassocieerde neuronen in LLM's (Gao et al., 2025), met
   drie bevindingen die voor SSL direct relevant zijn: minder dan 0,1‰ van
   de neuronen volstaat om zo'n epistemische toestand te coderen; dat
   gedrag is bij te sturen door activaties te schalen zónder het model te
   hertrainen; en die patronen ontstaan al in de pretraining — de capaciteit
   zit dus in elk modern LLM. SSL stelt de spiegelvraag: waar H-Neurons
   pathologische activiteit *onderdrukt*, registreert SSL lege posities en
   vraagt of er een intern signaal bestaat voor de *houdbaarheid van het
   afwezige*. In de verre uitbouw is `weight` daar zelfs als
   activatie-schaling te interpreteren (het "niveau 2" uit de theorie).
   Het meetinstrument is gebouwd en drievoudig gevalideerd; de vraag staat
   klaar voor modellen van de orde waarop het precedent is gevonden.
5. **Zwaardere teksten.** Payoff meten op dichte, moeilijke documenten waar
   het gemiste punt echt pijn doet.

**De horizon:**

6. **De schaduwlaag als standaardcomponent.** Elke serieuze agent-stack
   heeft een geheugenlaag nodig die invloed laat verdienen in plaats van
   geeft. SSL is het bewijs dat zo'n laag bouwbaar, testbaar en auditeerbaar
   is. De theorie wijst zelf aan waar de waarde het grootst is: overal waar
   interacties zich over meerdere beurten uitstrekken en kleine
   afwezigheden herhaaldelijk relevant blijken — literatuurreview en
   onderzoek, langlopende juridische analyses, journalistiek, beleidswerk,
   code-review over sessies heen, diagnostische gesprekken. En onderwijs als
   geboortegrond en eerste toepassingsdomein: een systeem dat opmerkt wat
   een leerling of een les structureel overslaat, en dat vermoeden pas laat
   meewegen als het gevalideerd is.

## 9. Waarom dit ertoe doet

De AI-wereld lost het geheugenprobleem van agents op dit moment vooral op
met vertrouwen: onthoud alles, en hoop dat het goed gaat. Dat schaalt niet —
niet technisch, niet maatschappelijk en niet juridisch. Systemen die
beslissingen meesturen zullen moeten kunnen laten zien **waarom** iets
invloed had, **wanneer** dat gerechtvaardigd werd en **hoe** het herroepen
kan worden.

SSL levert daarvoor een werkend, gemeten antwoord uit Nederland: een
geheugendiscipline waarin elke invloed verdiend, gelogd, herspeelbaar en
falsifieerbaar is — en die in blinde toetsing laat zien dat discipline en
kwaliteit geen tegenpolen zijn, maar elkaars voorwaarde. De muur met
post-its én de verificatie vóór de voorpagina.

Wat er stáát is indrukwekkend, bij elk modern model. Wat er **ontbreekt** is
de volgende grens. Daar bouwen wij.

---

## Verder lezen

| Wat | Waar |
|---|---|
| Canonieke theorie (4.6) | `docs/00_shadow_seed_learning_4_6.md` |
| Volledige bewijsweging A–G | `docs/research/ssl-integrale-evaluatie.md` |
| Positionering: discipline als kern | `docs/research/positioning-synthese.md` |
| De levende schaduwlaag (demo) | `docs/research/shadow-chat-demo.md` |
| Modelinterne verkenning (laag G) | `docs/research/laag-g-scoping.md` |
| Alle blinde reviewrondes, ruwe data | `benchmarks/open_review/rounds/` |

## Referenties

- Fu, H. Y., Shrivastava, A., Moore, J., West, P., Tan, C., & Holtzman, A.
  (2025). *AbsenceBench: Language Models Can't Tell What's Missing.*
  arXiv:2506.11440.
- Gao, C. et al. (2025). *H-Neurons: On the Existence, Impact, and Origin of
  Hallucination-Associated Neurons in LLMs.* arXiv:2512.01797.
- Kendall, A., & Gal, Y. (2017). *What Uncertainties Do We Need in Bayesian
  Deep Learning for Computer Vision?* NeurIPS.
- Schmidhuber, J. (2011). *Formal Theory of Creativity, Curiosity and
  Intelligence.* IEEE Trans. Autonomous Mental Development.
- Settles, B. (2009). *Active Learning Literature Survey.* University of
  Wisconsin–Madison.
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for
  Knowledge-Intensive NLP Tasks.* NeurIPS.
- Asai, A. et al. (2023). *Self-RAG.* · Jiang, Z. et al. (2023). *FLARE.* ·
  Yan, S.-Q. et al. (2024). *CRAG.* · Shinn, N. et al. (2023). *Reflexion.* ·
  Li, M. et al. (2026). *S2G-RAG.*
- Khot, T., Sabharwal, A., & Clark, P. (2019). *What's Missing: A Knowledge
  Gap Guided Approach for Multi-hop Question Answering.*
- Josselyn, S. A., & Tonegawa, S. (2020). *Memory engrams: Recalling the
  past and imagining the future.* Science.

De volledige referentielijst met verwant werk staat in
`docs/08_referenties.md`.

## Claimgrens van dit document

Dit is een verhalend overzicht, geen meetrapport. Waar het cijfers noemt,
komen die uit de gecommitteerde rounds en de integrale evaluatie; waar het
vooruitkijkt, is dat richting, geen belofte. De doctrine geldt ook hier:
gevonden ≠ waar ≠ sturend — en enthousiasme ≠ bewijs.
