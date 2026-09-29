# Hugging Face Space test deployment

This branch is a **hosted functional-test profile**, not the supported `production-local` deployment claim.

It keeps the shipped Shadowseed Workbench, semantic embedding path, Validation Gate, evidence submission and point-of-use logic unchanged. The only deployment difference is that Gradio listens on `0.0.0.0:7860`, which is required inside a Hugging Face Docker Space.

## Safety boundary

Use a **Private** Hugging Face Space. The Workbench is a single-user product and this branch does not add hosted multi-user authentication or tenant isolation.

The default workspace is ephemeral:

```text
/tmp/shadowseed-workspace
```

If the Space has persistent storage attached, set:

```text
SHADOWSEED_WORKSPACE=/data/shadowseed
```

## Deploy

1. Create a new Hugging Face Space.
2. Select **Docker** as the SDK.
3. Keep the Space **Private**.
4. Push this branch's contents to the Space repository.
5. Wait for the Space build to reach **Running**.

## Functional test

1. Open **Chat**.
2. Change **Model provider** to **Hugging Face Transformers - local model**.
3. Enter a small causal language-model ID that fits the Space hardware.
4. Keep **Semantic embedding** on **sentence-transformers**.
5. Leave **Allow lexical toy embeddings** off.
6. Keep live SSL mode.
7. Create the chat and send enough turns for a shadow seed to appear.
8. Open **Shadow**, select the seed and inspect its audit timeline.
9. Open **Submit independently verified support**.
10. Add a stable source reference, verification note and the independent verification checkbox.
11. Submit the support and inspect the Gate result.
12. Ask a later relevant question and inspect whether point-of-use authorization permits the promoted seed to surface.

Successful path:

```text
real model -> semantic embedding -> candidate -> shadow seed
-> verified evidence -> Validation Gate -> point-of-use -> possible influence
```

This does not replace the standalone release checks or the 24-hour exact-main soak for v0.7.2.
