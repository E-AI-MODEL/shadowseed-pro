# Shadowseed Workbench 0.10.1

Shadowseed Workbench 0.10.1 restores full researcher control to the local Workbench while keeping the ordinary chat surface compact. It also introduces an explicit opt-in update check for future standalone releases.

## Full control without clutter

The main Workbench now keeps the conversation in the center and uses two collapsible sidebars:

- Regie on the left for presets, model/provider selection and detailed runtime configuration;
- Audit on the right for the live backend state, active configuration and latest turn data.

The ordinary starting presets are Observeren, Gebalanceerd and Onderzoekend. Presets are only starting configurations. Once an individual value is changed, the actual persisted configuration is authoritative and the UI treats the session as customized.

## Microcontrol and God mode

Researchers can directly adjust key runtime controls including surfacing, authority profile, Gate policy, recurrence and self-reinforcement.

God mode exposes the complete configurable session/core settings as JSON. It writes only to local runtime configuration. It never edits repository files, commits to Git, or rewrites source code.

Embedding backend/model changes are blocked after seeds exist unless the explicit force control is enabled, because persisted vectors may otherwise no longer match the embedding space.

## Live audit

The right audit sidebar exposes the actual active configuration and recent runtime state, including turn count, stored and currently authorized seeds, surfaced seeds, influence decisions, authority profile, Gate policy, recurrence mode, surfacing top-k, full configuration and the latest turn report.

Inspection now exposes persisted, session and core configuration snapshots so the UI can show what the runtime is actually using.

## Opt-in updates

The Workbench now includes Menu -> Updates.

- Manual Controleer nu is always available.
- Automatisch controleren bij starten is off by default and must be enabled explicitly.
- The updater reads only official GitHub Releases from E-AI-MODEL/shadowseed-pro.
- Only the standalone artifact for the current operating system and machine architecture is accepted.
- The published manifest and SHA256SUMS are checked before a downloaded bundle is accepted.
- Download happens only after the user clicks the download action.
- The updater does not write to Git, modify source files or silently install a replacement application.

Existing 0.10.0 standalone users need to install 0.10.1 manually once. From 0.10.1 onward, the Workbench can check for and download verified future builds.

## Compatibility and authority

0.10.1 does not introduce a second authority path. Presets and advanced controls write to the same persisted SessionConfig/SSLCoreConfig consumed by the canonical runtime. Gate and authority semantics continue to be interpreted by the existing Validation Gate.

Existing workspaces remain separate from the application bundle under the normal local workspace path and are not replaced by application updates.

## Claim boundary

0.10.1 remains a Research Preview. The additional controls increase inspectability and experimental freedom; they do not establish that a more permissive configuration is more correct, safer or better performing.
