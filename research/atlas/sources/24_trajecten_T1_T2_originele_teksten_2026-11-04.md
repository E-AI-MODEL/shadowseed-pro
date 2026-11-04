# Oorspronkelijke onderzoeksvragen van 24 tweeturntrajecten

**Brongebonden leesdossier, 4 november 2026.** De originele modelantwoorden zijn letterlijk overgenomen uit `OWNER/observed-owner.json`. De T1-tekst is nodig om te beoordelen wat T2 echt toevoegt. Dit is geen nieuwe onafhankelijke of blinde beoordeling. De volgorde is voor lezen gesorteerd; de tekst en receipts zijn niet veranderd.

Bij elk antwoord staat de oorspronkelijke checksum. De labels in de subkoppen komen uit een apart, handmatig gecodeerd CSV-bestand en zijn geen labels van de oorspronkelijke onderzoekers.

## B-D1 | battery_after_T3 | deliberate_search | herhaling 1

**Voorlopige interpretatie:** Voegt temperatuur als mogelijke gemeenschappelijke oorzaak toe.

### Eerste modelbeurt | SHA-256 `09da93b8937e9236c66a7cd794f2bc0b8864c04b38a0dcc4496fa5e4c91bb5e3`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één van de periodes. De klokafwijking is niet berekend; er is geen tweede boei als controlegroep. Er is niet gemeld dat de beelden uit die periode aantoonbaar anders waren, of wanneer de spanningsdaling precies optrad.

**Onderscheidende vraag:** Ging een spanningsdaling vooraf aan veranderingen in de beeldvorming, of hing de spanningsdaling juist samen met het moment of de activiteit van de camera? Dat onderscheidt de hypothese *spanning beïnvloedt de beelden* van een omgekeerde richting, zoals *camera-activiteit gaat samen met spanningsdaling*. Geen van beide relaties is met de huidige beschrijving vastgesteld.

**Toetsbare waarneming:** Leg in een nieuwe meting spanning, camera-activiteit en ruwe beelden vast met een gecontroleerde gedeelde klok. Onderzoek dan of veranderingen in beeldkenmerken systematisch ná spanningsdalingen optreden, of dat spanningsdalingen juist vaker ná of tijdens camera-activiteit optreden. Een gecontroleerde test met bekende, stabiele scènes en gevarieerde voedingsspanning kan aanvullend toetsen of spanning de beeldvorming kán beïnvloeden. Geen van die waarnemingen op zichzelf bewijst de oorzaak van de eerdere grensverschillen.

**Ontbrekende gegevens:** De bestaande melding geeft geen tijdsverloop, beeldkenmerken of gesynchroniseerde registraties. Daarom kan deze nieuwe richting niet met de beschreven gegevens worden getoetst.
```

### Tweede modelbeurt | SHA-256 `00bfe992eb7e1c071753fbf83f8603605707cbbce27e5f3a1b4835fe64a814d4`

```text
**Feit:** De beschrijving meldt een lage batterijspanning tijdens één periode, maar bevat geen tijdreeks van spanning en beeldkenmerken. Ook zijn temperatuur en andere omstandigheden niet vermeld. De bestaande waarneming kan dus geen verband tussen spanning en beeldvorming aantonen.

**Mogelijke nieuwe afhankelijkheid:** Een derde factor, zoals temperatuur, zou zowel de gemeten batterijspanning als de camera-uitvoer kunnen beïnvloeden. Dan kan spanning en beeldkwaliteit samen veranderen zonder dat de spanning zelf de beelden veroorzaakt. Dit is een hypothese, geen gemeld kenmerk van de situatie.

**Weerlegbare toets:** Test de camera met een stabiele, bekende scène bij gecontroleerd gevarieerde spanning én temperatuur, en registreer beide samen met de beelden. Als beeldkenmerken bij gelijke temperatuur systematisch met de spanning veranderen, blijft een spanningsinvloed mogelijk; als het verband verdwijnt zodra temperatuur constant wordt gehouden, past dat eerder bij temperatuur als verklaring. De test kan een effect onder die omstandigheden toetsen, maar niet bewijzen wat de oorzaak was van de eerdere grensverschillen.

Voor de bestaande periode ontbreken de gegevens om deze toets achteraf uit te voeren. Dit is dus een nieuwe toets voor vervolgmetingen, geen conclusie over de eerdere meting.
```

## B-D2 | battery_after_T3 | deliberate_search | herhaling 2

**Voorlopige interpretatie:** Werkt belasting en temperatuur uit na de eerdere omgekeerde-oorzaaksvraag.

### Eerste modelbeurt | SHA-256 `3dca5b3b245462174cb5b846c199647516fcb2a4003c4b6272fc62c67aadd4ed`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. Er is geen tweede boei, de behuizing is niet verwisseld en de klokafwijking is onbekend. De beschrijving zegt niet of de spanningsdaling vóór, tijdens of na de relevante beeldopnamen plaatsvond.

**Onderscheidende onderzoeksvraag:** *Kan de spanningsdaling juist zijn opgetreden als gevolg van camera- of systeemactiviteit, in plaats van die activiteit of de grensschatting te hebben beïnvloed?* Dat is een omgekeerde-richtinghypothese, geen vastgesteld mechanisme; er is geen informatie dat zulke activiteit de spanning daadwerkelijk verandert.

**Toetsbare waarneming:** registreer bij toekomstige metingen spanning en cameragebeurtenissen met hoge tijdsresolutie en een gedeelde klok, ook tijdens perioden zonder beeldopnamen. Als spanningsdalingen herhaaldelijk ná opnamen of andere systeemactiviteit optreden, past dat bij de omgekeerde richting. Als ze consequent al vóór zulke activiteit beginnen, wordt die verklaring minder aannemelijk. Een enkele periode of alleen vijfminutengemiddelden kan de volgorde niet betrouwbaar vaststellen.

Dit levert een nieuwe, toetsbare vraag op, maar geen conclusie over wat er in de bestaande periode is gebeurd.
```

### Tweede modelbeurt | SHA-256 `0d3464591650ed389bac88bcc5acf3ac4d6681b0e0e8faf40897abbe26bb7091`

```text
**Feit:** Er is een melding van lagere batterijspanning tijdens één periode. De beschikbare beschrijving vermeldt geen gelijktijdige stroom- of temperatuurmetingen, geen meetfrequentie voor de spanning en geen gecontroleerde vergelijking tussen activiteit en inactiviteit van de camera.

**Nieuwe, onderscheidende vraag:** Was de gemelde lage spanning een aanhoudende verandering in de batterijtoestand, of een tijdelijke spanningsdaling die samenhing met elektrische belasting of temperatuur? Dat is een andere mogelijke afhankelijkheid dan alleen de tijdsvolgorde van spanning en camera-activiteit. Belasting en temperatuur zijn hier mogelijke verklaringen, geen vastgestelde factoren.

**Weerlegbare toets:** registreer in een vervolgmeting met een gedeelde klok de spanning, stroom, temperatuur en cameragebeurtenissen met voldoende tijdsresolutie. Vergelijk spanningen tijdens vergelijkbare temperaturen en camerabelasting, en vergelijk ook perioden met en zonder beeldopnamen. Een daling die vooral tijdens hogere stroom optreedt en daarna herstelt, past bij een tijdelijke belastingseffecthypothese; een daling die onder vergelijkbare belasting en temperatuur aanhoudt, past daar minder goed bij. Dat onderscheid toetst de spanningsdynamiek, maar toont op zichzelf niet aan dat de spanning de beeldkwaliteit of grensschatting beïnvloedde.

**Ontbrekende gegevens:** zonder zulke gelijktijdige metingen is niet vast te stellen of deze afhankelijkheid in de gemelde periode speelde. De nieuwe toets is dus denkbaar voor vervolgmetingen, maar levert geen nieuwe conclusie over de bestaande waarneming.
```

## B-D3 | battery_after_T3 | deliberate_search | herhaling 3

**Voorlopige interpretatie:** De omgekeerde richting was al in T1 genoemd; T2 formuleert factoriële proef.

### Eerste modelbeurt | SHA-256 `72d9267ef255f471d17ae97294ccca7abb688144b0a1f6704e9f3dfdd7fa4a1b`

```text
**Onderscheidende onderzoeksvraag:** Is de lage batterijspanning een oorzaak van veranderingen in de camerabeelden, of slechts een gelijktijdige aanwijzing voor andere omstandigheden die de beelden beïnvloeden? De tweede mogelijkheid keert de gebruikelijke aanname om: spanning hoeft niet de oorzaak te zijn, ook als ze samenvalt met afwijkende grensschattingen.

**Feiten:** Van één periode is gemeld dat de batterijspanning lager was. Er is geen tweede boei als controlegroep, de behuizing is niet verwisseld en de camera- en sensorklokken zijn niet gecontroleerd gesynchroniseerd. De beschikbare informatie stelt geen verband of oorzaak vast.

**Toetsbare hypothese:** Als lage spanning zelf de beeldvorming beïnvloedt, zouden beelden van een onveranderlijke scène bij lagere spanning systematisch anders kunnen uitvallen dan beelden bij hogere spanning, bij gelijkblijvende camera-instellingen. Een gecontroleerde proef kan spanning variëren en tegelijk spanning, beeldinstellingen en beeldkenmerken registreren. Geen reproduceerbaar verschil binnen het geteste spanningsbereik zou die hypothese daar verzwakken, maar niet uitsluiten dat andere veldomstandigheden ertoe deden.

Om de omgekeerde mogelijkheid in het veld te beoordelen, zouden gesynchroniseerde registraties van spanning, stroomverbruik, opname-instellingen en beeldtijdstippen nodig zijn. Die gegevens ontbreken nu; bovendien is niet bekend hoe de camera of voeding reageert op verschillende opnameomstandigheden. Daarom volgt uit de gemelde lage spanning op zichzelf **geen nieuwe conclusie over de oorzaak** van de grensverschillen.
```

### Tweede modelbeurt | SHA-256 `671672f4460a36dd9dd4bca6cd635060f578d7a8c384998c1b0c33b2b1d8aa30`

```text
De eerdere vraag maakt vooral **spanning → beeldvorming** en een mogelijke derde factor bespreekbaar. Een andere, toetsbare afhankelijkheid is de omgekeerde richting: **opnameactiviteit of stroomverbruik → spanningsdaling**. Dan kan lage spanning samenvallen met afwijkende beelden omdat de opnamebelasting beide beïnvloedt, zonder dat de spanningsdaling zelf de beeldverandering veroorzaakt.

**Feiten:** Er is een logmelding van lage batterijspanning tijdens één periode. Er zijn geen tweede boei, ruwe bewegingssensorwaarden of berekende klokafwijking vermeld. Ook zijn geen gegevens gegeven over stroomverbruik, opnamebelasting of spanning bij de camera zelf.

**Hypothese:** Meer opnameactiviteit kan de spanning doen dalen; een spanningsdaling kan daarnaast eventueel de beeldvorming beïnvloeden. Dit zijn afzonderlijke mogelijkheden, geen vastgestelde relaties.

**Toets:** Voer een proef uit met een onveranderlijke scène. Varieer opnameactiviteit en voedingsspanning onafhankelijk van elkaar, en registreer gelijktijdig de spanning bij de camera, het stroomverbruik, de instellingen en beeldkenmerken. Als de spanning daalt bij hogere opnamebelasting terwijl een stabiele voeding de beeldkenmerken gelijk houdt, ondersteunt dat de mogelijkheid dat belasting de spanningsdaling verklaart, niet dat lage spanning de beeldverandering veroorzaakt. Als beeldkenmerken bij gelijkblijvende belasting reproduceerbaar veranderen wanneer alleen de spanning wordt verlaagd, ondersteunt dat juist een effect van spanning binnen het geteste bereik.

De bestaande veldmelding kan deze richtingen niet uit elkaar halen. Zonder zulke gecontroleerde of beter gesynchroniseerde gegevens volgt er dus geen nieuwe conclusie over de oorzaak van de grensverschillen.
```

## B-O1 | battery_after_T3 | ordinary | herhaling 1

**Voorlopige interpretatie:** Voegt belichting als moderator toe aan bestaande spanningstest.

### Eerste modelbeurt | SHA-256 `0a6f1e32ebabfaf5a08c8ab40be64940dc9662d4af270a6fb5b641e658f7148c`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. Er is geen tweede boei als controlegroep, en de klokafwijking tussen camera en bewegingssensor is onbekend. De eerdere voorgestelde benchtest met een onveranderlijke scène en verschillende voedingsspanningen is al een mogelijke toets.

**Onderscheidende onderzoeksvraag:** Verandert bij lagere voedingsspanning de *beeldkwaliteit* — bijvoorbeeld contrast of belichting — op een manier die de geschatte grens tussen helder en troebel water verschuift, ook wanneer de scène zelf niet verandert?

**Toetsbare waarneming:** Maak onder gecontroleerde omstandigheden opnamen van dezelfde onveranderlijke scène bij verschillende spanningen, en laat de grensschatting beoordelen zonder dat beoordelaars de spanningsinstelling kennen. Een spanningsafhankelijke verandering in beelden of grensschattingen zou de hypothese ondersteunen; het uitblijven daarvan onder die testomstandigheden zou haar verzwakken. Geen van beide uitkomsten bewijst op zichzelf wat er tijdens de veldperiode gebeurde.

**Ontbrekende gegevens:** Uit de beschrijving blijkt niet of de lage spanning samenviel met veranderde beeldkwaliteit of met de eerder genoemde afwijkende grensschattingen. Die veldsamenhang kan daarom nu niet worden vastgesteld.
```

### Tweede modelbeurt | SHA-256 `023d8286b2ee7d5fa0ad8686afa25476c635b2496335733617357fa32d9e886c`

```text
**Feit:** De eerdere vraag stelde een benchtest voor met dezelfde onveranderlijke scène bij verschillende voedingsspanningen. Er is niet vermeld onder welke belichting die test zou plaatsvinden, of hoe de camera-instellingen daarop reageren.

**Nieuwe, conditionele onderzoeksvraag:** Is een eventueel effect van lage voedingsspanning op de grensschatting afhankelijk van de belichting? Dat is een andere toets dan alleen nagaan óf spanning bij één testopstelling verschil maakt.

**Weerlegbare toets:** Gebruik een scène met een bekende, vaste grens en test meerdere spanningsniveaus bij zowel heldere als zwakke belichting. Houd overige omstandigheden zo constant mogelijk en laat de grensschattingen blind beoordelen. Als het verschil tussen spanningsniveaus verandert met de belichting, ondersteunt dat een afhankelijkheid van belichting; als dat niet gebeurt, verzwakt dat die hypothese binnen de geteste omstandigheden.

**Ontbrekende gegevens:** Er is niets bekend over de belichting tijdens de periode met lage spanning. Zelfs een uitkomst in de test zou daarom niet aantonen dat belichting de veldverschillen heeft veroorzaakt.
```

## B-O2 | battery_after_T3 | ordinary | herhaling 2

**Voorlopige interpretatie:** Voegt instelmodus toe aan dezelfde spanningstest.

### Eerste modelbeurt | SHA-256 `fd43f8442f5e01d3cbdf79170ea8ae8a344decbec7b7f4460bab7d412be37148`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. De behuizing is niet verwisseld en er is geen tweede boei als controlegroep.

**Toetsbare vraag:** Kan een lagere voedingsspanning, bij gelijkblijvende camera-instellingen en een onveranderlijke scène, de beeldkwaliteit of de geschatte grens tussen helder en troebel water veranderen?

Een toets zou bestaan uit gecontroleerde opnamen bij verschillende spanningen, met dezelfde camera en scène, en een vooraf vastgelegde maat voor beeldkwaliteit of grensschatting. Als die uitkomsten niet veranderen binnen de meetonzekerheid, wordt deze specifieke mogelijkheid minder aannemelijk; een verandering zou laten zien dat spanning onder die testomstandigheden invloed kán hebben.

Dit is geen nieuwe, onafhankelijke veldtoets: dezelfde gecontroleerde spanningsproef is al voorgesteld. **Ontbrekende gegevens** zijn onder meer de precieze spanningsverloopgegevens, camerabeelden en de tijdsrelatie ertussen. De huidige informatie rechtvaardigt dus geen nieuwe conclusie over de veldperiode.
```

### Tweede modelbeurt | SHA-256 `ac6d681dbfcf630271eaf0cdab02ce4eabdf1ee0b327ebd273aee3d1a0021d77`

```text
**Feit:** Er is een melding van lage batterijspanning tijdens één veldperiode. Er is niet vermeld of de camera automatische belichtings- of andere aanpasbare instellingen gebruikt.

**Onderscheidende, toetsbare vraag:** Hangt een eventueel effect van voedingsspanning op de grensschatting af van de camera-instellingen — bijvoorbeeld doordat het effect alleen optreedt wanneer instellingen automatisch kunnen veranderen?

Dat is een andere voorwaarde dan alleen testen of spanning bij een onveranderlijke scène invloed kán hebben. Een toets zou bij meerdere spanningsniveaus opnamen vergelijken met instellingen vastgezet en, als de camera dat ondersteunt, met automatische instellingen. Scène en overige omstandigheden moeten gelijk blijven. Een verschil tussen die twee condities zou wijzen op een mogelijke afhankelijkheid van de instellingen; geen verschil binnen de meetonzekerheid zou die specifieke mogelijkheid verzwakken.

**Ontbrekende gegevens:** Of de camera zulke automatische instellingen heeft en of die tijdens de veldperiode actief waren, is onbekend. De toets kan daarom alleen worden voorgesteld als de camera die modi ondersteunt. Zelfs een gevonden effect in een laboratoriumtest zou op zichzelf niet aantonen dat dit de veldwaarneming verklaart.
```

## B-O3 | battery_after_T3 | ordinary | herhaling 3

**Voorlopige interpretatie:** Voegt vooraf vastgelegd overgangscontrast toe.

### Eerste modelbeurt | SHA-256 `253c29f1939c81526831e54a20220396d7de76b172a264ab6d372e186b4ea4ab`

```text
**Feit:** Een externe log meldt lagere batterijspanning tijdens één periode. De behuizing is niet verwisseld en er is geen tweede boei als controlegroep. De klokafwijking is niet vastgesteld.

**Toetsbare vraag:** Verandert de geschatte grens tussen helder en troebel water wanneer de camera bij lagere spanning werkt, als de scène, camera-instellingen en verwerking gelijk blijven?

**Toets:** Maak onder gecontroleerde omstandigheden herhaalde opnamen van een onveranderlijke scène bij verschillende gemeten spanningen. Vergelijk blind beoordeelde grensschattingen en beeldkenmerken. Een herhaalbare verandering bij lagere spanning ondersteunt een effect onder die testomstandigheden; uitblijven ervan weerlegt zo’n effect niet absoluut, maar begrenst het binnen de geteste spanningen en meetnauwkeurigheid.

**Ontbrekende gegevens:** De huidige veldinformatie toont niet of de lage spanning samenviel met veranderingen in beeldkwaliteit of grensschattingen; de onzekere klok maakt die koppeling bovendien lastig. De voorgestelde test kan dus een mogelijk camera-effect toetsen, maar niet vaststellen dat spanning het verschil in de betreffende veldperiode veroorzaakte.
```

### Tweede modelbeurt | SHA-256 `2d9b4250954e1bf76b626e67c4b9fd1e2d22048caff91b4ecfa879b71da19f22`

```text
**Feit:** De voorgestelde test vergelijkt spanningsniveaus bij een onveranderlijke scène en gelijk gehouden camera-instellingen. Er zijn geen resultaten van die test gegeven.

**Nieuwe, voorwaardelijke onderzoeksvraag:** Hangt een eventueel effect van de voedingsspanning op de grensschatting af van hoe duidelijk de overgang tussen helder en troebel water in het beeld is? Dat is een andere vraag dan óf spanning onder één testconditie effect heeft: ze onderzoekt of de relatie verschilt tussen scènes met een duidelijke en een vage overgang.

**Toets:** Neem onder gecontroleerde omstandigheden beelden op bij meerdere gemeten spanningen én bij scènes met verschillende, vooraf vastgelegde overgangscontrasten. Houd de camera-instellingen en verwerking gelijk, herhaal de opnamen en laat beoordelaars de grens blind schatten. Vergelijk vervolgens of het verschil tussen spanningsniveaus varieert met het overgangscontrast. Als dat verschil niet groter is dan de meetonzekerheid binnen de geteste omstandigheden, vindt de toets geen steun voor zo’n afhankelijkheid; dat sluit haar buiten die omstandigheden niet uit.

**Ontbrekende gegevens:** Er is niet vermeld of de oorspronkelijke grensschatting vooral onzeker is bij vage overgangen. De nieuwe toets onderzoekt daarom een mogelijke afhankelijkheid, niet een reeds aangetoond kenmerk van de veldgegevens.
```

## B-P1 | battery_after_T3 | placebo | herhaling 1

**Voorlopige interpretatie:** Verwerpt de domeinvreemde notitie; geen andere toets.

### Eerste modelbeurt | SHA-256 `09495791daf8f439d153f318061ddc2daa4b658700982ba9e885ca411b5f7f17`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. Er zijn geen gegevens genoemd over slijtvastheidsmetingen; die aantekening biedt daarom geen onderbouwde nieuwe onderzoeksvraag voor deze casus.

**Toetsbare vraag:** Verandert de geschatte grens tussen helder en troebel water wanneer de camera bij lagere voedingsspanning werkt, terwijl scène en camera-instellingen gelijk blijven?

