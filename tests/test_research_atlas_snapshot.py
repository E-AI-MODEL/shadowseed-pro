"""Controleer de bronintegriteit van de Research Atlas zonder modelaanroepen."""
import csv
import hashlib
import json
from pathlib import Path


ATLAS = Path(__file__).resolve().parents[1] / "research" / "atlas"
SOURCES = {
    "findings": "34_bevindingen_bronafhankelijkheid_2026-11-04.csv",
    "relations": "verbindingskaart_tussen_34_bevindingen_2026-11-04.csv",
    "trajectories": "24_trajecten_vergelijkingsmatrix_2026-11-04.csv",
}


def snapshot():
    return json.loads((ATLAS / "data" / "atlas.json").read_text(encoding="utf-8"))


def source_rows(name):
    with (ATLAS / "sources" / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_csv_hashes_match_registered_provenance():
    data = snapshot()
    for section, name in SOURCES.items():
        path = ATLAS / "sources" / name
        assert path.is_file()
        assert data["provenance"][section]["filename"] == name
        assert data["provenance"][section]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_findings_match_original_source_fields():
    data = snapshot()
    source = source_rows(SOURCES["findings"])
    expected = [
        {
            "id": row["id"],
            "source_family": row["bronfamilie"],
            "stage": row["observatiestap"],
            "observation": row["oorspronkelijke_bronzin"],
            "boundary": row["bewijsgrens"],
            "source_url": row["bronlink"],
            "status": "reported_in_source",
        }
        for row in source
    ]
    assert len(expected) == 34
    assert len({row["id"] for row in expected}) == 34
    assert data["findings"] == expected


def test_relations_keep_alternatives_checks_and_valid_finding_links():
    data = snapshot()
    source = source_rows(SOURCES["relations"])
    expected = [
        {
            "id": row["id"],
            "finding_ids": row["betrokken_bevindingen"].split(),
            "question": row["onderzoeksvraag"],
            "observation": row["brongebonden_aanwijzing"],
            "alternative": row["sterkste_tegenverklaring"],
            "existing_material": row["nog_te_doen_met_bestaand_materiaal"],
            "status": "research_hypothesis",
            "check": row["onderscheidende_controle"],
        }
        for row in source
    ]
    assert len(expected) == 13
    assert data["relations"] == expected
    finding_ids = {row["id"] for row in data["findings"]}
    assert all(set(row["finding_ids"]).issubset(finding_ids) for row in expected)
    assert all(row["alternative"] and row["check"] for row in expected)


def test_trajectory_groups_match_source_without_claiming_independent_studies():
    data = snapshot()
    source = source_rows(SOURCES["trajectories"])
    expected = []
    for row in source:
        expected.append({
            "moment": row["moment"],
            "arm": row["arm"],
            "n": int(row["trajectories"]),
            "new_factor": int(row["new_factor"]),
            "refinement": int(row["refinement"]),
            "no_case_test": int(row["no_case_test"]),
            "families_count": int(row["families_count"]),
            "families": row["families"],
            "mean_word_jaccard": float(row["mean_word_jaccard"]),
            "coding": row["label_provenance"],
        })
    assert len(expected) == 8
    assert sum(row["n"] for row in expected) == 24
    assert data["trajectories"] == expected


def test_atlas_local_documentation_links_resolve():
    import re

    text = (ATLAS / "README.md").read_text(encoding="utf-8")
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        assert (ATLAS / link.split("#", 1)[0]).resolve().is_file(), link
