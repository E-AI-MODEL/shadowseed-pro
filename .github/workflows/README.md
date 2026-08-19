# Active Workflows

The repository has seven active workflows:

- `ci.yml`: lint, tests, branch coverage, checkout cleanliness, package build, and wheel smoke tests.
- `workbench-ci.yml`: focused Workbench tests, clean wheel-extra installation, CLI checks, and headless UI smoke tests.
- `workbench-portability.yml`: clean-install portability checks on Linux, macOS, and Windows plus the Workbench container build.
- `standalone-workbench.yml`: the product quality gate and frozen standalone builds for Linux, macOS, and Windows. Pull requests remain path-filtered so unrelated review work does not build three frozen products. Every push to `main` runs the workflow, because release publication is bound to the exact current `main` SHA and a later non-product commit must not leave the repository without a fresh eligible release candidate. Each bundle must pass its packaged self-test before upload.
- `release-workbench.yml`: fail-closed prerelease publication after a successful `Standalone Workbench` run on `main`; it verifies exact source SHA during preflight and again immediately before publication, plus manifests, provenance, checksums, wheel/sdist installation, and the published assets.
- `open-set-hf-review.yml`: manually triggered Hugging Face open-set research runs.
- `slm-model-benefit.yml`: manually triggered small-language-model benefit runs.

Original retired workflows remain under `archive/source-workflows/` for provenance only.
