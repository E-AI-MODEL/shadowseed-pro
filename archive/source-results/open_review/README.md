# Open-set HF review batch

Deze artifactset komt uit een handmatige workflow met Hugging Face intake.

Run-parameters:

- source_id: `ag_news_test`
- limit: `12`
- offset: `30`
- detector: `model`
- model_backend: `hf-transformers`
- model_id: `microsoft/Phi-3.5-mini-instruct`

Inhoud:

- `open_set_seed_output.json`: de seed-output per item
- `open_set_review_packets.json`: review-packets voor menselijke beoordeling
- `open_set_seed_review_summary.json`: geaggregeerde summary (pending tot review klaar)
- `open_set_disagreements.json`: seeds met gemengde reviewverdicts
- `open_set_review_report.md`: leesbaar Markdown-rapport

Interpretatie:

- dit is een aparte evidencelaag (evidence_layer: open_set_seed_quality)
- dit is geen standaard regressierun
- status is `review_in_progress` totdat menselijke reviewers packets hebben ingevuld
- lees deze laag niet als vervanging van de fixture-regressies
- herhaal voor een nieuwe open-set ronde niet automatisch dezelfde `offset`; anders test je dezelfde HF-items opnieuw
- alleen `detector=model` met een echte taalmodel-backend (`hf-transformers` of `ollama`) voldoet aan de 4.6 een-zinsclaim;
  adapter_v1, adapter_v2 en de fixture model-backend zijn baseline-infrastructuur, geen Laag-C bewijs
