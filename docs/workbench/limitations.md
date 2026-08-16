# Workbench 0.4 limitations

Shadowseed Workbench 0.4.0 is a tester preview for local, single-user use. It is
not a production service, an authorization boundary for multiple users, or a
scientific evidence generator by itself.

## Security and deployment

- The supported native server binds to loopback by default.
- There is no built-in login, account separation, TLS termination, CSRF policy
  for hostile networks, or tenant isolation.
- `--allow-remote` is an explicit advanced option for trusted environments that
  provide their own network controls.
- The Docker image listens on `0.0.0.0` inside the container so it can be
  reached through a port mapping. The documented mapping publishes the port on
  host loopback only.

## Data handling

- Session prompts, answers, seeds and audit data are stored locally in the
  tester workspace.
- Full reports are content-bearing exports and must be treated accordingly.
- Support bundles are intentionally content-minimized but may still reveal
  backend/model choice, platform metadata and structural session counts.
- Redaction is defense in depth, not permission to paste credentials into a
  conversation. Testers should avoid unnecessary secrets and personal data.

## Runtime authority

- The Workbench has no direct weight, status, promotion or contradiction-state
  editor.
- Tester feedback is `record_only` by default.
- Live sessions provide a separate verified-support action. It submits an
  operator-attested, provenance-bearing signal to the existing Validation Gate;
  it cannot directly choose a Gate decision or final weight.
- The operator or host application is the trust anchor for that attestation.
  The Workbench validates required fields and deduplication identity, not source
  truth.
- Seed authority remains governed by the existing Validation Gate and
  point-of-use checks.
- A promoted seed is only eligible for consideration; promotion does not force
  influence.

## Evaluation limits

- Side-by-side and blind comparison presents baseline and Shadowseed-visible
  answers from evaluation sessions for human review; live sessions intentionally
  have no isolated baseline. The Workbench does not infer statistical
  significance or scientific validity.
- Fixture runs are deterministic product smokes, not model-effect evidence.
- Workbench tests and exports must not be represented as new benchmark evidence.
- `benchmarks/results/**` remains a separately governed evidence area.

## Compatibility

- Python 3.10 and 3.12 are covered by the repository CI for this preview.
- Windows, macOS and Linux get clean-install Workbench portability smokes.
- The browser UI uses the Gradio 6 API family through the `[workbench]` extra.
- Workspace schema migration support remains deliberately conservative; always
  create a backup before using a newer prerelease against valuable tester data.
