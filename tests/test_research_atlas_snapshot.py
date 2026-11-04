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


FROZEN_SOURCE_SHA256 = {
    "findings": "b7c69246f5f7b3799db838506eba50ec96028fa9660a315d6f2e2caed4e56014",
    "relations": "b3f7610a3862790da96041ef601c2fb58ea0bb5b070508198a5f9a564cdbe87d",
    "trajectories": "f5dec37fb3a878a5a381f24f49e39f0f1d35db624c93431b6df1a7f1ab78a50c",
}

FROZEN_AUDIT_SHA256 = {
    "24_trajecten_T1_T2_originele_teksten_2026-11-04.md": "6c8a81c15b9267885cdd3d66a12c206e772c5f591a0d450b69654e4d99475dd3",
    "24_trajecten_T2_beoordeling_2026-11-04.csv": "5fca4d676bb3b79022b420e399d976ef1de96a245f05115969146a78c9a4e42b",
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
        expected = FROZEN_SOURCE_SHA256[section]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        assert data["provenance"][section]["sha256"] == expected


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


def test_original_trajectory_audits_are_byte_identical():
    for filename, expected_hash in FROZEN_AUDIT_SHA256.items():
        file = ATLAS / "sources" / filename
        assert file.is_file()
        assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_hash


def test_24_source_trajectories_match_their_documented_answer_hashes():
    import re

    dossier = (
        ATLAS / "sources" / "24_trajecten_T1_T2_originele_teksten_2026-11-04.md"
    ).read_text(encoding="utf-8")
    codings = source_rows("24_trajecten_T2_beoordeling_2026-11-04.csv")
    assert len(codings) == 24
    by_id = {item["case_id"]: item for item in codings}
    assert len(by_id) == 24
    sections = re.split(r"^## ([BH]-[DOPS]\\d) \\|", dossier, flags=re.MULTILINE)
    assert len(sections) == 49
    for case_id, section in zip(sections[1::2], sections[2::2]):
        assert case_id in by_id
        hashes = re.findall(
            r"^### (Eerste|Tweede) modelbeurt \\| SHA-256 \`([0-9a-f]{64})\`",
            section,
            re.MULTILINE,
        )
        assert [kind for kind, _ in hashes] == ["Eerste", "Tweede"]
        assert hashes[0][1] == by_id[case_id]["first_answer_sha256"]
        assert hashes[1][1] == by_id[case_id]["second_answer_sha256"]


def test_24_trajectory_codings_reproduce_all_eight_aggregate_groups():
    coded = source_rows("24_trajecten_T2_beoordeling_2026-11-04.csv")
    groups = {}
    for item in coded:
        groups.setdefault((item["moment"], item["arm"]), []).append(item)
    assert len(groups) == 8
    for row in snapshot()["trajectories"]:
        items = groups[(row["moment"], row["arm"])]
        assert row["n"] == len(items) == 3
        for code in ("new_factor", "refinement", "no_case_test"):
            assert row[code] == sum(item["delta_code"] == code for item in items)
        assert row["families_count"] == len({item["concept_family"] for item in items})
