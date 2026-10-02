"""Contextual, semantics-preserving help for the Shadowseed Workbench.

The help layer explains one product concept at a time. It never invents a new
policy or merges independent backend mechanisms into one UI concept.
"""

from __future__ import annotations

from typing import Any


_FEATURES: dict[str, dict[str, str | tuple[str, ...]]] = {
    "conversation": {
        "title": "Gesprek kiezen",
        "eli8": (
            "Zie dit als een schrift. Elk gesprek heeft zijn eigen pagina's én zijn eigen "
            "Shadowseed-geheugen. Als je een ander gesprek kiest, kijk je in een ander schrift."
        ),
        "does": "Kiest welke persistente sessie Chat, Shadow en Bronnen samen tonen.",
        "does_not": "Verandert geen Gate, seeds, authority of modelinstellingen.",
        "relations": (
            "Onafhankelijk: alleen de actieve sessie verandert; de inhoud van andere sessies blijft gelijk.",
        ),
    },
    "new_chat": {
        "title": "Nieuwe chat",
        "eli8": (
            "Je begint met een leeg schrift. Shadowseed heeft daar nog geen eerdere punten uit "
            "andere gesprekken in staan."
        ),
        "does": "Maakt een nieuwe live SSL-sessie met de gekozen modelprovider en veilige standaardinstellingen.",
        "does_not": "Kopieert geen seeds of authority uit het vorige gesprek.",
        "relations": (
            "Vereist: een geldige modelkeuze.",
            "Onafhankelijk: een nieuwe chat verandert bestaande gesprekken niet.",
        ),
    },
    "model": {
        "title": "Model en provider",
        "eli8": (
            "Het model is de schrijver van het antwoord. Shadowseed is het notitieboek ernaast. "
            "Een slimmere schrijver maakt Shadowseed niet automatisch machtiger."
        ),
        "does": "Kiest welk model de antwoorden genereert.",
        "does_not": "Geeft een seed geen authority en omzeilt de Validation Gate niet.",
        "relations": (
            "Onafhankelijk van authority: modelkwaliteit en seed-authority zijn verschillende dingen.",
            "Vereist toestemming wanneer de gekozen provider inhoud extern verwerkt.",
        ),
    },
    "external_consent": {
        "title": "Toestemming voor externe verwerking",
        "eli8": (
            "Dit vinkje is een deurbel: je zegt alleen dat de app naar buiten mág sturen als de "
            "gekozen provider dat nodig heeft. Het vinkje stuurt zelf niets."
        ),
        "does": "Geeft expliciete toestemming voor een configuratie die chatinhoud extern kan verwerken.",
        "does_not": "Schakelt geen provider in en verandert geen SSL-logica.",
        "relations": (
            "Vereist bij een externe provider zoals OpenAI.",
            "Onafhankelijk bij lokale generatie via Ollama of lokaal Hugging Face.",
        ),
    },
    "send": {
        "title": "Bericht versturen",
        "eli8": (
            "Je stelt een vraag. Eerst kijkt Shadowseed of een oud geheugenpunt nu relevant én "
            "toegestaan is. Daarna schrijft het model het antwoord. Vervolgens kijkt Shadowseed "
            "of er nieuwe mogelijke geheugenpunten zijn."
        ),
        "does": (
            "Voert één normale live beurt uit via prepare-turn, point-of-use, generatie en "
            "post-generation observatie."
        ),
        "does_not": "Promoveert niet automatisch elk nieuw geheugenpunt en behandelt herhaling niet als waarheid.",
        "relations": (
            "Als same-turn vergelijking aan staat: er komt één extra, niet-mutating no-SSL generatie bij.",
            "Als self-reinforcement uit staat: kandidaten uit een antwoord dat SSL-context kreeg worden niet teruggevoerd in recurrence/authority.",
        ),
    },
    "compare": {
        "title": "Vergelijk dit antwoord zonder SSL",
        "eli8": (
            "We laten dezelfde schrijver dezelfde vraag twee keer beantwoorden. Eén keer met de "
            "toegestane Shadowseed-notities en één keer zonder die notities."
        ),
        "does": (
            "Maakt een same-turn control met dezelfde pre-turn geschiedenis en hetzelfde generatiepad, "
            "maar zonder surfaced Shadow Seeds."
        ),
        "does_not": (
            "Bouwt geen tweede gesprek vanaf het begin op en schrijft het control-antwoord niet terug "
            "naar SSL-geheugen."
        ),
        "relations": (
            "Aan: één extra modelgeneratie voor deze beurt.",
            "Uit: alleen de normale SSL-beurt wordt gegenereerd.",
            "Onafhankelijk van Gate-authority: vergelijken geeft een seed geen extra authority.",
        ),
    },
    "shadow": {
        "title": "Shadow",
        "eli8": (
            "Shadow is de lade met briefjes die misschien later nuttig zijn. Een briefje in de lade "
            "is nog niet hetzelfde als: dit is waar."
        ),
        "does": "Toont persistente seeds en hun actuele lifecycle-, Gate- en gebruiksstatus.",
        "does_not": "Wijzigt niets zolang je alleen kijkt.",
        "relations": (
            "Onthouden ≠ toegestaan.",
            "Toegestaan ≠ relevant.",
            "Relevant ≠ automatisch aangeboden.",
            "Aangeboden ≠ bewezen oorzaak van een tekstverschil.",
        ),
    },
    "contradiction": {
        "title": "Tegenspraak registreren",
        "eli8": (
            "Je plakt een rood briefje op één geheugenpunt: er is een serieuze tegenspraak die eerst "
            "moet worden opgelost voordat dit punt weer een antwoord mag sturen."
        ),
        "does": "Maakt via de canonical contradiction-route een open contradiction record voor de seed.",
        "does_not": "Verwijdert de seed niet en wist eerder bewijs niet.",
        "relations": (
            "Blokkeert: een open contradiction blokkeert point-of-use influence.",
            "Sterker dan ondersteuning op point-of-use: extra verified evidence heft een open contradiction niet automatisch op.",
        ),
    },
    "verified_support": {
        "title": "Geverifieerde ondersteuning toevoegen",
        "eli8": (
            "Je zegt niet alleen 'ik heb dit ergens gelezen'. Je zegt: 'ik heb deze bron buiten het "
            "model gecontroleerd en dit ondersteunt precies dit geheugenpunt.'"
        ),
        "does": "Voegt onafhankelijk gecontroleerde support toe via de bestaande evidence- en Validation-Gate-route.",
        "does_not": "Maakt de seed niet automatisch waar en omzeilt een open contradiction niet.",
        "relations": (
            "Versterkt: evidence-backed authority kan sterker worden wanneer geldige, onafhankelijke support wordt toegevoegd.",
            "Vereist: expliciete verificatie-attestatie en een stabiele bronreferentie.",
            "Blokkeert niet: alleen support toevoegen heft een bestaande contradiction niet op.",
        ),
    },
    "sources": {
        "title": "Bronnen verwerken",
        "eli8": (
            "Je geeft Shadowseed extra leesvoer. Hij mag er dingen in opmerken en onthouden, maar hij "
            "mag niet zeggen: 'het stond in een document, dus het is waar.'"
        ),
        "does": "Verwerkt tekst als observatie-input en kan nieuwe seeds of recurrence opleveren.",
        "does_not": "Zet broninhoud niet automatisch om in verified evidence of authority.",
        "relations": (
            "Versterkt: herhaling/recurrence kan toenemen wanneer hetzelfde idee opnieuw onafhankelijk wordt waargenomen.",
            "Bij evidence-backed Gate: recurrence alleen mag geen verified evidence vervangen.",
            "Onafhankelijk: bronverwerking verandert de modelprovider niet.",
        ),
    },
    "research": {
        "title": "Onderzoek",
        "eli8": (
            "Dit is het proeflokaal. Hier mag je aan losse onderdelen draaien om te zien wat er gebeurt. "
            "Die knoppen horen niet in het gewone gesprek omdat ze verschillende onderzoeksvragen testen."
        ),
        "does": "Houdt experimentele configuraties en meetopzetten buiten de normale productflow.",
        "does_not": "Verandert niets zolang geen expliciet research-experiment is gestart.",
        "relations": (
            "Longitudinale A/B, self-reinforcement, alternatieve embeddings en Gate-experimenten blijven afzonderlijke functies.",
        ),
    },
    "technical_audit": {
        "title": "Technische audit",
        "eli8": (
            "Dit is de achterkant van het speelgoed waar je de tandwielen kunt zien. "
            "Je kijkt alleen; je draait hier niet aan de SSL-logica."
        ),
        "does": "Toont read-only sessie-, seed- en auditgegevens voor controle en reproduceerbaarheid.",
        "does_not": "Wijzigt geen seed, Gate, authority, recurrence of gesprekshistorie.",
        "relations": (
            "Onafhankelijk: openen of bekijken verandert geen runtimegedrag.",
            "Helpt uitleg controleren: de technische velden moeten overeenkomen met de gewone UI-taal.",
        ),
    },
    "semantic_matching": {
        "title": "Semantisch matchen",
        "eli8": (
            "Dit helpt herkennen dat 'de kat zit op de bank' en 'het dier ligt op de sofa' ongeveer "
            "hetzelfde kunnen bedoelen, ook als de woorden verschillen."
        ),
        "does": "Bepaalt hoe betekenis/relevantie tussen vragen en seeds wordt gematcht.",
        "does_not": "Bepaalt niet of een seed waar is en geeft geen authority.",
        "relations": (
            "Versterkt: semantische matching kan relevante parafrases beter terugvinden dan alleen woordoverlap.",
            "Onafhankelijk van Gate: beter terugvinden geeft een seed niet meer authority.",
        ),
    },
    "longitudinal": {
        "title": "Longitudinale vanilla-vergelijking",
        "eli8": (
            "Je laat twee aparte schriftjes naast elkaar groeien: één zonder SSL en één met SSL. "
            "Na een tijdje kijk je hoe ver de verhalen uit elkaar zijn gaan lopen."
        ),
        "does": "Onderhoudt een onafhankelijke vanilla-history om cumulatieve paddivergentie te onderzoeken.",
        "does_not": "Isoleert niet alleen het huidige SSL-effect op één beurt.",
        "relations": (
            "Kan duur/trager zijn: bij laat starten kan historische vanilla-replay nodig zijn.",
            "Onafhankelijk van de normale same-turn vergelijking: dit beantwoordt een andere onderzoeksvraag.",
        ),
    },
    "same_turn_revision": {
        "title": "Herziening in dezelfde beurt",
        "eli8": (
            "Shadowseed schrijft niet opnieuw vanaf nul. Als een nieuw geheugenpunt in deze beurt "
            "geautoriseerd raakt, mag het bestaande conceptantwoord één keer voorzichtig worden aangepast."
        ),
        "does": (
            "Geeft de revision-rol maximaal één extra pass met de echte draft en alleen geautoriseerde "
            "candidate-context."
        ),
        "does_not": (
            "Geeft modeloutput geen recurrence, evidence of authority en start geen herhalende feedbacklus."
        ),
        "relations": (
            "Revision en self-derived observaties zijn aparte mechanismen.",
            "De herziene tekst blijft SSL-blootgesteld in provenance.",
            "SELF_DERIVED blijft onder de normale Gate-policies fail-closed voor authority.",
        ),
    },
    "self_reinforcement": {
        "title": "Legacy self-reinforcement-instelling",
        "eli8": (
            "Oude sessies hadden één knop voor twee verschillende dingen. In 0.11 wordt die oude knop "
            "alleen nog vertaald naar herziening in dezelfde beurt."
        ),
        "does": "Behoudt oude sessies zonder opnieuw een modeloutput-naar-recurrence-lus te openen.",
        "does_not": "Laat SSL-blootgestelde modeloutput niet meetellen als gewone recurrence of bewijs.",
        "relations": (
            "Nieuwe UI gebruikt allow_same_turn_revision rechtstreeks.",
            "Self-derived observaties houden een aparte provenance-policy.",
        ),
    },
}


