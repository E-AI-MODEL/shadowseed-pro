# AbsenceBench-runkaart

Dit document is de standaard runkaart voor de eerste AbsenceBench-lane in deze repo.

## Benchmarkdoel

Toetsen of een SSL 4.5-conditie betere absence detection oplevert dan een baselineconditie zonder expliciete SSL-sturing.

## Bron en host

- dataset-host: `harveyfin/AbsenceBench` op Hugging Face
- paper-host: `2506.11440` op Hugging Face Papers
- code-host: `harvey-fin/absence-bench` op GitHub
- publieke benchmarksite: `absencebench.github.io`

## Fase-3 executionstatus

Op 2 mei 2026 geldt:

- host_status: `aanwezig`
- runner_status: `runnerstructuur aanwezig`
- executionstatus: `benchmarkvoorbereiding`
- execution-gap aanwezig: `ja`

## Waarom nog geen echte benchmarkrun

Hoewel de publieke bronlagen zichtbaar zijn en de upstream repo een evaluatie-entrypoint toont, ontbreken in deze repo nog harde live-bevestigingen voor:

- end-to-end benchmarkuitvoering vanuit een gecontroleerde `shadowseed`-route
- definitieve provider- en modelkeuze
- stabiele outputmapping naar het lokale resultschema

## Startcommand-template

```bash
python evaluate.py --model_family <provider> --model <model> --in_dir tests --out_dir results
```

Dit template is afgeleid van de huidige upstream README, maar telt in `shadowseed` nog niet als bewijs van een afgeronde live run.

## Outdated-blokkade

Als de upstream repo later outdated blijkt, valt de route automatisch terug naar:

- `runner_status = outdated`
- `executionstatus = execution-gap aanwezig`
- geen `echte benchmarkrun`
