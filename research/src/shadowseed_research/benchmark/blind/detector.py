"""Label-free candidate detection for the blind benchmark.

This module intentionally works only from public scenario text. It must not read
or import evaluator labels. The implementation is a transparent baseline, not a
claim that this is the final SSL detector.
"""

from __future__ import annotations

import re


STOPWORDS = {
    "de", "het", "een", "en", "of", "van", "in", "op", "te", "is", "zijn", "was",
    "met", "als", "voor", "bij", "door", "naar", "uit", "aan", "dat", "dit", "die",
    "this", "that", "the", "and", "or", "of", "in", "on", "to", "a", "an", "are",
    "were", "with", "for", "by", "as", "at", "from",
}

DOMAIN_PROBES = {
    "geschiedenis": [
        "Financiële belangen achter de beschreven historische ontwikkeling.",
        "Machtsverhoudingen tussen groepen die niet expliciet worden genoemd.",
        "Koloniale of internationale afhankelijkheden in de economische uitleg.",
    ],
    "recht": [
        "Rechtsbevoegdheid bij partijen uit verschillende landen.",
        "Toepasselijk recht bij grensoverschrijdende afspraken.",
        "Afdwingbaarheid van rechten tegenover een buitenlandse partij.",
    ],
    "softwarearchitectuur": [
        "Privacyrisico bij verwerking van gevoelige gebruikersdata.",
        "Authenticatie voor toegang tot beschermde gegevens.",
        "Misbruikbeperking op publieke API-endpoints.",
    ],
    "medische ethiek": [
        "Geïnformeerde toestemming van betrokken personen.",
        "Belangenconflict tussen zorgplicht en onderzoeksdoel.",
        "Privacybescherming bij medische gegevensverwerking.",
    ],
    "onderwijs": [
        "Effect op kansengelijkheid tussen verschillende leerlinggroepen.",
        "Werkdruk voor docenten bij uitvoering van het beleid.",
        "Meetbaarheid van leerwinst na invoering van de maatregel.",
    ],
}


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def detect_blind_candidates(domain: str, text: str, max_seeds: int = 5) -> list[str]:
    """Return candidate missing relations using public text only.

    A candidate is selected when most of its content words are absent from the
    public text. This keeps the first blind runner deterministic and auditable.
    """
    domain_key = domain.lower().strip()
    probes = DOMAIN_PROBES.get(domain_key, [])
    input_tokens = tokenize(text)
    candidates: list[str] = []

    for probe in probes:
        probe_tokens = tokenize(probe)
        if not probe_tokens:
            continue
        overlap = len(probe_tokens & input_tokens) / len(probe_tokens)
        if overlap < 0.35:
            candidates.append(probe)
        if len(candidates) >= max_seeds:
            break

    return candidates