**Toets:** Maak herhaalde opnamen van een onveranderlijke, bekende scène bij verschillende voedingsspanningen en vergelijk de grensschattingen met hun meetonzekerheid. Een systematisch verschil buiten die onzekerheid zou de mogelijkheid ondersteunen dat spanning de beeldvorming of grensschatting beïnvloedt. Geen verschil binnen de geteste omstandigheden zou die mogelijkheid verzwakken, maar niet uitsluiten dat spanning in het veld via andere omstandigheden meespeelt.

**Beperking:** Zo’n test kan niet vaststellen dat de lage spanning de afwijking in de veldperiode veroorzaakte. Daarvoor ontbreken onder meer betrouwbare tijdskoppeling en aanvullende veldgegevens.
```

### Tweede modelbeurt | SHA-256 `77252d242b8f7c7db5fc06cd9218f06e821b3bbbb05aaae2805af179f1fde34b`

```text
**Feit:** De casus noemt een mogelijke lage batterijspanning, maar geen slijtvastheidsmetingen of slijtage aan de apparatuur. De aantekening over afwijkende slijtvastheidsmetingen voegt daarom geen onderbouwde informatie toe.

**Conclusie:** Er volgt geen nieuwe, casusgebonden onderzoeksvraag over slijtvastheid. Die vraag zou pas toetsbaar worden als zulke metingen daadwerkelijk bestaan en duidelijk is welk onderdeel of materiaal ermee is bedoeld. Dan zouden herhaalde metingen, met hun meetonzekerheid, kunnen uitwijzen of de afwijkingen reproduceerbaar zijn. Zonder die gegevens zou dat onderzoek een niet-vermelde grootheid introduceren, niet een nieuwe afhankelijkheid van de eerder voorgestelde spanningstest onderzoeken.
```

## B-P2 | battery_after_T3 | placebo | herhaling 2

**Voorlopige interpretatie:** Noemt mogelijkheid slechts onder expliciete voorwaarde; geen onderbouwde casustoets.

### Eerste modelbeurt | SHA-256 `39140b1e2f7e5c3d065ff152bed05932dc4ad629074f012c4fb487626339d1c0`

```text
**Feit:** De voorgeschiedenis noemt een periode met lagere batterijspanning, maar geen slijtvastheidsmetingen. De aantekening over slijtvastheid levert daarom geen onderbouwde onderzoeksvraag voor deze casus op.

**Mogelijke toetsbare vraag:** *Gaan lagere batterijspanningen samen met veranderingen in de beeldkwaliteit van de boeicamera?* Dat is een vraag naar samenhang, geen aanname dat er een verband bestaat.

**Toetsende waarneming:** vergelijk beeldkwaliteitsmaten van frames met bijbehorende spanningsregistraties, rekening houdend met de onzekere klokafwijking. Een gecontroleerde test van de camera bij verschillende voedingsspanningen kan daarnaast toetsen of spanningsverandering beeldkwaliteit kán beïnvloeden. Er zijn geen spanningsreeks, klokcorrectie of beeldkwaliteitsmetingen vermeld; zonder zulke gegevens kan de vraag nu niet worden beantwoord.
```

### Tweede modelbeurt | SHA-256 `33da4bce05bdcf8bac66664d113b8568deb7b757362e93da230dac9b32c3554d`

```text
**Feit:** De voorgeschiedenis vermeldt een periode met lagere batterijspanning en een mogelijke vergelijking met beeldkwaliteit. Er zijn geen slijtvastheidsmetingen of aanwijzingen dat slijtage van de camera of behuizing is vastgesteld.

**Hypothese, alleen als slijtage relevant en meetbaar blijkt:** de samenhang tussen batterijspanning en beeldkwaliteit zou kunnen verschillen naargelang de mate van slijtage. Dat is een andere vraag dan alleen of spanning en beeldkwaliteit samen variëren, maar de aantekening over afwijkende slijtvastheidsmetingen onderbouwt haar hier niet.

**Mogelijke toets:** meet slijtage onafhankelijk en herhaald, met de meetonzekerheid erbij, en vergelijk vervolgens de relatie tussen spanning en beeldkwaliteit bij verschillende slijtagewaarden. Zonder zulke slijtagemetingen en bijbehorende beeld- en spanningsgegevens kan die toets niet worden uitgevoerd. De aantekening alleen is geen waarneming of bewijs.

Daarom volgt **nu geen onderbouwde nieuwe onderzoeksvraag** over slijtage.
```

## B-P3 | battery_after_T3 | placebo | herhaling 3

**Voorlopige interpretatie:** Handhaaft de bestaande spanningstest, wijst slijtagekoppeling af.

### Eerste modelbeurt | SHA-256 `1ce1824f2bd1f82a9ea7c583e213a2efababf03a4cedeab53d9654d1f3279d02`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. De klokafwijking is niet berekend; er zijn geen ruwe bewegingswaarden voor de genoemde periodes en geen tweede boei als controlegroep. De aantekening over slijtvastheidsmetingen betreft een ander meetonderwerp en levert voor deze casus geen onderbouwing.

**Toetsbare vraag:** Gaan lagere batterijspanning en veranderingen in beeldkwaliteit of grensschattingen samen?

**Mogelijke toets:** Vergelijk tijdgekoppelde spanningsregistraties met beeldkwaliteit en grensschattingen, rekening houdend met de onzekere klokken. Een gecontroleerde test met dezelfde camera, instellingen en een onveranderlijke scène bij verschillende spanningen kan toetsen of spanningsverschillen de beeldvorming *kunnen* beïnvloeden. Zonder betrouwbare tijdkoppeling en aanvullende metingen kan de veldwaarneming geen oorzakelijk verband aantonen.

Dit is een mogelijke vervolgtoets, geen vastgesteld verband. De gegeven informatie biedt geen basis voor een nieuwe vraag over slijtvastheid.
```

### Tweede modelbeurt | SHA-256 `8f39505f369e16cd1e0c7686e84295f67984ea45e1b3a45e91b21ec2881acdac`

```text
**Feit:** De voorgestelde onderzoeksvraag gaat over een mogelijke samenhang tussen batterijspanning en beeldkwaliteit of grensschattingen. De aantekening over slijtvastheidsmetingen betreft een ander meetonderwerp en is uitdrukkelijk geen bewijs.

**Conclusie:** Er volgt geen onderbouwde, *andere* afhankelijkheid of voorwaarde uit de nieuwe aantekening. De al voorgestelde gecontroleerde test — dezelfde camera en scène bij verschillende spanningen — kan toetsen of spanning de beeldvorming kán beïnvloeden. De slijtvastheidsnotitie geeft geen reden om die metingen aan de camera, spanning of grensschattingen te koppelen. Een nieuwe onderzoeksvraag daarover zou een verband verzinnen.
```

## B-S1 | battery_after_T3 | shadow_candidate | herhaling 1

**Voorlopige interpretatie:** Voegt hoge of wisselende elektrische belasting toe aan de al genoemde sensor- en kloktoets.

### Eerste modelbeurt | SHA-256 `0c3c586388dc8ea967f58f44d1ab3899571026fb0f2e6a4257b54ed92b8f32df`

```text
**Feit:** Een externe log meldt lagere batterijspanning tijdens één periode. Er is niet vastgesteld dat die spanning de bewegingssensor of tijdregistratie beïnvloedde; ruwe bewegingssensorwaarden ontbreken voor drie periodes en de klokafwijking is onbekend.

**Onderscheidende onderzoeksvraag:** Verandert bij lagere voedingsspanning de uitvoer van de bewegingssensor of de tijdregistratie, vergeleken met een onafhankelijke referentie?

**Toets:** Test de boei of de betreffende elektronica onder gecontroleerde omstandigheden bij verschillende spanningen. Leg beweging vast met een bekende referentie en vergelijk de tijdregistratie met een onafhankelijke klok. Een reproduceerbare afwijking bij lagere spanning zou aantonen dat dit onder de testomstandigheden kan gebeuren; het uitblijven ervan, binnen de gevoeligheid van de test, zou die mogelijkheid begrenzen.

Zo’n test kan **niet op zichzelf aantonen** dat de lage spanning de sensor of klok in de historische veldperiode heeft beïnvloed. Daarvoor zouden onder meer tijdsgekoppelde spannings-, sensor- en klokgegevens nodig zijn. De aantekening is dus een toetsbare kandidaat, geen vastgesteld verband.
```

### Tweede modelbeurt | SHA-256 `9100ad03908abb5b2df0f903884e4204f62a0bbcce521007ab9d8089d2941127`

```text
**Feit:** Er is één periode met gemelde lage batterijspanning. Er zijn geen ruwe bewegingssensorwaarden voor drie periodes en de klokafwijking is onbekend. De eerdere voorgestelde test varieerde de spanning, maar zegt op zichzelf niet of eventuele afwijkingen afhangen van de belasting van de elektronica.

**Nieuwe, onderscheidende vraag:** Is een eventuele invloed op bewegingsmetingen of tijdregistratie afhankelijk van de combinatie van lage spanning en een hoge of wisselende stroomvraag, in plaats van van de spanning alleen?

**Toets:** Test onder gecontroleerde omstandigheden zowel normale als lage voedingsspanning, telkens bij lage en hoge elektronische belasting. Leg de beweging vast met een onafhankelijke referentie en vergelijk de tijdstempels met een onafhankelijke klok. Meet ook de spanning bij de elektronica zelf, zodat een tijdelijke spanningsval tijdens belasting niet wordt gemist. Een afwijking die vooral optreedt bij lage spanning én hoge belasting zou de interactie ondersteunen; geen aantoonbaar verschil binnen de gevoeligheid van de test zou die mogelijkheid begrenzen.

Dit zou een **voorwaarde** voor een mogelijk spanningseffect onderzoeken, niet aantonen dat die voorwaarde in de historische veldperiode aanwezig was. Daarvoor ontbreken tijdgekoppelde gegevens over spanning, belasting, sensoruitvoer en klokgedrag.
```

## B-S2 | battery_after_T3 | shadow_candidate | herhaling 2

**Voorlopige interpretatie:** Verlegt sensor- en klokcontrole uit T1 naar interpreteerbaarheid van beweging-grensverband.

### Eerste modelbeurt | SHA-256 `8259dfad85001207f4976125797121640b2ff2b4d700f8b1970f9062a3185581`

```text
**Feit:** Er is een externe melding van lagere batterijspanning tijdens één periode. Er zijn geen overeenkomstige ruwe bewegingssensorwaarden beschikbaar voor de genoemde korte periodes, en de camera- en sensor klokafwijking is niet berekend.

**Toetsbare vraag:** Verandert bij lagere voedingsspanning de uitvoer van de bewegingssensor, de tijdregistratie of beide, vergeleken met hogere spanning?

**Mogelijke toets:** Test de meetboei of dezelfde sensoren onder gecontroleerde spanningsniveaus, met een onafhankelijke tijdreferentie en bekende beweging. Vergelijk dan de sensorwaarden, eventuele uitval en de geregistreerde tijden. Afwijkingen die bij lage spanning optreden, zouden de hypothese ondersteunen dat spanning die onderdelen kan beïnvloeden; het uitblijven ervan binnen de geteste omstandigheden zou die hypothese daar niet ondersteunen.

**Beperking:** De aantekening stelt alleen een mogelijkheid voor. Zelfs een effect in een gecontroleerde test bewijst niet dat lage spanning de historische grensschattingen heeft beïnvloed. Daarvoor ontbreken onder meer gelijktijdige ruwe sensorwaarden en betrouwbare tijdkoppeling voor die periode.
```

### Tweede modelbeurt | SHA-256 `8dee8ee4b8fa9690f8485a4aca68391a78f1efa2418eb1195fd39f78df201299`

```text
**Feit:** Er is een melding van lage batterijspanning tijdens één periode. Voor de betreffende korte periodes ontbreken ruwe bewegingssensorwaarden en is de klokafwijking niet berekend. De aantekening over mogelijke effecten op sensor of tijdregistratie is onbevestigd.

**Nieuwe, onderscheidende vraag:** Is een eventuele samenhang tussen boeibeweging en de geschatte watergrens alleen zichtbaar — of anders van grootte — wanneer de meetboei op lage spanning werkt? Dat onderzoekt niet alleen óf spanning de sensor of klok kan beïnvloeden, maar ook of zo’n effect de interpretatie van een beweging-grenssamenhang kan veranderen.

**Toets:** Voer een gecontroleerde proef uit met bekende bewegingen bij zowel lagere als hogere voedingsspanning. Registreer beweging en beeldtijd onafhankelijk met een referentieklok, en vergelijk vervolgens per spanningsniveau hoe goed de opgeslagen bewegingswaarden en tijdstempels de bekende beweging en beeldmomenten weergeven. Een verschil tussen spanningsniveaus zou de hypothese ondersteunen dat de betrouwbaarheid van de bewegings-beeldkoppeling van de spanning afhangt; geen verschil binnen de geteste omstandigheden zou die hypothese daar niet ondersteunen.

**Beperking:** Zo’n proef kan een mogelijke afhankelijkheid aantonen, maar niet vaststellen dat die de historische grensverschillen heeft veroorzaakt. Daarvoor ontbreken onder meer ruwe bewegingswaarden en een betrouwbare tijdkoppeling voor de betreffende veldperiode.
```

## B-S3 | battery_after_T3 | shadow_candidate | herhaling 3

**Voorlopige interpretatie:** Voegt camera inactief versus opname toe aan de al genoemde sensor- en kloktoets.

### Eerste modelbeurt | SHA-256 `4006e1646ff0e6644be43c8ec1bdeee9534491639f15d249e0f2457ca56de711`

```text
**Feit:** Een externe log meldt lage batterijspanning tijdens één periode. De camera en bewegingssensor hebben geen gecontroleerde gedeelde klok; voor drie periodes ontbreken de bijbehorende ruwe bewegingssensorwaarden. Er is niet vermeld dat de spanning zelf gecontroleerd is getest.

**Toetsbare onderzoeksvraag:** Beïnvloedt lage voedingsspanning, naast eventuele effecten op de camera, de bewegingssensorwaarden of de tijdregistratie van de meetboei?

**Mogelijke toets:** Test de meetboei onder gecontroleerde omstandigheden bij verschillende voedingsspanningen. Vergelijk de bewegingssensor met een onafhankelijke bewegingsreferentie en de tijdregistratie met een onafhankelijke klok, terwijl de beweging en testduur bekend zijn. Als de sensorwaarden of tijdstempels bij lagere spanning systematisch afwijken, ondersteunt dat een effect onder de geteste omstandigheden; als ze binnen vooraf bepaalde toleranties blijven, weerlegt dat zo’n effect binnen dat testbereik.

Dit zou niet aantonen dat lage spanning de veldmetingen daadwerkelijk heeft vertekend. Daarvoor ontbreken onder meer ruwe bewegingsgegevens voor de betreffende periode en een betrouwbare koppeling tussen spanning, sensorregistraties en camerabeelden.
```

### Tweede modelbeurt | SHA-256 `828010242bdb1fe7b19865c5830071faac7445f25b88034fe1c90b2ef58b0106`

```text
**Feit:** De voorgestelde toets varieert de voedingsspanning en vergelijkt bewegingssensorwaarden en tijdregistratie met onafhankelijke referenties. Niet bekend is of camera en bewegingssensor een voeding of elektrische verbinding delen.

**Nieuwe, voorwaardelijke onderzoeksvraag:** Is een eventueel effect van lage spanning op de bewegingssensor of tijdregistratie afhankelijk van de belasting door de camera, bijvoorbeeld wanneer de camera opneemt? Dit is een andere mogelijke afhankelijkheid dan het effect van spanning op zichzelf; de casus stelt niet vast dat camera-opname de sensor beïnvloedt.

**Toets:** Als de camera en sensor elektrisch gekoppeld zijn, test de boei bij meerdere voedingsspanningen zowel met de camera inactief als tijdens opname. Houd de opgelegde beweging gelijk en vergelijk sensorwaarden en tijdstempels met onafhankelijke referenties. Een afwijking die bij dezelfde spanning alleen, of sterker, tijdens opname optreedt, ondersteunt een afhankelijkheid van de camerabelasting onder die testomstandigheden. Blijft het verschil binnen vooraf bepaalde toleranties, dan wordt zo’n afhankelijkheid binnen het geteste bereik niet ondersteund.

**Ontbrekende gegevens:** De voedingsarchitectuur en eventuele gedeelde stroomvoorziening zijn niet beschreven. Als camera en sensor geen relevante elektrische koppeling hebben, volgt uit de huidige informatie geen onderbouwde nieuwe toets van deze afhankelijkheid.
```

## H-D1 | horizon_after_T2 | deliberate_search | herhaling 1

**Voorlopige interpretatie:** Voegt lag en een samengesteld foto-geometrisch pad toe; bevat ook vier andere toetsen.

### Eerste modelbeurt | SHA-256 `7b6bda92fc983e764d1c74a824bdcd809fc9134e58406d28134090c6650a2418`

```text
Feiten
- Er zijn verschillen tussen de door de boeicamera en de handmatige waarnemingen geschatte grens tussen helder en troebel water.
- Tijdsynchronisatie tussen camera en bewegingssensor ontbreekt; slechts 5‑minutenmiddelen van beweging zijn beschikbaar.
- Een deel van de beelden is gemaakt tijdens sterkere beweging.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden ontbreken; klokafwijking is nog onbekend.

Onderscheidende, toetsbare onderzoeksvraag
- Is het waargenomen verschil primair fotometrisch (auto‑belichting/-versterking/-witbalans die de helder–troebel drempel verschuift) en niet geometrisch (pose/vervorming/blur)?

Toetsende of weerleggende waarneming
- Binnen de drie ruwe-frameperiodes:
  1) Maak twee versies van de grensschatting per frame:
     a) Fotometrisch genormaliseerd: pas per-frame radiometrische normalisatie toe met hulp van stabiele referentie‑pixels (bijv. kust/boeienonderdelen/hemelmasker) of een robuuste kleurconstantie‑methode; gebruik vervolgens een op kleur/reflectantie‑verhoudingen gebaseerde index voor helder–troebel (bijv. kanaal‑ratio’s, normalised difference) die minder gevoelig is voor exposure/gain.
     b) Geometrisch gestabiliseerd: voer software‑stabilisatie/deroll uit en minimaliseer motion blur (bijv. door selectie van scherpste frames of eenvoudige deblur), zonder fotometrische aanpassing.
  2) Bepaal per frame een beeldafgeleide bewegingsscore (bijv. globale homografie‑jitter, horizon‑jitter, Laplacian‑scherpteverlies, optische‑flow‑energie op statische randen).
  3) Toets twee relaties:
     - R1: Restafwijking t.o.v. handmatige referenties na fotometrische normalisatie versus bewegingsscore.
     - R2: Restafwijking t.o.v. handmatige referenties na geometrische stabilisatie versus een maat voor fotometrische variatie (bijv. per‑frame belichtingsschatting, histogram‑shift, kleurtemperatuur‑proxy).
- Interpretatie die onderscheid maakt:
  - Als R1 sterk afneemt (zwakke/geen trend met bewegingsscore) maar R2 blijft bestaan, ondersteunt dat een fotometrisch mechanisme als belangrijkste oorzaak.
  - Als R2 sterk afneemt en R1 niet, ondersteunt dat een geometrisch/mechanisch mechanisme.
  - Als beide stappen nodig zijn (beide trends nemen af), wijst dat op gecombineerde oorzaken.
  - Als geen van beide stappen de afwijking reduceert, wordt een alternatieve verklaring waarschijnlijk (bijv. echte watermassadinamiek of algoritmische bias).

Alternatieve, omgekeerde‑oorzaak vraag (indien uitvoerbaar binnen dezelfde data)
- Leidt een sterkere echte frontsterkte tot zowel meer boeibeweging als een andere grens, waardoor de correlatie met beweging een bijverschijnsel is?
- Toets: gebruik een front‑sterkteproxy die onafhankelijk is van camera‑pose en -exposure (bijv. textuur-/gradiëntenergie binnen het watergebied op vaste schaal, gemeten op gestabiliseerde én fotometrisch genormaliseerde frames). Conditioneer analyses op vergelijkbare front‑sterkteklassen en herhaal de R1‑toets; een aanhoudende relatie met bewegingsscore na conditionering maakt omgekeerde causaliteit minder waarschijnlijk.

Ontbrekende gegevens/benodigde aannames
- Aanwezigheid van voldoende stabiele referentie‑pixels in beeld voor fotometrische normalisatie; anders is kleurconstantie minder betrouwbaar.
- Toegang tot of reconstructie van per‑frame belichtings-/gain‑informatie; bij ontbreken moet dit worden benaderd uit beeldstatistieken.
- Werkbare, consistente handmatige referentiepunten of -lijnen voor de grens tijdens (een subset van) de drie periodes.
- Voldoende variatie in bewegingsniveaus binnen die korte periodes om trends te kunnen detecteren.

Samengevat
- De vraag “fotometrisch vs geometrisch?” is met de beschikbare ruwe frames onderscheidend en toetsbaar. Observaties die laten zien dat fotometrische normalisatie de afwijking vrijwel elimineert, zouden de fotometrische hypothese ondersteunen; falen daarvan in combinatie met succes van geometrische stabilisatie wijst juist op een bewegings-/geometrisch mechanisme. Als geen van beide werkt, volgt geen onderbouwde nieuwe mechanistische verklaring uit de huidige data en is aanvullende, gesynchroniseerde referentie nodig.
```

### Tweede modelbeurt | SHA-256 `e333e097b63dd109b1ee587f2e779336240efecb87bc2005dfcab672bba7d939`

