"""Contextual, semantics-preserving help for the Shadowseed Workbench.

The help layer explains one product concept at a time. It never invents a new
policy or merges independent backend mechanisms into one UI concept.
"""

from __future__ import annotations

from typing import Any


_FEATURES: dict[str, dict[str, str | tuple[str, ...]]] = {
    "conversation": {
        "title": "Gesprek kiezen",
        "plain": (
            "Elk gesprek heeft zijn eigen geschiedenis en zijn eigen Shadowseed-geheugen. "
            "Als je een ander gesprek opent, wissel je dus ook van die context. Er wordt niets "
            "uit een ander gesprek samengevoegd."
        ),
        "does": "Kiest welke persistente sessie Chat, Shadow en Bronnen samen tonen.",
        "does_not": "Verandert geen Gate, seeds, authority of modelinstellingen.",
        "relations": (
            "Onafhankelijk: alleen de actieve sessie verandert; de inhoud van andere sessies blijft gelijk.",
        ),
    },
    "new_chat": {
        "title": "Nieuwe chat",
        "plain": (
            "Een nieuw gesprek begint zonder eerdere berichten of geheugenpunten uit andere "
            "gesprekken. Bestaande gesprekken blijven opgeslagen, maar doen pas weer mee wanneer "
            "je ze zelf opent."
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
        "plain": (
            "Het taalmodel schrijft het antwoord. Shadowseed bepaalt alleen welke eerder onthouden "
            "punten als context mogen worden aangeboden. Dat zijn twee verschillende rollen."
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
        "plain": (
            "Sommige providers verwerken tekst buiten je computer. Met dit vinkje geef je daar "
            "expliciet toestemming voor. Het vinkje zelf verstuurt niets en verandert niets aan SSL."
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
        "plain": (
            "Bij ieder bericht bepaalt Shadowseed eerst of eerder onthouden informatie relevant "
            "én toegestaan is. Daarna maakt het model het antwoord. Vervolgens kan Shadowseed "
            "nieuwe mogelijke geheugenpunten opmerken."
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
        "plain": (
            "Deze optie laat dezelfde vraag ook zonder Shadowseed-context beantwoorden. Zo kun je "
            "de twee antwoorden naast elkaar bekijken zonder een tweede gesprek op te bouwen."
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
        "plain": (
            "Shadow toont wat Shadowseed heeft onthouden en in welke status ieder geheugenpunt "
            "staat. Onthouden betekent nog niet dat het punt waar is of een antwoord mag beïnvloeden."
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
        "plain": (
            "Met tegenspraak leg je vast dat er serieuze informatie is die tegen een geheugenpunt "
            "ingaat. Zolang die blokkade open staat, mag dat punt niet aan een antwoord worden aangeboden."
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
        "plain": (
            "Hier voeg je ondersteuning toe die je buiten het model hebt gecontroleerd en die "
            "specifiek bij dit geheugenpunt hoort. Dat is sterker dan alleen herhaling, maar maakt "
            "het punt niet automatisch waar."
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
        "plain": (
            "Bronnen geven Shadowseed extra materiaal om in te observeren. Daaruit kunnen "
            "geheugenpunten ontstaan of terugkomen. De inhoud van een bron wordt niet automatisch "
            "als bewijs behandeld."
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
        "plain": (
            "Onderzoek bevat functies waarmee je afzonderlijke SSL-mechanismen kunt testen of "
            "vergelijken. Ze staan apart van de gewone chat, zodat experimentele instellingen niet "
            "ongemerkt onderdeel van normaal gebruik worden."
        ),
        "does": "Houdt experimentele configuraties en meetopzetten buiten de normale productflow.",
        "does_not": "Verandert niets zolang geen expliciet research-experiment is gestart.",
        "relations": (
            "Longitudinale A/B, self-reinforcement, alternatieve embeddings en Gate-experimenten blijven afzonderlijke functies.",
        ),
    },
    "technical_audit": {
        "title": "Technische audit",
        "plain": (
            "Hier zie je de technische gegevens achter wat de gewone interface samenvat. Deze "
            "weergave is bedoeld om te controleren en te reproduceren wat er is gebeurd; alleen "
            "kijken verandert niets aan de runtime."
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
        "plain": (
            "Semantisch matchen kijkt naar betekenis in plaats van alleen naar dezelfde woorden. "
            "Daardoor kan een anders geformuleerde vraag toch bij hetzelfde geheugenpunt passen."
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
        "plain": (
            "Bij een longitudinale vergelijking lopen twee antwoordgeschiedenissen naast elkaar: "
            "één met Shadowseed en één zonder. Zo onderzoek je hoe de trajecten over meerdere "
            "beurten uit elkaar kunnen groeien."
        ),
        "does": "Onderhoudt een onafhankelijke vanilla-history om cumulatieve paddivergentie te onderzoeken.",
        "does_not": "Isoleert niet alleen het huidige SSL-effect op één beurt.",
        "relations": (
            "Kan duur/trager zijn: bij laat starten kan historische vanilla-replay nodig zijn.",
            "Onafhankelijk van de normale same-turn vergelijking: dit beantwoordt een andere onderzoeksvraag.",
        ),
    },
    "self_reinforcement": {
        "title": "Self-reinforcement",
        "plain": (
            "Bij self-reinforcement mag output die al met Shadowseed-context is gemaakt opnieuw "
            "bijdragen aan de geheugenlus. Dat kan patronen sneller versterken, maar maakt causale "
            "interpretatie moeilijker en blijft daarom experimenteel."
        ),
        "does": (
            "Laat kandidaten uit SSL-blootgestelde antwoorden terug de recurrence/authority-lus in en "
            "kan een begrensde same-turn refinement activeren wanneer nieuwe promotie optreedt."
        ),
        "does_not": "Maakt bewijs niet onafhankelijk en heft contradictions niet op.",
        "relations": (
            "Aan: feedbacklus wordt sterker en causale interpretatie wordt moeilijker.",
            "Uit: SSL-blootgestelde output kan zijn eigen recurrence/authority niet versterken.",
            "Blijft onder Gate en point-of-use; het is geen bypass.",
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
        self_loop = bool(view.get("allow_self_reinforcement", False))

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

        if self_loop:
            lines.append(
                "**Self-reinforcement staat aan.** SSL-blootgestelde output kan de eigen geheugenlus "
                "versterken. Dat is experimenteel."
            )
        else:
            lines.append(
                "**Self-reinforcement staat uit.** Als een antwoord SSL-context kreeg, worden kandidaten "
                "uit dat antwoord niet teruggevoerd om dezelfde recurrence/authority-lus te versterken."
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

        if gate == "evidence_backed" and not self_loop:
            lines.append(
                "**Combinatie Gate evidence-backed + self-reinforcement uit:** herhaling **kan** een patroon "
                "zichtbaarder maken, maar eigen SSL-output **mag niet** de recurrence/authority-lus versterken "
                "en recurrence alleen **mag niet** verified evidence vervangen."
            )
        elif gate == "evidence_backed" and self_loop:
            lines.append(
                "**Combinatie Gate evidence-backed + self-reinforcement aan:** eigen SSL-output **kan** de "
                "geheugenlus versterken, maar authority **moet nog steeds** voldoen aan de evidence-backed Gate."
            )
        elif gate == "exploratory" and self_loop:
            lines.append(
                "**Combinatie exploratory Gate + self-reinforcement aan:** recurrence **kan** authority sterker "
                "maken en eigen SSL-output **kan** die lus verder voeden. Dit is de meest versterkende researchcombinatie."
            )
        elif gate == "exploratory":
            lines.append(
                "**Combinatie exploratory Gate + self-reinforcement uit:** recurrence **kan** authority verhogen, "
                "maar SSL-blootgestelde output **mag niet** zijn eigen recurrence versterken."
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
