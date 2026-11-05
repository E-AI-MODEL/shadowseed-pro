# Anchor-tail: kleine, vooraf vastgelegde liveproef

Datum: 5 november 2026. Verkennend, twee fictieve gevallen. Geen claim over echte neurale verborgen redeneringen.

## Vraag
Kan een lager gerangschikte maar plausibele mogelijkheid na een verkorte samenvatting en twee extra werkafspraken alsnog worden onderzocht, en verschilt dat bij gewoon doorgaan, extra reflectie, gewone notities en een gewichtloos bewaarde kandidaat?

## Werkelijke ingreep
- Een GPT-4.1 Chat Completions-aanroep kiest één eerste onderzoeksspoor A-D. Met `logprobs=true` en maximaal twintig `top_logprobs` bekijken we de kansen op **de eerste token** die een van de vier vooraf opgestelde labels is. Dit zijn géén kansen dat een volledig antwoord juist is.
- De minst waarschijnlijke **waargenomen** alternatief-tokenletter buiten de eerste keuze wordt de onderzoekskandidaat. Minder dan twee waargenomen labels stopt het experiment; geen verzonnen tail-rangorde.
- GPT-4.1 maakt vervolgens één korte samenvatting en twee opvolgende werkafspraken. Die drie outputs zijn voor **alle vier eindcondities exact gelijk**. De tail-kandidaat verschijnt daarin niet bewust als nieuwe extra instructie.
- Per casus wordt hierna vooraf geschreven, scenario-specifieke nieuwe informatie voor de geselecteerde kandidaat zichtbaar. Die informatie is **bewust kandidaatvriendelijk**; een positieve uitkomst bewijst geen natuurlijk herontdekkingsvoordeel.
- Vier eindvragen worden in willekeurige volgorde aan hetzelfde model voorgelegd, zonder gedeelde eindcontext: regular (geen extra opdracht); reflect (gerichte check van het hoofdspoor); ordinary_note (de kandidaat als gewone notitie); shadow_weightless (dezelfde kandidaat expliciet als onbewezen en vrijblijvend bewaard). De laatste twee armen bezitten aanvullende informatie. Zij zijn alleen onderling inhoudsgelijk.

## Wat bewaren we
Alle prompts, provider-response-ID's, model-ID, tokenverbruik, volledige antwoorden, eerste-tokenlogkansen en hashes. Geen geheimen. Verwerping of afbreking maakt ook een gedeeltelijk bestand.

## Wat niet is onderzocht
- Geen echte autonome seedgeboorte: de vier opties zijn geschreven door de onderzoeker.
- Geen productengine, geen echte Gate of gewichtsverandering. De gewichtsloze notitie is een gecontroleerde onderzoeksinterventie.
- Geen gehele antwoordkansen, geen rechtstreekse toegang tot verborgen redeneringen, geen bewijs over de kwaliteit van de extreme staart.
- Geen statistische generalisatie, geen blinde onafhankelijke beoordeling.
- De deelnemer/model ziet bij de eindvraag dezelfde nieuwe informatie, maar alleen de note-armen zien de letterlijk teruggehaalde mogelijkheid.

## Succes en mogelijke teleurstelling
We bekijken per casus of de laaggewaardeerde optie in de eindantwoordtekst als serieuze, toetsbare mogelijkheid terugkomt; of ze de vaste werkrichting onterecht verdringt; of de reflectiearm haar zonder geheugen vindt; en of de notitie- en weightless-vormgeving werkelijk verschillen. Als alle vier de optie even goed behandelen, is dit een niet-onderscheidende proef.

Model: `gpt-4.1`, maximaal 16 echte modelaanroepen, geen automatische retry, geraamde kostenbeveiliging $0,50. De bestaande GitHub Actions Environment `OpenAI key` levert `secrets.OPENAI_KEY`. Geen kosten buiten dit experiment, geen wijzigingen aan productiecode of main.