def _current_combination(
    view: dict[str, Any] | None,
    *,
    compare_enabled: bool,
    provider: str | None,
    hosted_confirmed: bool,
    seed: dict[str, Any] | None,
) -> list[str]:
    lines: list[str] = []

    if view:
        gate = str(view.get("effective_gate_policy_id", "unknown"))
        authority = str(view.get("authority_profile_id", "unknown"))
        same_turn_revision = bool(
            view.get(
                "allow_same_turn_revision",
                view.get("allow_self_reinforcement", False),
            )
        )
        self_derived_policy = str(
            view.get("self_derived_signal_policy", "fail_closed")
        )

        if gate == "evidence_backed":
            lines.append(
                "**Gate nu: evidence-backed.** Herhaling kan een patroon sterker zichtbaar maken, "
                "maar mag verified evidence niet vervangen voor authority."
            )
        elif gate == "exploratory":
            lines.append(
                "**Gate nu: exploratory.** Recurrence kan via deze researchpolicy bijdragen aan authority; "
                "het blijft geen extern bewijs."
            )
        else:
            lines.append(f"**Gate nu:** `{gate}` · authority-profiel `{authority}`.")

        if same_turn_revision:
            lines.append(
                "**Herziening in dezelfde beurt staat aan.** Een nieuw geautoriseerd geheugenpunt kan "
                "het bestaande draftantwoord maximaal één keer laten herzien."
            )
        else:
            lines.append(
                "**Herziening in dezelfde beurt staat uit.** De eerste zichtbare draft blijft dan de "
                "enige generatie voor deze beurt."
            )

        if self_derived_policy == "bounded_experimental":
            lines.append(
                "**Self-derived observaties staan in onderzoeksmodus.** Ze mogen voor audit worden "
                "bewaard, maar verhogen geen canonical recurrence en leveren geen authority."
            )
        else:
            lines.append(
                "**Self-derived authority staat fail-closed.** SSL-blootgestelde modeloutput kan de "
                "eigen recurrence- of authority-lus niet versterken."
            )

        embedding = str(view.get("embedding_backend", "lexical"))
        if embedding in {"sentence-transformers", "openai"}:
            lines.append(
                f"**Semantisch matchen staat aan via `{embedding}`.** Parafrases kunnen daardoor "
                "makkelijker als relevant worden herkend. Dit **versterkt alleen de matching**, niet de authority."
            )
        else:
            lines.append(
                "**Lexicale matching is actief.** Woordoverlap telt zwaarder; semantisch vergelijkbare "
                "parafrases kunnen daardoor minder makkelijk terugkomen. Dit **verslapt matching**, niet authority."
            )

        surface_top_k = int(view.get("surface_top_k", 2))
        if surface_top_k <= 0:
            lines.append(
                "**Surfacing staat effectief uit.** Ook een geautoriseerde en relevante seed kan dan niet "
                "aan het antwoord worden aangeboden."
            )
        else:
            lines.append(
                f"**Surfacing staat aan (maximaal {surface_top_k}).** Een geautoriseerde seed **kan** "
                "worden aangeboden als hij relevant is; hij **moet niet** worden aangeboden."
            )

        if gate == "evidence_backed":
            lines.append(
                "**Combinatie met evidence-backed:** recurrence kan een patroon zichtbaar maken, maar "
                "verified external evidence blijft de authority-basis. Revision verandert dat niet."
            )
        elif gate == "exploratory":
            lines.append(
                "**Combinatie met exploratory:** onafhankelijke recurrence kan authority bijdragen. "
                "SSL-blootgestelde modeloutput telt daarbij niet als nieuwe recurrence."
            )


    if compare_enabled:
        lines.append(
            "**Same-turn vergelijking staat aan.** Deze beurt kost één extra control-generatie, "
            "maar de control verandert het SSL-geheugen niet."
        )
    else:
        lines.append(
            "**Same-turn vergelijking staat uit.** Er is geen extra control-generatie."
        )

    normalized_provider = str(provider or "").strip().lower()
    if normalized_provider == "openai":
        lines.append(
            "**Provider is extern.** Zonder expliciete toestemming mag deze configuratie niet worden uitgevoerd."
            if not hosted_confirmed
            else "**Provider is extern en toestemming is gegeven.** Dit verandert geen seed-authority."
        )
    elif normalized_provider in {"ollama", "hf-transformers", "fixture"}:
        lines.append(
            "**Generatiepad is lokaal/demo.** Externe-provider-toestemming versterkt of verzwakt SSL hier niet."
        )

    if seed:
        if bool(seed.get("blocking", False)):
            lines.append(
                "**Dit geheugenpunt heeft een open contradiction.** Point-of-use is geblokkeerd, "
                "ook als er ondersteuning of historische promotie aanwezig is."
            )
        elif bool(seed.get("current_gate_authorized", False)):
            lines.append(
                "**Dit geheugenpunt is momenteel Gate-geautoriseerd.** Het kan nog steeds alleen worden "
                "aangeboden wanneer het bij de actuele vraag relevant is."
            )
        else:
            lines.append(
                "**Dit geheugenpunt is niet Gate-geautoriseerd.** Relevantie alleen is dus niet genoeg om het aan te bieden."
            )

    return lines


