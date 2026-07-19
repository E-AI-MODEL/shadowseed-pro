# AbsenceBench run card

- Benchmark: `AbsenceBench`
- Run type: `benchmark_preparation`
- Execution status: `execution_gap`
- Host status: `present`
- Runner status: `structure_present`
- Execution gap: `true`

Suggested upstream command template:

```bash
python evaluate.py --model_family <provider> --model <model> --in_dir tests --out_dir results
```

Before a live result is accepted, record the exact upstream revision, environment, model, provider, input data, output file, and mapping into the Shadowseed result schema.
