# CLI Command Map

Deze pagina legt vast hoe de `shadowseed` CLI gelezen moet worden.

Niet elke command heeft dezelfde status.
De CLI heeft daarom vijf commandolagen:

1. standaard regressie- en smoke-routes
2. standaard aanvullende evidenceroutes
3. handmatige research-routes
4. retrieval-, backend- en AbsenceBench-routes
5. applicatie- en demoroutes

## 1. Standaard regressie- en smoke-routes

Deze commands horen direct bij de huidige standaard meetketen.

| Command | Rol | Status |
|---|---|---|
| `run-gap-suite` | regressie voor bekende SSL-gaps | standaard |
| `run-false-positive-suite` | negatieve controle en beperkte ruisfiltering | standaard |
| `run-benefit-suite` | kleine benchmark voor antwoordwinst | standaard |
| `run-model-benefit-suite` | fixture-smoke en optionele echte modelrun | standaard voor fixture, handmatig voor echte backend |
| `run-blind-benchmark` | labelscheiding en methodologische smoke | standaard |
| `run-absencebench-smoke` | technische smoke voor de lokale AbsenceBench-route | standaard |
| `analyze-results` | rapportage uit resultaatbestanden | standaard |

Deze laag is er om de basis betrouwbaar te houden.

## 2. Standaard aanvullende evidenceroutes

Deze commands draaien nu mee in de standaardpublicatie, maar moeten nog steeds gelezen worden als aanvullende evidencelagen en niet als volledige eindvalidatie.

| Command | Rol | Status |
|---|---|---|
| `run-adversarial-gate-benchmark` | vergelijkt de huidige Gate met zwakkere promotieregels | standaard aanvullende evidencelaag |
| `run-probe-utility-benchmark` | vergelijkt seed-geleide vervolgacties met bredere baselines | standaard aanvullende evidencelaag |

Hoofdregel:

> deze routes zijn zichtbaar genoeg om standaard mee te publiceren, maar nog niet volwassen genoeg om als enige hoofdclaim te dragen.

## 3. Handmatige research-routes

Deze commands verdiepen het bewijs verder, maar draaien niet automatisch mee in elke standaardpublicatie.

| Command | Bewijslaag | Status |
|---|---|---|
| `fetch-open-set-hf-batch` | open-set intake | handmatig |
| `run-open-set-seed-review` | open-set seedkwaliteit | handmatig |
| `summarize-open-set-seed-review` | open-set samenvatting | handmatig |
| `run-dialectic-falsification` | Laag G instap: dialectische falsificatie van promoted seeds | handmatig |
| `run-activation-probe` | Laag G spoor 2: activatiescheiding tussen verdict-klassen (signaal, geen verdict); `--verdicts` ontkoppelt de verdictbron, `--read-location neuron` leest op het H-Neurons-punt (down_proj-input), sparse L1-detector met LOOCV + permutatie zit in elk rapport | handmatig (fake-smoke in CI-tests; hf opt-in) |

Voor deze laag is het doel niet alleen output maken, maar vooral reviewerbare en stabiele artefacts opbouwen.

## 4. Retrieval-, backend- en AbsenceBench-routes

Deze commands zijn nuttig voor diagnose, infrastructuur of optionele verdiepende runs.

| Command | Rol | Status |
|---|---|---|
| `run-retrieval-benchmark` | retrievalkwaliteit van de vectorstore | handmatig |
| `run-retrieval-model-benchmark` | effect van opgehaalde context op modelantwoord | handmatig |
| `run-ssot-smoke` | SSOT en falsificatiebasis smoke-test | handmatig |
| `run-vectorstore-smoke` | vectorstore backend smoke-test | handmatig |
| `prepare-absencebench-bundle` | bouw een preparation bundle | utility |
| `fetch-absencebench-sample` | haal een sample op | utility |
| `run-absencebench-local` | draai een lokale AbsenceBench-run | utility |

Legacy aliases blijven voorlopig ondersteund voor compatibiliteit.

### Aanvullende handmatige research-routes (voor volledigheid)

| Command | Rol | Status |
|---|---|---|
| `run-ssl-session` | cross-turn sessiesuite (W9f/W10); bron van de blinde A/B-packs | handmatige research |
| `run-wild-payoff` | payoff op wilde/onbekende teksten (W4) | handmatige research |
| `run-adversarial-payoff` | payoff onder adversarial condities | handmatige research |
| `run-generative-payoff` | payoff-verkenning voor generatieve seeds | handmatige research |
| `run-probe-feedback-behavior-suite` | gedragssuite voor probe-feedback-lifecycle (laag E-instap) | handmatige research |
| `run-ssl-vs-rag` | SSL-seed vs RAG head-to-head harness (fixture-getest) | handmatige research |
| `list-open-set-models` | toon dispatchbare open-set modellen | utility |

## 5. Applicatie- en demoroutes

Deze commands demonstreren de gevalideerde mechaniek in gebruik, maar voeden geen bewijslaag.

| Command | Rol | Status |
|---|---|---|
| `chat` | levende schaduwlaag in een echt gesprek, met agent-contract en audit-trail | demo, geen bewijslaag |

Zie `docs/research/shadow-chat-demo.md` voor de claimgrens.

## Waarom deze indeling belangrijk is

Zonder deze indeling lijkt het alsof alle commands dezelfde bewijslast hebben.
Dat is niet zo.

De repo wil juist zichtbaar maken:

- wat de basis bewaakt;
- wat als aanvullende evidencelaag meegepubliceerd wordt;
- wat nog handmatige research is;
- wat vooral infrastructuur of utility is;
- wat demonstratie is en dus geen bewijslast draagt.

## Korte beleidszin

> eerst duidelijk maken welke command welke bewijslaag voedt, daarna pas verder uitbreiden.
