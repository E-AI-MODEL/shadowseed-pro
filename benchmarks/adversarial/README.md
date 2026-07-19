# Adversarial gate benchmarks

These cases test whether invalid, contradictory, stale, or unsupported seeds can influence output. The suite should stress the actual validation gate rather than only detector quality.

A failure is severe when a weightless or rejected seed changes retrieval, answer text, warnings, or downstream action without a logged gate decision.
