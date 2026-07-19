import json
import re
from pathlib import Path

OUTPUT_DIR = Path("results/paper_ingest")


def extract_text(file: Path):
    if file.suffix == ".txt":
        return file.read_text(encoding="utf-8")
    if file.suffix == ".pdf":
        try:
            import fitz
        except ImportError:
            raise RuntimeError("Install: pip install shadowseed[paper]")
        doc = fitz.open(file)
        return "\n".join(page.get_text() for page in doc)
    return ""


def simple_claim_split(text: str):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 40]


def is_atomic(claim: str):
    return len(re.split(r"[,;]", claim)) <= 1


def claim_to_seed(claim: str):
    return {
        "seed_text": claim,
        "status": "candidate",
        "atomic": is_atomic(claim),
    }


def claim_to_ssot(claim: str):
    return {
        "text": claim,
        "status": "llm_proposed",
        "source": "paper",
    }


def run_pipeline(input_dir: str = "data/papers"):
    input_path = Path(input_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file in input_path.glob("*"):
        if file.suffix not in {".txt", ".pdf"}:
            continue

        text = extract_text(file)
        claims = simple_claim_split(text)

        seeds = [claim_to_seed(c) for c in claims]
        ssot_chunks = [claim_to_ssot(c) for c in claims]

        scenarios = [
            {
                "question": f"What is missing or unclear in: {c[:80]}",
                "expected_additions": ["clarification", "context", "validation"],
            }
            for c in claims[:5]
        ]

        out_dir = OUTPUT_DIR / file.stem
        out_dir.mkdir(exist_ok=True)

        (out_dir / "claims.json").write_text(json.dumps(claims, indent=2), encoding="utf-8")
        (out_dir / "seeds.json").write_text(json.dumps(seeds, indent=2), encoding="utf-8")
        (out_dir / "scenarios.json").write_text(json.dumps(scenarios, indent=2), encoding="utf-8")
        (out_dir / "ssot_proposals.json").write_text(json.dumps(ssot_chunks, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run_pipeline()