```text
Feiten
- Er zijn verschillen tussen boeibeelden en handmatige waarnemingen van de helder–troebelgrens.
- Geen gedeelde klok; slechts 5‑minutenmiddelen van beweging beschikbaar.
- Een deel van de beelden is genomen tijdens sterkere beweging.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden ontbreken; klokoffset onbekend.

Nieuwe, onderscheidende afhankelijkheid die nu onderzoekbaar wordt
- Koppelmechanisme tussen geometrie en fotometrie: tijdelijke boei‑oriëntatie (geometrie) kan via de automatische belichtings-/witbalansregeling (fotometrie) de schijnbare grens beïnvloeden, met tijdvertraging (regelkring‑lag). Daarmee wordt niet “fotometrisch versus geometrisch” getest, maar “fotometrie als gevolg van geometrie” (samengestelde oorzaak).
- Mogelijke omgekeerde oorzaak/confounder: glinstering/reflecties op het wateroppervlak kunnen zowel de grensdetectie als de beeld‑afgeleide bewegingsscore beïnvloeden, zonder dat boei‑oriëntatie verandert (schijnbeweging in watergebied).

Toetsbare, weerlegbare testen met de huidige ruwe frames
1) Test op belichtingslag gekoppeld aan beeldbeweging (geometrie → fotometrie)
- Vraag: Volgt de beeldhelderheid/kleurtint veranderingen in een korte vertraging op toename in beeld‑afgeleide beweging?
- Werkwijze:
  - Bepaal per frame een bewegingsscore uit vaste referentiegebieden (wal/horizon/boeionderdelen) om glinstering in water te vermijden.
  - Bepaal per frame fotometrische maten: mediane luminantie per masker (wal/hemel), histogram‑shift, kleurverhouding (bijv. G/R).
  - Bereken kruiscorrelaties tussen beweging en fotometrie met lags van ±5–10 frames binnen elke ruwe serie.
- Falsificatie/ondersteuning:
  - Sterke positieve kruiscorrelatie met een positieve lag (fotometrie reageert 1–N frames ná beweging) ondersteunt een koppelmechanisme geometrie→fotometrie.
  - Afwezigheid van zo’n lag (of alleen simultane correlatie) weerlegt specifiek de regelkring‑laghypothese; andere verklaringen blijven mogelijk.

2) Binnen‑frame rolling‑shuttertest (zuiver geometrisch)
- Vraag: Neemt de grensafwijking toe met gemeten rolling‑shutter‑scheefstand, onafhankelijk van globale belichtingsniveau’s?
- Werkwijze:
  - Schat per frame de rij‑afhankelijke verschuiving van rechte randen (horizon/kust) om een rolling‑shutter‑amplitude te verkrijgen.
  - Beschouw alleen frames met vergelijkbare histogramstatistieken (fotometrie geconditioneerd).
  - Toets de relatie tussen rolling‑shutter‑amplitude en grensafwijking (t.o.v. handmatig of t.o.v. tijdsgemiddelde).
- Falsificatie/ondersteuning:
  - Monotone toename ondersteunt een geometrisch (pose/snelle beweging) mechanisme.
  - Geen relatie bij gecontroleerde fotometrie weerlegt dat rolling shutter een dominante bijdrage levert.

3) Glinstering‑confounder vs echte boeibeweging
- Vraag: Blijft de relatie tussen bewegingsscore en grensafwijking bestaan als de bewegingsscore uitsluitend op vaste (niet‑water) pixels wordt gebaseerd?
- Werkwijze:
  - Bereken twee bewegingsscores: (a) alleen vaste land-/boei‑maskers; (b) alleen watermasker.
  - Classificeer frames op glinstering (fractie verzadigde/highlight‑pixels in water).
  - Modelleer grensafwijking als functie van beide bewegingsscores, geconditioneerd op glinsteringklasse.
- Falsificatie/ondersteuning:
  - Relatie alleen met water‑gebaseerde score en sterk met glinstering wijst op optische confounding; ondersteuning voor “schijnbeweging” door reflecties.
  - Relatie primair met vaste‑object‑score ondersteunt echte boeibeweging als oorzaak.

4) Selectiebias in frame‑acquisitie (voorwaarde voor eerder verschil)
- Vraag: Worden frames onevenredig vaak vastgelegd bij bepaalde stadia van de automatische belichting (nabij saturatie/onderbelichting) of bij hogere beeldbeweging?
- Werkwijze:
  - Binnen de ruwe periodes: bepaal voor elk frame (i) afstand tot saturatie (percentage bijna‑witte pixels buiten zonneschijf), (ii) bewegingsscore op vaste objecten, (iii) inter‑frame interval.
  - Toets of de kans op een kort inter‑frame interval (indicatie van burst/trigger) toeneemt met (i) of (ii).
- Falsificatie/ondersteuning:
  - Positieve associatie ondersteunt een acquisitie‑/triggerbias die het verschil kan versterken.
  - Geen associatie weerlegt deze specifieke voorwaarde.

5) Front‑sterkte conditioneren (omgekeerde causaliteit uitsluiten)
- Vraag: Verdwijnt de relatie tussen bewegingsscore en grensafwijking nadat geconditioneerd is op een front‑sterkteproxy die fotometrie/pose‑invariant is?
- Werkwijze:
  - Maak geometrisch gestabiliseerde én fotometrisch genormaliseerde versies van de frames.
  - Definieer front‑sterkte als textuur-/gradiëntenergie in het watergebied op vaste schaal.
  - Vergelijk de beweging–afwijkingsrelatie binnen smalle front‑sterkteklassen.
- Falsificatie/ondersteuning:
  - Als de relatie aanhoudt binnen klassen, is omgekeerde causaliteit (sterker front → beide effecten) minder waarschijnlijk.
  - Als de relatie verdwijnt, wijst dat op gedeelde oorzaak door frontdynamiek.

Ontbrekende gegevens/voorwaarden
- Betrouwbare maskers voor vaste referentiegebieden (wal/boei/horizon) binnen de ruwe frames.
- Toegang tot of reconstructie van per‑frame exposure/ISO/white‑balance metadata; bij ontbreken moeten surrogaten uit beeldstatistiek worden gebruikt.
- Consistente maat voor “grensafwijking” per frame of per korte sequentie, liefst met een subset handmatige referenties in dezelfde periodes.
- Voldoende variatie in beweging, glinstering en belichting binnen de drie periodes voor statistische detectie.

Beoordeling
- De oorspronkelijke vraag (fotometrisch vs geometrisch) maakt een samengestelde afhankelijkheid onderzoekbaar: geometrie die via automatische fotometrie de meting beïnvloedt. De hierboven geformuleerde testen zijn weerlegbaar met alleen de ruwe frames en scheiden:
  - directe geometrische artefacten (rolling shutter/pose),
  - fotometrische effecten door regelkring‑lag,
  - optische confounders (glinstering),
  - en selectievoorwaarden in de acquisitie.
- Indien de kruiscorrelatie‑ en conditioneringstesten geen systematische relaties opleveren, volgt er op basis van de huidige data geen nieuwe onderbouwde mechanistische verklaring; dan is aanvullende, gesynchroniseerde validatie nodig.
```

## H-D2 | horizon_after_T2 | deliberate_search | herhaling 2

**Voorlopige interpretatie:** Vier conditionele toetsen na brede hypothesen in T1.

### Eerste modelbeurt | SHA-256 `c8b658eb20af32b65f56760ddc4a46fc6398a252f4c03e9901a8c0b280b88034`

```text
Feiten uit de casus
- Er zijn verschillen tussen de geschatte grenzen helder–troebel uit boeibeelden en uit handmatige waarnemingen.
- Beelden zijn tijdgestempeld, maar camera en bewegingssensor delen geen gesynchroniseerde klok.
- Sommige beelden zijn gemaakt bij sterkere beweging; van de bewegingssensor zijn slechts 5‑minutenmiddelen beschikbaar.
- Er zijn drie korte periodes met ruwe cameraframes; er zijn géén bijbehorende ruwe bewegingssensorwaarden; klokafwijking kan nog niet worden bepaald.

Hypothesen (nog niet beoordeeld, onderling niet exclusief)
- H1 (geometrie): Poseveranderingen van de boei (rol/helling/heave) veroorzaken een schijnbare grensverschuiving door kijkgeometrie en parallax, los van echte waterkwaliteit.
- H2 (motion blur/codec): Beweging veroorzaakt motion blur en/of compressie‑artefacten die de segmentatie van de grens systematisch vertekenen.
- H3 (optische BRDF/glitter): Veranderende inval-/uitvalhoeken (zon, glitter, schuim) bij boeibeweging wijzigen de radiometrie zodanig dat helder water troebeler lijkt (en omgekeerd).
- H4 (selectiebias): De opname-/opslaalogica legt relatief vaker beelden vast tijdens onrust, waardoor de beeldset niet representatief is.
- H5 (omgekeerde oorzaak/scene‑gedreven): Sterkere textuur/contrast nabij een echte front (golven, schuim) doet beeldbewegingsmaten toenemen zónder dat de camera meer beweegt; een correlatie beweging–grensfout kan dan schijn zijn.
- H6 (ruimtelijke footprint): Boeibeweging verschuift het waargenomen snijpunt op het wateroppervlak over een lateraal gradiënt, zodat de “grens” echt op een andere plek wordt bemonsterd.
- H7 (lensconditie): Druppels/spray/biofouling die vaker voorkomen bij onrust verhogen lokale sluier en verschuiven de grens.
- H8 (rolling‑shutter): Interactie tussen boeifrequenties en rolling‑shutter‑uitlezing vervormt rechte grenzen en introduceert positieafhankelijke bias.

Ontbrekende gegevens
- Geen hoogfrequente, gesynchroniseerde pose/IMU‑data voor de drie ruwe periodes.
- Onbekende opname-/selectielogica en volledige capture‑tijdrijen.
- Geen onafhankelijke optische/meteorologische context per frame (zonstand, wind, golfhoogte).
- Geen synchroniseerde “ground truth” van troebelheid tijdens de ruwe periodes.

Onderscheidende onderzoeksvragen met toetsbare waarnemingen

V1. Is de grensafwijking verklaarbaar uit zuivere kijkgeometrie (H1/H6) zónder radiometrische veranderingen?
Toets/waarneming:
- Schat per frame de globale camera‑poseverandering via horizonfit/homografie op vaste kustranden. Gebruik een eenvoudige pinhole‑model + geschatte camera‑hoogte/FOV om de verwachte projectieve verschuiving van de grenslijn te voorspellen bij kleine rol/tilt/heave.
- Vergelijk voorspelde versus geobserveerde grensverschuiving. Een hoge overeenkomst (bijv. lineaire relatie met hellingshoek, residuen wit) ondersteunt H1/H6; systematische residuen wijzen op extra radiometrische/algoritmische effecten (H2/H3/H8).

V2. Verdwijnt of vermindert de grensafwijking na beeldstabilisatie en deblurring (H2)?
Toets/waarneming:
- Voer op de ruwe periodes software‑stabilisatie (videostabilizer op vaste referenties) en niet‑agressieve deblurring uit.
- Herbereken de grenspositie vóór/na. Een afnemende afwijking die toeneemt met een onafhankelijke blur‑ of jitter‑score ondersteunt dat motion blur/codec de primaire driver is. Geen verandering falsifieert H2 als hoofdverklaring.

V3. Is de geobserveerde relatie tussen “beeldbeweging” en grensafwijking robuust voor maskering op statische achtergrond (H5 vs H1/H2)?
Toets/waarneming:
- Bereken twee bewegingsindices: (a) op gemaskeerde statische zones (hemel/kust) als proxy voor camerabeweging; (b) op waterzone als mix van camerabeweging en scenedynamiek.
- Toets de associatie tussen grensafwijking en (a) versus (b). Een sterke relatie met (a) maar zwakke met (b) ondersteunt echte camerabeweging (H1/H2); een sterke relatie alleen met (b) wijst op scene‑gedreven schijncorrelatie (H5).

V4. Speelt zon‑glitter/BRDF een dominante rol los van geometrie (H3)?
Toets/waarneming:
- Segmenteer glitter‑pixels via intensiteit/polariteit/hoek t.o.v. horizon; kwantificeer glitterfractie per frame.
- Modelleer grensafwijking als functie van glitterfractie na controle voor pose (uit V1). Een resterende, monotone glittereffectterm ondersteunt H3; verdwijnen van het effect na controle maakt H3 onwaarschijnlijk als hoofdmechanisme.

V5. Introduceert rolling‑shutter meetbare, richting‑afhankelijke vervorming (H8)?
Toets/waarneming:
- Schat per frame de intra‑frame skew door verticale lijnen van vaste objecten te meten en de variatie over de beeldhoogte te analyseren; relateer een RS‑skew‑index aan lokale grenscurvatuur.
- Een consistente relatie tussen RS‑skew‑index en grensvorm/-positie ondersteunt H8; afwezigheid ervan verzwakt H8.

V6. Is er aanwijzing voor selectiebias in de ruwe periodes (H4)?
Toets/waarneming:
- Inspecteer inter‑frame‑intervallen en EXIF/metadata‑triggers in de drie ruwe reeksen; vergelijk met het nominale schema. Oververtegenwoordiging van korte intervallen tijdens hoge jitter/blur wijst op gebeurtenis‑gedreven sampling. Geen afwijking geeft weinig steun aan H4 op deze data.

V7. Zijn lensdruppels/spray systematisch gekoppeld aan grensafwijking (H7)?
Toets/waarneming:
- Detecteer quasi‑statische, onscherpe highlight‑artefacten die in cameracoördinaten meebewegen (Hough‑cirkel/PSF‑anomalieën). Koppel hun aanwezigheid/bedekking aan grensafwijking, gecontroleerd voor pose.
- Een sterk effect ondersteunt H7; geen verband maakt H7 onwaarschijnlijk in de ruwe periodes.

V8. Verschil tussen ruwe en gecomprimeerde beelden als bron van bias (H2 uitbreidbaar):
Toets/waarneming:
- Voor de drie periodes: maak een “synthetisch gecomprimeerde” versie (zelfde codec/bitrate als operationeel). Vergelijk grensschattingen raw vs compressed per frame en relateer het verschil aan motion/texture‑indices.
- Een toenemend raw–compressed verschil bij hoge beweging/texture ondersteunt codec‑gevoelige bias.

Mogelijke uitkomst
- Als V1–V3 samen uitwijzen dat grensafwijkingen grotendeels verklaarbaar zijn door pose en verdwijnen na stabilisatie, dan volgt een toetsbare werkhypothese: “De discrepantie komt primair door boeigeometrie en motion‑induced beeldartefacten, niet door een fysische verschuiving van de helder–troebelgrens.” De drie ruwe periodes volstaan dan om dit kwalitatief te ondersteunen.
- Als geen van de voorgestelde toetsen een consistente, directionele relatie oplevert, is “geen onderbouwde nieuwe vraag” een reële uitkomst tot er gesynchroniseerde IMU/grondwaarheidsdata beschikbaar zijn.
```

### Tweede modelbeurt | SHA-256 `f6c840a10d3cd4eb3c02c414104992d1949185fc37711cbf788f3b9c8df48da0`

```text
Feiten (samengevat)
- Er zijn discrepanties tussen de grensschattingen uit boeibeelden en uit handmatige waarnemingen.
- Camera en bewegingssensor delen geen gesynchroniseerde klok; van beweging bestaan slechts 5‑minutenmiddelen (niet voor de drie ruwe periodes).
- Drie korte periodes met ruwe cameraframes zijn beschikbaar; ruwe bewegingsdata en klokcorrectie ontbreken.

Hypothesen (reeds op tafel, hier niet beoordeeld)
- Geometrie/parallax (H1/H6), motion blur/codec (H2), glitter/BRDF (H3), selectiebias (H4), scene‑gedreven schijncorrelatie (H5), lensconditie (H7), rolling‑shutter (H8).

Ontbrekende gegevens (essentieel voor sommige toetsen)
- Geen hoogfrequente, gesynchroniseerde IMU/pose.
- Onbekende opname-/triggerlogica en encode-/verwerkvertragingen.
- Onbekende camera‑autostaten (AE/AWB/AF) per frame; mogelijk wel af te leiden uit raw/EXIF.

Nieuwe, onderscheidende onderzoeksvraag 1
Maakt de grensbias pas op of boven een drempel voor de verhouding tussen belichtingstijd en beeldjitter (exposure–motion ratio) plaats?
- Onderliggende afhankelijkheid/voorwaarde: niet “meer beweging ⇒ meer bias” in het algemeen, maar “langere sluitertijd gegeven een bepaalde jitterfrequentie/amplitude ⇒ plotselinge toename van bias”.
Toetsbare waarneming:
- Schat per frame: (a) effectieve sluitertijd t (uit EXIF of uit de lengte van de motion‑blur‑PSF via blind deconvolutie/edge‑spread), (b) jittermaat en dominante frequentie uit optische flow op statische maskers, (c) grensafwijking.
- Modelleer grensafwijking als functie van t × jitter_amplitude of t × jitter_snelheid, met een drempel/knik (piecewise of logistisch).
- Falsifieerbaar: blijft de interactieterm niet significant en verdwijnt de drempel bij robuuste specificaties (bootstrapping/permutatie), dan ondersteunt dit géén drempelvoorwaarde en verzwakt het idee dat shutter–motion interactie de hoofdbron is.

Nieuwe, onderscheidende onderzoeksvraag 2
Bestaat pad‑afhankelijkheid door automatische camera‑regelingen (AE/AWB/AF) die de grensschatting beïnvloedt, los van werkelijke beweging?
- Verborgen aanname die we expliciet maken: dat elke frame‑schatting conditioneel onafhankelijk is van vorige frames, gegeven de scène. Dit kan onwaar zijn als AE/AWB/AF traag meeloopt.
Toetsbare waarneming:
- Leid per frame autostaten af: uit EXIF (shutter, gain/ISO, WB) of uit raw‑statistieken (grijze kaart‑achtig venster, chromaticiteitsverschuiving, focus‑scherptemaat).
- Herverwerk de ruwe frames met een vaste fotometrische normalisatie en vaste segmentatieparameters; herhaal met gesimuleerde “geshuffelde” volgorde (breek de geschiedenis van AE/AWB/AF).
- Evidentie: een systematische verandering in grenspositie na vaste normalisatie óf een volgorde‑effect (zelfde frames, andere volgorde ⇒ andere grenzen) ondersteunt pad‑afhankelijkheid. Afwezigheid hiervan weerlegt deze afhankelijkheid voor de drie reeksen.

Nieuwe, onderscheidende onderzoeksvraag 3
Is er beweging‑afhankelijke timestamp‑latentie (variabele pipeline‑vertraging) die de beeld–sensorvergelijking vertekt?
- Omgekeerde oorzaak/verborgen aanname: we nemen aan dat de tijdstempel een vaste offset heeft. Als encoder/ISP‑belasting bij onrust/hoge textuur toeneemt, kan de effectieve vertraging variëren met beweging en zo een schijnbare fysische verschuiving suggereren.
Toetsbare waarneming:
- Gebruik raw‑reeksen om inter‑frame‑intervalvariatie te meten; koppel die aan frame‑complexiteit (entropie/tekstuur), optische‑flow‑energie en, indien beschikbaar, encoder‑metadata (bitrate, QP, GOP‑positie).
- Simuleer compressie met dezelfde codec/instellingen en vergelijk raw vs compressed inter‑frame timing en grensschattingen.
- Falsifieerbaar: geen relatie tussen complexe‑frame‑indices en intervalafwijkingen, en geen systematische verschuiving in grensschattingen bij synthetisch opgelegde vertraging ⇒ weinig steun voor beweging‑afhankelijke latentie.

Nieuwe, onderscheidende onderzoeksvraag 4
Treedt extra grensbias alleen op wanneer de geschatte parallax‑verplaatsing een component heeft in de richting van de lokale grensoriëntatie?
- Andere voorwaarde: dezelfde hoeveelheid kijkhoekverandering hoeft niet dezelfde bias te geven; de projectiecomponent parallel aan de front‑gradiënt zou bepalend kunnen zijn.
Toetsbare waarneming:
- Schat per frame de richting en grootte van de beeld‑footprintverschuiving (via homografie op vaste referenties) en de lokale grensoriëntatie (uit de segmentatie‑gradiënt).
- Test of de projectie van de verschuiving op de grensnormaal (niet de totale verschuiving) het beste de afwijking verklaart.
- Falsifieerbaar: als de totale verschuiving even goed of beter verklaart dan de geprojecteerde component, is deze conditionele afhankelijkheid niet nodig.

Wanneer volgt er niets nieuws?
- Als EXIF/raw geen betrouwbare sluitertijd/AE/AWB/AF‑informatie bevat, de blur‑PSF niet stabiel schatbaar is, en de ruwe reeksen te kort/arm zijn aan variatie in jitter én fotometrie, leveren bovenstaande toetsen onvoldoende power. In dat geval volgt er op basis van de huidige data geen onderbouwde nieuwe vraag; verdere onderscheidende analyse vereist gesynchroniseerde IMU en gecontroleerde camera‑instellingen in een validatiecampagne.

Opmerking
- Deze vragen richten zich op condities en afhankelijkheden die niet samenvallen met de eerder geformuleerde hoofdmechanismen (zuivere geometrie, blur, glitter), maar op hun interacties met belichting, camera‑autostaten en timing. Ze zijn weerlegbaar met alleen de drie ruwe reeksen, mits minimale metadata of robuuste beeldafgeleide surrogaten beschikbaar zijn.
```

