# Shadowseed Workbench 0.12.2

Shadowseed Workbench 0.12.2 is a security fix for the packaged local web client.
It remains a Research Preview and is the next production-local assurance candidate.

## Loopback web API host validation

The `shadowseed-web` server binds only to loopback, but 0.12.0 and 0.12.1 did not
validate the `Host` header and accepted `Origin == http://<Host>` as same-origin.
With DNS rebinding, a web page could re-resolve its own hostname to 127.0.0.1 and
call the local API as same-origin: read sessions and messages, create sessions and
submit operator-verified evidence as the local operator. The Gate itself was not
bypassed, but external web content could act as the trusted local operator.

Every request (API, static files, OPTIONS and HEAD) must now present a trusted
loopback `Host` on the server's actual bound port: `127.0.0.1:<port>`,
`localhost:<port>`, or the server's own loopback bind address (for example
`127.0.0.2:<port>`). The bound port is read from the running server, so the
launcher's fallback port keeps working. The existing Origin allowlist remains a
second layer. Regression tests cover rebound reads,
session creation and evidence submission.

## Release status

Published `v0.12.1` remains available as a Research Preview but is not eligible for
production-local promotion. Gate, evidence, authority and point-of-use rules are
unchanged.

Known limitation: same-turn revision only runs when a seed is promoted by recurrence
in the same turn. Under the default `evidence_backed` Gate that does not happen, so
a configured revision model role is inactive in ordinary web sessions.

0.12.1 added a gap-resilience benchmark harness and case set; no live-model
gap-resilience result is committed yet.

## Release and use

Publication requires the normal exact-SHA Release Workbench checks and verified
Windows, macOS and Linux assets. Production-ready/local promotion additionally
requires the manual Production Release Assurance run against `v0.12.2` while
`main` equals the release SHA, the 24-hour unchanged-candidate use period with a
normal Workbench use cycle and `shadowseed doctor`, and no unresolved P0/P1
findings.