def render_feature_help(
    feature_id: str,
    *,
    view: dict[str, Any] | None = None,
    compare_enabled: bool = False,
    provider: str | None = None,
    hosted_confirmed: bool = False,
    seed: dict[str, Any] | None = None,
) -> str:
    feature = _FEATURES.get(feature_id)
    if feature is None:
        return "Geen uitleg beschikbaar voor deze functie."

    relations = feature.get("relations", ())
    relation_lines = "\n".join(f"- {item}" for item in relations)
    combination_lines = "\n\n".join(
        _current_combination(
            view,
            compare_enabled=compare_enabled,
            provider=provider,
            hosted_confirmed=hosted_confirmed,
            seed=seed,
        )
    )

    return (
        f"## ⓘ {feature['title']}\n\n"
        f"### Alsof je 8 bent\n{feature['eli8']}\n\n"
        f"### Wat doet dit echt?\n{feature['does']}\n\n"
        f"### Wat doet dit níet?\n{feature['does_not']}\n\n"
        f"### Samen met andere functies\n{relation_lines}\n\n"
        "**Legenda:** *versterkt* = een signaal/route kan sterker worden, niet 'meer waar'. "
        "*Verslapt* = een route wordt minder sterk of onderdrukt. *Blokkeert* = harde stop voor die route. "
        "*Onafhankelijk* = verandert die andere functie niet.\n\n"
        f"### Huidige combinatie\n{combination_lines}"
    )


def feature_ids() -> tuple[str, ...]:
    return tuple(_FEATURES)