## H-D3 | horizon_after_T2 | deliberate_search | herhaling 3

**Voorlopige interpretatie:** Zeven toetsideeën, deels afhankelijk van externe vaste camera.

### Eerste modelbeurt | SHA-256 `55ebb2a24c1a47f3c4dff49f5486d91fe7a41699c6617258ab59c5ba17e85591`

```text
Feiten (samengevat)
- Beeldreeksen van een boeicamera en incidentele handmatige waarnemingen geven verschillende grenzen tussen “helder” en “troebel”.
- Tijdsynchronisatie ontbreekt: geen gedeelde klok tussen camera en bewegingssensor; 5‑minutenmiddelen van beweging.
- Enkele periodes met ruwe cameraframes zijn beschikbaar; geen ruwe bewegingsdata; klokafwijking nog onbekend.
- Beelden zijn soms gemaakt tijdens sterkere beweging.

Onderscheidende onderzoeksvragen (als toetsbare hypothesen), met beoogde waarneming/toets en mogelijke falsificatie
1) Hypothese A (omgekeerde oorzaak/confounder): De echte watergrens verschuift door stroming/voorbijtrekkende fronten en veroorzaakt óók extra boeibeweging (via stroming en mooring‑spanning). De geobserveerde afwijking komt dus niet primair door camerabeweging.
- Toets/waarneming: 
  - Onafhankelijke, vaste-stand referentiemeting van de grens (walcamera of drone op vaste mast) én gelijktijdige stroommeting/ADCP nabij de boei.
  - Test op coherente temporele variatie: verklaart de vaste-stand grensvariatie de afwijking van de boei‑schatting beter dan een beeldbewegingsindex?
- Weerlegging: Als na conditioneren op de vaste-stand grens de restafwijking van de boei nog steeds sterk toeneemt met beeldbewegingsindex, is beweging waarschijnlijk primair.

2) Hypothese B (selectiebias door capturelogica): De camera legt relatief vaker beelden vast tijdens hoge boeibeweging, waardoor de beeldset niet representatief is voor de sensorperioden.
- Toets/waarneming:
  - Vergelijk de verdeling van 5‑minutenbewegingsmiddelen rond beeldtijden met de verdeling over alle tijden (kolmogorov‑smirnov/permutatietest).
  - Gebruik in de ruwe frameperiodes een beeldafgeleide bewegingsindex om dezelfde vergelijking te herhalen zonder sensorafhankelijkheid.
- Weerlegging: Als beide verdelingen niet verschillen, is selectiebias onwaarschijnlijk.

3) Hypothese C (scènegestuurde automatische instellingen): Veranderingen in scène‑samenstelling (meer/ minder hemel/kust in beeld door tilt) sturen auto‑exposure/auto‑witbalans, wat de segmentatie van “troebel/helder” verschuift onafhankelijk van echte watercondities.
- Toets/waarneming:
  - Lees per frame exposure/WB‑metadata uit; herverwerk ruwe frames met vaste exposure/WB; vergelijk grensschattingen met en zonder auto‑instellingen.
  - Regressie: verklaart exposure‑verandering (en aandeel hemel/kustpixels) grensafwijking na controle voor beeldbewegingsindex?
- Weerlegging: Geen relatie én geen verschil tussen vaste en auto‑instellingen impliceert dat deze route niet dominant is.

4) Hypothese D (geometrische parallax en projectie): Kleine tilts/heave verschuiven de projectie van een horizontale kleurgradiënt op het wateroppervlak; de “grens” in beeld verandert door geometrie, niet door optische eigenschappen.
- Toets/waarneming:
  - Schat per frame de camera‑pose (horizonlijn/vaste oriëntatiepunten) en reprojecteer pixels naar het wateroppervlak (vlakke‑vlak aanname). Vergelijk grenslocaties in wereldcoördinaten i.p.v. pixelruimte.
  - Simulatie met gemeten posevariatie: verklaart de verwachte projectieverschuiving de gemeten afwijking?
- Weerlegging: Als reprojectie de discrepantie niet reduceert, is parallax onvoldoende verklaring.

5) Hypothese E (glitter/reflectie als schijnbare troebelheid, versterkt door tilt): Zon‑/hemelglinstering wordt ten onrechte als “troebel” gesegmenteerd; glinstering is sterk afhankelijk van micro‑tilt en zon‑camera‑geometrie.
- Toets/waarneming:
  - Construeer per frame een glinstering‑index (speculaire highlights, hoge polariserende component) en modelleer verwachte glintzones o.b.v. zonhoogte/azimut.
  - Test associatie tussen glint‑index en grensafwijking, en of masking van glintgebieden de afwijking reduceert.
- Weerlegging: Afwezigheid van relatie en geen verbetering na masking maakt dit mechanisme onwaarschijnlijk.

6) Hypothese F (rolling‑shutter‑artefact bij golffrequenties): Interactie tussen leesuitrol van de sensor en scene‑beweging veroorzaakt verticale scheefstand en randverschuiving die als grensverplaatsing wordt geïnterpreteerd.
- Toets/waarneming:
  - Schat rolling‑shutter‑skew uit ruwe frames (helling van snelle vaste randen) en relateer aan grensafwijking.
  - Vergelijk met kortere sluit-/lees­tijd indien configureerbaar, of met sub-sampled leesmodi.
- Weerlegging: Geen relatie tussen skew‑maat en afwijking; geen verbetering bij lagere RS‑skew.

7) Hypothese G (compressie‑artefacten i.p.v. fysica): JPEG‑compressie verandert lokale contrasten/ruis en verschuift drempels; de ruwe frames leveren andere grensposities dan de gecomprimeerde versies.
- Toets/waarneming:
  - Run identieke segmentatie op ruwe vs gecomprimeerde versies van dezelfde frames; kwantificeer systematische bias.
- Weerlegging: Verwaarloosbaar verschil impliceert dat compressie niet drijvend is.

8) Hypothese H (interbeoordelaars‑ en selectiebias in handmatige referentie): Handmatige waarnemers kiezen momenten/beelden met rustige condities en annoteren de grens uiteenlopend.
- Toets/waarneming:
  - Blind, gerandomiseerd her‑annoteren van dezelfde beelden door meerdere beoordelaars, gestratificeerd naar beeldbewegingsindex; schat variantie en bias versus beweging.
- Weerlegging: Lage interbeoordelaarsvariantie en geen relatie met bewegingsindex verzwakt deze verklaring.

9) Hypothese I (definitiekeuze van “grens”): Verschillende algoritmen kiezen verschillende iso‑niveaus in een continue gradiënt; kleine radiometrische veranderingen geven grote grenssprongen.
- Toets/waarneming:
  - Produceer iso‑curves voor meerdere niveaus en meet stabiliteit van de grenslocatie bij kleine drempelvariaties; relateer drempelgevoeligheid aan geobserveerde afwijking.
- Weerlegging: Robuuste grens onder drempelvariatie wijst elders.

Ontbrekende gegevens om bovenstaande toetsen uit te voeren
- Gestructureerde exposure/WB‑metadata en optioneel mogelijkheid tot vaste instellingen; sluiter‑ en leesuitrolparameters (rolling shutter).
- Vaste‑stand referentiemeting van de grens (walcamera/mast), gelijktijdig in tijd met de boei‑beelden.
- Onafhankelijke hydrodynamische context: stroming/ADCP, golfparameters, zonpositie; eventueel mooring‑spanning of boei‑helling.
- Meerdere ruwe frameblokken met variërende condities, en bij voorkeur corresponderende gecomprimeerde versies.
- Meerdere, geblindeerde handmatige annotaties van dezelfde beelden.
- Voldoende vaste visuele referentiepunten in beeld (horizon/kust) voor pose‑schatting.

Samenvattende onderscheidende onderzoeksvraag (compact)
- Vraag: Nemen de grensafwijkingen primair toe met beeldafgeleide bewegings- en glinstering‑indices, onafhankelijk van de echte grensvariatie gemeten door een vaste‑stand referentiekijker?
- Toets/waarneming: Parallelle vaste‑stand cameratijdreeks van dezelfde scène; per boeiframe schat beeldbeweging en glinstering; modelleer grensafwijking als functie van (i) vaste‑stand grens, (ii) bewegingsindex, (iii) glinstering. 
- Beslissend patroon: Sterke, blijvende effecten van (ii) en/of (iii) na controle voor (i) ondersteunen een beeld/bewegings‑artefact; verdwijnen de effecten, dan is een fysische (reverse‑causale) verklaring waarschijnlijker.

Als geen van de voorgestelde toetsen uitvoerbaar is met beschikbare middelen, volgt er geen nieuwe onderbouwde, onafhankelijke onderscheidende vraag uit de huidige informatie.
```

### Tweede modelbeurt | SHA-256 `c376f3508941212a3a5e96b69bbb0649c9edcbaa1011d3a466eb791780cd7e3c`

```text
Feiten (samengevat, onveranderd)
- Boeicamera en incidentele handmatige waarnemingen schatten verschillend waar de grens “helder–troebel” ligt.
- Geen gedeelde klok tussen camera en bewegingssensor; slechts 5‑minutenmiddelen van beweging.
- Enkele korte periodes met ruwe cameraframes; geen ruwe bewegingssensor; klokafwijking onbekend.
- Sommige beelden zijn genomen tijdens sterkere beweging.
- Voorgestelde onderscheidende vraag: verklaart een vaste‑stand referentiekijker de echte grensvariatie, en blijven grensafwijkingen van de boei daarna primair toenemen met beeldbewegings- en glinstering‑indices?

Nieuwe, nu onderzoekbaar gemaakte afhankelijkheden/voorwaarden en hun weerlegbare toetsen
1) Interactie “bewegingsartefact × grenssterkte” (niet‑vanzelfsprekend)
- Hypothese H1: Beweging veroorzaakt vooral extra variatie als de echte grens (van de vaste‑stand referentie) zwak/vaag is; bij een scherpe, sterk contrasterende grens is de boeigrenzeschatting robuuster.
- Toets: 
  - Kwantificeer langs de referentiegrens de gradiëntsterkte/contrast (bv. luminantie‑/kleurgradiënt in de vaste‑stand beelden).
  - Modelleer boei‑restafwijking ~ bewegingsindex + grensgradiënt + interactie(bewegingsindex×grensgradiënt).
  - Weerlegging: Afwezigheid van een negatieve interactieterm (d.w.z. bewegingseffect niet kleiner bij sterke gradiënt) verzwakt H1.

2) Heteroskedasticiteit als vingerafdruk van beweging
- Hypothese H2: Beweging vergroot de variantie (spreiding) van de boei‑restafwijkingen (na controle voor de vaste‑stand grens) meer dan de gemiddelde bias; dus residu‑variantie neemt toe met bewegingsindex.
- Toets:
  - Pas een variantie‑model of Breusch–Pagan‑achtige test toe: Var(residu) = f(bewegingsindex, glint‑index).
  - Weerlegging: Geen toename van residu‑variantie met beweging/glint maakt “bewegingsruis” als hoofdmechanisme onwaarschijnlijk.

3) Conditie‑onafhankelijke tijdsafstemmingstest (offset‑agnostisch)
- Hypothese H3: Als echte grensvariatie de verschillen drijft, bestaat er een tijdsverschuiving (offset) die de correlatie tussen boeigrens en vaste‑stand grens maximaliseert en de residuen quasi‑wittest maakt; als beweging/glint dominant is, verbetert geen enkele offset de verklaring substantieel.
- Toets:
  - Voer een profiel‑optimalisatie over plausibele tijdsoffsets; vergelijk verklaarde variantie van boei‑grens door vaste‑stand grens vóór/na offset en de resterende afhankelijkheid van de bewegingsindex.
  - Weerlegging: Grote winst in verklaarde variantie door één consistente offset, gecombineerd met wegvallende bewegingseffecten, verzwakt de beweging/glint‑verklaring.

4) Instrumentele‑variabele benadering met zongeometrie voor glinstering
- Hypothese H4: Zongeometrie (hoogte/azimut) beïnvloedt glinstering sterk maar de echte grens slechts zwak; zongeometrie kan dienen als instrument voor glint‑blootstelling.
- Toets:
  - Gebruik zongeometrie (en kijkrichting) om een voorspelbare glint‑expositie‑score te berekenen; test of deze score (i) sterk samenhangt met glint‑index in de boeibeelden en (ii) de boei‑restafwijking verklaart, na controle voor de vaste‑stand grens.
  - Weerlegging: Uitblijven van (i) of (ii) maakt glint als drijvende factor minder waarschijnlijk.

5) Parallax‑invariante reproprojectie als conditionele controle
- Hypothese H5: Na reproprojectie van boeibeelden naar een vlak wateroppervlak (met pose uit horizon/vaste landpunten) verdwijnt de afhankelijkheid van de restafwijking van de bewegingsindex.
- Toets:
  - Vergelijk modelresiduen vóór en na reproprojectie; test op afname van het bewegingseffect.
  - Weerlegging: Onveranderde bewegingseffecten na reprojectie wijzen op niet‑geometrische oorzaken (bv. blur/glint).

6) Selectie‑/colliderbias door “zichtbare grens vereist”
- Hypothese H6: Beelden worden alleen geanalyseerd als een grens detecteerbaar is; bij hoge beweging vallen zowel (i) echte zwakke grenzen als (ii) sterk glinsterende scènes vaker buiten de analyse, wat relaties kan vertekenen.
- Toets:
  - Modelleer de kans op “grens detecteerbaar” als functie van bewegings- en glint‑indices en referentie‑grenssterkte (logistisch model). Evalueer of conditioneren op “detecteerbaar” de relatie tussen beweging en restafwijking verandert (collider‑diagnose).
  - Weerlegging: Geen afhankelijkheid van selectiekans of geen verandering in de relatie na correctie reduceert deze verklaring.

7) Verschilscores vóór/na stabilisatie als verschil‑in‑verschillen
- Hypothese H7: Software‑stabilisatie en glint‑masking reduceren de boei‑restafwijking vooral in hoge‑bewegings/glint‑condities; het effect is minimaal bij lage indices.
- Toets:
  - Compute Δafwijking = (onbewerkt − gestabiliseerd/gemaskerd) en modelleer Δafwijking ~ bewegingsindex + glint‑index.
  - Weerlegging: Afwezigheid van grotere verbeteringen bij hoge indices verzwakt de artefact‑hypothese.

Ontbrekende gegevens/voorwaarden voor bovenstaande toetsen
- Vaste‑stand referentietijdreeks met voldoende temporele overlap en zicht op dezelfde watermassa.
- Zongeometrie, kijkrichting en mogelijkheid tot pose‑schatting (horizon/vaste punten) in beide camerabeelden.
- Beeldafgeleide indices: beweging (optical flow, scherpte), glinstering, en indien mogelijk reproprojectieparameters.
- Consistente segmentatie‑uitvoer en een maat voor grensgradiënt/contrast in de referentiebeelden.
- Mogelijkheid om software‑stabilisatie en glint‑masking toe te passen.

Beoordeling: maakt de voorgestelde vraag iets nieuws onderzoekbaar?
- Ja. Met een vaste‑stand referentie wordt niet alleen “de echte grens” observeerbaar, maar worden ook conditionele relaties en interacties onderzoekbaar die zonder referentie niet identificeerbaar waren:
  - Interactie tussen beweging en grenssterkte (H1) en heteroskedasticiteitspatroon (H2) onderscheiden ruis‑ van bias‑mechanismen.
  - Offset‑agnostische alignering (H3) scheidt tijdssynchronisatieproblemen van beeldartefacten.
  - Zongeometrie als instrument (H4) introduceert een exogene variatiebron voor glinstering.
  - Reproprojectie‑controle (H5) test expliciet het geometrische kanaal.
  - Selectie‑/collideranalyse (H6) adresseert een verborgen aanname over analysemogelijkheid.
  - Verschil‑in‑verschillen na bewerking (H7) toetst causaliteit van correcties.

Als de vaste‑stand referentie, pose‑schatting of zongeometrie‑informatie niet realiseerbaar zijn, volgt er geen nieuwe onderbouwde toetsbare afhankelijkheid uit de huidige situatie bovenop eerder voorgestelde analyses; de extra onderscheidingskracht ontstaat juist door deze externe/structurele informatie.
```

## H-O1 | horizon_after_T2 | ordinary | herhaling 1

**Voorlopige interpretatie:** Specificeert binnen-exposure smear als mediator boven algemene bewegingsanalyse.

### Eerste modelbeurt | SHA-256 `8f4a9098bdee2673399f0946620b873b7912631ebfea68690982f058c631d94c`

```text
Feiten
- Er zijn verschillen tussen de geschatte helder–troebelgrens uit boeibeelden en uit handmatige waarnemingen.
- Beelden zijn tijdgestempeld; camera en bewegingssensor delen geen gecontroleerde klok.
- Sommige beelden zijn gemaakt tijdens sterkere boeibeweging.
- Bewegingssensorwaarden zijn slechts als 5‑minutenmiddelen beschikbaar.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensordata ontbreken; klokafwijking blijft onbekend.

Hypothesen (onderling onderscheidend)
- H1 (bewegingsartefact): Geometrische poseverandering en/of motion blur door boeibeweging veroorzaken een systematische verschuiving van de grens in beeld. Voorspellingen: (i) grensafwijkingen nemen monotone toe met beeldafgeleide bewegingsscores; (ii) na software‑stabilisatie/deblurring nemen die afwijkingen aantoonbaar af.
- H2 (optisch/radiometrisch): Variaties in belichting/glitter/exposure verklaren vooral de verschillen. Voorspellingen: grensafwijkingen correleren sterker met glint-/belichtingsindices dan met bewegingsscores; stabilisatie helpt weinig.
- H3 (fysische variatie in water): De werkelijke grens verandert snel op (sub)seconde‑schaal binnen de bursts. Voorspelling: ook bij lage beweging en gunstige optiek blijft de grens temporeel instabiel en niet herstelbaar door stabilisatie/deblurring.

Ontbrekende gegevens
- Geen gesynchroniseerde, hoogfrequente bewegingsmetingen.
- Onzekere timing en beperkte dichtheid van handmatige waarnemingen.
- Geen onafhankelijke, vaste referentiecamerahoek of in‑situ troebelheidsground‑truth tijdens de drie bursts.
- Onbekende camera‑instellingen per frame (sluitertijd, gain) indien niet gelogd.

Onderscheidende onderzoeksvraag
Verklaart een beeldafgeleide bewegingsindex binnen korte frame‑reeksen (seconden) de afwijking en de interne incoherentie van de helder–troebelgrens beter dan radiometrische/glint‑indices, en neemt die afwijking af na digitale stabilisatie of deblurring?

Toetsende waarneming (uitvoerbaar met de drie ruwe frame‑reeksen)
- Stap 1: Per frame schatten
  - Bewegingsscore M: combinatie van horizon-/homografie‑jitter, optische‑flow‑energie op vaste referenties (kust/horizon), en blur/scherpte‑maat.
  - Radiometrische indices R: glint‑fractie op water, gemiddelde luminantie, histogram‑compressie (indicatie van exposure), kleurverhouding.
  - Grensmeting G: positie van de helder–troebelgrens via het bestaande algoritme.
- Stap 2: Interne referentie
  - Definieer per burst een robuuste lokale referentiegrens G_ref (bijv. mediaan over frames met laagste M en laagste R).
  - Bereken afwijking D = |G − G_ref| per frame.
- Stap 3: Analyse vóór correctie
  - Toets monotone associaties D~M en D~R met rangcorrelatie en partiële rangcorrelatie (M gegeven R, en omgekeerd), binnen bursts; combineer p‑waarden via meta‑analyse.
- Stap 4: Analyse ná correctie
  - Pas software‑stabilisatie en, separaat, deblurring toe; herbereken D.
  - Bepaal ΔD = D_vóór − D_ná per frame en relateer ΔD aan M en R.
- Beslisregels (falsifieer/ondersteun)
  - Ondersteunt H1: sterke, consistente D~M (partieel t.o.v. R) én positieve ΔD die toeneemt met M.
  - Ondersteunt H2: zwakke/geen D~M, maar sterke D~R; ΔD ≈ 0 onafhankelijk van M.
  - Ondersteunt H3: D blijft hoog bij lage M en lage R, en ΔD ≈ 0.

Opmerking bij beperkingen
- Slechts drie korte periodes beperken de power; gebruik binnen‑burst permutatietests en robuuste maten. Zonder externe ground‑truth blijft de uitkomst indicatief, maar wel toetsbaar en onderscheidend tussen H1 en H2/H3. Mocht geen consistente relatie met M of R worden gevonden, dan volgt hieruit: geen onderbouwde nieuwe onderscheidende richting met de huidige data.
```

### Tweede modelbeurt | SHA-256 `66c0d724a3e2183e864467de526eb4d33d96eec3ca5a56ac008d5ebccef18ab9`

