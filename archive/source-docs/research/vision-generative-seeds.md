# Shadow Seed Learning — visie: de schaduw die meereist, van "kunnen staan" naar "moeten staan"

**Status:** richtinggevend visiedocument. Geen bewijs, geen evaluatieclaim. Het
scherpt de *bedoeling* van SSL aan en zet het pad uit naar wat de repo nog niet
kan. Bij botsing over mechaniek blijft `docs/00_shadow_seed_learning_4_6.md`
leidend; dit verfijnt het doelbeeld dat 00_ beschrijft, en steunt op de
theoretische fundamenten in 4.5 (`docs/legacy/00_shadow_seed_learning_4_5.md`,
§2 en §18).

> Ontstaan uit een gesprek (2026-06-14), na de eerste end-to-end payoff-meting
> (round 008). Het legt vast wat shadow seeds *uniek* maakt, omdat de huidige
> canon en evaluatiematrix in de praktijk op iets smallers optimaliseren
> (volledigheid) dan de visie vraagt — wat verklaart waarom open-set
> seedkwaliteit op "relevant maar triviaal" bleef hangen.

---

## 1. De kern: "wat had hier kúnnen staan", niet "wat had hier móéten staan"

De gangbare lezing van een gap is een **omissie**: een verwacht element dat
ontbreekt. Dat is completeness-toetsing — nuttig, maar klein. Het is ook wat de
detector tot v0.3g feitelijk deed, en waarom open-set seedkwaliteit op "relevant
maar triviaal" plateau bleef (round 005–007).

De eigenlijke ambitie is generatief:

> **Wat had hier kunnen staan** — een invalshoek, een kader, een relatie die het
> antwoord had kunnen optillen — en die misschien tot een beter antwoord leidt
> dan een LLM, óók met RAG, ooit zelf zou vinden?

"Moeten staan" is een checklist. "Kunnen staan" is de niet-genomen weg, de
aangrenzende mogelijkheid. Dat onderscheid bepaalt of SSL een
volledigheidscontrole is of een **navigatie-instrument**.

Dit rust direct op de drie theoretische pijlers van 4.5 §2:

- **Epistemische onzekerheid** (Kendall & Gal 2017): SSL meet de reduceerbare
  (epistemische), niet de aleatorische onzekerheid — "ik merk dat hier iets zou
  moeten zijn dat er niet is", geen confidence-score.
- **Computationele nieuwsgierigheid** (Schmidhuber 2011): een "kunnen staan" is
  de drang om de entropie in de eigen kennisrepresentatie te verlagen — actief
  zoeken naar wat de eigen onwetendheid reduceert.
- **Active Learning** (Settles 2009): het systeem bepaalt zélf welk ontbrekend
  punt het meest informatief is, en stelt dáár zijn vraag/retrieval/falsificatie
  op — in plaats van passief te wachten.

## 2. Waarom dit voorbij het RAG-plafond reikt

- **RAG haalt op wat bestaat en wat de query activeert** — antwoorden op vragen
  die je al kunt formuleren, uit een corpus dat al geschreven is. Bekende
  onbekenden. Het plafond van RAG is "alles wat vindbaar is".
- **Een shadow seed is de vraag die je niet wíst te stellen.** Hij ontstaat niet
  uit een query tegen een corpus, maar uit de *vorm van dít antwoord in de eigen
  latente ruimte van het model*. Daarmee zit hij **stroomopwaarts van RAG**: een
  seed kan de zoekopdracht genereren die RAG nooit had gevormd — dat is precies
  de Retrieval Probe (de seed stuurt de retrieval, niet andersom).

Het overschot is intrinsiek én contextueel: niet "wat zegt de encyclopedie dat
mist", maar "wat zegt mijn eigen representatie dat hier opvallend afwezig is,
juist hier". Geen externe index kent de vorm van díé afwezigheid. RAG *stapelt*
feiten; een goed geplaatste seed **herkadert** — en één herkadering kan een
antwoord meer optillen dan duizend opgehaalde feiten. (Vgl. 4.5 §19: SSL
detecteert wat retrieval níét activeerde; het vervangt RAG/FLARE/CRAG niet maar
ligt eronder.)

