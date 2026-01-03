# Collector Service

## Setup (local)

1. Create a virtual environment and install dependencies:

   ```sh
   cd services/collector
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment variables:

   ```sh
   cp ../../.env.example ../../.env
   ```

   Fill in the Azure and Power BI values in `.env`.

## Debug CLI

Fetch refresh history for a single dataset and output normalized events.

```sh
cd services/collector
set -a
. ../../.env
set +a
python -m collector.cli --workspace-id <workspace-id> --dataset-id <dataset-id> --pretty
```

Add `--raw` to see the Power BI API response without normalization.
Schema validation runs by default for normalized output; use `--no-validate-schema` to skip.
Use `--schema-path` if your schema lives outside the repo root.

List available workspaces:

```sh
python -m collector.cli --list-workspaces --pretty
```

List datasets in a workspace:

```sh
python -m collector.cli --list-datasets --workspace-id <workspace-id> --pretty
```

## Tests

```sh
cd services/collector
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```