```text
Feiten
- Er zijn systematische verschillen tussen de grensschatting uit boeibeelden en handmatige waarnemingen.
- Beelden zijn tijdgestempeld, maar camera en bewegingssensor hebben geen gedeelde klok; van de sensor bestaan alleen 5‑minutenmiddelen.
- Sommige beelden zijn genomen bij sterkere boeibeweging.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensordata ontbreken.

Hypothesen en nieuw onderzoekbare afhankelijkheid/voorwaarde
- H1a (nieuwe, specifieker toetsbare afhankelijkheid binnen “bewegingsartefact”): Niet zozeer de inter‑frame poseverandering (M), maar de binnen‑exposure beweging (motion smear tijdens de sluitertijd, versterkt door rolling‑shutter‑uitlezing) is de dominante mediator die de grensverschuiving veroorzaakt.
  - Voorspellingen:
    1) Een per‑frame smeermaat S (afgeleid uit rolling‑shutter‑skew en blur) verklaart de grensafwijking D beter dan de inter‑frame bewegingsscore M.
    2) Deblurring met een PSF afgeleid uit S reduceert D significant; residualen correleren niet langer met S.
- H2 (alternatief binnen “optisch/radiometrisch”): Radiometrische/glint‑indices R verklaren D beter dan S; deblurring op basis van S helpt niet of nauwelijks.
- H3 (restcategorie): Zelfs bij lage S en lage R blijft D hoog en ongevoelig voor stabilisatie/deblurring; snelle fysische variatie of segmentatiekwetsbaarheid zonder directe link met beweging of radiometrie.

Ontbrekende gegevens
- Onbekend of de camera rolling‑shutter gebruikt en wat de lees-/sluitertijd is.
- Mogelijk ontbreken in alle frames voldoende vaste referenties (horizon/kustlijn/mast) om skew robuust te meten.
- Onbekende interne camera‑parameters (brandpunt, lensvervorming) kunnen absolute schattingen bemoeilijken; relatieve maten per burst volstaan waarschijnlijk.

Toetsbare, onderscheidende onderzoeksvraag (nieuwe invalshoek)
Is de grensafwijking D binnen de drie ruwe frame‑reeksen sterker gemedieerd door binnen‑exposure smeer S (rolling‑shutter‑skew en blur) dan door inter‑frame posejitter M of radiometrische/glint‑indices R, en verdwijnt de relatie met S na PSF‑gebaseerde deblurring?

Weerlegbare toets (uitvoerbaar met de drie ruwe frame‑reeksen)
- Stap 1: Per frame schatten
  - S (smeer): 
    - Rolling‑shutter‑skew: lineaire/affiene vervorming tussen boven- en onderbeeld gemeten op rechte randen (horizon, mast, kustrand) of via rANSAC‑homografieverschil per beeldrij; proxy voor hoek­snelheid × uitleestijd.
    - Blur/scherpte: Laplacian‑variantie of MTF‑achtig contrast.
    - Combineer tot gestandaardiseerde S (bijv. PCA/z‑scores).
  - M (inter‑frame jitter): globale homografie-/horizon‑jitter en optische‑flow‑energie tussen opeenvolgende frames op vaste referenties.
  - R (radiometrie): glint‑fractie op water, gemiddelde luminantie, histogram‑compressie, kleurverhoudingen.
  - G: grenspositie per frame; D = |G − G_ref| met G_ref als mediaan over frames met laagste S én laagste R binnen elke burst.
- Stap 2: Vergelijk verklaarde variantie
  - Modelleer D met robuuste regressie/rangmethoden binnen bursts:
    - D ~ S
    - D ~ M
    - D ~ R
    - D ~ S + M + R (partiële effecten).
  - Beslisregels vóór correctie:
    - Ondersteunt H1a als S een significante, grotere partiële bijdrage levert dan M en R, consistent over bursts.
- Stap 3: PSF‑geleide correctie
  - Stel per frame een 1D/2D lineaire motion‑PSF afgeleid uit S op; pas niet-blinde deconvolutie toe.
  - Herbereken G en D; bereken ΔD = D_vóór − D_ná.
  - Beslisregels na correctie:
    - Ondersteunt H1a als ΔD > 0 significant is en toeneemt met S; partiële correlatie tussen D_ná en S verdwijnt.
    - Ondersteunt H2 als ΔD ≈ 0 terwijl D vooral door R wordt verklaard (ook na eventuele belichtings‑normalisatie).
    - Ondersteunt H3 als D hoog blijft bij lage S en lage R en ΔD ≈ 0.
- Controleanalyse (conditionering als extra voorwaarde)
  - Herhaal de analyses op een subset met lage R (weinig glint/exposure‑afwijking). Blijft het S‑effect overeind, dan is radiometrische confounding onwaarschijnlijk.
  - Omgekeerd: subset met lage S; test of D primair met R samenhangt.

Wat maakt dit nieuw?
- Deze toets introduceert een expliciete mediator (binnen‑exposure smeer S) die met alleen de ruwe frames objectief te schatten is en die de causaliteit “boeibeweging tijdens belichting → grensverschuiving” onderscheidt van “inter‑frame posejitter” en van “radiometrische verstoringen”.
- De voorwaarde “relatie verdwijnt na PSF‑gebaseerde deblurring” is falsifieerbaar en specifieker dan eerder geteste associaties.

Wanneer volgt er niets nieuws?
- Als de camera geen detecteerbare rolling‑shutter‑artefacten vertoont, er geen bruikbare vaste referenties in beeld zijn én blurmaten onbetrouwbaar blijken binnen de korte bursts, dan kan S niet robuust worden geschat. In dat geval levert deze invalshoek geen onderbouwde, nieuwe onderscheidende toets op met de huidige data.
```

## H-O2 | horizon_after_T2 | ordinary | herhaling 2

**Voorlopige interpretatie:** Werkt al voorgestelde stabilisatie en ankers uit met scheidbaarheid en drempels.

### Eerste modelbeurt | SHA-256 `0a6b8191debd87e9a2b046e6ec6dda03d35fa473555cc345aeffbce20ddb71a2`

```text
Feiten (gegeven)
- Er zijn verschillen tussen de grensschattingen uit boeibeelden en incidentele handmatige waarnemingen.
- Camera en bewegingssensor hebben geen gedeelde, gecontroleerde klok; klokoffset/drift onbekend.
- Sommige beelden zijn genomen tijdens sterkere beweging; van de sensor zijn slechts 5‑minutenmiddelen beschikbaar.
- Er zijn drie korte periodes met ruwe cameraframes; ruwe bewegingssensorwaarden ontbreken; klokafwijking kan niet worden berekend.

Hypothesen (te onderscheiden mechanismen, geen van allen als feit gepresenteerd)
- H1 Geometrisch/motion‑blur mechanisme: boeibeweging (poseverandering en/of motion blur) verschuift de schijnbare helder–troebelgrens in het beeld.
- H2 Optisch/radiometrisch mechanisme: variatie in licht (schittering, contrast, bewolking) beïnvloedt de drempeling/segmentatie van de grens, ook zonder grote poseverandering.
- H3 Bemonsteringsmechanisme: de camera bemonstert momenten/locaties die fysisch afwijken van die van de handmatige waarnemingen (sub‑5‑minuten variatie, ruimtelijke mismatch), los van beweging of licht.

Ontbrekende gegevens
- Frame‑specifieke, gesynchroniseerde bewegingsdata; absolute camera‑pose t.o.v. wateroppervlak.
- Onafhankelijke, gelijktijdige “ground truth” van de helder–troebelgrens (bijv. in‑situ troebelheidsmeter of een vaste referentiecamerapositie).
- Gestandaardiseerde, reproduceerbare referentie van de handmatige grensbepaling.
- Kwantitatieve maat voor lichtcondities per frame (schitteringsindex, wolkendekking, zonpositie in beeld).

Onderscheidende onderzoeksvraag 1
- Vraag: Neemt de afwijking tussen de beeld‑gebaseerde grens en een referentie systematisch toe met een beeldafgeleide bewegingsindex, en verdwijnt/vermindert dit effect na software‑stabilisatie of deblurring?
- Toetsende waarneming:
  - Bereken per ruwe frame: (i) een bewegingsindex uit de beelden (bijv. horizon‑/homografie‑jitter, optische‑flow‑energie op vaste kustranden, blur‑maat), (ii) de grenspositie vóór en na stabilisatie/deblurring, (iii) een referentiegrens: handmatige annotatie per frame óf, als dat ontbreekt, een interne proxy (consistentie met nabijgelegen frames in rustige periodes).
  - Statistische toets: relateer afwijking vóór/na correctie aan de bewegingsindex; test op een positieve, monotone relatie vóór correctie en een significante reductie van deze relatie na correctie.
- Potentiële uitkomst en interpretatie:
  - Bevestiging H1: sterke relatie met bewegingsindex; correcties reduceren de relatie en de afwijking.
  - Weerlegging H1: geen relatie, of correcties veranderen niets wezenlijks.

Onderscheidende onderzoeksvraag 2
- Vraag: Verklaart cameraroll/pose (geometrische indicator) de richting en grootte van de grensverschuiving beter dan radiometrische/reflectie‑indicatoren (schitterings- of contrastindices), gegeven dezelfde bewegingssterkte?
- Toetsende waarneming:
  - Extraer per frame: (a) roll/pitch‑schatting via horizonfit of homografie, (b) radiometrische/glitter‑indices (speculaire hooglichten, polariteit, globale en lokale contrastmaten), (c) grensafwijking t.o.v. referentie.
  - Voer een multivariabele regressie of partiële correlatie uit; vergelijk verklaarde variantie (of informatiecriteria) van modellen met alleen geometrische termen vs alleen radiometrische termen vs gecombineerd.
- Potentiële uitkomst en interpretatie:
  - Bevestiging H1 (geometrisch dominant): geometrische termen verklaren significant meer dan radiometrische termen; richting van de fout komt overeen met de teken van roll/pitch.
  - Bevestiging H2 (optisch dominant): radiometrische/glitter‑termen domineren; geometrie voegt weinig toe.

Onderscheidende onderzoeksvraag 3
- Vraag: Blijft de relatie tussen bewegingsindex en grensafwijking bestaan na conditioneren op lichtcondities en opname‑timing t.o.v. tij/wind (proxy’s voor H3)?
- Toetsende waarneming:
  - Stratificeer frames op lichtconditie (bijv. lage vs hoge schitteringsindex) en op externe tijdcovariaten (tijfase, wind); test de slope van afwijking vs bewegingsindex binnen strata.
- Potentiële uitkomst en interpretatie:
  - Persistente slope binnen strata ondersteunt H1; verdwijnen van de slope binnen strata ondersteunt H2/H3.

Wanneer geen onderbouwde nieuwe vraag?
- Als handmatige frame‑specifieke referenties niet beschikbaar zijn én interne proxies onbetrouwbaar blijken (bij te korte reeksen of extreme heterogeniteit), kan geen extra onderscheidende toets met de huidige data worden geformuleerd. In dat geval is aanvullende, gesynchroniseerde referentiemeting (bijv. korte validatiecampagne met walcamera en IMU met gedeelde klok) eerst nodig om verder te onderscheiden.
```

### Tweede modelbeurt | SHA-256 `a75c338e9567c661f5ef461639c2ce56299bccfbd0e78a65f103276a1b1d157e`

```text
Feiten (gegeven)
- Er zijn drie korte periodes met ruwe cameraframes (zonder gesynchroniseerde bewegingsdata).
- Er bestaan afwijkingen tussen grensschattingen uit boeibeelden en handmatige waarnemingen.
- Klokken van camera en bewegingssensor zijn niet gedeeld; alleen 5‑minutenmiddelen van beweging zijn beschikbaar.

Te onderzoeken afhankelijkheid/voorwaarde die nu zichtbaar wordt
- De eerder voorgestelde toets (relatie tussen grensafwijking en beeldafgeleide beweging, en effect van stabilisatie/deblurring) veronderstelt dat:
  1) Geometrische poseverandering (inter‑frame) en motion blur (intra‑frame) in de ruwe frames te onderscheiden zijn via respectievelijk achtergrond‑gebaseerde homografie/horizon‑jitter en anisotrope scherptematen.
  2) Er in de frames voldoende statische referenties (horizon, kustlijn, vaste boeien/masten) aanwezig zijn om een betrouwbare homografie te schatten.
- Deze voorwaarden zelf zijn nu onderzoekbaar met de ruwe frames (zonder klok): we kunnen per frame zowel een pose‑proxy als een blur‑proxy afleiden en testen of ze informatief en niet‑collineair zijn.

Weerlegbare toets A: scheidbaarheid van geometrie vs blur (voorwaarde 1)
- Observaties:
  - Per frame: een blur‑anisotropie‑index (bijv. variatie van Laplacian in orthogonale richtingen; PSF‑richting).
  - Per frame‑paar: globale pose/jitter (homografie op statische achtergrond of horizonhoek; optische‑flow op niet‑water‑pixels).
  - Per frame: geschatte grenspositie (algoritmisch segmenteren; desnoods handmatige annotatie op een steekproef).
- Toets:
  - Pas een model toe: grensafwijking ~ pose‑proxy + blur‑proxy + interactie.
  - Falsifieerbaarheid:
    - Indien beide proxy’s zwak of sterk gecorreleerd zijn (multicollineariteit) en geen onafhankelijke bijdrage leveren, is de kernvoorwaarde (scheidbaarheid) niet vervuld en de eerder voorgestelde toets niet interpreteerbaar.
    - Indien pose‑proxy significant verklaart maar blur‑proxy niet (of omgekeerd), wordt respectievelijk H1‑geometrie of H1‑blur specifieker ondersteund; het alternatief wordt weerlegd binnen deze datasets.

Weerlegbare toets B: differentieel effect van correcties (maakt de mechanistische afhankelijkheid toetsbaar)
- Observaties:
  - Voor elk frame een “vóór” en “na” versie na:
    1) Alleen homografie‑stabilisatie (op achtergrondfeatures).
    2) Alleen deblurring (niet‑blind of blind, consistent toegepast).
  - Grenspositie voor elk van deze versies.
- Toets:
  - Verwachting bij geometrisch dominante fouten: homografie‑stabilisatie reduceert de grensafwijking en haar variantie; deblurring heeft beperkt effect.
  - Verwachting bij blur‑dominantie: deblurring reduceert afwijking; stabilisatie heeft beperkt effect.
  - Placebo‑controle: toepassen van een willekeurige (niet‑passende) homografie mag de afwijking niet systematisch reduceren.
  - Falsifieerbaarheid:
    - Als geen van beide correcties systematisch effect heeft, wordt de bewegingshypothese (H1) verzwakt en krijgen H2/H3 meer gewicht binnen deze data.
    - Als beide correcties effect hebben maar zonder relatie met hun respectieve proxy (pose of blur), is de voorgestelde mechanistische interpretatie niet houdbaar (weerlegd).

Weerlegbare toets C: noodzakelijke zichtbaarheid van statische referenties (voorwaarde 2)
- Observaties:
  - Aantal en ruimtelijke dekking van stabiele features per frame; reprojection error van de homografie; consistentie van horizonfit.
- Toets:
  - Stel drempels voor feature‑count en reprojection error vast. Indien niet gehaald, markeer frames/perioden als “geen betrouwbare geometrie mogelijk”.
  - Falsifieerbaarheid:
    - Als de meeste frames de drempels niet halen, is de voorwaarde voor geometrische scheiding niet vervuld en volgt er geen onderbouwde toepassing van de eerdere toets voor H1‑geometrie (niets nieuws testbaar zonder aanvullende data, zoals een vaste referentiecamerapositie).

Ontbrekende gegevens die de interpretatie beperken
- Onafhankelijke, gelijktijdige referentie van de grens (grondwaarheid) om absolute bias te scheiden van ruis.
- Betrouwbare exposure‑metadata (sluitertijd/ISO) om blur door weinig licht te onderscheiden van blur door beweging.
- Consistente handmatige annotaties per frame (interbeoordelaarsvariatie).

Conclusie
- Ja, de zojuist voorgestelde vraag maakt nieuwe voorwaarden expliciet onderzoekbaar: de scheidbaarheid tussen geometrische pose en motion blur, en de beschikbaarheid van statische referenties. Met ruwe frames kunnen deze voorwaarden zelf falsifieerbaar worden getest via (A) de onafhankelijke verklaringskracht van pose‑ en blur‑proxy’s en (B) het differentiële effect van stabilisatie versus deblurring, met (C) een voorafgaande kwaliteitsdrempel voor homografie‑betrouwbaarheid.
- Indien toets A/C falen (geen scheidbaarheid of onvoldoende referenties), volgt er met de huidige data geen nieuwe, onderbouwde onderscheidende mogelijkheid; aanvullende, gesynchroniseerde referentiemetingen zijn dan noodzakelijk.
```

## H-O3 | horizon_after_T2 | ordinary | herhaling 3

**Voorlopige interpretatie:** Voegt conditionele onafhankelijkheid en intra-burst settling toe.

### Eerste modelbeurt | SHA-256 `19847fc45d06a1d0380dc95f940ad1203cb5dec8a548dae10dedc517787bbbaf`

```text
Feiten
- Automatische boei met beeldreeksen; incidentele handmatige waarnemingen.
- Verschillen in de geschatte grens tussen helder en troebel water.
- Geen gedeelde klok tussen camera en bewegingssensor.
- Sommige beelden bleken tijdens sterkere beweging genomen; van de sensor zijn alleen 5‑minutenmiddelen beschikbaar.
- Drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden; klokafwijking nog onbekend.

Hypothesen (concurrerend)
- H1 (bewegingsartefact): Boeibeweging veroorzaakt via posewijziging en/of motion blur een systematische verschuiving van de geschatte grens in het beeld.
- H2 (optische confounders): Variatie in verlichting/schittering en wateroppervlakreflecties veroorzaakt schijnbare grensverschuiving, grotendeels onafhankelijk van boeibeweging.
- H3 (fysische variabiliteit): De werkelijke helder–troebelgrens verschuift in ruimte/tijd zodanig dat verschillen niet primair door beeldartefacten worden gedreven.

Onderscheidende onderzoeksvraag 1
- Vraag: Conditie op vergelijkbare lichtomstandigheden, neemt de afwijking van de geautomatiseerde grensschatting t.o.v. menselijke frame‑annotaties toe met een beeldafgeleide bewegingsindex?
- Toetsende waarneming:
  - Bereken per ruwe frame een bewegingsscore (bijv. globale homografie‑jitter, optische‑flow‑energie buiten water, en een blur/scherpte‑maat).
  - Laat onafhankelijke beoordelaars de grens op diezelfde frames annoteren (blinded voor bewegingsscore); neem hun consensus als referentie.
  - Kwantificeer per frame de absolute afwijking van het algoritme t.o.v. de referentie en toets de (monotone) associatie met de bewegingsscore (bijv. Spearman, stratificatie in kwintielen).
  - Sterke positieve relatie ondersteunt H1; afwezigheid ervan ondermijnt H1 t.o.v. H2/H3.

Onderscheidende onderzoeksvraag 2
- Vraag: Vermindert softwarematige stabilisatie/deblurring de afwijking tussen geautomatiseerde grensschatting en menselijke frame‑annotaties vooral in frames met hoge beeldbewegingsscore?
- Toetsende waarneming:
  - Verwerk dezelfde frames met en zonder stabilisatie/deblurring.
  - Meet de afwijking t.o.v. de menselijke referentie in beide condities en test het interactie‑effect met de bewegingsscore.
  - Selectieve foutreductie bij hoge beweging ondersteunt H1; geen of uniforme verandering wijst eerder op H2/H3.

Onderscheidende onderzoeksvraag 3
- Vraag: Bij lage beeldbeweging (onder een vooraf gekozen drempel), hangt de afwijking systematisch samen met een licht-/schitteringsindex?
- Toetsende waarneming:
  - Definieer een licht/schitteringsindicator per frame (bijv. intensiteitshistogram‑scheefheid, highlight‑fractie in hemel/oppervlakmaskers, polariteit van reflecties).
  - Analyseer alleen lage‑bewegingsframes en toets de relatie tussen deze indicator en de grensafwijking.
  - Een duidelijke relatie ondersteunt H2; afwezigheid verzwakt H2.

Ontbrekende gegevens die de scherpte van de toets beperken
- Onafhankelijke “ground truth” van helderheid/troebelheid gelijktijdig met de frames.
- Gesynchroniseerde, hoogfrequente bewegingsdata (IMU) om beeldbewegingsindices te valideren.
- Volledige camerametadata (exposure, gain, white balance) en externe condities (wind, golfhoogte, bewolking).
- Informatie over de opname‑triggerlogica (om selectiebias te beoordelen).

Samenvattend
- De meest onderscheidende, nu uitvoerbare toets gebruikt alleen de ruwe frames: toets of grensafwijkingen met een beeldafgeleide bewegingsindex meegroeien (vraag 1) en of stabilisatie die afwijkingen selectief reduceert (vraag 2). Deze toetsen zijn onafhankelijk van de ontbrekende klok- en IMU‑data en kunnen H1 versus H2/H3 onderscheiden binnen de beschikbare periodes. Als geen van beide relaties optreedt, volgt voor deze data geen onderbouwde nieuwe richting vanuit de bewegingshypothese.
```

### Tweede modelbeurt | SHA-256 `7c48624bb2f191b24a090845359f6dce2fef48f06efc4ecc033497b479888e19`

