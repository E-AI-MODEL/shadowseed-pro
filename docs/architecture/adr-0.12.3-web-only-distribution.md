# ADR candidate: Shadowseed 0.12.3 web-first distribution

Status: **candidate under verification**. This document records alternatives; it is not release approval.
Related: #199 (0.12.3), #200 (Pillow dependency finding).

## Question

How do we ship an audited, local, self-contained product without changing the
canonical Python SSL engine, weakening the Gate, or waiting for the legacy Gradio stack?

## Divergent comparison

| Option | What it changes | Evidence / drawback | Decision |
| --- | --- | --- | --- |
| Upgrade Gradio + Pillow 13 | Legacy UI and image stack | Gradio requirements currently declare Pillow <13; Pillow 13 requires Python >=3.11 | Revisit when upstream removes its cap |
| Force Pillow 13 under Gradio | Dependency resolver and runtime contract | Breaks declared compatibility and may fail at runtime; no meaningful assurance | Reject |
| Ignore Pillow advisories | Security checking only | Vulnerable distribution remains; hides the problem | Reject |
| Backport / maintain a local Pillow fork | Native image parser and all packaged builds | Expensive review and platform build burden, beyond product purpose | Reject |
| Replace browser client with a new framework | UI and delivery layer | Duplicates an already working static-export client and loopback API | Reject |
| Container-only distribution | Installation method | Useful optional channel, but unsuitable as a simple desktop download | Supplement |
| **Separate packaged browser product** | Bundling and CI closure only | Existing \`shadowseed-web\` uses a loopback stdlib server, existing Next static export and canonical Python services | **Prototype this** |

The active legacy \`workbench\` extra remains available as an **explicitly
unsupported-for-secure-release** research surface until Gradio resolves Pillow 13.
The accepted shipping dependency inventory MUST exclude Gradio and Pillow; omitting
them in prose or excluding merely their import paths is insufficient.

## Convergent implementation

1. Keep \`shadowseed-web\` as the entry point. Avoid changing SSL, persistence,
   authority, evidence, contradiction and point-of-use behavior.
2. Assemble a PyInstaller web-only bundle from that entry point. Collect hashed
   static assets, preserve the existing macOS sealing/roundtrip process, and
   prove a real fixture turn via a frozen self-test.
3. Before any publication, audit the **exported exact shipped** dependency closure
   with strict \`pip-audit\`, a lock check and an SBOM. Assert Gradio, Pillow,
   heavy model providers and other excluded optional stacks are absent.
4. Run cross-platform clean install/build, checksums, artifact provenance, and
   user-start tests. Later change the *canonical release* workflow to use these
   results instead of the old combined Gradio/Next archive. Do not claim an
   old Gradio bundle is safe on the strength of a web-only audit.
5. Do the local live Ollama use cycle separately. No production-local claim is
   justified by a fixture or deterministic test.

## Boundaries and open checks

* Python 3.10 remains supported by the **engine**. The standalone build may use
  Python 3.12; support of an individual frozen binary is based on its platform.
* Source \`uv.lock\` still represents **all** optional extras, including the
  vulnerable legacy UI. A strict shipped-closure audit must work from \`uv export\`
  without \`--extra workbench\`. Do not silently relabel a full-lock audit as safe.
* Gradio-dependent CI and tests remain a separate legacy-health signal; any
  required check and release assurance change needs an explicit, reviewed edit.
* Keep license/provenance files as integrity material. Ownership of the
  repository does not change external package version requirements.
* If the exploratory workflow or frozen smoke fails, keep PR draft and do
  not merge into #199.

Sources checked 2026-10-21:
- https://github.com/gradio-app/gradio/blob/main/requirements.txt
- https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html
- https://pillow.readthedocs.io/en/stable/installation/python-support.html
