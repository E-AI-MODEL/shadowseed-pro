# Active Workflows

The repository has six active workflows:

- `ci.yml`: lint, tests, coverage, checkout-cleanliness, package build, and wheel smoke tests.
- `workbench-ci.yml`: focused Workbench tests for relevant pull requests and pushes.
- `workbench-portability.yml`: Workbench portability checks and a deployable artifact.
- `release-workbench.yml`: release publication after a successful portability run.
- `open-set-hf-review.yml`: manually triggered Hugging Face open-set research runs.
- `slm-model-benefit.yml`: manually triggered small-language-model benefit runs.

Original retired workflows remain under `archive/source-workflows/` for reference.
