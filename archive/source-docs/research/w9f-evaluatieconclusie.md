# W9f evaluatieconclusie

> Status: current
> Date: 2026-06-30
> Evidence layer: cross-turn payoff / lifecycle doctrine / blind review
> Current source: yes

## Doel van dit document

Dit document zet de W9f-stand vast na de follow-up baseline, de blind A/B-review en de review-artifacts.

De kern is dat W9f niet als los experiment naast SSL moet worden gelezen. W9f operationaliseert de bestaande SSL-doctrine in een multi-turn setting:

- `trace` bewaart aanwezigheid zonder invloed;
- `weight` bepaalt pas na Gate-promotie invloed;
- TrTL houdt een seed levend wanneer nieuwe context hem herkent;
- TTL laat seeds verdwijnen wanneer herkenning uitblijft;
- de Validation Gate voorkomt dat een losse herkenning meteen antwoordgedrag stuurt.

W9f toont dat deze levenscyclus in een echte sessie antwoordruimte kan openen die de baseline zonder SSL niet als optie had gehad.

## Kernconclusie

W9f bevestigt het cross-turn **mechanisme** op veilige doctrine-drempels, maar de **payoff-kwaliteit** is in de blinde review reviewer-afhankelijk gebleken. W9f is daarom een baseline-*kandidaat*, geen afgesloten bewijsronde.

Wat staat (mechanisme):

- de pipeline detecteert terugkerende of latente context;
- cluster-recurrence brengt parafrastische herhaling samen zonder de veilige opslag-dedup los te laten;
- representatives, niet hele clusters, gaan door de Gate;
- representatives blijven levend wanneer recurrence via non-representative members binnenkomt;
- surfaced context kan later antwoordruimte openen.

Wat nog niet staat (kwaliteit/payoff):

- de blinde review op veilige drempels kwam **gespleten** terug — twee reviewers oneens op 7/8 (zie `benchmarks/open_review/rounds/round_022/human_review/`), precies op de vraag of gesurfacete context verrijking of ruis is.

Recurrence- of promotion-tuning is dus niet de openstaande stap — het mechanisme vuurt. De openstaande stap is **use-time discipline**: wanneer mag een promoted seed het antwoord sturen?

## Wat de blind A/B-review wel meet

De blind A/B-review meet niet simpelweg of GPT-4.1 door SSL algemeen wordt verslagen.

De juiste lezing is:

```text
vraag + sessiehistorie -> SSL seed discovery -> recurrence/surfacing -> GPT-4.1 met extra context -> alternatief antwoord
```

De review beoordeelt dus of de door SSL geopende antwoordruimte bruikbaar is.

Zonder SSL zouden deze specifieke antwoordvarianten niet als testoptie hebben bestaan. Het experiment is daarom geen klassieke model-vs-model benchmark, maar een kwaliteitscontrole op SSL-gegenereerde antwoordruimte.

## Wat de review niet bewijst

De review bewijst niet:

- dat SSL elk antwoord beter maakt;
- dat SSL GPT-4.1 algemeen verslaat;
- dat elke promoted seed waardevol is;
- dat seed-gebruik automatisch veilig is;
- dat de claim al scenario- of domein-onafhankelijk is.

Dat hoeft ook niet de W9f-claim te zijn.

## Wat W9f wel bewijst

W9f ondersteunt de smallere en sterkere claim:

> SSL kan latente sessiecontext gewichtloos vasthouden, later valideren of surfacen, en daardoor aanvullende antwoordruimte openen die er anders niet was. Of die ruimte ook consistent *waardevol* is, is de open kwaliteitsvraag.

Deze claim sluit aan op de 4.6-doctrine: wat een model mist wordt geen direct antwoordgewicht, maar eerst een trace. Pas na herhaalde herkenning en Gate-promotie mag de seed invloed krijgen.

## Review-uitkomst in cijfers

Twee onafhankelijke reviewers scoorden hetzelfde blinde A/B-pack (8 cross-turn items, gpt-4.1, veilige drempels). Volledige data en analyse: `benchmarks/open_review/rounds/round_022/human_review/`.