```text
Feiten
- Automatische boei levert beeldreeksen; incidentele handmatige waarnemingen bestaan.
- Verschillen in de geschatte grens helder–troebel.
- Geen gedeelde klok tussen camera en bewegingssensor; van de sensor zijn alleen 5‑minutenmiddelen beschikbaar.
- Drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden; klokoffset onbekend.

Nieuwe, nu onderzoekbare afhankelijkheid A: Conditionele irrelevantie van sensorbeweging
- Hypothese A (weerlegbaar): Gegeven een beeldafgeleide bewegingsindex M en een licht/schitteringsindex L, voegt het 5‑minutenbewegingsgemiddelde S geen verklaarkracht meer toe voor de grensafwijking E (fout van het automatische algoritme t.o.v. menselijke frame‑annotatie).
- Toetsbare voorspelling:
  - Koppel elk frame aan het bijbehorende 5‑minutenvenster (voor zover de tijdstempels dit toelaten).
  - Modelleer E ~ f(M, L) en toets vervolgens of S conditioneel onafhankelijk is van E: voeg S toe en test ΔR² of een partiële correlatie ρ(E, S | M, L).
  - H0: ρ(E, S | M, L) = 0 (S is conditioneel irrelevant). Verwerpen van H0 wijst op een extra, niet‑door‑M gevangen afhankelijkheid (bijv. selectie/triggering of aliasing door klokmismatch).
- Benodigde gegevens:
  - Per frame: E (vereist blinde menselijke annotaties), M (beeldafgeleid), L (beeldafgeleid, bijv. highlight‑fractie/contrast), 5‑minutenvenster‑ID voor S.
- Mogelijke uitkomsten en interpretatie:
  - S niet significant gegeven M en L: beeldbewegingsproxy is voldoende; extra mechanisme via S wordt niet ondersteund.
  - S wel significant: er is een resterende afhankelijkheid die duidt op capture‑selectie, klokaliasing of bewegingseffecten die M niet vastlegt. Dit maakt gerichte vervolgtoetsen naar triggerlogica/klokmismatch zinvol.

Nieuwe, nu onderzoekbare afhankelijkheid B: Camera‑autocontrole als mediator (exposure/WB‑settling)
- Hypothese B (weerlegbaar): Binnen korte frame‑reeksen (“bursts”) neemt E systematisch af over de frame‑index, onafhankelijk van M, wat wijst op stabilisatie van automatische belichting/white balance als foutbron.
- Toetsbare voorspelling:
  - Selecteer bursts met voldoende lengte; conditioneer op lage variatie in M en L binnen de burst.
  - Toets monotone trend van E over de frame‑index (bijv. Kendall’s tau of een mixed‑effects model met random burst‑intercept).
  - Optioneel: schat een exposure‑proxy per frame (blur‑gebaseerde effectieve sluitertijd of helderheids‑autogain‑schatting) en test het interactie‑effect E ~ M + L + exposure + index.
  - Een significante dalende trend (of significante exposure‑term) ondersteunt B; afwezigheid ervan verzwakt B.
- Benodigde gegevens:
  - Ruwe frames per burst; menselijke annotaties voor E; beeldafgeleide M en L; burst‑segmentatie.
- Mogelijke uitkomsten en interpretatie:
  - Positieve bevestiging: praktische mitigatie mogelijk (eerste k frames negeren of exposure pinnen); verklaart verschillen zonder extra fysisch mechanisme.
  - Geen trend: camera‑settling is geen dominante mediator; focus verschuift terug naar beweging/optiek.

Ontbrekende gegevens en beperkingen
- Voldoende overlap van frames met 5‑minutenvensters om S te koppelen; aantal frames per venster/burst kan beperkt zijn.
- Menselijke referentie‑annotaties nodig om E te bepalen.
- Herkenbare statische context voor robuuste M- en L‑schattingen bij variabele scènes.
- S blijft een ruwe maat; significante effecten zijn indicatief, niet definitief causaal.

Wanneer niets nieuws volgt
- Als S conditioneel irrelevánt is (A bevestigd) én er geen intra‑burst trend of exposure‑effect is (B verworpen), volgt er geen onderbouwde nieuwe afhankelijkheid uit de huidige data: de eerder voorgestelde beeldbewegings‑ en stabilisatie‑toetsen putten de onderscheidende mogelijkheden binnen deze dataset uit. Een volgende stap vereist dan externe, gesynchroniseerde metingen of onafhankelijke ground truth.
```

## H-P1 | horizon_after_T2 | placebo | herhaling 1

**Voorlopige interpretatie:** Specificeert tijdschaal en directe lag na algemene covariatie in T1.

### Eerste modelbeurt | SHA-256 `6ab37fd41945d4010b14ae8213c83b3f76317aee4392cd584b48a75ed0064214`

```text
Feiten
- Er zijn verschillen tussen de door de boeicamera afgeleide grens “helder–troebel” en handmatige waarnemingen.
- Tijdsynchronisatie tussen camera en bewegingssensor ontbreekt; er zijn alleen 5‑minutenmiddelen van beweging.
- Een deel van de beelden is genomen tijdens sterkere boeibeweging.
- Voor drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden en een gezamenlijke klok ontbreken.

Hypothesen (als te toetsen mogelijkheden, geen vaststellingen)
- H1 Beweging/pose en motion blur van de camera veroorzaken een schijnbare verschuiving van de grens in het beeld.
- H2 Werkelijke, snelle veranderingen in de waterkolom (frontdynamiek) veroorzaken de grensverschillen; beeldartefacten spelen geen dominante rol.
- H3 Beeldverwerking/algoritmiek (drempels, belichting/reflecties) introduceert systematische bias die samenvalt met, maar niet wordt veroorzaakt door, boeibeweging.

Ontbrekende gegevens
- Gesynchroniseerde, hoogfrequente bewegingsdata (IMU) en exacte tijdsrelatie met frames.
- Onafhankelijke “ground truth” voor troebelheid/helderheid rond de beeldlocatie.
- Volledige camerametadata (sluitertijd, gain, white balance) tijdens de ruwe frameperiodes.

Onderscheidende onderzoeksvraag
- Vraag A: Treedt de gemeten grensverschuiving binnen korte tijdvensters (seconden) systematisch op in samenhang met beeldafgeleide camerageometrie en blur, op een tijdschaal die fysisch onwaarschijnlijk is voor echte frontverplaatsing?
  - Toetsende waarneming: Gebruik de ruwe framereeksen om per frame (i) horizon-/homografie‑helling en een blur/scherptemaat en (ii) de grenspositie te schatten. Onderzoek binnen-burst regressies/correlaties en lag-analyse tussen pose/blur en grenspositie. Herhaal na software‑stabilisatie of deblurring. Een sterke, onmiddellijke covariatie die verdwijnt na stabilisatie ondersteunt H1; afwezigheid daarvan wijst richting H2/H3.

Aanvullende, onderscheidende deelvragen met bijbehorende waarnemingen
- Vraag B: Verdwijnt of vermindert de bias t.o.v. handmatige waarnemingen wanneer alleen lage‑bewegingsframes (volgens beeldbewegingsindex) worden gebruikt?
  - Waarneming: Stratificeer beelden op percentielen van een beeldbewegingsscore; vergelijk bias/variantie van de grensschatting per stratum met handmatige notities. Monotone afname ondersteunt H1.
- Vraag C: Is de intra-burst variatie in grenspositie groter dan verwacht uit plausibele frontdynamiek bij de gegeven stromings-/golfschaal?
  - Waarneming: Kwantificeer de frame‑tot‑frame spreiding van de grens binnen bursts; vergelijk met een eenvoudige fysische bovengrens voor frontverplaatsing per seconde (afgeleid uit typische stroomsnelheden). Variatie ver boven die bovengrens ondersteunt H1; vergelijkbare of lagere variatie laat H2/H3 open.
- Vraag D: Is de schijnbare grens gevoelig voor belichtingsparameters onafhankelijk van beweging?
  - Waarneming: Indien sluitertijd/gain metadata beschikbaar zijn: conditioneer op lage beweging en test associatie tussen belichting en grenspositie. Sterke gevoeligheid bij lage beweging ondersteunt H3.

Beoordeling “Gewichtloze onderzoeks­aantekening”
- De aantekening over “oriëntatie en slijtbaankoördinaten per paneel” is inhoudelijk niet gerelateerd aan de beschreven kustboei‑beeldmeting en draagt hier geen toetsbare, relevante hypothese aan. Voor deze casus afwijzen als niet‑toepasbaar.
```

### Tweede modelbeurt | SHA-256 `bb933d19d0953d86bb38f9b6ec06f6d89153ded800da16063810fddfe51f58ab`

```text
Feiten
- Er zijn drie korte reeksen met ruwe cameraframes (zonder ruwe bewegingssensor en zonder gedeelde klok).
- Er bestaan verschillen tussen de door de boeicamera afgeleide grens “helder–troebel” en handmatige waarnemingen.
- Eerder geformuleerd: binnen-burst covariatie tussen beeldafgeleide pose/blur en grenspositie kan H1 (bewegingsartefact) onderscheiden van H2/H3.

Hypothese (te toetsen mogelijkheid, geen vaststelling)
- H1a (uitwerking van H1): De grensafwijking bevat een hoogfrequent component dat coherent is met frame-tot-frame camerabeweging/blur; echte frontdynamiek draagt hoofdzakelijk laagfrequente variatie.

Ontbrekende gegevens
- Eventueel camerametadata (sluitertijd/gain) om blur-mechanismen beter te duiden; niet strikt noodzakelijk voor de hieronder voorgestelde toets.
- Externe stromings-/windsnelheden zouden de fysisch plausibele front­snelheid kwantificeren; niet strikt noodzakelijk voor de frequentiescheidingstoets.

Nieuwe, onderscheidende afhankelijkheid die nu onderzoekbaar wordt
- Tijdschaalafhankelijkheid: als het verschil door beeldartefacten komt, moet de grensafwijking binnen bursts een sterke, onmiddellijke (0–1 frame lag) en hoogfrequente samenhang vertonen met beeldafgeleide pose/blur. Echte frontverplaatsing kan op deze sub‑seconde schaal niet betekenisvol variëren.

Weerlegbare toets (falsifieerbaar, met alleen de ruwe frames)
1) Extracties per frame
   - Grenspositie in beeld (zelfde methode als gebruikt voor de grensschatting).
   - Pose/bewegingsproxy’s: globale homografie-/horizonjitter, optische‑flow‑energie op vaste referenties (kust/horizon), blur/scherpte‑maat (bv. Laplacian-variantie).
2) Detrending
   - Verwijder laagfrequente variatie uit beide reeksen (bv. high‑pass >0.5–1 Hz of lokale polynoom/LOESS) om te focussen op frame‑schaal dynamiek.
3) Coherentie- en lag-analyse
   - Bereken kruiscorrelatie en fasecoherentie tussen grensresiduen en pose/blur-residuen binnen elke burst.
   - Toets H0: “Geen associatie op hoge frequenties en geen 0–1‑frame‑lag piek” met permutatie/phase‑randomisatie van één reeks; controleer family‑wise error over frequentiebanden.
4) Stabilisatie‑gevoeligheid (controle)
   - Pas software‑stabilisatie/deblurring toe op de frames; herbereken grensresiduen. Toets of de hoogfrequente samenhang en variantie significant afnemen.

Mogelijke uitkomsten en betekenis
- Sterke hoogfrequente coherentie en 0–1‑frame‑lag piek; coherentie daalt na stabilisatie
  - Steunt H1a: grensafwijking gedreven door camerabeweging/blur. Voorwaarde “hoogfrequente koppeling” is hiermee vervuld.
- Geen hoogfrequente coherentie; verschillen blijven na stabilisatie
  - Falsifieert H1a voor deze bursts; laat H2 (snellere fysische variatie dan aangenomen) of H3 (algoritmische/optische bias onafhankelijk van beweging) open.
- Alleen laagfrequente samenhang
  - Wijst op gedeelde langzame drijvers (licht, kijkgeometrie op minuten­schaal) en vraagt aanvullende controle op belichting/algoritmiek (richting H3).

Waarom dit iets nieuws toevoegt
- De eerdere vraag keek naar covariatie “in het algemeen”. De nu voorgestelde toets maakt specifiek de afhankelijkheid aan tijdschaal en onmiddellijke lag onderzoekbaar, iets wat wél onderscheidt tussen een optisch/kinematisch artefact (sub‑seconde) en plausibele frontdynamiek (trager). Dit is toetsbaar met alleen de ruwe frames en dus nieuw gegeven de databeperkingen.

Beperkingen
- Korte bursts beperken statistische power; combineer resultaten over bursts met robuuste methoden.
- Confounders zoals schittering kunnen óók hoogfrequent zijn; reduceer met masker op niet‑water (horizon/kust) voor pose‑schatting en met polariteitscontroles in de segmentatie.

Beoordeling gewichtsloze onderzoeksaantekening
- “Oriëntatie en slijtbaankoördinaten per paneel” is niet gerelateerd aan de boeicamera‑casus; levert hier geen nieuwe, toetsbare afhankelijkheid. Verwerpen voor deze context.
```

## H-P2 | horizon_after_T2 | placebo | herhaling 2

**Voorlopige interpretatie:** Voegt lagtest toe en werkt stabilisatie/blur als controle uit.

### Eerste modelbeurt | SHA-256 `135706af1a1594b93f7d2c0bb60c5186464506fe1794cee6bda6e9e336fc25a9`

```text
Feit
- Er zijn verschillen tussen de door de boeicamera afgeleide grens “helder–troebel” en incidentele handmatige waarnemingen.
- Camera en bewegingssensor delen geen gesynchroniseerde klok; bewegingsdata bestaan als 5‑minutenmiddelen.
- Sommige beelden zijn genomen tijdens sterkere beweging (op basis van 5‑minutenmiddelen).
- Er zijn drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden; klokafwijking blijft onbekend.

Hypothesen en onderscheidende onderzoeksvragen met toetsende waarneming
1) Beweging als primaire oorzaak
- Vraag: Neemt de afwijking in grensschatting monotone toe met een beeldafgeleide bewegingsindex, onafhankelijk van lichtcondities?
- Toets: Bereken per frame een bewegingsscore (optische‑flow‑energie, homografie‑jitter, blur‑maat) en een licht-/glintproxy (bijv. intensiteit aan hemelmasker, speculaire highlight‑ratio). Modelleer afwijking ~ bewegingsscore + lichtproxy. Sterke, significante positieve associatie voor beweging (na controle) ondersteunt de hypothese; afwezigheid ervan weerlegt haar.

2) Optische glint/kijkhoek als primaire oorzaak (onderscheid tegen 1)
- Vraag: Kan een glintindex op basis van zon‑camera‑geometrie de afwijking verklaren wanneer de beeldbewegingsscore laag is?
- Toets: Selecteer frames met lage bewegingsscore. Schat per frame een glintindex uit zonpositie (tijd/locatie) en geschatte kijkrichting (horizon-/homografie‑schatting). Test associatie tussen glintindex en afwijking. Een duidelijke relatie bij lage beweging ondersteunt een optisch mechanisme; geen relatie weerlegt dit.

3) Geometrische pose/footprint‑verschuiving versus motion blur (onderscheid binnen “beweging”)
- Vraag: Verklaart frame‑tot‑frame pose‑verandering (kijkrichting/roll/pitch) de afwijking sterker dan blur?
- Toets: Decomposeer bewegingsscore in (a) globale pose (homografie/horizonhoek) en (b) blur‑maat. Vergelijk verklaringskracht (bijv. ΔAIC of partiële R²) voor afwijking. Overwicht van (a) wijst op footprint‑/parallaxeffect; overwicht van (b) op resolutieverlies door blur.

4) Selectiebias in beeldopnames
- Vraag: Worden beelden relatief vaker vastgelegd tijdens bovengemiddelde boeibeweging, wat een systematische bias kan introduceren?
- Toets: Vergelijk de verdeling van 5‑minutenbewegingsmiddelen op tijdstippen met beelden versus alle tijdstippen (bijv. KS‑test). Een verschuiving naar hogere waarden ondersteunt selectiebias; geen verschil weerlegt het.

5) Effect van stabilisatie als causale indicatie
- Vraag: Vermindert software‑stabilisatie/deblurring systematisch de afwijking?
- Toets: Pas beeldstabilisatie en, apart, deblurring toe op ruwe reeksen. Vergelijk de afwijking vóór/na per frame (gepaarde test/bootstrapping). Betekenisvolle reductie ondersteunt een beweging/blur‑mechanisme; geen verandering weerlegt het.

Ontbrekende gegevens die de toets versterken
- Absoluut gesynchroniseerde IMU‑data (korte validatiecampagne) om beeldafgeleide bewegingsscores te verifiëren.
- Externe licht/glint‑covariaten (bewolkingsgraad, polariserend effect) of een vaste referentiecamera aan wal.
- Objectieve, gelijktijdige “ground truth” troebelheid (in‑situ sensor) om menselijke variatie te isoleren.

Beoordeling “gewichtloze onderzoeksaantekening”
- De opmerking over oriëntatie en slijtbaankoördinaten per paneel is niet relevant voor deze boei‑/kustbeeldcasus en draagt hier geen toetsbare vraag bij; verwerpen voor deze context.

Samenvatting
- Een onderscheidende, nu toetsbare vraag is of de afwijking primair samenhangt met beeldafgeleide beweging (en welk submechanisme: pose versus blur) dan wel met optische glint/kijkhoek. De benodigde waarneming is een per‑frame bewegings- en glintindex uit de ruwe cameraframes, gevolgd door associatietests en interventies (stabilisatie/deblurring). Als deze analyses geen consistente relaties tonen, volgt er momenteel geen onderbouwde nieuwe vraag zonder extra data.
```

### Tweede modelbeurt | SHA-256 `71dbc43b41c44b93b0f854c416431488c9d04ea00e6639ac4ec264be37870adf`

```text
Feit
- Er zijn systematische verschillen tussen grensschattingen uit boeicamera‑beelden en incidentele handmatige waarnemingen.
- Er is geen gedeelde, gesynchroniseerde klok tussen camera en bewegingssensor; slechts 5‑minutenmiddelen zijn beschikbaar.
- Drie korte reeksen met ruwe cameraframes zijn beschikbaar; ruwe bewegingssensorwaarden ontbreken.

Nieuwe, nu onderzoekbare afhankelijkheid/voorwaarde
- Temporele voorrang binnen ruwe bursts: als boeibeweging de oorzaak is, dan zouden veranderingen in beeldafgeleide beweging (pose/blur) de gemeten grensverschuiving met een korte positieve vertraging voorafgaan binnen dezelfde burst. Dit is toetsbaar zonder absolute klok of IMU, omdat alleen de relatieve frametijd nodig is.

Hypothese
- H0 (weerlegbaar): Binnen korte ruwe reeksen is er geen systematische temporele voorrang van beeldafgeleide beweging t.o.v. grensverschuiving; geobserveerde afwijkingen komen niet primair door boeibeweging.
- H1: Veranderingen in beeldafgeleide beweging gaan grensverschuivingen op korte schaal (enkele frames) systematisch vooraf.

Toets (weerlegbaar ontwerp)
- Per ruwe reeks:
  - Bereken per frame twee tijdseries: (i) bewegingsproxy’s uit beeld (bijv. globale pose‑jitter via homografie/horizonhoek en een blur‑maat), en (ii) de geschatte grenspositie helder–troebel (in pixels of genormaliseerd beeldcoördinaat).
  - Verwijder langzame trends (bijv. high‑pass of lokale detrending) zodat korte‑termijnfluctuaties overblijven.
  - Bereken de kruiscorrelatiefunctie tussen beweging en grenspositie en schat de lag met maximale correlatie.
  - Permuteer framevolgorde binnen de burst als nuldistributie of gebruik fase‑randomisatie; herhaal de analyse om een p‑waarde/credible interval voor de dominante positieve lag te krijgen.
- Beslissingscriteria:
  - Evidentie voor H1: consistente piek bij kleine positieve lags (beweging leidt grens) in meerdere bursts, robuust over zowel pose‑ als blur‑proxy’s.
  - Evidentie tegen H1: symmetrische of nul‑kruiscorrelatie; of een dominante negatieve lag (grens “leidt” beweging), of resultaten verdwijnen onder milde detrending/robustheidstests.

Aanvullende onderscheidende voorwaarde die nu testbaar is
- Invariantie na referentie‑stabilisatie (pose versus niet‑bewegingsfactoren):
  - Hypothese: Als geometrische pose de driver is, dan verdwijnt het grootste deel van de grensafwijking nadat globale camerabeweging is verwijderd op basis van vaste referenties (kustrand/horizon).
  - Toets: Voer frame‑naar‑frame videostabilisatie uit met alleen wal/horizon‑features (water gemaskeerd). Herbereken de grens. Een substantiële en systematische reductie van afwijkingen ondersteunt pose‑geïnduceerde fouten; uitblijven daarvan weerlegt die verklaring en verschuift de aandacht naar blur of optische confounders.

- Blootstelling/blur‑voorwaarde zonder EXIF:
  - Hypothese: Als motion blur bijdraagt, dan correleert een beeldinterne blur‑lengteschaal (bijv. PSF‑lengte gemeten aan scherpe wal‑randen) monotone met de grensafwijking, zelfs na stabilisatie.
  - Toets: Kwantificeer per frame een blur‑lengte op vaste randen; modelleer afwijking ~ blur‑lengte. Afwezigheid van relatie weerlegt blur als primaire factor.

Ontbrekende gegevens
- Gelijktijdige, absolute referentie van troebelheid om menselijke interpretatie en waterdynamiek te scheiden (in‑situ sensor).
- Expliciete belichtingsmetadata; bij ontbreken kan de voorgestelde blur‑proxy dienen maar blijft indirect.
- Meer en langere ruwe reeksen om de temporele‑voorrangstoets met genoeg power te doen.

Conclusie
- Ja, de eerder voorgestelde vraag maakt een nieuwe, weerlegbare voorwaarde onderzoekbaar: temporele voorrang van beeldafgeleide beweging ten opzichte van grensverschuiving binnen ruwe bursts, die geen gedeelde klok vereist. Deze kan worden getoetst met kruiscorrelatie en permutationele nulmodellen, aangevuld met een referentie‑gestabiliseerde analyse om pose en blur te onderscheiden. Als deze toetsen geen consistente relaties of voorrang aantonen, volgt er op basis van de huidige data geen nieuwe onderbouwde vraag zonder extra metingen.

Beoordeling gewichtloze onderzoeksaantekening
- De notitie over oriëntatie en slijtbaankoördinaten per paneel is niet relevant voor de beschreven boei‑/kustbeeldcasus en levert hier geen toetsbare toevoeging; verwerpen voor deze context.
```