## 3. De unificatie: gewicht is de as van mogelijkheid → noodzaak

Het beslissende inzicht: "kunnen staan" en "moeten staan" zijn **geen twee
soorten seeds, maar dezelfde seed op verschillende punten van de gewichtsas.**

```
geboorte                                              consolidatie
"had hier KUNNEN staan"  ───── weight stijgt ──────► "moet hier staan"
weight = 0.0                   via de Gate            weight hoog
speculatief, in de schaduw     (herkenning +          gevestigd, mag sturen
kost niets als het niets is     evidentie +
                                overleefde falsificatie)
```

- Een seed wordt geboren als **mogelijkheid** — gewichtloos, in de schaduw.
- Naarmate hij validatie verdient (de Validation Gate), stijgt zijn gewicht.
- Bij genoeg gewicht is de mogelijkheid een **noodzaak** geworden: nu staat vast
  dat dit hoort, het *moet* er zijn.

Dit is precies de geheugenconsolidatie-dynamiek (Frankland & Bontempi 2005;
Josselyn & Tonegawa 2020; 4.5 §17): een fragiel kandidaat-engram dat via
reactivatie en hertoetsing consolideert, en daarna niet alleen sterker is maar
*actief nieuwe situaties helpt begrijpen*. De `trace`/`weight`/Gate-machinerie
die al in de repo staat **ís** deze mogelijkheid→noodzaak-motor.

**Gevolg voor de detector.** De `weight = 0.0`-geboorte is geen technisch detail
maar de vergunning om ambitieus te zijn: een speculatieve "kunnen"-seed kost
niets zolang hij niets is, en levert geen ruis op — hij wacht gewichtloos. Daarom
mag de detector generatief en gedurfd zijn; de gewichts- en Gate-laag sorteert
wel welke mogelijkheden uitharden tot noodzaak. De timide detector (alleen veilige
omissies → triviaal) was dus een *onderbenutting* van de architectuur, niet een
grens ervan. Kracht en discipline zijn dezelfde munt.

## 4. De schaduw die meereist: het gesprek als selectiedruk

De naam is een dubbelzin, en SSL gebruikt beide betekenissen tegelijk:

- **schaduw** — nog niet echt, latent, gewichtloos: het donkere wachten;
- **schaduwen** — volgen, meelopen, observeren: zoals een detective een
  verdachte schaduwt.

Een shadow seed met gewicht 0 **reist mee in het gesprek**. Hij verblijft
"waardeloos" in de vectorruimte, maar **schaduwt het echte antwoord** — en juist
door dat meelopen ontdekt hij, beurt na beurt, of hij potentie heeft. Hij is
geduldig én op zoek; en het geduld is de voorwaarde voor het ontdekken, want
gewichtloosheid maakt wachten gratis.

Dit beeld valt exact op de mechaniek (en is daarmee de operationele spec voor
wat de repo nog niet levend toont — zie gat 5):

| beeld | mechaniek |
|---|---|
| reist mee in het gesprek | leeft in shadow memory door de levenscyclus (NEW → ACTIVE → DECAYING → DORMANT), niet één keer beoordeeld en weggegooid |
| schaduwt het echte antwoord | elke beurt wordt zijn embedding tegen de nieuwe context gehouden (TrTL / cosine-match); drijft het gesprek zijn kant op → reactivatie, `trace += 2.0` |
| ontdekt zijn potentie | herhaalde reactivatie + externe evidentie + overleefde falsificatie → de Gate tilt `weight`; anders vervaagt `trace` → dormant → expired, kosteloos en geruisloos |

