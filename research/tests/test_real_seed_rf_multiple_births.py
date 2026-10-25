"""Regression for a REAL canonical Engine with several simultaneous births.

The earlier one-seed fake passed but the GPT-5 stage-2 run stopped at the
second follow-up checkpoint. This builds multiple model-formatted proposals
at each actual observed turn, without network calls or any evidence claim.
"""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np

from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    MAX_CALLS, MAX_EMBEDDINGS, MAX_TOKENS, OUTPUT_CAP,
    INQUIRY_INSTRUCTIONS, NOTES_INSTRUCTIONS, run,
)
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DETECTOR_INSTRUCTIONS, HOST_INSTRUCTIONS,
)
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "real_seed_rf_inquiry_v1.json"

CANDIDATES = [
    [
        "1. Onbekende ruimtelijke offset: de twee sensoren bemonsteren mogelijk niet exact dezelfde plek/volume van het materiaal, waardoor lokale, echte transiënten alleen in kanaal 1 verschijnen.",
        "2. Tijdgemultiplexte ADC- of kanaalvolgorde-afhankelijk crosstalk/glitch in de front-end die specifiek kanaal 1 beïnvloedt.",
        "3. Firmware kan een periodieke self-test/auto-zero/diagnostische injectie op kanaal 1 hebben geïntroduceerd die als uitschieter wordt gelogd.",
    ],
    [
        "1. Onduidelijkheid hoe 'activiteit van de regelkast' is gedefinieerd en tijdgesynchroniseerd met kanaal-1-metingen.",
        "2. Onzekerheid of samplefrequentie en samplingfase aliasing of intermitterende detectie van storingsspikes veroorzaakt.",
        "3. Onbepaaldheid van de statistische sterkte van de correlatie tussen regelkastactiviteit en kanaal-1-uitschieters.",
    ],
    [
        "1. Onbekend of de tijdsmismatch constant of variabel is, wat bepalend is voor correlatie- en uitlijningsanalyses.",
        "2. Onbekende integratietijd en sample/hold-gedrag waardoor aliasing niet kan worden beoordeeld.",
        "3. Onzekerheid over onafhankelijkheid van beide kanalen in de keten, ondanks de uitgangsaanname.",
    ],
]


class MultiBirthProvider(BoundedProvider):
    def __init__(self):
        super().__init__(
            "NO_NETWORK_FAKE_KEY", model_call_cap=MAX_CALLS,
            embedding_call_cap=MAX_EMBEDDINGS,
            all_token_cap=MAX_TOKENS, output_token_cap=OUTPUT_CAP,
        )
        self.detector_calls = 0
        self.serial = 0

    def _post(self, endpoint, payload):
        if endpoint == "embeddings":
            text = payload["input"][0]
            vector = np.zeros(1536, dtype=float)
            # Distinct stable semantic placeholder vectors, no false
            # recurrence from a constant embedding.
            vector[int(sha256(text.encode()).hexdigest()[:5], 16) % 1536] = 1.0
            return {"data": [{"index": 0, "embedding": vector.tolist()}],
                    "usage": {"total_tokens": 18}}
        assert endpoint == "responses"
        self.serial += 1
        instructions = payload["instructions"]
        if instructions == DETECTOR_INSTRUCTIONS:
            text = "\n".join(CANDIDATES[min(self.detector_calls, 2)])
            self.detector_calls += 1
        elif instructions == HOST_INSTRUCTIONS:
            text = (
                "Twee afzonderlijke sensorstromen verschillen soms. Een "
                "regelkasthypothese is niet onafhankelijk bewezen."
            )
        elif instructions == NOTES_INSTRUCTIONS:
            text = "Twee sensoren meten een materiaal; de oorzaak blijft onbewezen."
        elif instructions == INQUIRY_INSTRUCTIONS:
            text = json.dumps({
                "question": "Welke onafhankelijke proef onderscheidt deze twee mogelijkheden?",
                "test": "Een apart meetinstrument en gelogde vergelijkingsreeks.",
                "uncertainty": "Geen zelfstandige testresultaten beschikbaar.",
            })
        else:
            raise AssertionError("unexpected model role")
        return {
            "id": f"mock_{self.serial}", "model": "gpt-5",
            "status": "completed",
            "usage": {"input_tokens": 125, "output_tokens": 220},
            "output": [{"content": [{"type": "output_text", "text": text}]}],
        }


def test_real_canonical_session_multiple_births_each_turn_retains_original_checkpoint():
    provider = MultiBirthProvider()
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = run(data, provider)
    assert result["first_seed"] is not None
    assert result["first_seed"]["weight"] == 0
    assert result["first_seed"]["sham_source"] == "different_real_T0_detector_item_not_first_seed"
    assert provider.detector_calls == 3
    assert all(
        item["followup"]["seed_id"] == result["first_seed"]["id"]
        for item in result["turns"][1:]
    )
    assert all(
        item["followup"]["seed_state_after_turn"]["weight"] == 0
        for item in result["turns"][1:]
    )
    assert result["status"] == "completed_exploratory_real_seed_and_arm_questions"
