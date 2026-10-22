---
title: Shadowseed • Layer G 14B
emoji: 🔬
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 5.49.1
python_version: 3.12
app_file: app.py
license: other
license_name: PolyForm Noncommercial License 1.0.0
license_link: https://github.com/E-AI-MODEL/shadowseed-pro/blob/main/research/LICENSE
models:
  - Qwen/Qwen2.5-14B-Instruct
suggested_hardware: zero-a10g
startup_duration_timeout: 1h
---

# Shadowseed Layer G: experimenteel instrument

Dit is een Gradio Space voor **ZeroGPU**, bedoeld voor gratis gebruik.
De enige invoer is een fictief laboratoriumvoorbeeld. Het model wordt
binnen ZeroGPU met NF4 4-bit geladen; activaties worden vastgelegd tijdens
de oorspronkelijke generatie. Geen OpenAI-aanroepen, gebruikersprompts
of beoordelingslabels in de modelinvoer.

De bestanden in deze Space worden opgebouwd uit de canonieke onderzoekscode
in de Shadowseed GitHub-repository. De meetresultaten bewijzen niet dat
Shadowseed niet-uitgesproken of onbekende kennisrelaties identificeert.

Bronnen: https://github.com/E-AI-MODEL/shadowseed-pro/issues/203
