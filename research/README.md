# Shadowseed Research

This directory contains benchmark and evaluation tooling. It is not part of the
normal Shadowseed product distribution.

For repository research work, install the product package first and then the
research package:

    pip install -e .
    pip install --no-deps -e ./research

The canonical research import namespace is shadowseed_benchmark. Historical
shadowseed.benchmark.* imports remain available only as a compatibility path
when this research package is present.
