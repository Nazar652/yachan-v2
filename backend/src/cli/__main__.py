import argparse

from src.bootstrap.container import setup_di
from src.cli import create_admin, dump_openapi, embed_posts

COMMANDS = [create_admin, dump_openapi, embed_posts]


def main() -> None:
    parser = argparse.ArgumentParser(prog="yachan", description="yachan-v2 admin cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    handlers = {}
    for module in COMMANDS:
        command_parser = subcommands.add_parser(module.COMMAND, help=module.HELP)
        module.configure(command_parser)
        handlers[module.COMMAND] = module.handle

    args = parser.parse_args()

    setup_di()
    handlers[args.command](args)


if __name__ == "__main__":
    main()