De diepe consequentie: **niet wíj beoordelen de seed bij geboorte — het gesprek
doet dat, over tijd.** Dat is de ontsnapping uit de round-007-val (te bang om
gedurfd te zijn → alleen triviale omissies). De gewichtloze, geduldige seed hoeft
het oordeel niet vooraf te vellen; hij stelt het uit aan de dialoog. **Het gesprek
zelf is de selectiedruk:** de goede seed wordt steeds opnieuw aangeraakt en groeit;
de lege vervaagt zonder iets te kosten. Tijd doet het werk dat een vooraf-oordeel
niet kan.

Twee gespiegelde mechanismen dragen die selectiedruk, recht uit
geheugenconsolidatie: **TrTL** (Trigger-to-Live) houdt een seed levend zodra het
gesprek hem herkent, en **TTL** (Time-to-Live) laat hem vervagen als die
herkenning uitblijft — tot **EXPIRED**, waarna hij terminaal verdwenen is. Een
gefalsificeerde of irrelevante seed zakt niet alleen in `weight` maar loopt ook
zijn TTL uit en kan niet terugkomen (geen reactivatie, geen Gate, geen
dedup-herleving). Zo is "kosteloos wachten" geen "eeuwig blijven hangen": de
schaduw die niets oplevert lost vanzelf en onomkeerbaar op. (Round 014 toonde
waarom dat moet: een slechte seed die tóch de revisie haalt, schaadt — dus de
veiligheid hoort in de levenscyclus vóór het handelen, niet in de revisiestap.)

## 5. Rugwind van binnenuit: H-neuronen en Niveau 2

SSL leeft nu op **Niveau 1**: een externe vectorruimte, waar `weight` de
retrieval-rangschikking stuurt. **Niveau 2** is modelintern (4.5 §16.2): `trace`
wordt activatiesterkte van gemarkeerde neurale posities, `weight` wordt de
α-parameter in activation-scaling — `weight = 0.0 → α = 1.0` (geen interventie),
`weight > 0 → α > 1.0` (versterking naar evenredigheid). Op Niveau 2 *ís* gewicht
dus letterlijk activatiesterkte: dezelfde "kunnen → moeten"-as, nu in neuronen.

**H-neuronen** (Gao et al. 2025) zijn het empirische precedent dat dat niveau
echt bestaat (4.5 §18): een spaarzame subset — minder dan 0.1‰ van de neuronen —
onderscheidt betrouwbaar feitelijk van gehallucineerd; je kunt erop ingrijpen
*zonder hertraining* (activation scaling); en het patroon ontstaat al in
pretraining, dus het zit in elk modern LLM. De pipeline is open en herbruikbaar
(github.com/thunlp/H-Neurons, MIT).

H-neuronen en SSL zijn **spiegelbeelden op hetzelfde substraat — het epistemische
zelfmodel:**

- H-neuronen: detecteer pathologische *aanwezigheid* (hallucinatie) → onderdruk de
  activatie, bínnen de beurt.
- SSL: detecteer structurele *afwezigheid* ("kunnen staan") → registreer
  gewichtloos, valideer, versterk, tússen de beurten.

Hetzelfde orgaan van zelf-herkenning, twee richtingen op. Daaruit volgt de
rugwind: naarmate de **eigen herkenning in het LLM beter wordt** — een reële
trend — werkt dat twee kanten tegelijk op:

1. **Meer potentie voor SSL.** Hoe scherper het model zijn eigen epistemische
   toestand intern kent, hoe betrouwbaarder het de "kunnen staan"-afwezigheden
   voelt. Detectie van de niet-genomen weg wordt minder gokwerk.
2. **Minder kans op hallucinatie, juist waar het ertoe doet.** Generatieve
   "kunnen"-seeds liggen dicht bij hallucinatie, dus de falsificatie-Gate (gat 4)
   moet streng zijn. H-neuronen geven een **modelintern falsificatiesignaal** in
   plaats van een lexicale check: de Gate kan van binnenuit zien of een
   speculatieve seed een echte latente mogelijkheid is of een verzinsel.

