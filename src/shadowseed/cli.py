"""Command line interface for Shadow Seed Learning."""

from __future__ import annotations

import argparse
from importlib import resources

from shadowseed.benchmark.open_set_candidate_adapter import SUPPORTED_DETECTORS
from shadowseed.detection.model_detector import SUPPORTED_MODEL_BACKENDS
from shadowseed.cli_dispatch import execute_command


VECTOR_BACKENDS = ["memory", "faiss", "chroma"]
MODEL_BACKENDS = ["fixture", "hf-transformers", "ollama", "openai"]


def _data_path(filename: str) -> str:
    """Return an installed package-data path for a bundled JSON fixture."""
    return str(resources.files("shadowseed").joinpath("data", filename))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shadowseed",
        description=(
            "Command-line interface for Shadow Seed Learning.\n"
            "Standard regression and smoke commands coexist with opt-in research commands.\n"
            "Legacy command aliases remain available for compatibility."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare-absencebench-bundle",
        aliases=["prepare-absencebench"],
        help="[absencebench] build a preparation bundle",
    )
    prepare.set_defaults(command="prepare-absencebench-bundle")
    prepare.add_argument(
        "--output",
        default="absencebench/preparation_result.json",
        help="Relative path inside benchmarks/results.",
    )

    local = subparsers.add_parser(
        "run-absencebench-local",
        aliases=["run-local-absencebench"],
        help="[absencebench] run AbsenceBench locally",
    )
    local.set_defaults(command="run-absencebench-local")
    local.add_argument("--input", required=True, help="JSON file containing local scenarios.")
    local.add_argument(
        "--output",
        default="absencebench/local_result.json",
        help="Relative path inside benchmarks/results.",
    )

    hf = subparsers.add_parser(
        "fetch-absencebench-sample",
        aliases=["fetch-absencebench"],
        help="[absencebench] fetch a sample for local inspection",
    )
    hf.set_defaults(command="fetch-absencebench-sample")
    hf.add_argument("--output", default="data/absencebench_sample.json")
    hf.add_argument("--limit", type=int, default=10)

    ssl = subparsers.add_parser(
        "run-gap-suite",
        help="[standard] regression suite for known SSL gaps",
    )
    ssl.add_argument("--input", default=_data_path("gap_test_suite_4_5.json"))
    ssl.add_argument("--output", default="results/ssl45_gap_suite.json")
    ssl.add_argument("--turns", type=int, default=3)

    fp = subparsers.add_parser(
        "run-false-positive-suite",
        help="[standard] negative control and Gate noise filtering",
    )
    fp.add_argument(
        "--input",
        default=_data_path("gap_test_suite_false_positive_4_5.json"),
    )
    fp.add_argument("--output", default="results/ssl45_false_positive_suite.json")

    benefit = subparsers.add_parser(
        "run-benefit-suite",
        help="[standard] small benchmark for answer improvement",
    )
    benefit.add_argument(
        "--input",
        default=_data_path("ssl45_benefit_suite.json"),
    )
    benefit.add_argument("--output", default="results/ssl45_benefit_suite.json")
    benefit.add_argument("--turns", type=int, default=3)

    model_benefit = subparsers.add_parser(
        "run-model-benefit-suite",
        help="[standard/manual] fixture smoke or optional real-model run",
    )
    model_benefit.add_argument(
        "--input",
        default=_data_path("ssl45_model_benefit_suite.json"),
    )
    model_benefit.add_argument("--output", default="results/ssl45_model_benefit_suite.json")
    model_benefit.add_argument("--turns", type=int, default=3)
    model_benefit.add_argument(
        "--backend",
        choices=MODEL_BACKENDS,
        default="fixture",
        help=(
            "Model backend. fixture is a deterministic CI smoke backend. "
            "hf-transformers runs a real local model through Transformers "
            "(requires --model-id and the models extra). ollama uses a real model through "
            "a local Ollama server (requires --model-id and a running "
            "`ollama serve` process with the model pulled). openai uses a hosted model through "
            "the OpenAI API (requires --model-id, the openai extra, and "
            "OPENAI_API_KEY in the environment)."
        ),
    )
    model_benefit.add_argument("--model-id", default=None)
    model_benefit.add_argument("--max-new-tokens", type=int, default=220)
    model_benefit.add_argument(
        "--semantic-embedding-backend",
        choices=["none", "lexical", "openai"],
        default="none",
        help=(
            "Optional semantic coverage metric alongside lexical matching. none disables it "
            "(CI default). lexical is a deterministic hash. openai uses real "
            "embeddings and requires the openai extra plus OPENAI_API_KEY. It measures whether the "
            "gap is addressed semantically instead of repeated literally."
        ),
    )
    model_benefit.add_argument("--embedding-model", default=None)
    model_benefit.add_argument("--semantic-threshold", type=float, default=0.55)

    blind = subparsers.add_parser(
        "run-blind-benchmark",
        help="[standard] methodological smoke test for label separation",
    )
    blind.add_argument(
        "--input",
        default=_data_path("blind_suite_public.json"),
        help="Public scenarios without evaluator labels.",
    )
    blind.add_argument(
        "--labels",
        required=True,
        help="Private file containing expected_gaps and must_not_add labels.",
    )
    blind.add_argument("--output", default="results/blind_benchmark.json")
    blind.add_argument("--turns", type=int, default=3)
    blind.add_argument("--max-seeds", type=int, default=5)

    open_set_hf = subparsers.add_parser(
        "fetch-open-set-hf-batch",
        help="[manual] fetch a small Hugging Face batch for open-set seed review",
    )
    open_set_hf.add_argument(
        "--source-id",
        default="ag_news_test",
        help="Source ID from the open-set Hugging Face source registry.",
    )
    open_set_hf.add_argument(
        "--registry",
        default=_data_path("open_set_hf_sources.json"),
        help="JSON file containing source definitions for Hugging Face open-set intake.",
    )
    open_set_hf.add_argument(
        "--output",
        default="benchmarks/open_review/input/hf_ag_news_test_batch.json",
        help="Path for the normalized open-set batch.",
    )
    open_set_hf.add_argument("--limit", type=int, default=12)
    open_set_hf.add_argument("--offset", type=int, default=0)

    open_set = subparsers.add_parser(
        "run-open-set-seed-review",
        help="[manual] open-set scaffold with review packets",
    )
    open_set.add_argument("--input", default=_data_path("open_set_seed_review_sample.json"))
    open_set.add_argument("--output", default="results/open_review/open_set_seed_output.json")
    open_set.add_argument(
        "--review-packets",
        default="results/open_review/open_set_review_packets.json",
        help="Path for human review packets.",
    )
    open_set.add_argument(
        "--reviewer-id",
        dest="reviewer_ids",
        action="append",
        default=None,
        help=(
            "Reviewer ID that receives a pending packet row. Repeat this option for "
            "multiple reviewers. Defaults to reviewer_a and reviewer_b."
        ),
    )
    open_set.add_argument(
        "--detector",
        choices=SUPPORTED_DETECTORS,
        default="adapter_v1",
        help=(
            "Candidate generator used when an item has no explicit candidate_seeds. "
            "adapter_v1 is the compatible regex-template baseline; adapter_v2 is "
            "text-grounded; model uses the language-model detector and also "
            "requires --model-backend."
        ),
    )
    open_set.add_argument(
        "--model-backend",
        choices=SUPPORTED_MODEL_BACKENDS,
        default="fixture",
        help=(
            "Model backend used by the detector. Relevant only with --detector model. "
            "fixture is deterministic and prefixes seeds with [FIXTURE]. "
            "hf-transformers requires --model-id and the models extra. ollama "
            "requires --model-id and a running server with the model pulled."
        ),
    )
    open_set.add_argument(
        "--model-id",
        default=None,
        help=(
            "Model ID for --model-backend. Use a Hugging Face repository ID for "
            "hf-transformers or an Ollama model name for ollama."
        ),
    )
    open_set.add_argument(
        "--max-new-tokens",
        type=int,
        default=400,
        help="Maximum number of tokens generated per item.",
    )
    open_set.add_argument(
        "--prompt-variant",
        choices=["absence", "generative"],
        default="absence",
        help=(
            "Detector prompt. absence asks what is missing. generative asks which "
            "useful perspective could have appeared. Relevant only with --detector model."
        ),
    )

    open_set_summary = subparsers.add_parser(
        "summarize-open-set-seed-review",
        help="[manual/reporting] summarize completed open-set review packets",
    )
    open_set_summary.add_argument(
        "--input",
        default="results/open_review/open_set_review_packets.json",
        help="JSON file containing completed review packets.",
    )
    open_set_summary.add_argument(
        "--output",
        default="results/open_set_seed_review_summary.json",
        help="Path for the aggregated review summary.",
    )
    open_set_summary.add_argument(
        "--disagreements-output",
        default="results/open_review/open_set_disagreements.json",
        help="Path for seed-level disagreements that need manual follow-up.",
    )
    open_set_summary.add_argument(
        "--report-output",
        default="results/open_review/open_set_review_report.md",
        help="Path for the readable open-set summary.",
    )

    list_models = subparsers.add_parser(
        "list-open-set-models",
        help="[info] show the curated Hugging Face model list for detector and SLM commands",
    )
    list_models.add_argument(
        "--registry",
        default=_data_path("open_set_models.json"),
        help="JSON registry containing curated models.",
    )
    list_models.add_argument(
        "--output",
        default=None,
        help="Optional output path for the table; defaults to stdout.",
    )

    adversarial = subparsers.add_parser(
        "run-adversarial-gate-benchmark",
        help="[manual] compare the current Gate with weaker promotion rules",
    )
    adversarial.add_argument(
        "--input",
        default=_data_path("adversarial_gate_benchmark.json"),
    )
    adversarial.add_argument(
        "--output",
        default="results/adversarial_gate_benchmark.json",
    )
    adversarial.add_argument(
        "--casebook",
        default="results/adversarial_gate_casebook.md",
        help="Path for the readable baseline-versus-Gate casebook.",
    )

    probe = subparsers.add_parser(
        "run-probe-utility-benchmark",
        help="[manual] behavioral scaffold for follow-up, retrieval, and dialectic probes",
    )
    probe.add_argument("--input", default=_data_path("ssl45_probe_utility_suite.json"))
    probe.add_argument("--output", default="results/ssl45_probe_utility_suite.json")

    probe_behavior = subparsers.add_parser(
        "run-probe-feedback-behavior-suite",
        help="[manual] Layer E lifecycle test: reward, penalty, clamping, demotion, and status blocking",
    )
    probe_behavior.add_argument(
        "--input",
        default=_data_path("probe_feedback_behavior_suite.json"),
    )
    probe_behavior.add_argument(
        "--output",
        default="results/probe_feedback_behavior_suite.json",
    )
    probe_behavior.add_argument(
        "--casebook",
        default="results/probe_feedback_behavior_casebook.md",
        help="Path for the readable per-scenario verdict casebook.",
    )

    vectorstore = subparsers.add_parser(
        "run-vectorstore-smoke",
        help="[manual] vector-store backend smoke test",
    )
    vectorstore.add_argument("--output", default="results/vectorstore_smoke.json")
    vectorstore.add_argument("--backend", choices=VECTOR_BACKENDS, default="memory")

    ssot = subparsers.add_parser(
        "run-ssot-smoke",
        help="[manual] SSOT and falsification-foundation smoke test",
    )
    ssot.add_argument("--output", default="results/ssot_smoke.json")
    ssot.add_argument("--backend", choices=VECTOR_BACKENDS, default="memory")

    retrieval = subparsers.add_parser(
        "run-retrieval-benchmark",
        help="[manual] retrieval quality of the selected vector store",
    )
    retrieval.add_argument("--input", default=_data_path("retrieval_benchmark.json"))
    retrieval.add_argument("--output", default="results/retrieval_benchmark.json")
    retrieval.add_argument("--backend", choices=VECTOR_BACKENDS, default="memory")
    retrieval.add_argument("--k", type=int, default=3)

    retrieval_model = subparsers.add_parser(
        "run-retrieval-model-benchmark",
        help="[manual] effect of retrieved context on model output",
    )
    retrieval_model.add_argument("--input", default=_data_path("retrieval_output_benchmark.json"))
    retrieval_model.add_argument("--retrieval-input", default=_data_path("retrieval_benchmark.json"))
    retrieval_model.add_argument("--output", default="results/retrieval_model_benchmark.json")
    retrieval_model.add_argument("--vector-backend", choices=VECTOR_BACKENDS, default="memory")
    retrieval_model.add_argument("--model-backend", choices=MODEL_BACKENDS, default="fixture")
    retrieval_model.add_argument("--model-id", default=None)
    retrieval_model.add_argument("--max-new-tokens", type=int, default=220)
    retrieval_model.add_argument("--top-k", type=int, default=3)

    ssl_vs_rag = subparsers.add_parser(
        "run-ssl-vs-rag",
        help="[manual/research] gap 3: SSL Retrieval Probe (query=gap) versus ordinary RAG (query=question)",
    )
    ssl_vs_rag.add_argument("--data", default=_data_path("ssl_vs_rag_benchmark.json"))
    ssl_vs_rag.add_argument("--output", default="results/ssl_vs_rag_benchmark.json")
    # Only the backends make_output_model actually supports — advertising
    # ollama here would crash at runtime (Codex #139). openai is supported.
    ssl_vs_rag.add_argument(
        "--model-backend", choices=["fixture", "hf-transformers", "openai"], default="fixture"
    )
    ssl_vs_rag.add_argument("--model-id", default=None)
    ssl_vs_rag.add_argument("--max-new-tokens", type=int, default=220)
    ssl_vs_rag.add_argument("--top-k", type=int, default=3)
    ssl_vs_rag.add_argument(
        "--use-centroid",
        action="store_true",
        help="Use one centroid query for the seed constellation instead of a per-seed union.",
    )
    ssl_vs_rag.add_argument(
        "--embedding-backend",
        choices=["lexical", "openai"],
        default="lexical",
        help=(
            "Retrieval embedder. lexical is a deterministic 128-dimensional hash "
            "for CI and mechanism tests. openai uses real embeddings and requires "
            "the openai extra plus OPENAI_API_KEY."
        ),
    )
    ssl_vs_rag.add_argument(
        "--embedding-model",
        default=None,
        help="Embedding model ID for the OpenAI embedding backend.",
    )

    adv_payoff = subparsers.add_parser(
        "run-adversarial-payoff",
        help="[manual/research] discrimination test: force a bad seed into the revision",
    )
    adv_payoff.add_argument("--input", default=_data_path("adversarial_payoff_suite.json"))
    adv_payoff.add_argument("--output", default="results/adversarial_payoff_suite.json")
    adv_payoff.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    adv_payoff.add_argument("--model-id", default=None)
    adv_payoff.add_argument("--max-new-tokens", type=int, default=400)

    wild_payoff = subparsers.add_parser(
        "run-wild-payoff",
        help="[manual/research] P0/W1: real open-set seeds through the payoff pipeline",
    )
    wild_payoff.add_argument("--input", default=_data_path("wild_payoff_suite.json"))
    wild_payoff.add_argument("--output", default="results/wild_payoff_suite.json")
    wild_payoff.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    wild_payoff.add_argument("--model-id", default=None)
    wild_payoff.add_argument("--max-new-tokens", type=int, default=400)
    wild_payoff.add_argument(
        "--semantic-embedding-backend", choices=["none", "lexical", "openai"], default="none"
    )
    wild_payoff.add_argument("--embedding-model", default=None)

    gen_payoff = subparsers.add_parser(
        "run-generative-payoff",
        help="[manual/research] P0/W5: generative candidate frames through the payoff pipeline",
    )
    gen_payoff.add_argument("--input", default=_data_path("generative_payoff_suite.json"))
    gen_payoff.add_argument("--output", default="results/generative_payoff_suite.json")
    gen_payoff.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    gen_payoff.add_argument("--model-id", default=None)
    gen_payoff.add_argument("--max-new-tokens", type=int, default=400)
    gen_payoff.add_argument(
        "--semantic-embedding-backend", choices=["none", "lexical", "openai"], default="none"
    )
    gen_payoff.add_argument("--embedding-model", default=None)

    dialectic = subparsers.add_parser(
        "run-dialectic-falsification",
        help="[manual/research] Layer G entry point: challenge promoted seeds against "
        "the source (FALSIFIED -> Gate contradiction; HOLDS -> bounded feedback)",
    )
    dialectic.add_argument("--input", default=_data_path("dialectic_falsification_fixture.json"))
    dialectic.add_argument("--output", default="results/dialectic_falsification.json")
    dialectic.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    dialectic.add_argument("--model-id", default=None)
    dialectic.add_argument("--max-new-tokens", type=int, default=200)

    act_probe = subparsers.add_parser(
        "run-activation-probe",
        help="[manual/research] Layer G track 2: MLP activation separation between "
        "dialectical verdict classes; the signal never changes seed state",
    )
    act_probe.add_argument("--input", default=_data_path("dialectic_falsification_fixture.json"))
    act_probe.add_argument("--output", default="results/activation_probe.json")
    act_probe.add_argument("--backend", choices=["fake", "hf"], default="fake",
        help="'fake' validates harness mechanics only; 'hf' probes a real model and requires the models extra.")
    act_probe.add_argument("--model-id", default=None)
    act_probe.add_argument("--pooling", choices=["statement", "full", "stelling"], default="statement",
        help="'statement' pools only statement tokens; 'full' pools the entire prompt. 'stelling' is a legacy alias.")
    act_probe.add_argument("--verdicts", default=None,
        help="Path to a dialectic_falsification artifact whose external verdict "
        "labels should be used instead of fixture labels.")
    act_probe.add_argument("--read-location", choices=["mlp_out", "neuron"], default="mlp_out",
        help="'mlp_out' reads the MLP block output; 'neuron' reads the input to "
        "the down projection, matching the per-neuron H-Neurons location.")
    act_probe.add_argument("--sparse-permutations", type=int, default=500,
        help="Number of label shuffles for the sparse L1 classifier permutation "
        "control. Zero runs LOOCV without a p-value; default 500.")
    act_probe.add_argument("--model-revision", default=None,
        help="Hugging Face model revision, commit SHA, or tag used to pin the "
        "probed model. Empty uses the latest snapshot.")
    act_probe.add_argument("--require-verdict-coverage", action="store_true",
        help="Require an external verdict label for every input case and fail on "
        "incomplete coverage instead of silently probing a subset.")
    act_probe.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default=None,
        help="Load precision for the probed model. The default is float32; pooled "
        "activations are always converted to float32.")

    chat = subparsers.add_parser(
        "chat",
        help="[demo] interactive SSL shadow layer (manager, Gate, TTL/TrTL, agent contract)",
    )
    chat.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    chat.add_argument("--model-id", default=None)
    chat.add_argument("--max-new-tokens", type=int, default=700)
    chat.add_argument("--embedding-backend", choices=["lexical", "openai"], default="lexical")
    chat.add_argument("--embedding-model", default=None)
    chat.add_argument("--surface-threshold", type=float, default=0.30)
    chat.add_argument(
        "--surface-top-k",
        type=int,
        default=2,
        help="Maximum number of validated seeds that may influence one turn.",
    )
    chat.add_argument(
        "--early-turn-margin",
        type=float,
        default=0.10,
        help="Extra relevance margin during the first conversation turns.",
    )
    chat.add_argument(
        "--early-turn-history",
        type=int,
        default=5,
        help="Number of initial turns that use the early-turn margin.",
    )
    chat.add_argument(
        "--resurface-margin",
        type=float,
        default=0.15,
        help="Extra relevance margin after a seed was recently used; halves each turn.",
    )
    chat.add_argument("--recurrence-mode", choices=["pairwise", "cluster"], default="cluster")
    chat.add_argument("--script", default=None,
        help="File with one question per line for a non-interactive session.")
    chat.add_argument("--transcript", default=None,
        help="Write the session transcript and audit trail to this JSON path.")
    chat.add_argument("--show-shadow", action="store_true",
        help="Show shadow-layer diagnostics after each turn.")
    chat.add_argument("--probe-corpus", default=None,
        help="Corpus (JSON chunks or plain text) probed by promoted seeds; "
        "results indicate presence, not steering or truth.")
    chat.add_argument("--probe-top-k", type=int, default=3,
        help="Number of hits per retrieval probe arm (default: 3).")

    ssl_session = subparsers.add_parser(
        "run-ssl-session",
        help="[manual/research] W9: multi-turn SSL through the real pipeline (manager, Gate, TTL/TrTL)",
    )
    ssl_session.add_argument("--input", default=_data_path("ssl_session_suite.json"))
    ssl_session.add_argument("--output", default="results/ssl_session_suite.json")
    ssl_session.add_argument("--backend", choices=MODEL_BACKENDS, default="fixture")
    ssl_session.add_argument("--model-id", default=None)
    ssl_session.add_argument("--max-new-tokens", type=int, default=400)
    ssl_session.add_argument(
        "--embedding-backend", choices=["lexical", "openai"], default="lexical"
    )
    ssl_session.add_argument("--embedding-model", default=None)
    ssl_session.add_argument(
        "--surface-threshold",
        type=float,
        default=0.30,
        help="Cosine relevance threshold for a promoted seed to surface on a later turn.",
    )
    ssl_session.add_argument(
        "--surface-top-k",
        type=int,
        default=2,
        help="Use-time cap for the most relevant promoted seeds that may influence one turn. Promotion is permission, not an obligation. Use -1 for no cap.",
    )
    ssl_session.add_argument(
        "--early-turn-margin",
        type=float,
        default=0.10,
        help="Extra relevance margin during the first --early-turn-history turns. It changes fit selection and never blocks a turn. Use 0 to disable.",
    )
    ssl_session.add_argument(
        "--early-turn-history",
        type=int,
        default=5,
        help="Number of initial zero-indexed turns that use the early-turn margin.",
    )
    ssl_session.add_argument(
        "--resurface-margin",
        type=float,
        default=0.15,
        help="Extra relevance margin after a seed was recently used. The margin halves on each later turn. Weight remains controlled only by the Gate. Use 0 to disable.",
    )
    ssl_session.add_argument(
        "--dedup-threshold",
        type=float,
        default=None,
        help="Per-run deduplication threshold. Lower values merge more paraphrastic gaps so recurrence can accumulate. The doctrine default remains 0.85.",
    )
    ssl_session.add_argument(
        "--min-occurrences",
        type=int,
        default=None,
        help="Per-run recurrence threshold for the Gate.",
    )
    ssl_session.add_argument(
        "--promotion-threshold",
        type=float,
        default=None,
        help="Per-run weight threshold for promotion. A conversation fixture may override it.",
    )
    ssl_session.add_argument(
        "--recurrence-mode",
        choices=["pairwise", "cluster"],
        default="pairwise",
        help="cluster mode counts paraphrastic gaps together for recurrence without weakening strict storage deduplication.",
    )
    ssl_session.add_argument("--cluster-threshold", type=float, default=None,
        help="Cosine threshold for recurrence clustering; used only in cluster mode.")
    ssl_session.add_argument("--auto-calibrate", action="store_true",
        help="Automatically calibrate the recurrence threshold from conversation length.")

    analyze = subparsers.add_parser(
        "analyze-results",
        help="[reporting] create a report and charts from result files",
    )
    analyze.add_argument("--results-dir", default="results")
    analyze.add_argument("--output-dir", default="results/analysis")

    nlp = subparsers.add_parser(
        "run-absencebench-smoke",
        aliases=["run-nlp-smoke"],
        help="[standard] technical smoke test for the local AbsenceBench command",
    )
    nlp.set_defaults(command="run-absencebench-smoke")
    nlp.add_argument("--input", default=_data_path("local_absencebench_sample.json"))
    nlp.add_argument("--output", default="absencebench_smoke.json")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = execute_command(args)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
