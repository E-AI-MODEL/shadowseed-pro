# Shadowseed Workbench 0.12.1

Shadowseed Workbench 0.12.1 packages the detector and local model-role improvements
merged after 0.12.0. It remains a Research Preview.

## Gap detection

- Detector-born candidates use the unspecified type and begin with zero weight.
- Atomicity is based on one bounded gap rather than a hard 18-word limit.
- Bounded prior clean conversation context helps resolve references; it does not
  count as evidence. SSL-influenced live answers are excluded from that context.
- The parser accepts useful two-word labels such as “Authentication mechanism”
  while retaining filters for bare proper names, copied text and few-shot leaks.
- Detector prompt contracts are version 0.6 and the behavior projection is v2.

## Local model roles

Generation, detection and same-turn revision have explicit model roles. Detection
can use its own model and token budget. Unconfigured detection roles retain the
primary generation configuration.

For new web sessions using a primary DeepSeek R1 or Llama 3.1 model, the local
balanced profile assigns detection and revision to an already installed Gemma2
model when one is discoverable. Generation stays on the selected primary model.
Detection receives a 220-token budget. The session header displays active roles.
No models are downloaded automatically; without Gemma2 the single-model behavior
is preserved. Existing sessions retain their saved configuration.

## Research findings

The research package adds gap-resilience measurements and records R1 revision-role
and paired Dutch/English results. Those small screens do not establish general
answer-quality improvement or laptop latency. English is not a reliability
guarantee, and UI language is independent of model-role routing.

## Release and use

The packaged web client and existing Gradio Workbench remain available. The thin
standalone uses local Ollama; hosted OpenAI still requires its explicit provider
extra. Gate, evidence, authority and point-of-use rules are unchanged.

Publication requires the normal exact-SHA Release Workbench checks and verified
Windows, macOS and Linux assets. This release does not by itself complete the
separate production-ready/local assurance and 24-hour candidate use period.