Dit keert de spanning om die in de naïeve lezing zit ("hoe generatiever, hoe
risicovoller"): de generatieve potentie en de hallucinatie-rem **schalen samen
mee** met modelverbetering. De trend van betere modellen is geen bedreiging voor
SSL maar rugwind — de "kunnen staan"-seed mag gedurfder worden omdat de interne
zelf-herkenning de misser opvangt. De falsificatie-Gate hoort dus uiteindelijk
**modelintern** te zijn; daar ontmoeten H-neuronen en de gewichts-as elkaar.

## 6. Wat hiervoor nog niet in de repo staat (het pad)

Oorspronkelijk geverifieerd tegen de code op 2026-06-14; **bijgewerkt
2026-07-04**. De repo bouwt de *toevoer en boekhouding* van seeds goed
(detectie, gewichtloze opslag, Gate, levenscyclus, constellations) plus een
losse, gewone RAG-pijplijn. De stukken die SSL *uniek en voorbij-RAG* maken zijn
inmiddels grotendeels gebouwd (zie de ✅-markeringen): items 1, 2, 4 en 5 staan
er; wat resteert is de echte SSL-vs-RAG head-to-head-run (item 3, gat 3) en een
plausibel model voor de Laag G-meting (item 4). Geprioriteerd:

1. **Generatieve seed-modus ("kunnen staan").** ✅ *Capability gebouwd
   (2026-06-15).* Naast de omissie-prompt is er nu een `generative`-variant in
   `open_set_model_detector.py` (prompt v0.4-gen) die de niet-genomen
   weg / het verklarende kader vraagt, bedraad door `make_detector_backend` →
   `run-open-set-seed-review --prompt-variant generative` → summary-provenance.
   Doctrine-veilig: gewichtloze kandidaten, geen verzonnen feiten, gebonden aan
   déze tekst; waarde downstream geoordeeld (`02_atomic_seeds` §2). **Nog te
   doen:** een echte model-dispatch + blinde review (round 009) die toetst of
   "kunnen staan"-seeds inhoudelijk rijker zijn dan de omissie-seeds — gebouwd
   is niet hetzelfde als bewezen.
2. **Retrieval Probe operationeel (de brug SSL→RAG).** ✅ *Bridge gebouwd (2026-06-15):* `seed_retrieval_probe.py` — de query komt uit de seed/centroid i.p.v. de vraag; `retrieval_probe_vs_question` levert `seed_only_chunk_ids` (wat de seed vindt en de vraag niet), de meethandle voor gat 3. Deterministisch getest. ✅ *Live consumer gebouwd (2026-07-02):* `shadowseed chat --probe-corpus` — promoted seeds (of de manager-constellatie-centroid, wanneer `probe_type="retrieval"` vuurt) zoeken per beurt echt in een corpus; `seed_only_chunk_ids` staat in het beurtsrapport als *aanwezigheid, geen sturing* (hits gaan nooit de antwoordprompt in). **Nog te doen:** de head-to-head met echte embeddings (gat 3), en het ontwerpbesluit of/hoe seed-gevonden context het antwoord mag verrijken — dat is een contractvraag, geen retrievalvraag.
3. **SSL-seed vs RAG head-to-head.** ✅ *Harness gebouwd (2026-06-15):* `ssl_vs_rag_benchmark.py` + `run-ssl-vs-rag` — zelfde model/prompt, alleen de retrieval-query verschilt (vraag vs gap); blinde paren + `answer_pair_winrate`. Fixture-getest. **Nog te doen:** een echte run met een hf-embeddingmodel (de `lexical_embedding`-hash is te grof voor betekenisvolle retrieval) + blinde review — dat levert het eerste 'voorbij RAG'-getal. Er is geen test van de claim "beter dan een
   LLM met RAG ooit zelf zou vinden". Nodig: dezelfde vraag/corpus, waarbij de
   seed een richting opent die gewone RAG mist. Dit *bewijst* de unieke waarde.
4. **Echte falsificatie voor speculatieve seeds** — uiteindelijk modelintern
   (§5). ✅ *Eerste iteratie doorlopen (2026-07-03/04):* een echte dialectische
   "valt dit weg te argumenteren?"-toets (`run-dialectic-falsification`,
   WEERLEGD → Gate-contradictie, HOUDT_STAND → bounded, nooit promotie) plus de
   activatie-sonde met permutatie-controle (`run-activation-probe`). Met gpt-4.1
   als echte oordeelbron en distilgpt2/pythia als gesondeerd model: een schoon
   **nulresultaat** (rounds 026–028) — geen aantoonbare interne steun op kleine
   Engelse modellen, wat het correcte antwoord is. **Nog te doen:** een
   NL-capabel/groter model dat het oordeel plausibel kán encoderen (Laag G blijft
   open richting, geen must). Zie `docs/research/laag-g-scoping.md`.
5. **Levende schaduw-geheugenlaag over beurten** (§4). ✅ *Operationeel
   gedemonstreerd (2026-07-02):* `shadowseed chat` (PR #164) — een seed wordt
   gewichtloos geboren in een echt gesprek, reist mee in de schaduw, promoveert
   via de Gate en stuurt pas daarna een láter antwoord; het
   `shadowseed_agent`-contract staat live op de invloedgrens, de audit-trail is
   replaybaar en `/falsify` maakt falsificatie gebruikersgedreven. Expliciet een
   applicatiedemo op de gevalideerde mechaniek, geen bewijslaag
   (`docs/research/shadow-chat-demo.md`).

## 7. Wat de payoff-test (round 008) hieraan toevoegde

De scherpste les: SSL hielp alleen waar het handelen op seeds **geen schade** deed
(de gewichtloze, additieve injectie: 3/3) en faalde waar een vrije herschrijving
met ongewicht over het antwoord heerste (1/3). De Gate-filosofie geldt dus niet
alleen voor *welke* seeds actief worden, maar voor *hoe* ze de wereld raken.
Dezelfde discipline — gewichtloos tot verdiend — is de maat voor zowel detectie
als gebruik. Het reële doel is een revisie die én do-no-harm is én vloeiend
integreert, met de additieve injectie als vangnet.

## 8. De koers, in één regel

> Genereer gedurfde mogelijkheden ("kunnen staan"), houd ze gewichtloos en laat
> ze meereizen als schaduw van het antwoord, laat het gesprek en de Gate ze tot
> noodzaak ("moeten staan") promoveren, val terug op de interne zelf-herkenning
> (H-neuronen) om hallucinatie te falsificeren, en gebruik alleen wat gewicht
> heeft verdiend — gericht op het betere antwoord dat besloten ligt in wat het
> model níét zei, voorbij het plafond van het opvraagbare.

Dit blijft richting, geen bewijs. Elke stap hoort de 4.6 evidence-discipline te
volgen: gescheiden lagen, geen totaalscore, eerlijk over wat vandaag werkt en wat
doelbeeld is.

## Referenties

- Kendall, A., & Gal, Y. (2017). *What Uncertainties Do We Need in Bayesian Deep
  Learning for Computer Vision?* NeurIPS 2017. arXiv:1703.04977.
- Schmidhuber, J. (2011). *Formal Theory of Creativity, Curiosity and
  Intelligence.* IEEE TAMD 2(3), 230-247.
- Settles, B. (2009). *Active Learning Literature Survey.* UW-Madison TR 1648.
- Gao, C., Chen, H., Xiao, C., Chen, Z., Liu, Z., & Sun, M. (2025). *H-Neurons:
  On the Existence, Impact, and Origin of Hallucination-Associated Neurons in
  LLMs.* arXiv:2512.01797. Code: github.com/thunlp/H-Neurons (MIT).
- Frankland, P. W., & Bontempi, B. (2005). *The organization of recent and remote
  memories.* Nature Reviews Neuroscience 6(2), 119-130.
- Josselyn, S. A., & Tonegawa, S. (2020). *Memory engrams: Recalling the past and
  imagining the future.* Science 367(6473), eaaw4325.
