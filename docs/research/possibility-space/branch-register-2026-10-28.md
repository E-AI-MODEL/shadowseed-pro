# Branchregister Shadowseed Pro (momentopname 28 oktober 2026)

> Dit is een inventaris van de **remote branchrefs**, geen oordeel over de inhoud van een branch. De lijst is samengesteld uit de GitHub REST-pagina's `branches?per_page=100` en `pulls?state=all&per_page=100` (inclusief vervolgpagina's). De PR-koppeling is gemaakt op exact dezelfde head-branchnaam. Een historische gemergede PR betekent niet automatisch dat de huidige branchkop is gemerged. De inventaris is niet live en kan na dit moment verouderen.

- Repository: https://github.com/E-AI-MODEL/shadowseed-pro
- `main` op inventarisatiemoment: `1a8e0947ff09f5bfe09b939a2dd4345a7ae2bb18`
- Remote branches: **166** (inclusief `main`).
- In GitHub opgehaalde PR-records: **227**; daarvan **15 open**, alle open PR's zijn op dit moment concept-PR's.
- Branches zonder PR-match in de opgehaalde records: **19**. Dit is geen bewijs dat ze ongebruikt zijn.

## Open PR's en directe merge-afhankelijkheden

| PR | Head-branch | Base-branch | Status |
| --- | --- | --- | --- |
| [#264](https://github.com/E-AI-MODEL/shadowseed-pro/pull/264) | `docs/observation-first-readme-20261028` | `main` | Concept |
| [#263](https://github.com/E-AI-MODEL/shadowseed-pro/pull/263) | `research/raw-stage-trajectory-reconstruction-20261028` | `main` | Concept |
| [#262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262) | `feature/pro-weightless-unresolved-birth-20261028` | `main` | Concept |
| [#261](https://github.com/E-AI-MODEL/shadowseed-pro/pull/261) | `research/pro-atomicity-fate-audit-20261028` | `main` | Concept |
| [#260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) | `research/q1q2-two-point-48-20261028` | `main` | Concept |
| [#259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259) | `docs/research-archive-map-20261027` | `main` | Concept |
| [#258](https://github.com/E-AI-MODEL/shadowseed-pro/pull/258) | `research/g0-dual-model-gpt5-luna-ab-20261027` | `research/g0-late-birth-two-followups-20261027` | Concept |
| [#257](https://github.com/E-AI-MODEL/shadowseed-pro/pull/257) | `research/g0-late-birth-two-followups-20261027` | `research/g0-method-readiness-20261027` | Concept |
| [#256](https://github.com/E-AI-MODEL/shadowseed-pro/pull/256) | `research/g0-method-readiness-20261027` | `research/g0-multicase-real-ab-20261026` | Concept |
| [#255](https://github.com/E-AI-MODEL/shadowseed-pro/pull/255) | `research/g0-multicase-real-ab-20261026` | `research/g0-exact-seed-ablation-20261025` | Concept |
| [#254](https://github.com/E-AI-MODEL/shadowseed-pro/pull/254) | `research/g0-exact-seed-ablation-20261025` | `research/q1-q2-real-seed-rf-20261025` | Concept |
| [#251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251) | `research/q1-q2-real-seed-rf-20261025` | `research/g0-exploratory-real-model-stage1-20261025` | Concept |
| [#250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250) | `research/g0-exploratory-real-model-stage1-20261025` | `main` | Concept |
| [#244](https://github.com/E-AI-MODEL/shadowseed-pro/pull/244) | `research/ssot-legacy-review-preflight-20261025` | `fix/ssot-explicit-relation-review-20261025` | Concept |
| [#243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243) | `fix/ssot-explicit-relation-review-20261025` | `main` | Concept |

## Lezen vóór samenvoegen of opruimen

- De onderzoeksketen is gestapeld: **#250 → #251 → #254 → #255 → #256 → #257 → #258**. De pijl betekent: de volgende PR bouwt op de head van de vorige. Behandel de afzonderlijke resultaten en beperkingen als aparte historische waarnemingen. Niet direct vanuit de laatste head in `main` samenvoegen.
- Het SSOT-controlepaar is **#243 → #244**; #244 bouwt op de nog openstaande #243 en is geen zelfstandige productvrijgave.
- **#259** maakt een historisch onderzoeksarchief en PR-kaart, **#260** legt een afzonderlijke 48-call proef vast, **#261** onderzoekt intake/verlies, **#262** stelt ander runtimegedrag voor, **#263** reconstrueert trajecten, en **#264** ordent documentatie. Ze hebben alle zes `main` als PR-base maar zijn inhoudelijk niet onderling uitwisselbaar.
- Bij #258 en andere gestapelde onderzoeksbranches kunnen eigen commits en gewijzigde mainline uiteenlopen. Controleer bij eventuele integratie eerst de actuele vergelijking en conflictsituatie; neem geen oude CI-uitkomst automatisch over.
- Het open karakter van een PR, een historisch merged-label, of een oude branchnaam geeft **geen** toestemming om branches, ruwe data of onderzoeksgeschiedenis te verwijderen. Dit register is geen opruiminstructie.
- Voor herkomst en wetenschappelijke claims verwijzen de PR-bodies naar de exacte commit, Action-run, gebruikte bronnen en eventuele private artifacts. Dit register reproduceert geen afgeschermde ruwe teksten, sleutels of reviewer-toewijzingen.

## Volledige inventaris van remote branches

De commit is de volledige head-SHA op het moment van de inventarisatie. `Geen PR-match` betekent uitsluitend dat onder de huidige branchnaam geen bijbehorende PR-head in de opgehaalde records is aangetroffen.

| Branch | Head-commit (SHA) | Gevonden PR-historie |
| --- | --- | --- |
| `0.11-behavior-config-epoch` | `15a221191f6e0b40e4e861425215f6bd7d649ff1` | [#164](https://github.com/E-AI-MODEL/shadowseed-pro/pull/164) (gesloten PR) |
| `0.11-behavior-config-epoch-mainline` | `05bacf02ad70b7b881c7af3ddd91b5f7d9ee037e` | [#166](https://github.com/E-AI-MODEL/shadowseed-pro/pull/166) (gemergede PR) |
| `0.11-behavior-epoch` | `0250c02104fa4b12c0a031cb93763cb65fb991f1` | Geen PR-match |
| `0.11-config-statefulness-metadata` | `0dfe5b2521eb8912a9ca1f858bb846ac98e583a2` | [#153](https://github.com/E-AI-MODEL/shadowseed-pro/pull/153) (gemergede PR) |
| `0.11-current-gate-policy-alignment` | `de131d7f2da18dc817b2975ab652b292331ef7be` | [#150](https://github.com/E-AI-MODEL/shadowseed-pro/pull/150) (gemergede PR) |
| `0.11-human-ssl-orchestration` | `f49009a48fcf87a2a4541a7ede71017afcf3894a` | [#154](https://github.com/E-AI-MODEL/shadowseed-pro/pull/154) (gemergede PR) |
| `0.11-lifecycle-expiry-gate-boundary` | `fc04200123d6194839b79aee5427118804299b97` | [#151](https://github.com/E-AI-MODEL/shadowseed-pro/pull/151) (gemergede PR) |
| `0.11-mainline-pr-d-f` | `30d64573b2677aa47c0839633241fac5de0eb177` | [#165](https://github.com/E-AI-MODEL/shadowseed-pro/pull/165) (gemergede PR) |
| `0.11-normal-controls-no-legacy` | `d014851ccce6058d005953fa34ecf0ae29509c2f` | [#152](https://github.com/E-AI-MODEL/shadowseed-pro/pull/152) (gemergede PR) |
| `0.11-orchestration-ux` | `c9254125363fec3e9e4723c45a44ce3cc08a764f` | [#158](https://github.com/E-AI-MODEL/shadowseed-pro/pull/158) (gemergede PR) |
| `0.11-prompt-contract-audit` | `780e4532339b8edc6ad6aeaf8c30909880b6a2b2` | [#156](https://github.com/E-AI-MODEL/shadowseed-pro/pull/156) (gemergede PR) |
| `0.11-revision-model-role` | `d60396e5de27f950269e0ed344037dea0383528d` | [#157](https://github.com/E-AI-MODEL/shadowseed-pro/pull/157) (gemergede PR) |
| `0.11-self-derived-revision-split` | `bc21cc32fd0698de72fc5db1a068eccf01028832` | [#155](https://github.com/E-AI-MODEL/shadowseed-pro/pull/155) (gemergede PR) |
| `0.11-structural-config-safety` | `e8a0f1bc4bcf7fa059169a98b5870a7462fd9c2b` | [#149](https://github.com/E-AI-MODEL/shadowseed-pro/pull/149) (gemergede PR) |
| `admin/fix-protection-audit-trail` | `69c3eaeb7d184a899266c319f3f0791dd75a720c` | [#94](https://github.com/E-AI-MODEL/shadowseed-pro/pull/94) (gemergede PR) |
| `admin/repair-protection-verification` | `73cc8582eb0dee836f3dd5f723af927ceda2f2d1` | [#91](https://github.com/E-AI-MODEL/shadowseed-pro/pull/91) (gemergede PR) |
| `admin/verify-main-protection` | `05b1a8c815751cc9c473ce77cd0e84a3c2561112` | [#90](https://github.com/E-AI-MODEL/shadowseed-pro/pull/90) (gemergede PR) |
| `admin/verify-required-ci` | `20b89917694fa60874483bbe95b16705e681811a` | [#93](https://github.com/E-AI-MODEL/shadowseed-pro/pull/93) (gemergede PR) |
| `adr-009-runtime-component-orchestration` | `c7f81681e72ce88bebf02292bfec1fd386b8a5ab` | [#146](https://github.com/E-AI-MODEL/shadowseed-pro/pull/146) (gemergede PR) |
| `agent/evidence-quality-qwen7b` | `8fdbe6596cb799569146421c866831e78bf6f2c7` | [#61](https://github.com/E-AI-MODEL/shadowseed-pro/pull/61) (gesloten PR) |
| `agent/release-0.5.1-publish-fix` | `15895339c2c171208da352eb962805ed262457ce` | [#85](https://github.com/E-AI-MODEL/shadowseed-pro/pull/85) (gemergede PR) |
| `architecture/production-readiness-phase-0` | `75b1f206bef5c18f2ee51c26520e9b5403c4ff44` | [#89](https://github.com/E-AI-MODEL/shadowseed-pro/pull/89) (gemergede PR) |
| `archive/raw-artifacts-20261027` | `1a8e0947ff09f5bfe09b939a2dd4345a7ae2bb18` | Geen PR-match |
| `bench/gap-resilience-hf-runner` | `ab0a7823903820c45099a6a09c25e65b6e0a3cca` | [#186](https://github.com/E-AI-MODEL/shadowseed-pro/pull/186) (gesloten PR) |
| `bench/gap-resilience-v1` | `7c811e99e224629cfff698a0378b75a901218068` | [#185](https://github.com/E-AI-MODEL/shadowseed-pro/pull/185) (gemergede PR) |
| `bench/qwen7b-gap-resilience-live1` | `c8f949d9254627c220f148a0afc906b0aa1a7850` | [#187](https://github.com/E-AI-MODEL/shadowseed-pro/pull/187) (gesloten PR) |
| `bench/r1-revision-role` | `7d179dfc913ff70cc054b8e513c8a0487554654e` | [#190](https://github.com/E-AI-MODEL/shadowseed-pro/pull/190) (gemergede PR) |
| `chore/pva-doctrine-terminology-2026-10-22` | `f3ec86c124ab88247e0739a6cbe3c817a6508219` | Geen PR-match |
| `chore/release-0.7.0` | `5fcaa5e1483289fd7bf771fa27a1f0d13ea23a54` | [#113](https://github.com/E-AI-MODEL/shadowseed-pro/pull/113) (gemergede PR), [#109](https://github.com/E-AI-MODEL/shadowseed-pro/pull/109) (gemergede PR) |
| `ci/separate-merge-checks-release-assurance` | `0595576fb42a00f4ba771bea73a96671ab59b4ff` | [#171](https://github.com/E-AI-MODEL/shadowseed-pro/pull/171) (gesloten PR) |
| `ci/separate-merge-checks-release-assurance-mainline` | `0ae76bac4984e63f111d823c06b82ab5e941f3d2` | [#172](https://github.com/E-AI-MODEL/shadowseed-pro/pull/172) (gemergede PR) |
| `claude/confident-franklin-b168go` | `58d598c8ef29681882a00f9df4647b28793ea184` | [#237](https://github.com/E-AI-MODEL/shadowseed-pro/pull/237) (gemergede PR), [#218](https://github.com/E-AI-MODEL/shadowseed-pro/pull/218) (gemergede PR), [#217](https://github.com/E-AI-MODEL/shadowseed-pro/pull/217) (gemergede PR), [#216](https://github.com/E-AI-MODEL/shadowseed-pro/pull/216) (gemergede PR), [#215](https://github.com/E-AI-MODEL/shadowseed-pro/pull/215) (gemergede PR), [#214](https://github.com/E-AI-MODEL/shadowseed-pro/pull/214) (gemergede PR), [#213](https://github.com/E-AI-MODEL/shadowseed-pro/pull/213) (gemergede PR), [#212](https://github.com/E-AI-MODEL/shadowseed-pro/pull/212) (gemergede PR), [#211](https://github.com/E-AI-MODEL/shadowseed-pro/pull/211) (gemergede PR), [#210](https://github.com/E-AI-MODEL/shadowseed-pro/pull/210) (gemergede PR), [#209](https://github.com/E-AI-MODEL/shadowseed-pro/pull/209) (gemergede PR), [#208](https://github.com/E-AI-MODEL/shadowseed-pro/pull/208) (gemergede PR), [#195](https://github.com/E-AI-MODEL/shadowseed-pro/pull/195) (gemergede PR), [#194](https://github.com/E-AI-MODEL/shadowseed-pro/pull/194) (gemergede PR) |
| `claude/session-q73qmu` | `c8ce2507a2cf99fc4008315b483a06bfec401940` | [#117](https://github.com/E-AI-MODEL/shadowseed-pro/pull/117) (gemergede PR), [#105](https://github.com/E-AI-MODEL/shadowseed-pro/pull/105) (gemergede PR) |
| `cleanup/mainline-maintenance-hygiene` | `479e866cd87bd29c3a34e681cc4f83d849f39391` | [#167](https://github.com/E-AI-MODEL/shadowseed-pro/pull/167) (gemergede PR) |
| `cleanup/remove-legacy-workbench-ui-mainline` | `a7eb950c6e8d48e7c5287ec30cd589f121248326` | [#168](https://github.com/E-AI-MODEL/shadowseed-pro/pull/168) (gemergede PR) |
| `cleanup/remove-retired-simple-app` | `d8ce1e54aaacccc2147ffe3129667f51b35416d8` | [#162](https://github.com/E-AI-MODEL/shadowseed-pro/pull/162) (gesloten PR) |
| `cleanup/research-status-after-0.10.1` | `859a64004db202e0fde785d916cbdb1e067aac6f` | [#159](https://github.com/E-AI-MODEL/shadowseed-pro/pull/159) (gesloten PR) |
| `cleanup/slim-workbench-app-entrypoint` | `190bf80bab30b8e338904cdad991504439ed04a6` | [#163](https://github.com/E-AI-MODEL/shadowseed-pro/pull/163) (gesloten PR) |
| `cleanup/split-current-legacy-workbench-tests` | `7d6815b2eb407030f4bda3215ebbef8251f47360` | [#161](https://github.com/E-AI-MODEL/shadowseed-pro/pull/161) (gesloten PR) |
| `cleanup/workbench-version-display` | `39ab8b37d50a34c89c0936c90cc62ffd48046ddd` | [#160](https://github.com/E-AI-MODEL/shadowseed-pro/pull/160) (gesloten PR) |
| `dependabot/github_actions/actions-7b3aab91a4` | `aa3ba6c097d553088b08bb2554d812f7230b5539` | [#107](https://github.com/E-AI-MODEL/shadowseed-pro/pull/107) (gesloten PR) |
| `dependabot/pip/python-runtime-5a90e9007b` | `50a34cee92ab27a1838651a1ebc7b1563d71d825` | [#99](https://github.com/E-AI-MODEL/shadowseed-pro/pull/99) (gesloten PR) |
| `dependabot/uv/python-runtime-109a84ff75` | `30462e18f23b23af2cbcdda81a8ef507a9195e72` | [#106](https://github.com/E-AI-MODEL/shadowseed-pro/pull/106) (gesloten PR) |
| `docs/history-source-of-truth-cleanup-2026-10-22` | `f3ec86c124ab88247e0739a6cbe3c817a6508219` | Geen PR-match |
| `docs/observation-first-readme-20261028` | `ff5d6695418b24ca5e84dad972a2955c2ff291f3` | [#264](https://github.com/E-AI-MODEL/shadowseed-pro/pull/264) (open / concept) |
| `docs/paper-071-provenance` | `40eb2cf4acff537ffd4712d350be878f30e12020` | [#115](https://github.com/E-AI-MODEL/shadowseed-pro/pull/115) (gemergede PR) |
| `docs/possibility-space-thesis-20261024` | `9c1dc5e3347e199148075e615f5862fc508ece43` | [#219](https://github.com/E-AI-MODEL/shadowseed-pro/pull/219) (gemergede PR) |
| `docs/post-release-0.11.0-status` | `3462f9530a49abf0ceade71e5fbd48797d16ce39` | [#176](https://github.com/E-AI-MODEL/shadowseed-pro/pull/176) (gemergede PR) |
| `docs/post-release-0.11.1-status` | `3bb0c4cb6073ed9b64f96d948eb898e3af921e5e` | [#178](https://github.com/E-AI-MODEL/shadowseed-pro/pull/178) (gesloten PR) |
| `docs/published-0.12.1-confidence-pass` | `203b58025e565869ce15f03161943ea02a29be73` | [#193](https://github.com/E-AI-MODEL/shadowseed-pro/pull/193) (gesloten PR) |
| `docs/pva-history-and-terminology-2026-10` | `42d5e1aea0bf311d37ce61062148234bcba58c3c` | Geen PR-match |
| `docs/pva-inquiry-legacy-terminology-2026-10-22` | `ec3712b9a672e5c9c9e51e9ee37140146f0e33b9` | Geen PR-match |
| `docs/research-archive-map-20261027` | `888cabab15b3a860938574ec41a61bf997db2968` | [#259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259) (open / concept) |
| `docs/research-index-archive-audit-20261027` | `1a8e0947ff09f5bfe09b939a2dd4345a7ae2bb18` | Geen PR-match |
| `docs/shadowseed-history-pva-and-noise-audit-2026-10-22` | `c7fe4893d7609c728b1ec5bd57bacad90a7a5138` | Geen PR-match |
| `docs/shadowseed-pro-hld` | `d35703000eb0bec668c855dd8a6fda67f07b9284` | [#118](https://github.com/E-AI-MODEL/shadowseed-pro/pull/118) (gemergede PR) |
| `docs-0.11-implementation-matrix` | `d639a8eb06d9410ba98743b0c069cd61e534f9a8` | [#148](https://github.com/E-AI-MODEL/shadowseed-pro/pull/148) (gemergede PR) |
| `feat/inquiry-first-seed-intent` | `c358965222f1f90e6b8ea9a2b79807dbf27032b1` | [#202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) (gesloten PR) |
| `feat/layer-g-vnext-preflight` | `2aac56196f5f3c54de8162df699ec437e0745325` | [#204](https://github.com/E-AI-MODEL/shadowseed-pro/pull/204) (gesloten PR) |
| `feat/local-balanced-model-roles` | `d9127aaac66d41c1e4725c185a916f5c5ea8196b` | [#191](https://github.com/E-AI-MODEL/shadowseed-pro/pull/191) (gemergede PR) |
| `feat/model-role-routing` | `9c27d95d2e015983c723b345991d0ec5300923c6` | [#189](https://github.com/E-AI-MODEL/shadowseed-pro/pull/189) (gemergede PR) |
| `feat/native-chat-k1-runtime` | `51d49f1dc7c989abc2e88917ad7100f27eb97292` | [#198](https://github.com/E-AI-MODEL/shadowseed-pro/pull/198) (gemergede PR) |
| `feat/shadowseed-authority-profiles` | `40bc37f2bdc1307b20f1d59c8524ce858ce2b92f` | [#127](https://github.com/E-AI-MODEL/shadowseed-pro/pull/127) (gesloten PR) |
| `feat/standalone-ssl-engine` | `4b165d6651151b521452ddefa3aeeaf0ab7b69be` | [#119](https://github.com/E-AI-MODEL/shadowseed-pro/pull/119) (gemergede PR) |
| `feat/0.12.3-web-only-distribution` | `253b12654b60c7c51f57cab15655cbde970cb276` | [#201](https://github.com/E-AI-MODEL/shadowseed-pro/pull/201) (gemergede PR) |
| `feature/ollama-semantic-embeddings-mainline` | `55ef3c9ae9fd35eca5d8f500a2f623334583dd4c` | [#173](https://github.com/E-AI-MODEL/shadowseed-pro/pull/173) (gemergede PR) |
| `feature/pro-weightless-unresolved-birth-20261028` | `bdb027df4ab711158f195c1ddbb4dd3b79ef45cb` | [#262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262) (open / concept) |
| `feature/thin-workbench-dependencies` | `f3692a5520ce7731d3a484ad28d93dd2d136348b` | Geen PR-match |
| `feature/thin-workbench-dependencies-mainline` | `e05feeb3b208c310baaf70f098fad8e77e571cdc` | [#174](https://github.com/E-AI-MODEL/shadowseed-pro/pull/174) (gemergede PR) |
| `feature/web-client-foundation` | `6af62705b98803668b64974e588e34f55536a4eb` | [#179](https://github.com/E-AI-MODEL/shadowseed-pro/pull/179) (gemergede PR) |
| `feature/web-provider-setup` | `c4b381f7914e397647327cf0fac1c32a97eeb748` | [#181](https://github.com/E-AI-MODEL/shadowseed-pro/pull/181) (gemergede PR) |
| `feature/web-seed-actions` | `8c66ff233e31e2af1e8403de28750e6fbe0854d8` | [#180](https://github.com/E-AI-MODEL/shadowseed-pro/pull/180) (gemergede PR) |
| `feature/web-standalone-launcher` | `cba833746889afc6158be7e43116371e30fb5709` | [#182](https://github.com/E-AI-MODEL/shadowseed-pro/pull/182) (gemergede PR) |
| `feature/workbench-full-control` | `bf48aefa2aa03679e6c8ad899282877d595e7d8c` | [#144](https://github.com/E-AI-MODEL/shadowseed-pro/pull/144) (gemergede PR) |
| `feature/0.9-dutch-chat-ux` | `09de10bd12cd1aee0ea8697cd4e6c4c88ee77572` | [#129](https://github.com/E-AI-MODEL/shadowseed-pro/pull/129) (gemergede PR) |
| `fix/codex-production-assurance` | `21b275cdee82f49be2746547d34959239646483e` | [#112](https://github.com/E-AI-MODEL/shadowseed-pro/pull/112) (gemergede PR), [#108](https://github.com/E-AI-MODEL/shadowseed-pro/pull/108) (gemergede PR) |
| `fix/detector-intake-item-lineage-20261025` | `e42eca232cae3a2671aa0aacac46dfdcb94370d0` | [#246](https://github.com/E-AI-MODEL/shadowseed-pro/pull/246) (gemergede PR) |
| `fix/evidence-backed-role-routing` | `988a328f108668e65068270edbc7cc75dcb12b16` | [#197](https://github.com/E-AI-MODEL/shadowseed-pro/pull/197) (gemergede PR) |
| `fix/gap-seed-semantics-v012` | `08794b16d28cf31bebe9e1af9ef1b3401e88fb7c` | [#184](https://github.com/E-AI-MODEL/shadowseed-pro/pull/184) (gemergede PR) |
| `fix/independent-seed-origin-per-birth-20261025` | `b0da00159b02902273ffcefeecab2bb3ef734e57` | [#248](https://github.com/E-AI-MODEL/shadowseed-pro/pull/248) (gemergede PR) |
| `fix/macos-credential-free-release` | `167c8eb1aff4b48fb96f567a4502e8178cbd1b88` | [#126](https://github.com/E-AI-MODEL/shadowseed-pro/pull/126) (gemergede PR) |
| `fix/macos-developer-id-notarization` | `c22b93476697b3c742958e6658b3909db69604ec` | [#114](https://github.com/E-AI-MODEL/shadowseed-pro/pull/114) (gesloten PR) |
| `fix/macos-launch-0.9.3` | `83e1a164d582e33f1647eddf62480dcf391548b8` | [#133](https://github.com/E-AI-MODEL/shadowseed-pro/pull/133) (gesloten PR) |
| `fix/ollama-embedding-preflight-20261010` | `51d49f1dc7c989abc2e88917ad7100f27eb97292` | Geen PR-match |
| `fix/parser-two-word-gap-labels` | `bc67ab5446c7329ab6f9bc7e24f4c75a0a97c64e` | [#188](https://github.com/E-AI-MODEL/shadowseed-pro/pull/188) (gemergede PR) |
| `fix/production-local-integrity-guards` | `d2a949c03d23089508ced1bafdf2fa9ec2c082ca` | [#111](https://github.com/E-AI-MODEL/shadowseed-pro/pull/111) (gemergede PR) |
| `fix/release-evidence-query` | `11315453af25290d74394a44154218407071cc48` | [#141](https://github.com/E-AI-MODEL/shadowseed-pro/pull/141) (gemergede PR) |
| `fix/release-main-evidence-gates` | `f9ae73645e70c54b48a92c28814cde53c39bb2f7` | [#142](https://github.com/E-AI-MODEL/shadowseed-pro/pull/142) (gemergede PR) |
| `fix/research-lineage-release-compat-0125` | `fde902c23ae5a05b52728d138fbecf8c7207c3bd` | Geen PR-match |
| `fix/sentence-transformers-embedding-dimension-api` | `346685b24831ca5cb9451c431481ded78c04afb6` | [#170](https://github.com/E-AI-MODEL/shadowseed-pro/pull/170) (gemergede PR) |
| `fix/ssot-explicit-relation-review-20261025` | `f6688ea7ecce1d77bc28b3c61d8faf0aa8a520dd` | [#243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243) (open / concept) |
| `fix/ssot-reviewed-evidence-boundary-20261025` | `4c433c6e95733491e4b4720950bf997f5f1af634` | Geen PR-match |
| `fix/standalone-multiprocessing-bootstrap` | `cfd37134dd62cfdeb005eebe3615c2aa0a62998b` | [#169](https://github.com/E-AI-MODEL/shadowseed-pro/pull/169) (gemergede PR) |
| `fix/true-vanilla-ab-baseline` | `7acac296578107adb33453978cb0fa84ce2025cb` | [#131](https://github.com/E-AI-MODEL/shadowseed-pro/pull/131) (gemergede PR) |
| `fix/weightless-inquiry-lifecycle-acceptance` | `d23a49de724aecec9d0c3277d024e38cba427b11` | [#205](https://github.com/E-AI-MODEL/shadowseed-pro/pull/205) (gemergede PR) |
| `fix/0.12.3-complete-local-startup` | `9188357ad6113677b444f5d9bdb77dbd2a561e2f` | [#199](https://github.com/E-AI-MODEL/shadowseed-pro/pull/199) (gemergede PR) |
| `fix/0.12.3-product-baseline` | `a8dd07013abd0532169e9946849a8fb00e66c526` | [#196](https://github.com/E-AI-MODEL/shadowseed-pro/pull/196) (gesloten PR) |
| `fix/206-review-weightless-intake-20261023` | `6d6767272545d626e2d41f48e6187325b9e49d74` | [#207](https://github.com/E-AI-MODEL/shadowseed-pro/pull/207) (gemergede PR) |
| `hotfix/v0.6.0-license-eol` | `0e71ad10dfedd3ccc3ff12abb66b3e3d7e7b54a8` | [#87](https://github.com/E-AI-MODEL/shadowseed-pro/pull/87) (gemergede PR) |
| `hotfix/0.11.1-ollama-embedding-compat` | `ef9279316037d1b66d1fde6f1686c42245e0e2f2` | [#177](https://github.com/E-AI-MODEL/shadowseed-pro/pull/177) (gemergede PR) |
| `main` | `1a8e0947ff09f5bfe09b939a2dd4345a7ae2bb18` | Geen PR-match |
| `production/phase-1-supply-chain-guardrails` | `298cfb5094e2756646d3776d84fce3d0c92383df` | [#96](https://github.com/E-AI-MODEL/shadowseed-pro/pull/96) (gemergede PR) |
| `production/phase-2-actor-authorization` | `1b97f4e9ca4203b2cd16da8f60841e4e244f4984` | [#100](https://github.com/E-AI-MODEL/shadowseed-pro/pull/100) (gemergede PR) |
| `production/phase-3-durable-audit-migrations-recovery` | `d94531bee872828ea49d1bad65cbe11ad057fcb8` | [#101](https://github.com/E-AI-MODEL/shadowseed-pro/pull/101) (gemergede PR) |
| `production/phase-4-local-security-lifecycle` | `5972ae621a85b860fe1d7fa64279f8fc621ffc72` | [#102](https://github.com/E-AI-MODEL/shadowseed-pro/pull/102) (gemergede PR) |
| `production/phase-5-release-assurance` | `d3baa0a04ca3d7b3f8389be6da61fc216d9679d9` | [#104](https://github.com/E-AI-MODEL/shadowseed-pro/pull/104) (gemergede PR) |
| `refactor/physical-research-package-split` | `c16483aa6718c468b3b2c84e62d4430220990250` | [#121](https://github.com/E-AI-MODEL/shadowseed-pro/pull/121) (gesloten PR) |
| `refactor/product-research-import-boundary` | `683722f4472e70ff8ecd3ba3fbfc0c703de67206` | [#120](https://github.com/E-AI-MODEL/shadowseed-pro/pull/120) (gemergede PR) |
| `refactor/remove-product-benchmarks` | `5522f9f6c3f10602cc4774f97fed84066359be89` | [#125](https://github.com/E-AI-MODEL/shadowseed-pro/pull/125) (gemergede PR) |
| `refactor/research-package-boundary` | `21197647456bf531d744b965a04fe429444896e4` | [#122](https://github.com/E-AI-MODEL/shadowseed-pro/pull/122) (gemergede PR) |
| `refactor/research-runtime-routing` | `1489d97b87172a2b718ccfad3a3f730520c761c7` | [#123](https://github.com/E-AI-MODEL/shadowseed-pro/pull/123) (gemergede PR) |
| `refactor/research-test-boundary` | `f0ec77da5c1072ad38feeaec7c4cdc3d428a3d9c` | [#124](https://github.com/E-AI-MODEL/shadowseed-pro/pull/124) (gemergede PR) |
| `release/v0.10.1` | `353d91075b9dd986a32fb8dfcc22acb9200a2fb3` | [#145](https://github.com/E-AI-MODEL/shadowseed-pro/pull/145) (gemergede PR) |
| `release/0.8.0-shadowseed-experience` | `7634cda91353a35fcf52a9deef9cb36601e0b0c0` | [#128](https://github.com/E-AI-MODEL/shadowseed-pro/pull/128) (gemergede PR) |
| `release/0.9.1` | `5b02db4cbaa4d0a4dfde1b29cb5019fbaaa900e7` | [#130](https://github.com/E-AI-MODEL/shadowseed-pro/pull/130) (gemergede PR) |
| `release/0.9.2` | `fffaead2e8b81987a38640e30a09fc0d6c5b5a95` | [#132](https://github.com/E-AI-MODEL/shadowseed-pro/pull/132) (gemergede PR) |
| `release/0.10.0` | `2968b7779970f214274123da0f9ff7acdf1f3810` | [#140](https://github.com/E-AI-MODEL/shadowseed-pro/pull/140) (gemergede PR) |
| `release/0.11.0-rc` | `9152b7455dc441473f658ef065bafd35ae3ebbb3` | [#175](https://github.com/E-AI-MODEL/shadowseed-pro/pull/175) (gemergede PR) |
| `release/0.12.0-prep` | `1da75eab49138e26502ab7488a0160091f9e8b30` | [#183](https://github.com/E-AI-MODEL/shadowseed-pro/pull/183) (gemergede PR) |
| `release/0.12.1-prep` | `f8b00b1c9e3c92264c257f4bd9c6dfd2c41824be` | [#192](https://github.com/E-AI-MODEL/shadowseed-pro/pull/192) (gemergede PR) |
| `research/ab5x-structural-intake-audit-20261023` | `6e06ae17fd8f7c557cef44faae3ff6b33a23cc83` | [#206](https://github.com/E-AI-MODEL/shadowseed-pro/pull/206) (gemergede PR) |
| `research/compression-retention-20261025` | `3451b6321e1dea581caccdd2bd014d2a049b6012` | [#221](https://github.com/E-AI-MODEL/shadowseed-pro/pull/221) (gemergede PR) |
| `research/fixed22-zero-20261023` | `49f7f4c37a3668fed6c7727dd90743f2dd95218e` | Geen PR-match |
| `research/g0-blind-semantic-review-packets-20261025` | `7966eea119c5aa1960aa485d8a26317c0c057649` | [#233](https://github.com/E-AI-MODEL/shadowseed-pro/pull/233) (gemergede PR) |
| `research/g0-discoveryworld-executor-smoke-20261025` | `127b0ef54115e704db9a73af82f3f46e2e42f0aa` | [#229](https://github.com/E-AI-MODEL/shadowseed-pro/pull/229) (gesloten PR) |
| `research/g0-discoveryworld-executor-smoke-main-20261025` | `d7ad5ed77a29d6c6858c25753d097f2b81478780` | [#230](https://github.com/E-AI-MODEL/shadowseed-pro/pull/230) (gemergede PR) |
| `research/g0-dual-model-gpt5-luna-ab-20261027` | `ea40b58c36a1a42685d7d2ed5fd84d6071de4c69` | [#258](https://github.com/E-AI-MODEL/shadowseed-pro/pull/258) (open / concept) |
| `research/g0-exact-seed-ablation-20261025` | `ed7e66c96e77839fda4a00b9b3fae0a09f409c5f` | [#254](https://github.com/E-AI-MODEL/shadowseed-pro/pull/254) (open / concept) |
| `research/g0-existing-shadow-travel-main-20261025` | `d4e04a0bcb467f93f49dea0ae92260d0552f1948` | [#238](https://github.com/E-AI-MODEL/shadowseed-pro/pull/238) (gesloten PR) |
| `research/g0-exploratory-real-model-stage1-20261025` | `abff8a02ea866313f33e6ec4f34724d5706e596b` | [#250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250) (open / concept) |
| `research/g0-external-executor-code-audit-20261025` | `bddc1b10b0163656876b53e05eba9cedd58d3028` | [#227](https://github.com/E-AI-MODEL/shadowseed-pro/pull/227) (gemergede PR) |
| `research/g0-late-birth-two-followups-20261027` | `deb7793578e50b96ab93088111a0c026ffe18270` | [#257](https://github.com/E-AI-MODEL/shadowseed-pro/pull/257) (open / concept) |
| `research/g0-method-readiness-20261027` | `affa79887a1adbf48c31266c58f011646c02253c` | [#256](https://github.com/E-AI-MODEL/shadowseed-pro/pull/256) (open / concept) |
| `research/g0-multicase-real-ab-20261026` | `826a32fe5ba0c40b7a94e17a6d438b69a41fc7c4` | [#255](https://github.com/E-AI-MODEL/shadowseed-pro/pull/255) (open / concept) |
| `research/g0-open-inquiry-executor-preflight-20261025` | `824fa18b0ff78d39f2ade38e19a17818b5ace0ba` | [#231](https://github.com/E-AI-MODEL/shadowseed-pro/pull/231) (gemergede PR) |
| `research/g0-real-shadowchat-world-bridge-20261025` | `8c8c313da180416d9e749b747ac35ca990d83ec2` | [#232](https://github.com/E-AI-MODEL/shadowseed-pro/pull/232) (gemergede PR) |
| `research/g0-resolve-feedback-regimes-20261025` | `a6cd62841b081fb6f7e5308a79ab5412b852f178` | [#226](https://github.com/E-AI-MODEL/shadowseed-pro/pull/226) (gemergede PR) |
| `research/g0-shadow-travel-corrected-main2-20261025` | `64b38efc61ca6fb4a1d7caee3ad781ea7d24119a` | [#239](https://github.com/E-AI-MODEL/shadowseed-pro/pull/239) (gemergede PR) |
| `research/g0-ssot-polarity-falsification-20261025` | `1516061106418bf45326afdc8c17817839753089` | [#240](https://github.com/E-AI-MODEL/shadowseed-pro/pull/240) (gemergede PR) |
| `research/g0-v3-review-readiness-20261025` | `e279f755a7d9fabfa7ddfc03e7b801dd94470a7c` | [#253](https://github.com/E-AI-MODEL/shadowseed-pro/pull/253) (gemergede PR) |
| `research/g0-weightless-inquiry-causal-boundary-20261025` | `38fcea8a50553ae468a7cf4a536ebba51eff3281` | [#236](https://github.com/E-AI-MODEL/shadowseed-pro/pull/236) (gesloten PR) |
| `research/gpt5-gpt6-bounded-api-pilot` | `13fda4189b3cff306642c41c47524dc3648bf1f4` | Geen PR-match |
| `research/live-compression-retention-20261025` | `6a111f480b97e8d611f9409d9e344f2356099f11` | [#222](https://github.com/E-AI-MODEL/shadowseed-pro/pull/222) (gemergede PR) |
| `research/next-ab-method-repair-20261026` | `38bc3a9a645b6d8638b85dc2392ce0618d1a2b71` | Geen PR-match |
| `research/possibility-pilot-20261024` | `6a279cd1a88d22e6e35d4f2a4a125bb9aaceda55` | [#220](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220) (gemergede PR) |
| `research/pro-atomicity-fate-audit-20261028` | `53d7b74a364689cf9ee489d620730632d1a2923e` | [#261](https://github.com/E-AI-MODEL/shadowseed-pro/pull/261) (open / concept) |
| `research/q1-q2-real-seed-rf-20261025` | `b3e81976be27a3ab52b9b92f4a9a5134c330962a` | [#251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251) (open / concept) |
| `research/q1q2-two-point-48-20261028` | `340f25fd32acc1acf411830f50b536eff6b1c5c1` | [#260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) (open / concept) |
| `research/raw-stage-trajectory-reconstruction-20261028` | `e7ca66d216c18bee57e0b1f5492b9640bb8d515b` | [#263](https://github.com/E-AI-MODEL/shadowseed-pro/pull/263) (open / concept) |
| `research/relational-candidate-admission-20261026` | `1a8e0947ff09f5bfe09b939a2dd4345a7ae2bb18` | Geen PR-match |
| `research/ssot-legacy-review-preflight-20261025` | `6c19b7fe39fb77dfebcf82163d157ad6d3e97d0d` | [#244](https://github.com/E-AI-MODEL/shadowseed-pro/pull/244) (open / concept) |
| `research/ssot-relation-review-contract-20261025` | `a6481f2524c4a74e205911780ac3705553cbf59a` | [#242](https://github.com/E-AI-MODEL/shadowseed-pro/pull/242) (gesloten PR) |
| `research/step1-eai-blindspot-method-audit-20261025` | `1028127969a94733527a5a265c672e4cf5e6ba08` | [#225](https://github.com/E-AI-MODEL/shadowseed-pro/pull/225) (gemergede PR) |
| `research/step1-gap-birth-instrument-20261025` | `377510150a31c0cc9488510113f657b575f0f625` | [#224](https://github.com/E-AI-MODEL/shadowseed-pro/pull/224) (gemergede PR) |
| `research/step1-model-signals-gap-origin-20261025` | `ea8c301a0b7dcb84e8c5684b186c3fe0a2968f44` | [#223](https://github.com/E-AI-MODEL/shadowseed-pro/pull/223) (gemergede PR) |
| `research/weightless-birth-lineage-integrated-20261025` | `1fabcd1d37d5e6684efa1ecbaa7e89ffe1420e6c` | [#247](https://github.com/E-AI-MODEL/shadowseed-pro/pull/247) (gemergede PR) |
| `research/weightless-longitudinal-handoff-20261025` | `dfcd95b510c90401ca68ae0de37c7d25e8c63f46` | [#249](https://github.com/E-AI-MODEL/shadowseed-pro/pull/249) (gemergede PR) |
| `research/weightless-origin-to-inquiry-handoff-20261025` | `001d53a98070dd80e376d09bfdcfd24524606957` | [#245](https://github.com/E-AI-MODEL/shadowseed-pro/pull/245) (gesloten PR) |
| `test/huggingface-space` | `d434c72b4b1a64789cb8b0a3c785fcd46fe7b9ba` | Geen PR-match |
| `ui/shadowseed-workbench-mockup` | `dc19ea3e627a67433246117548654232651016be` | [#139](https://github.com/E-AI-MODEL/shadowseed-pro/pull/139) (gemergede PR) |
| `ui/v0.10-workbench-cleanup` | `82fb71300861664c502868fcb4a2cc835ef97036` | [#143](https://github.com/E-AI-MODEL/shadowseed-pro/pull/143) (gesloten PR) |
| `upgrade/v0.6.0-evidence-research-access` | `925611c45aae9dc50238924bd1bcb7ee37fcf78d` | [#86](https://github.com/E-AI-MODEL/shadowseed-pro/pull/86) (gemergede PR) |
| `v0.11-gate-state-alignment` | `8fd1037b5e728ed66aecff624e309f2e6556f65b` | Geen PR-match |
| `v0.11-runtime-foundation` | `4a2ff9e5452ae2cd96acff96336371c9ae11fee1` | [#147](https://github.com/E-AI-MODEL/shadowseed-pro/pull/147) (gemergede PR) |
| `workbench/ollama-embeddings` | `f9f02eb5e84aa2a128b81902c78c46f5231c0c2e` | [#137](https://github.com/E-AI-MODEL/shadowseed-pro/pull/137) (gesloten PR) |
| `workbench/v0.10-ui-reset` | `b2cab1da046195636d24bd2c22bbbd05e6516eea` | [#134](https://github.com/E-AI-MODEL/shadowseed-pro/pull/134) (gemergede PR) |

## Reproductie van dit register

- [Branches API, pagina 1](https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/branches?per_page=100&page=1) en [pagina 2](https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/branches?per_page=100&page=2).
- [PR API, pagina 1](https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/pulls?state=all&per_page=100&page=1), [pagina 2](https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/pulls?state=all&per_page=100&page=2) en [pagina 3](https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/pulls?state=all&per_page=100&page=3).
- Opgehaald op 28 oktober 2026; de API-links hierboven geven bij later openen mogelijk al een andere stand. De head-SHA's hierboven leggen deze inventarisatie vast.
- Dit document verandert geen branch, PR-base, runtime, testuitslag, artifact, bewijslabel, Gate-regel of onderzoeksconclusie.
