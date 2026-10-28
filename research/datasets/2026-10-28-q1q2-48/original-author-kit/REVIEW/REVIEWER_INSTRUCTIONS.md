# Shadow Seed Learning: onafhankelijke beoordeling van 24 vervolgtrajecten

U ontvangt een van twee geblindeerde pakketten uit een verkennende proef. De twee onderzoeksmomenten horen bij één fictieve meetboeicasus. De oorspronkelijke hostgeschiedenis is zichtbaar om te beoordelen wat al gezegd is. De armtoewijzing, detectorseeds en intakestatus blijven voor de beoordelaar onbekend.

Beoordeel per traject **beide** vervolgantwoorden in hun context. Vul de velden onder `label` zelfstandig in en licht inhoudelijke keuzes toe onder `reason`. Kies per ja/nee-veld `true` of `false`; gebruik `null` wanneer het gegeven ontbreekt of een oordeel niet mogelijk is.

- `relation_found_without_stated_note`: benoemt het traject een specifieke relatie die niet als feit in de oorspronkelijke geschiedenis stond? Let op: een bestaande hypothese is niet hetzelfde als een vastgesteld feit.
- `distinct_second_relation`: opent de tweede vervolgbeurt inhoudelijk een andere relatie of voorwaarde dan de eerste, in plaats van een synoniem of uitgebreidere beschrijving?
- `falsifiable_test`: noemt het model een concrete waarneming die de beweerde relatie ook zou kunnen weerleggen?
- `not_in_original_history`: ontbreekt die specifieke nieuwe relatie werkelijk in de meegegeven oorspronkelijke hosttekst, inclusief reeds voorgestelde methoden?
- `only_paraphrase_or_echo`: wordt dezelfde gedachte vooral herhaald zonder een nieuwe toetsbare relatie?
- `unsupported_fact_claim`: wordt een niet-gemeten of niet-gemeld gegeven als vastgesteld gepresenteerd?
- `reason`: citeer een kort fragment uit het eerste of tweede antwoord dat het oordeel draagt. Leg bij twijfel vast wat ontbreekt.

**Geen voorkeur voor langere antwoorden.** Het correct weigeren om een irrelevante nieuwe relatie te verzinnen kan een goede uitkomst zijn. Niet alles wat nieuw klinkt is waar. Beoordeel de aanwezigheid van een *toetsbare onderzoeksmogelijkheid*, niet of het onderzoek al gedaan is.

Uw pakket toont niet welke arm de originele seed kreeg. Raad of zoek die niet op. Lees niet vooraf de publieke projectanalyse of de andere beoordelaar. Geef uw ingevulde JSON terug aan de onderzoeker. Het gedeelde reviewbestand bevat volledige oorspronkelijke modelantwoorden: behandel die als onderzoeksmateriaal en zet ze niet op een publieke website.

**Status bij levering:** 0 ingeleverde menselijke beoordelingen. De onderzoeksleider mag pas ontblinden nadat beide sets beoordelingen definitief zijn ingeleverd.