- **Inter-reviewer winnaar-overeenstemming: 1/8** (alleen CONV_STARTUP-t05). Dit is niet de round-019-overeenstemming (92%/98%); op veilige drempels is het oordeel reviewer-afhankelijk.
- **SSL/seed-variant geprefereerd: Reviewer A 1/8, Reviewer B 8/8** — vrijwel perfecte inversie (SSL/baseline-toewijzing afgeleid uit motivaties; de kop-bevinding 1/8 staat daar los van).
- **CONV_CITY is het meest gepolariseerd, niet het sterkste positieve signaal**: Reviewer A koos daar de seed-variant 0/4 ("ruis"/"diffuus"); Reviewer B 4/4.
- Het enige consensus-item (CONV_STARTUP-t05) is het meest concrete: waar de seed *operationaliseert* (virale piek → autoscaling/queues/rate-limiting) zijn beide reviewers het eens dat hij helpt; waar hij *breedte/thema* toevoegt, splitst het.

De onenigheid is structureel: Reviewer A straft "seed verdringt de vraag" af als ruis/vernauwing, Reviewer B beloont "rijker/geïntegreerd". Dat is de verrijking-vs-ruis-as.

Cruciaal: de gemarkeerde ruis zit in **gevalideerde, promoted** seeds (post-Gate), niet in ongefilterde supply. De Gate valideert persistentie + geen-contradictie, niet of déze seed dít antwoord scherper of juist smaller maakt.

## Besluit

Het W9f-mechanisme staat; de payoff-discipline is de open vraag.

De repo hoeft niet te blijven vragen "bestaat het cross-turn mechanisme?" — dat vuurt reproduceerbaar op veilige drempels. De scherpe, falsifieerbare vraag is nu tweeledig:

> 1. onder welke gebruiksdiscipline mag een surfaced seed het antwoord sturen — sturen bij aanscherping, dormant blijven bij vernauwing?
> 2. draagt diezelfde levenscyclus over naar andere domeinen, taken en modellen?

## Volgende fase

De volgende fase heeft twee parallelle sporen:

**Spoor 1 — use-time seed-discipline (potentieel-vs-must).** De ruis/vernauwing in round 022 zat in *promoted* seeds: het probleem is niet de Gate-supply maar de surfacing-stap die een promoted seed altijd laat sturen (`surface_threshold` ~0.30 + "betrek expliciet"). Doctrine-zuiver: een seed stuurt wanneer hij aanscherpt en blijft dormant wanneer hij zou vernauwen. Klaar wanneer: een surfacing/weave-discipline die de round-022-ruiscases dempt zonder de wins te verliezen.

**Spoor 2 — W10 doctrine-transfer.** Niet groter in dezelfde A/B-opzet, maar transfer van de bestaande levenscyclus:

- trace/weight-scheiding;
- TTL/TrTL;
- Gate-promotie;
- cluster-recurrence;
- cross-turn surfaced seeds;
- payoff of nuttige vervolgactie;
- seed-ruis en seed-vernauwing als expliciete foutklasse.

De hoofdvraag voor W10:

> blijft de cross-turn SSL-doctrine werken buiten de huidige startup/city-scenario's?

Mogelijke transferassen:

1. domeintransfer: onderwijs, onderzoek, beleid, productontwerp;
2. taaktransfer: Q&A, planning, kritiek, samenvatting, besluitondersteuning;
3. modeltransfer: gpt-4.1, kleinere OpenAI-modellen, lokale modellen;
4. reviewtransfer: één reviewprotocol voor wins, ties, ruis en seed-vernauwing.

## Repo-gevolg

De juiste status in de statusdocs:

- W9f-mechanisme: bevestigd op veilige drempels (cross-turn surfacing vuurt);
- W9f-payoff: baseline-kandidaat, reviewer-afhankelijk gebleken (round 022, 1/8 overeenstemming);
- blind A/B: kwaliteitscontrole op geopende antwoordruimte, geen absolute benchmark;
- volgende stap: use-time seed-discipline (potentieel-vs-must) + doctrine-transfer (W10).
