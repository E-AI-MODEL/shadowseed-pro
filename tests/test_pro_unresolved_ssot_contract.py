"""No source-match to Gate authority for an unresolved Pro possibility."""
import numpy as np

from shadowseed.manager import SSLManager
from shadowseed.ssot import SSOTManager
from shadowseed.vectorstore import InMemoryVectorStore


def test_unresolved_stays_weightless_with_verifiable_ssot_content():
    manager = SSLManager(embedding_fn=lambda _text: np.array([1.0, 0.0]))
    original = (
        "De spanning en de camera zijn niet onafhankelijk. "
        "De sensor moet afzonderlijk worden onderzocht."
    )
    ingest = manager.ingest_detection_candidates(
        [original], expand_short_fragments=False, split_broad=False
    )
    assert len(ingest["unresolved"]) == 1
    sid = ingest["unresolved"][0]["seed_id"]
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    ssot.ingest_document("Het betreft een bevestigde bron.", doc_id="verified")
    assert ssot.validate_open_seeds_against_ssot(threshold=0.0) == []
    seed = manager.get_seed(sid)
    assert seed.text == original
    assert seed.scope_status == "unresolved"
    assert seed.weight == 0
    assert seed.evidence_count == 0
    assert manager.gate_events == []
    assert ssot.search(original)