## H-P3 | horizon_after_T2 | placebo | herhaling 3

**Voorlopige interpretatie:** Voegt ruimtelijke signatuur en stationariteitsaanname toe.

### Eerste modelbeurt | SHA-256 `e3c1a12e022720058e9e354aa8fbf0acb706e157831dc5be981126c324078578`

```text
Feiten (gegeven in de casus)
- Er zijn verschillen tussen de geschatte grens “helder–troebel” uit boeibeelden en incidentele handmatige waarnemingen.
- Beelden zijn tijdgestempeld, maar camera en bewegingssensor delen geen gecontroleerde klok.
- Sommige beelden zijn genomen tijdens sterkere beweging; van de bewegingssensor bestaan alleen 5‑minutenmiddelen.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; geen ruwe bewegingssensorwaarden; klokafwijking nog onbekend.
- Er is geen vastgesteld fysisch mechanisme dat het verschil verklaart.

Kandidaat‑hypothesen (te toetsen, niet als feit)
- H1 Beweging/pose van de boei veroorzaakt geometrische verschuiving en/of motion blur, waardoor de grens in beeld systematisch verkeerd wordt geschat.
- H2 De grens verschuift fysiek in het water (ruimtelijke/temporoale variabiliteit), onafhankelijk van boeibeweging.
- H3 Variërende optische condities (licht/schittering/contrast) beïnvloeden het drempel/segmentatie‑algoritme, los van boeibeweging.
- H4 Capture‑logica selecteert relatief vaker beelden bij hogere beweging, waardoor een selectiebias ontstaat.

Ontbrekende gegevens die de discriminatie bemoeilijken
- Geen gesynchroniseerde, hoogfrequente bewegingsdata (oriëntatie/rol/helling/IMU) voor de ruwe frameperiodes.
- Geen absolute tijds‑offset/drift tussen camera en sensor.
- Beperkte “ground truth” tijdens de drie ruwe periodes (we weten niet of er gelijktijdige handmatige of referentiemetingen zijn).
- Onbekende en mogelijk variabele lichtcondities en camera‑instellingen per opname.

Onderscheidende onderzoeksvraag
V1 Is de afwijking tussen beeld‑afgeleide grens en handmatige referentie conditioneel (monotoon) toenemend met een per‑frame beeldbewegingsindex, en wordt die afwijking substantieel kleiner na software‑stabilisatie/deblurring?

Toetsende waarneming voor V1
- Waarneming 1a: Bereken per ruwe frame een beeldbewegingsindex (bijv. globale homografie‑jitter op horizon/vast land, optische‑flow‑energie buiten water, scherpte/blur‑maat). Modelleer de relatie tussen bewegingsindex en grensafwijking t.o.v. gelijktijdige handmatige of best beschikbare referentie. Een significante, positieve, robuuste trend ondersteunt H1; afwezigheid daarvan verzwakt H1 en maakt H2/H3 plausibeler.
- Waarneming 1b: Pas video‑stabilisatie en/of deblurring toe en herbereken de grens. Een selectieve reductie van de afwijking bij hoge bewegingsindex maar niet bij lage ondersteunt H1; geen verbetering wijst eerder naar H2/H3.

Aanvullende onderscheidende vraag
V2 Beweegt de geschatte grens mee met camera‑geometrie (beeldcoördinaten t.o.v. horizon/vaste referenties) of blijft zij vast in wereldcoördinaten?

Toetsende waarneming voor V2
- Waarneming 2: Gebruik vaste referentie‑features (horizon/landmark) in de ruwe frames om per frame een projectieve transformatie te schatten. Transformeer de grenspositie naar een genormaliseerd “wereld‑achtig” vlak. Als de grensverschuiving sterk afneemt na normalisatie, duidt dat op camera‑pose‑artefacten (H1). Blijft de verschuiving bestaan, dan wijst dat op echte watergrensvariatie of optische confounders (H2/H3).

Alternatieve onderscheidende vraag
V3 Is de grensafwijking sterker verklaard door licht‑/glansproxy’s dan door de bewegingsindex?

Toetsende waarneming voor V3
- Waarneming 3: Extraheer per frame optische covariaten (schitteringsratio, hemel‑helderheid, polarisatie‑achtige proxies via kleurkanalen, histogram‑contrast). Vergelijk verklaringskracht van modellen: grensafwijking ~ beweging vs ~ optische covariaten vs gecombineerd. Dominantie van optische termen ondersteunt H3; dominantie van beweging ondersteunt H1.

Pragmatische falsificatie‑vraag (indien uitvoerbaar)
V4 Repliceert de grensschatting in simultane beelden van een vaste walcamera zonder boeibeweging dezelfde afwijking op dezelfde momenten?

Toetsende waarneming voor V4
- Waarneming 4: Gelijktijdige opnames vanaf een starre wal‑opstelling richting hetzelfde waterdeel. Consistentie met de walcamera en afwijking vooral in boeibeelden tijdens hoge beeldbewegingsindex ondersteunt H1; gelijksoortige afwijkingen in beide systemen ondersteunen H2/H3.

Mogelijke uitkomst
- Als er in de drie ruwe periodes geen gelijktijdige referentie (handmatig of vaste camera) beschikbaar is én de optische variatie niet kan worden gescheiden van beweging, kan geen onderbouwde nieuwe onderscheidende vraag worden beantwoord met de huidige data. In dat geval rest hoogstens een methodologische pilot (bewegingsindex en stabilisatie) zonder definitieve discriminatie.

Beoordeling van de gewichtloze onderzoeksaantekening
- De notitie over “ontbrekende registratie van oriëntatie en slijtbaankoördinaten per paneel” lijkt thematisch niet relevant voor deze kustbeeld‑/troebelheidscontext. Ik verwerp deze kandidaat‑toets voor dit dossier wegens domein‑mismatch; zij draagt niet bij aan het onderscheiden van H1–H4 hierboven.
```

### Tweede modelbeurt | SHA-256 `a2022eadb790132f0558dd70adb290afe86591a6bb4c1501fcc71cbbbb150d04`

```text
Feiten
- Er zijn drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden.
- Alleen 5‑minutenmiddelen van de bewegingssensor bestaan buiten deze periodes.
- Geen gedeelde klok; absolute uitlijning camera–sensor blijft onzeker.
- Er is verschil tussen beeldafgeleide grens en handmatige waarnemingen; geen vastgesteld fysisch mechanisme.

Nieuwe afhankelijkheid/voorwaarde die nu onderzoekbaar wordt
- Tijdschalen‑scheiding binnen ruwe frame‑bursts: op secondenschaal mag de fysieke helder–troebelgrens weinig veranderen vergeleken met artefacten door boeibeweging en blur. Deze voorwaarde maakt een intra‑burst toets mogelijk die geen gesynchroniseerde sensor vereist.

Hypothese (toetsbaar, niet als feit)
- H1-intra: Binnen een korte ruwe frame‑periode correleert de afwijking van de grensschatting sterk en positief met een per‑frame beeldbewegingsindex; na stabilisatie/deblurring neemt die afwijking selectief af. Dit wijst op een bewegingsartefact.
- Alternatief H2/H3-intra: Binnen zo’n korte periode verklaart beweging de afwijking niet; variatie is minimaal of beter verklaard door optische condities (licht/schittering) of echte grensverplaatsing.

Weerlegbare toets 1: Intra‑burst stationariteit en co‑variatie
- Constructie:
  - Voor elk ruwe frame: (i) schat grenspositie, (ii) bereken beeldbewegingsindex (homografie‑jitter op horizon/landmarks, optische‑flow‑energie buiten water, scherpte/blur‑maat).
  - Modelleer binnen elke burst: grensafwijking t.o.v. burst‑mediaan ~ bewegingsindex.
  - Herhaal na software‑stabilisatie/deblurring.
- Falsifieerbare uitkomsten:
  - Sterke, monotone relatie vóór correctie én duidelijke reductie ná correctie ondersteunt H1-intra.
  - Afwezigheid van relatie en geen verbetering na correctie verzwakt H1-intra en maakt H2/H3-intra plausibeler.
- Waarom nieuw: benut alleen relatieve timing binnen bursts; absolute klok en externe sensor zijn niet nodig.

Weerlegbare toets 2: Ruimtelijk differentiële parallax‑signatuur
- Constructie:
  - Segmenteer de geschatte grens langs de beeldbreedte (links–midden–rechts).
  - Schat per segment de relatie tussen segment‑specifieke grensverschuiving en globale poseverandering (uit homografie/roll‑/pitch‑proxy).
- Falsifieerbare uitkomsten:
  - Tegenovergestelde of segment‑afhankelijke verschuivingsrichtingen die consistent zijn met verwachte projectieve/parallaxeffecten duiden op camera‑pose‑artefact (H1).
  - Gelijktijdige, gelijke richting/magnitude over alle segmenten wijst eerder op echte watergrensverplaatsing of uniforme optische confounders (H2/H3).

Aanvullende toets (optioneel, indien metadata beschikbaar): sluitertijd‑afhankelijkheid
- Verwachting: grensafwijking neemt sterker toe bij langere sluitertijden gegeven dezelfde bewegingsindex. Ontbreekt sluitertijd‑metadata, dan is deze toets nu niet uitvoerbaar.

Ontbrekende gegevens die de besliskracht beperken
- Geen gelijktijdige handmatige of onafhankelijke referentie binnen de drie ruwe periodes voor absolute bias‑schatting.
- Onbekende en mogelijk variabele belichting/exposure per frame; zonder EXIF vermindert scheiding tussen blur en contrastverlies.
- Beperkte lengte/aantal bursts kan de statistische power verlagen.

Conclusie
- De nieuwe, intra‑burst tijdschalen‑voorwaarde maakt twee weerlegbare toetsen mogelijk (co‑variatie met beeldbewegingsindex en parallax‑signatuur) die de bewegingshypothese (H1) onderscheiden van alternatieven zonder gesynchroniseerde sensor of gedeelde klok. Lukt het niet om significante patronen te vinden, dan volgt er geen nieuwe onderbouwde discriminatie uit de huidige data.

Beoordeling gewichtloze onderzoeksaantekening
- “Ontbrekende registratie van oriëntatie en slijtbaankoördinaten per paneel” is domeinvreemd aan deze kustbeeld/troebelheidscontext en draagt niet bij aan de onderscheidende toetsen hierboven; ik verwerp deze kandidaat als niet‑relevant voor dit dossier.
```

## H-S1 | horizon_after_T2 | shadow_candidate | herhaling 1

**Voorlopige interpretatie:** De anker-moderator staat al uitdrukkelijk in T1; T2 werkt rigiditeitstoets uit.

### Eerste modelbeurt | SHA-256 `88cb7bc2ab199cb59fc6227be17bd12ff7f36756d7d929d6a2a042af951364f5`

```text
Feit (gegeven in de casus)
- Er zijn verschillen tussen automatische beeldschattingen en incidentele handmatige waarnemingen van de grens helder–troebel.
- Beelden zijn tijdgestempeld, maar camera en bewegingssensor hebben geen gedeelde, gecontroleerde klok.
- Sommige beelden zijn gemaakt bij sterkere boeibeweging; de bewegingssensor leverde alleen 5‑minutenmiddelen.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden ontbreken; klokafwijking blijft onbekend.

Hypothesen en onderscheidende onderzoeksvragen (toetsbaar zonder gedeelde klok)
1) Beweging als primaire verklaarder (geometrisch/motion blur)
- Onderzoeksvraag: Neemt de afwijking van de grensschatting t.o.v. handmatige waarnemingen toe met een beeldafgeleide bewegingsscore, en daalt die afwijking na software‑stabilisatie/deblurring?
- Toets/waarneming: 
  - Bereken per frame/burst een bewegingsindex uit ruwe frames (bijv. globale posejitter via homografie/horizonfit, optische‑flow‑energie op vaste achtergrond, scherpte/blur‑maat).
  - Kwantificeer de relatie tussen bewegingsindex en grensafwijking; herhaal na beeldstabilisatie/deblurring.
  - Een monotone toename vóór correctie en reductie ná correctie ondersteunt de bewegingshypothese; afwezigheid daarvan verzwakt haar.

2) Optische confounding (schittering/licht) i.p.v. of naast beweging
- Onderzoeksvraag: Blijft de relatie tussen bewegingsscore en grensafwijking bestaan wanneer frames met sterke schittering of ongunstige lichtgeometrie worden uitgesloten of apart geanalyseerd?
- Toets/waarneming:
  - Label frames op schittering/reflectie (bijv. hoge speculaire intensiteit in een hemelmasker of langs de zonreflectie‑baan).
  - Stratificeer analyse in “met” vs “zonder” sterke schittering.
  - Persisterende relatie in beide strata wijst op beweging; verdwijnen van de relatie in “zonder schittering” wijst op optische oorzaak.

3) Modererende rol van vaste visuele ankers (beleid op de gewichtsloze aantekening)
- Onderzoeksvraag: Is de sterkte waarmee beweging de grensafwijking voorspelt afhankelijk van de aanwezigheid van vaste referenties (horizon/vaste kustlijnen/boeien) in beeld?
- Toets/waarneming:
  - Detecteer of stabiele ankers aanwezig zijn (zichtbare horizon, kustlijn, masten).
  - Vergelijk de helling/slope van “bewegingsscore → grensafwijking” tussen frames met vs zonder ankers.
  - Sterkere relatie zonder ankers en grotere verbetering na stabilisatie mét ankers ondersteunt de notie dat ankers cruciaal zijn voor betrouwbare ego‑bewegingscorrectie offshore.

4) Onrealistische intra‑burst dynamiek als artefact-indicator
- Onderzoeksvraag: Overschrijdt de frame‑tot‑frame variatie van de geschatte grens binnen een korte burst een fysisch plausibele verandering op die tijdschaal?
- Toets/waarneming:
  - Meet de binnen‑burst variabiliteit van de grenspositie en relateer die aan de bewegingsindex binnen dezelfde burst.
  - Een hoge variabiliteit die samenvalt met hoge bewegingsindex suggereert artefact; lage variabiliteit bij lage index is consistent met fysische stabiliteit.

5) Algoritmische gevoeligheid voor blur/pose
- Onderzoeksvraag: Is de geautomatiseerde grensdetectie systematisch gevoeliger voor synthetische blur/pose‑perturbaties dan handmatige interpretatie van dezelfde beelden?
- Toets/waarneming:
  - Pas gecontroleerde, synthetische motion blur en kleine homografie‑perturbaties toe op de ruwe frames.
  - Vergelijk de verandering in automatische grensschattingen met die in handmatig beoordeelde grensmarkeringen op dezelfde gemodificeerde beelden.
  - Een sterkere drift van het algoritme dan van de mens ondersteunt een verwerkings‑/algoritmische component.

Ontbrekende gegevens die de toetskracht beperken
- Aan- of afwezigheid en kwaliteit van vaste visuele referenties in de drie ruwe periodes.
- Cameraparameters per frame (sluitertijd, gain, rolling‑shutterprofiel), lensstatus (vervuiling/biofouling), en nauwkeurige projectiegeometrie t.o.v. wateroppervlak.
- Exacte tijdsrelatie tussen de ruwe frame‑periodes en beschikbare handmatige waarnemingen.
- Informatie over lichtcondities (zonhoogte/bewolking) tijdens de ruwe periodes.

Samenvattende keuze
- Er kan een onderscheidende, toetsbare vraag worden geformuleerd: of en in welke mate de beeldafgeleide bewegingsscore de grensafwijking verklaart, en of deze relatie wordt gemodereerd door de aanwezigheid van vaste visuele ankers en door schittering. De voorgestelde waarnemingen zijn uitvoerbaar met alleen de ruwe frames en vereisen geen gesynchroniseerde klok. Als deze relaties niet aantoonbaar zijn binnen de drie korte periodes, volgt er op basis van de huidige informatie geen nieuwe, onderbouwde onderscheidende vraag.
```

### Tweede modelbeurt | SHA-256 `3efe6212bc2f105842de001e78b996c40073eafaa06bada38dae9747bca4b572`

```text
Feit
- Er zijn drie korte periodes met ruwe cameraframes, maar geen ruwe bewegingssensorwaarden en geen gedeelde klok.
- Beeldafgeleide bewegingsschattingen zijn voorgesteld als onafhankelijke proxy.
- Onbevestigde aantekening: offshore kunnen vaste visuele ankers (horizon/kust/vaste objecten) ontbreken.

Hypothese / nieuwe onderscheidende vraag
- Voorwaarde-hypothese: Een beeldafgeleide bewegingsproxy is alleen valide als er in de frames voldoende rigide, niet-waterreferenties (horizon, kust, vaste objecten of stabiele hemelpatronen) aanwezig zijn waarop een consistente globale beweging (rigiditeit) kan worden vastgesteld.
- Onderscheidende vraag: Verliest de relatie “beeldbewegingsscore → grensafwijking” haar voorspelkracht wanneer frames geen rigide ankers bevatten (rigiditeitstest faalt), en wint zij voorspelkracht wanneer zulke ankers wel aantoonbaar aanwezig zijn (rigiditeitstest slaagt)?

Weerlegbare toets (zonder gedeelde klok)
1) Rigiditeitsscreening per framepaar/burst:
   - Segmenteer kandidaat-ankerregio’s: hemel/horizon, verre kust/structuren; maskeer water.
   - Pas een globale 2D-transformatie (bijv. homografie of similitude) op ankerfeatures toe.
   - Bereken de residuele fout (bijv. mediane reprojectiefout). Definieer drempels: “rigiditeit geslaagd” vs “gefaald”.
2) Beeldbewegingsscores berekenen:
   - Voor dezelfde frames: globale posejitter, optische-flow-energie op ankerregio’s, blur/scherpte.
3) Grensafwijking bepalen:
   - Bepaal per frame/burst de helder–troebelgrens (zoals nu gedaan) en de afwijking t.o.v. handmatige waarnemingen die temporeel voldoende nabij zijn.
4) Interactie-analyse:
   - Modelleer grensafwijking ~ bewegingsscore + rigiditeit (0/1) + interactie.
   - Toets of de helling van bewegingsscore significant is in de “rigiditeit geslaagd”-subset en niet significant in de “gefaald”-subset.
   - Bootstrap/permutatie voor betrouwbaarheidsintervallen gezien de kleine steekproef.
5) Falsifieerbaarheid:
   - Als de bewegingsscore ook zonder rigide ankers even goed of beter voorspelt, wordt de voorwaarde-hypothese weerlegd.
   - Als voorspelkracht sterk toeneemt mét rigide ankers en verdwijnt zónder, wordt de voorwaarde ondersteund.

Wat wordt hiermee nieuw onderzoekbaar?
- Niet alleen “of” beweging verklaart, maar “onder welke voorwaarde” de beeldafgeleide bewegingsproxy betrouwbaar is (aanwezigheid van rigide ankers). Dit maakt de toepasbaarheid van beeldgebaseerde correcties conditioneel toetsbaar.

Aanvullende, praktische variant (optioneel, nog steeds klokvrij)
- Synthetische-anker interventie: plaats tijdelijk een hoog-contrast marker op een starre mast zichtbaar in beeld of gebruik een walcamera met vaste kijkrichting als visueel anker; herhaal dezelfde analyse. Een sprong in voorspelkracht bij aanwezigheid van dit anker ondersteunt de voorwaarde.

Ontbrekende gegevens / beperkingen
- Onzeker of in de drie periodes voldoende ankerpixels aanwezig zijn; bij volledige afwezigheid kan de toets geen onderscheid maken.
- Nauwkeurigheid van de automatische grensschatting en beschikbaarheid van nabijgelegen handmatige referenties bepalen de power.
- Cameraparameters (sluitertijd/rolling shutter) ontbreken; residuen kunnen deels blur- in plaats van posefouten reflecteren.

Mogelijke uitkomsten en interpretatie
- Sterke interactie (alleen voorspelkracht mét rigide ankers): beeldbewegingsproxy is conditioneel valide; zonder ankers geen betrouwbare correctie te verwachten.
- Geen interactie (voorspelkracht onafhankelijk van ankers): de ankerafhankelijkheid wordt weerlegd; dan ligt de verklaring mogelijk meer bij radiometrische/optische factoren of bij algoritmische gevoeligheid die niet via posecorrigering oplosbaar is.
- Geen robuuste relatie in beide subsets: met de huidige data volgt geen nieuwe, onderbouwde onderscheidende vraag; extra data met expliciete ankers of metadata is nodig.
```

## H-S2 | horizon_after_T2 | shadow_candidate | herhaling 2

**Voorlopige interpretatie:** De ankerloze-proxyproblematiek staat al in T1; T2 geeft controles en vertakkingen.

### Eerste modelbeurt | SHA-256 `17537ac74713522dc3f67928b6694727732fd0a5a7597166475a43b5711c1d0a`

