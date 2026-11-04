"""Herhaal een onafhankelijke letterlijke screening van historische seed-vensters.

Dit is een nieuwe zoekregel, geen exacte replicatie van PR #283.
Er worden geen ruwe kandidaat- of hostteksten uitgevoerd of uitgegeven.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

STOPWORDS = frozenset("""
de het een en of is zijn wordt worden van voor door met over niet geen deze die
 dat dit maar dan dus omdat zoals als tot naar bij onder boven tussen binnen
 buiten op aan om te ter ten per uit nog ook kan kunnen moet moeten heeft hebben
 had hadden was waren waar wat welke welk hoeveel hoever eerst tweede derde een
 twee drie goed al alle alleen meer minder wel reeds hetzij zonder echter daarbij
 hetzelfde verschillende verschillend mogelijke mogelijk geheel zelf zelfde tijdens
 geval zowel andere anders ieder there this these those from with without into
 that which where while might should could would have has were been being even
 both some much many upon across than also only just each when then and the are
 for not but was who why what how case after before between
""".split())
WORD = re.compile(r"[^\W\d_]{4,}", re.UNICODE)


def pairs(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text or "").casefold()
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    stems = [w[:6] for w in WORD.findall(normalized) if w not in STOPWORDS]
    return {a + "/" + b for a, b in zip(stems, stems[1:])}


def screen(source: dict) -> dict:
    observations = []
    for case in source["cases"]:
        turns = case["turns"]
        for turn in turns:
            report = turn["canonical_report"]
            lineage = {item["observation_id"]: item["outcome"]
                       for item in report["intake_diagnostics"]["item_lineage"]}
            for observation in report.get("candidate_observations", []):
                observations.append((case, turn, observation, lineage.get(observation["observation_id"], "unknown")))

    frequency = Counter(pair for _, _, obs, _ in observations
                        for pair in pairs(obs["raw_text"]))
    matches = []
    windows = 0
    for case, born, observation, status in observations:
        born_pair = pairs(observation["raw_text"])
        excluded_at_birth = pairs(born["user_input"]) | pairs(born["host_answer"])
        for later in case["turns"]:
            if later["turn"] <= born["turn"]:
                continue
            windows += 1
            excluded = excluded_at_birth | pairs(later["user_input"])
            latter = pairs(later["host_answer"])
            shared = sorted(pair for pair in born_pair
                            if frequency[pair] <= 3 and pair not in excluded and pair in latter)
            if shared:
                matches.append({
                    "observation_id": observation["observation_id"],
                    "case_id": case["case_id"],
                    "birth_turn": born["turn"],
                    "later_turn": later["turn"],
                    "intake_outcome": status,
                    "matched_stem_pairs": shared,
                })
    return {
        "schema": "shadowseed-independent-lexical-screen-v1",
        "method": "NFKD/casefold, words >=4 letters, 6-letter prefixes, explicit stopwords, rare pairs <=3 candidate occurrences",
        "scope": "Exploratory lexical screening, not an independent semantic or causal assessment",
        "source_observations": len(observations),
        "later_windows": windows,
        "matched_windows": len(matches),
        "matched_candidate_occurrences": len({x["observation_id"] for x in matches}),
        "accepted_matches": sum(x["intake_outcome"] == "accepted" for x in matches),
        "rejected_matches": sum(x["intake_outcome"] == "rejected" for x in matches),
        "matches": matches,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, help="Originele observer-JSON, lokaal aanwezig")
    args = p.parse_args()
    result = screen(json.loads(args.source.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
