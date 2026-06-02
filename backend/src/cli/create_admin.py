import argparse
import asyncio
import getpass

from src.cli.scope import run_in_scope
from src.models.mod_account import ModRole
from src.services.mod_service import ModService

COMMAND = "create-admin"
HELP = "create an admin moderator account"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("username")


def handle(args: argparse.Namespace) -> None:
    password = _prompt_password()
    account = asyncio.run(
        run_in_scope(lambda: ModService().create_account(args.username, password, ModRole.ADMIN))  # type: ignore
    )
    print(f"created admin '{account.username}' (id={account.id})")


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    if not password:
        raise SystemExit("password must not be empty")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("passwords do not match")
    return password