```text
Feit
- Er zijn drie korte periodes met ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden ontbreken in die periodes.
- Er is geen gedeelde, gecontroleerde klok tussen camera en bewegingssensor; klokafwijking kan (nog) niet worden bepaald.
- Beelden zijn soms gemaakt bij sterkere beweging; van de sensor zijn slechts 5‑minutenmiddelen beschikbaar.
- Er bestaan verschillen in de geschatte grens helder–troebel tussen automatische beeldanalyse en incidentele handmatige waarnemingen.
- Er is geen vastgesteld fysisch mechanisme dat het verschil verklaart.

Hypothese (kandidaat, toetsbaar te maken)
H1 Beweging van de boei (geometrische poseverandering en/of motion blur) veroorzaakt systematische vertekening van de grensschatting in de beelden.
H2 Optische omstandigheden die met (maar niet door) beweging covariëren (schittering, variatie in belichting, wolken) veroorzaken de verschillen, onafhankelijk van boeigeometrie.
H3 Algoritmische/definitie‑verschillen (drempels, segmentatiekeuze, verschillende operationele definitie van “helder/troebel”) veroorzaken een bias die ook bij quasi‑stilstaande beelden aanwezig blijft.

Ontbrekende gegevens (relevant voor de toets)
- Instantane bewegingsdata (IMU) met gesynchroniseerde klok tijdens de ruwe frameperiodes.
- Betrouwbare, gelijktijdige handmatige referenties binnen nauwe tijdvensters rond de ruwe frames.
- Vaste referentie‑structuren in beeld (horizon/vaste kustranden) kunnen ontbreken offshore; daardoor zijn homografie‑/pose‑schattingen lastig of niet robuust.
- Gestandaardiseerde informatie over lichtcondities (zonstand, bewolking, reflecties) tijdens de ruwe frames.

Onderscheidende onderzoeksvraag
Blijft de afwijking tussen de beeldgebaseerde grensschatting en de handmatige referentie aanwezig in de subset van beelden met lage beeldafgeleide bewegingsscore?

Toets/waarneming om deze vraag te steunen of te weerleggen
- Benadering van de bewegingsscore zonder vaste ankers (geschikt als horizon/land ontbreekt):
  - Per frame: bereken scherpte-/blur‑maten (bijv. variantie van Laplacian, MTF‑achtige contrastmeting), en inter‑frame consistentie in textuur (bijv. optische‑flow‑energie op watertextuur, globale frame‑to‑frame translatie‑energie via feature‑tracking met RANSAC, zonder aannemen van starre scène).
  - Combineer tot een gestandaardiseerde bewegingsscore per frame of per korte frame‑sequentie.
- Stratificatie:
  - Selecteer een “lage‑beweging”-subset (bijv. laagste 10–20% van de bewegingsscoreverdeling binnen de ruwe periodes).
- Vergelijking:
  - Vergelijk in deze subset de grensschattingen met de best beschikbare handmatige waarnemingen in nabijgelegen tijd (met gevoeligheidsanalyse voor onbekende klokoffset door symmetrische tijdvensters/permutatie).
  - Modelleer de relatie tussen afwijking en bewegingsscore (bijv. robuuste regressie of permutatietest op monotone trend).
- Interpreteerbaarheid/falsifieerbaarheid:
  - Observatie A: Afwijking ~0 in de lage‑beweging‑subset en sterk oplopend met bewegingsscore ondersteunt H1 en verzwakt H2/H3.
  - Observatie B: Een significante, blijvende bias in de lage‑beweging‑subset falsifieert H1 als volledige verklaring en ondersteunt H3 (en/of H2).
  - Observatie C: Afwijking correleert met licht-/schitteringsindicatoren maar niet met bewegingsscore; dit ondersteunt H2.

Aanvullende, onafhankelijke observatie (optioneel, indien uitvoerbaar zonder vaste ankers)
- Software‑deblurring op hoge‑bewegingsscorebeelden (blind/non‑blind varianten) en vervolgens her‑schatting van de grens. Systematische reductie van de afwijking na deblurring zonder wijziging van drempels/definities ondersteunt H1; uitblijven daarvan ondersteunt H2/H3.
- Interne consistentietoets zonder handmatige referentie: convergeren grensschattingen binnen korte, quasi‑stille micro‑reeksen? Uitblijvende convergentie wijst op H3.

Beperkingen bij deze toets
- Zonder vaste referentie‑structuren is globale pose‑schatting (homografie/horizon‑jitter) onzeker; focus daarom op blur‑ en intra‑frame/inter‑frame textuurmaten.
- Incidentele handmatige waarnemingen en tijdsonzekerheid beperken de kracht van de vergelijking; rapporteer daarom resultaten als trend/associatie, niet als absolute correctie.
- Slechts drie korte periodes beperken de generaliseerbaarheid; de toets is indicatief.

Conclusie
Er is een onderscheidende, toetsbare vraag te formuleren: persisteren de verschillen bij lage beeldbewegingsscores? Die kan met de huidige ruwe frames (en zonder gesynchroniseerde IMU) worden onderzocht via beeldafgeleide bewegingsindices. De uitkomst kan H1 ondersteunen of falsifiëren en helpt H2/H3 te onderscheiden. Indien vaste referenties geheel ontbreken en handmatige referenties niet voldoende nabij zijn, kan de toets aan kracht verliezen; in dat geval volgt geen nieuwe, onderbouwde vraag die verder gaat dan deze conditionele associatietest.
```

### Tweede modelbeurt | SHA-256 `d664d388a5aa2371d3fe8293194630ba6c066b5142993c80f3fc1ab63ca7ff56`

```text
Feit
- Drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden in die periodes.
- Geen gedeelde, gecontroleerde klok tussen camera en bewegingssensor; offset/drift onbekend.
- Beelden soms gemaakt bij sterkere beweging; slechts 5‑minutenmiddelen van de bewegingssensor beschikbaar.
- Verschillen bestaan tussen beeldgebaseerde en incidentele handmatige schattingen van de helder–troebelgrens.
- Er is geen vastgesteld fysisch mechanisme dat het verschil verklaart.
- Onzeker of er vaste referentie‑structuren (horizon/kust/boeionderdelen) in beeld aanwezig zijn.

Hypothese (kandidaat, toetsbaar te maken)
- H1 Beweging van de boei veroorzaakt een systematische vertekening van de grensschatting.
  - H1a Pose/helling (zonder veel blur) kan al voldoende zijn om de grens te verschuiven.
- H2 Optische omstandigheden (schittering/variatie in belichting) veroorzaken de verschillen, los van boeigeometrie.
- H3 Algoritmische/definitie‑bias veroorzaakt blijvende afwijkingen, ook bij quasi‑stilstaande beelden.
- H4 (nieuw, hulpmiddel‑hypothese) De beeldafgeleide bewegingsscore meet werkelijk camera‑/boeibeweging en is niet gedomineerd door scène‑eigen dynamiek (golven).

Ontbrekende gegevens
- Instantane, gesynchroniseerde bewegingsdata tijdens de ruwe frameperiodes.
- Betrouwbare, gelijktijdige handmatige referenties nabij de ruwe frames.
- Zekerheid over aanwezigheid/afwezigheid en segmentatie van vaste referenties in beeld.
- Gestandaardiseerde licht-/schitteringsindicatoren; camerametadata (sluitertijd, gain) per frame.

Nieuwe, onderscheidende onderzoeksvraag die nu onderzoekbaar wordt
Meet de voorgestelde “lage‑beeldbewegingsscore” subset werkelijk lage camera‑/boeibeweging (en niet vooral golftextuur)? Met andere woorden: is de bewegingsscore een valide proxy voor ego‑beweging in deze ruwe periodes?

Waarom dit nieuw is
- De eerdere vraag (persisteren de verschillen bij lage beeldbewegingsscores?) veronderstelt impliciet dat de bewegingsscore camera‑/boeibeweging representeert. Die aanname is falsifieerbaar en maakt een cruciale afhankelijkheid expliciet: validiteit van de proxy, met of zonder vaste ankers in beeld.

Weerlegbare toets (zonder externe sensor; twee varianten afhankelijk van beschikbare ankers)

A. Met vaste referenties (bijv. horizon/kust/boeionderdelen) in beeld
- Methode
  - Segmenteer twee regio’s: vaste referentie‑ROI (horizon/land/vaste boeidelen) en water‑ROI.
  - Bereken per frame/sequentie:
    - Ego‑bewegingsindicator op referentie‑ROI: globale translatie/rotatie (feature‑tracking + RANSAC/homografie‑fit), horizon‑hoekjitter.
    - Scène‑dynamiekindicator op water‑ROI: optische‑flow‑energie/texture‑jitter.
  - Valideer de beeldbewegingsscore:
    - Toets correlatie met ego‑bewegingsindicator (verwacht hoog als de score echt camera‑beweging meet).
    - Toets partiële correlatie met scène‑dynamiek bij controle voor ego‑beweging (verwacht laag).
- Falsifieerbare uitkomsten
  - Uitkomst A1: Sterke relatie score ↔ ego‑bewegingsindicator, zwak met scène‑dynamiek → proxy valide. De “lage‑beweging”-subset is interpreteerbaar; vervolgtoets op H1/H2/H3 is betekenisvol.
  - Uitkomst A2: Zwakke relatie score ↔ ego‑bewegingsindicator, sterke met scène‑dynamiek → proxy niet valide. De eerdere vraag verliest bewijskracht; H1 kan niet fair getoetst worden met deze subset.

B. Zonder vaste referenties (offshore, geen horizon/land in beeld)
- Methode (camera‑specifieke signalen en negatieve controles)
  - Rollling‑shutter‑shear/jitter: kwantificeer inter‑lijn vervorming/kolomshear tussen opeenvolgende frames (indicator voor camera‑rotatie/versnelling, weinig gevoelig voor puur watergolven).
  - Sharpening/blur vs sluitertijd: gebruik per‑frame scherptemaat (Laplacian‑variantie) en, indien beschikbaar, sluitertijd/gain uit metadata; maak een samengestelde “camera‑bewegingsscore” uit shear + blur die specifiek is voor ego‑beweging.
  - Negatieve controle: bereken een alternatieve “water‑textuur‑score” (flow‑energie na hoge‑doorlaatfiltering binnen water‑ROI) die vooral scène‑dynamiek meet.
  - Valideer de beeldbewegingsscore door te toetsen of zij sterker correleert met shear/blur dan met de water‑textuur‑score.
- Falsifieerbare uitkomsten
  - Uitkomst B1: Sterke koppeling aan shear/blur, zwak aan water‑textuur → proxy redelijk valide → eerdere lage‑bewegingstoets is betekenisvol.
  - Uitkomst B2: Omgekeerd patroon → proxy niet valide → geen nieuwe onderbouwde toets op H1 met huidige data.

Aanvullende conditionele toets in de “valide proxy”-tak
- Binnen de “lage‑ego‑beweging”-subset, stratificeer op schitteringsindex/illumination (bijv. specular highlight fractie, lokale contrastcompressie).
  - Observatie C1: Afwijking ~0 en niet correlerend met schittering → ondersteunt H1a (pose/blur was dominante factor).
  - Observatie C2: Aanhoudende afwijking correlerend met schittering → ondersteunt H2 (optische confounders).
  - Observatie C3: Aanhoudende, niet‑schitteringsafhankelijke bias → ondersteunt H3 (algoritmiek/definitie).

Wanneer volgt er niets nieuws?
- Als er noch vaste referenties, noch camerametadata aanwezig zijn en rolling‑shutter‑artefacten niet detecteerbaar zijn, kan de validiteit van de bewegingsproxy niet onafhankelijk worden vastgesteld. Dan is de eerder voorgestelde lage‑bewegingsanalyse niet falsifieerbaar met de huidige ruwe frames, en volgt er geen nieuwe onderbouwde toets beyond indicatieve associaties.

Samenvatting
- Nieuwe voorwaarde onderzoekbaar: de validiteit van de beeldafgeleide bewegingsscore als proxy voor ego‑beweging (H4).
- Weerlegbare toets: differentieer ego‑beweging van scène‑dynamiek via (A) referentie‑ROI vs water‑ROI of (B) camera‑specifieke signalen (rolling‑shutter/blur) versus water‑textuur. De uitkomst bepaalt of de oorspronkelijke lage‑bewegingsvraag betekenisvol en toetsbaar is, en opent vervolgens een schone toets op H1/H2/H3; zo niet, dan volgt er met de huidige data geen nieuwe, robuuste mogelijkheid.
```

## H-S3 | horizon_after_T2 | shadow_candidate | herhaling 3

**Voorlopige interpretatie:** T1 stelt al testen met en zonder ankers voor; T2 verfijnt voorwaarden.

### Eerste modelbeurt | SHA-256 `ead44e9b477b16296b721ec7deb54554bd0afacee71220b12339c8f44a11024a`

```text
Feiten
- Er zijn verschillen tussen de geschatte grens “helder–troebel” uit boeibeelden en uit handmatige waarnemingen.
- Tijdsynchronisatie ontbreekt tussen camera en bewegingssensor; alleen 5‑minutenmiddelen van beweging zijn beschikbaar.
- Een deel van de beelden is genomen tijdens sterkere beweging.
- Van drie korte periodes zijn ruwe cameraframes beschikbaar; ruwe bewegingssensorwaarden ontbreken; klokafwijking kan niet worden berekend.

Hypothesen (niet als feit gepresenteerd)
- H‑A (geometrie): Posewijziging (rol/helling/parallax) verschuift de schijnbare grens in het beeld.
- H‑B (radiometrie): Motion blur/rolling‑shutter vermindert lokaal contrast en verplaatst drempelsegmentatie van de grens.
- H‑C (fysisch): De werkelijke grens in het water verschuift; verschillen komen niet primair door boeibeweging.
- H‑D (selectie): De afbeeldingslogica levert relatief vaker beelden tijdens hoge beweging, wat bias introduceert.

Ontbrekende gegevens
- Hoogfrequente, gesynchroniseerde bewegingsdata (IMU) en absolute tijdsafstemming.
- Onafhankelijke “ground truth” van troebelheid/helderheid in het gezichtsveld.
- Informatie over vaste referentie‑ankers in beeld (horizon/vaste kustranden) om homografie robuust te schatten.
- Logica en tijdschema van beeldopnames (mogelijk selectiemechanisme).

Onderscheidende onderzoeksvraag
V1. Is de grensafwijking primair te wijten aan geometrische poseverandering (H‑A) of aan radiometrische bewegingsvervaging (H‑B)?

Toetsende waarneming
- Gebruik de ruwe cameraframes uit de drie periodes en voer twee onafhankelijke correctiepaden uit op exact dezelfde frames met hoge beeldbewegingsscore (afgeleid uit de beelden zelf):
  1) Geometrische stabilisatie: schat en compenseer frame‑tot‑frame homografie/rotatie (met waar mogelijk horizon/vaste randen; bij gebrek daaraan gebruik globale feature‑velden en beperk de correctie tot rigide/affiene componenten). Segmenteer daarna opnieuw de grens.
  2) Deblurring zonder posecorrectie: pas blind/non‑blind deconvolutie toe (PSF geschat uit blur‑indicatoren) en herhaal de grenssegmentatie.
- Observeer per frame of per sequentie de verandering in afwijking t.o.v. handmatige referenties (of t.o.v. lage‑bewegingsframes uit nabijgelegen tijden) na (1) en na (2).

Falsifieerbare voorspellingen
- Sterkere foutreductie na (1) dan na (2) ondersteunt H‑A; het omgekeerde ondersteunt H‑B.
- Geen betekenisvolle verbetering na beide paden ondermijnt H‑A en H‑B en laat H‑C/H‑D plausibeler.
- Een gecombineerde stap (eerst 1, dan 2) die pas substantieel helpt suggereert gecombineerde mechanismen.

Aanvullende onderscheidende vraag (optioneel, gegeven beperkte data)
V2. Blijft er, na matching op lichtcondities en getij, een systematisch verschil in grensschatting tussen beelden met lage versus hoge beeldbewegingsscore?
- Waarneming: maak gematchte paren/sets op basis van tijd‑nabijheid, luminantie/reflectie‑indices en kijkrichting; test het verschil in grensafwijking tussen de lage‑ en hoge‑bewegingsstrata. Een nulverschil weerlegt dat beweging de dominante bron is; een toename ondersteunt H‑A/H‑B.

Opmerking bij ontbrekende ankers (gewichtloze aantekening)
- Indien vaste referenties (horizon/kust) in offshore‑beelden ontbreken, kan geometrische stabilisatie lastiger zijn. Toetsbaar: herhaal V1 afzonderlijk voor segmenten mét en zonder bruikbare referenties in beeld; als het onderscheidend vermogen alleen aanwezig is mét referenties, is vervolgmeting met zichtbare ankers (bijv. een simpele mast‑marker op de boei) aangewezen.

Als geen van deze waarnemingen een systematisch, reproduceerbaar patroon oplevert binnen de drie korte periodes, volgt er op dit moment geen onderbouwde nieuwe toetsbare mogelijkheid zonder extra data (gesynchroniseerde IMU, referentiemetingen of langere ruwe sequenties).
```

### Tweede modelbeurt | SHA-256 `6f7b814d19fb657e4041cfe9075c3130530e732f7eb05cb4d2c6f7e0c28e4c87`

```text
Feiten
- Er zijn drie korte periodes met ruwe cameraframes; geen ruwe bewegingssensorwaarden; gezamenlijke klok ontbreekt.
- Eerder voorgesteld onderscheid (V1): test of grensafwijking vooral komt door geometrische posewijziging (H‑A) versus radiometrische bewegingsvervaging (H‑B) via twee correctiepaden op dezelfde frames.

Nieuwe onderzoekbare afhankelijkheid/voorwaarde
- Aanwezigheid en detecteerbaarheid van vaste referentie‑ankers in beeld (horizon, kustlijn, vaste objecten) als noodzakelijke voorwaarde voor betrouwbare homografie/ego‑bewegingsschatting. Zonder zulke ankers kan pad (1) geometrische stabilisatie niet ondubbelzinnig worden beoordeeld, waardoor V1 niet identificeerbaar is.

Hypothesen over de afhankelijkheid (niet als feit)
- F‑1: Als er een stabiel en detecteerbaar anker (horizon/vaste rand) in beeld is, reduceert geometrische stabilisatie de grensafwijking significant meer dan deblurring wanneer H‑A domineert.
- F‑2: Als ankers ontbreken of onbetrouwbaar zijn, zal geometrische stabilisatie geen consistente verbetering geven, óók niet wanneer H‑A feitelijk meespeelt; daardoor lijkt H‑B (of H‑C) ten onrechte plausibeler.

Weerlegbare toets van de afhankelijkheid
- Stap 1: Automatisch ankerdetectie per frame
  - Horizon-/rechte‑lijn‑detectie (randextractie + Hough) en/of landmasker via kleur/tekstuur; label frames als “ankers‑aanwezig” versus “ankers‑afwezig/zwak”.
  - Kwaliteitsmaat per frame: ankerconsistentie over opeenvolgende frames (hoek/positie‑stabiliteit) en inliers‑aandeel bij rigide model.
- Stap 2: Uitvoeren van V1 gestratificeerd naar ankerstatus
  - Op dezelfde high‑motion frames twee paden toepassen: (1) geometrische stabilisatie (alleen toegestaan als ankerkwaliteit boven drempel ligt), (2) deblurring zonder posecorrectie.
  - Meet per frame/sequentie de verandering in grensafwijking t.o.v. een referentie (nabije low‑motion frames of handmatige waarnemingen indien beschikbaar).
- Falsifieerbare voorspellingen
  - P‑A (ondersteunt “ankers zijn noodzakelijke voorwaarde”): In “ankers‑aanwezig” reduceert (1) de fout significant meer dan (2); in “ankers‑afwezig” niet. Interactie‑term (ankerstatus × methode) is significant.
  - P‑B (weerlegt de afhankelijkheid): (1) presteert vergelijkbaar beter dan (2) zónder afhankelijkheid van ankerstatus, of (2) is over alle strata dominant; dan is ankerafhankelijkheid geen beperkende factor voor V1.
  - P‑C (ondermijnt V1 binnen huidige data): Geen significante verbetering van (1) zelfs in “ankers‑aanwezig”, en geen voordeel van (2); dan zijn H‑A/H‑B met deze data niet onderscheidbaar.

Aanvullende controlevoorwaarden die nu expliciet onderzoekbaar worden
- Constante camera‑intrinsieken per sequentie (f‑lengte/zoom, autofocus, rolling‑shutter‑variatie) als randvoorwaarde voor homografie.
  - Toets: lees per frame metadata/EXIF; test of intrinsics stabiel zijn. Voorspelling: Variatie in intrinsics correleert met misfit van het rigide model en vermindert winst van (1). Bij stabiele intrinsics moet het inliers‑aandeel en de foutreductie van (1) hoger zijn.
- Tekstuur/contrast van ankerregio’s als noodzakelijke informatiedichtheid.
  - Toets: relateer lokale SNR/contrast in ankerregio aan de kwaliteit van pose‑schatting en de foutreductie na (1). Monotone relatie ondersteunt de voorwaarde “voldoende informatiedichtheid”.

Ontbrekende gegevens die de toets beperken
- Onafhankelijke referentie van de grens of gelijktijdige low‑motion referentiebeelden voor alle drie periodes.
- Zekerheid over lichtcondities/glitter die ankerdetectie kan verstoren.

Wanneer volgt er niets nieuws?
- Als in de drie ruwe periodes geen frames met voldoende betrouwbare ankers kunnen worden gedetecteerd, én intrinsics/metadata ontbreekt of variabel is, dan is de afhankelijkheid niet empirisch toetsbaar met het huidige materiaal. In dat geval levert de voorgestelde vraag (V1) nu geen nieuwe, weerlegbare uitkomst op; extra data met expliciete referentie‑ankers (bijv. zichtbare mast‑marker of walzicht) of gesynchroniseerde IMU is dan vereist om de mechanismen te scheiden.
```

