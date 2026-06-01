import argparse
import json
from pathlib import Path

COMMAND = "dump-openapi"
HELP = "write the openapi schema as pretty json (to a file or stdout)"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-o", "--output", default=None, help="output path; stdout if omitted")


def handle(args: argparse.Namespace) -> None:
    from src import create_app

    schema = create_app().openapi()
    text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    if args.output is None:
        print(text)
        return

    Path(args.output).write_text(text, encoding="utf-8")
    print(f"wrote openapi schema to {args.output}")
