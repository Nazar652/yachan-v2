import argparse
import asyncio

from src.cli.scope import run_in_scope
from src.services.search_service import SearchService

COMMAND = "embed-posts"
HELP = "backfill semantic-search embeddings for existing posts"


def configure(parser: argparse.ArgumentParser) -> None:
    pass


def handle(args: argparse.Namespace) -> None:
    count = asyncio.run(run_in_scope(lambda: SearchService().index_all()))  # type: ignore
    print(f"indexed {count} posts")
