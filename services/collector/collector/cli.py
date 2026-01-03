from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

from .auth import PowerBITokenProvider
from .client import PowerBIClient
from .config import ConfigError, load_config
from .logging_utils import setup_logging
from .normalize import normalize_refresh_history


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Debug CLI for Power BI refresh history collection",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--list-workspaces",
        action="store_true",
        help="List workspaces the service principal can access.",
    )
    action.add_argument(
        "--list-datasets",
        action="store_true",
        help="List datasets in the given workspace.",
    )
    action.add_argument(
        "--refresh-history",
        action="store_true",
        help="Fetch refresh history for a dataset (default).",
    )

    parser.add_argument("--workspace-id")
    parser.add_argument("--dataset-id")
    parser.add_argument("--workspace-name")
    parser.add_argument("--dataset-name")
    parser.add_argument("--top", type=int)
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--schema-path",
        help="Path to RefreshEventV1 JSON schema.",
    )
    parser.add_argument(
        "--no-validate-schema",
        action="store_true",
        help="Skip JSON schema validation.",
    )
    return parser.parse_args()


def _default_schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / "refresh_event_v1.schema.json"


def _load_schema(path: str | None) -> dict:
    schema_path = Path(path) if path else _default_schema_path()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_payload(payload: object, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema)
    errors: list[str] = []

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            for err in validator.iter_errors(item):
                errors.append(f"[{index}] {err.message}")
    else:
        for err in validator.iter_errors(payload):
            errors.append(err.message)

    return errors


def main() -> int:
    args = _parse_args()

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    setup_logging(config.log_level)

    token_provider = PowerBITokenProvider(config)
    with PowerBIClient(config, token_provider) as client:
        if args.list_workspaces:
            payload = client.list_workspaces()
        elif args.list_datasets:
            if not args.workspace_id:
                print("--workspace-id is required for --list-datasets", file=sys.stderr)
                return 2
            payload = client.list_datasets(args.workspace_id)
        else:
            if not args.workspace_id or not args.dataset_id:
                print(
                    "--workspace-id and --dataset-id are required for refresh history",
                    file=sys.stderr,
                )
                return 2
            refreshes = client.get_refresh_history(
                workspace_id=args.workspace_id,
                dataset_id=args.dataset_id,
                top=args.top,
            )
            if args.raw:
                payload = refreshes
            else:
                payload = normalize_refresh_history(
                    refreshes,
                    workspace_id=args.workspace_id,
                    dataset_id=args.dataset_id,
                    workspace_name=args.workspace_name,
                    dataset_name=args.dataset_name,
                )

    if not args.raw and not args.no_validate_schema:
        schema = _load_schema(args.schema_path)
        errors = _validate_payload(payload, schema)
        if errors:
            print("Schema validation errors:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 3

    if args.pretty:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
