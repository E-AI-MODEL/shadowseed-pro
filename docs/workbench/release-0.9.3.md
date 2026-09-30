# Shadowseed Workbench 0.9.3

Shadowseed Workbench 0.9.3 is a macOS startup and packaging patch release on top of 0.9.2.

## Why this patch exists

The 0.9.2 release proved that the frozen executable could complete the packaged product self-test, but that did not prove the exact end-user launch path. The macOS first-launch helper removed quarantine and called `open Shadowseed.app`, then exited immediately. A user could therefore see Terminal report a completed process while the windowless app failed to become a usable local Workbench.

The 0.9.2 release also published only the Apple Silicon (`darwin-arm64`) macOS archive.

## macOS startup fix

0.9.3 changes the macOS launch contract:

- `Open Shadowseed.command` runs the bundled executable directly instead of handing it off to LaunchServices and immediately exiting;
- the Terminal session stays attached while Shadowseed is running;
- startup failures remain visible and point to the sanitized log in `~/.shadowseed/logs`;
- the helper detects an Intel Mac attempting to run the Apple Silicon archive and explains which archive is required;
- the bundled README tells users to keep the Terminal window open while the local Workbench is active.

The application remains loopback-only by default.

## Apple Silicon and Intel

The standalone workflow now builds two independently tested macOS archives:

- `darwin-arm64` for Apple Silicon;
- `darwin-x86_64` for Intel Macs.

The Intel lane uses the last compatible PyTorch 2.2 line while the other supported platforms keep the normal `torch>=2.2` dependency range.

## Stronger release test

The frozen self-test remains, but 0.9.3 adds a separate real startup probe. The release build must now:

1. start the actual frozen executable without self-test mode;
2. bind the Workbench to an ephemeral `127.0.0.1` port;
3. receive a real HTTP response from the local UI;
4. terminate the probe cleanly;
5. on macOS, repeat that server-startup proof from the exact round-tripped archive.

The release workflow requires this evidence for all standalone bundles and requires both macOS architectures before publication.

## Unchanged runtime behavior

0.9.3 does not change the Shadow Seed Learning runtime or the independent vanilla A/B design introduced in 0.9.2. It is a packaging, startup and platform-coverage patch.
