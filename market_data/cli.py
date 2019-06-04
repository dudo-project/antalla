import argparse
from . import commands

parser = argparse.ArgumentParser(prog="antalla")
subparsers = parser.add_subparsers(dest="command")
init_db_parser = subparsers.add_parser("init-db")

def run():
    args = parser.parse_args()
    if not args.command:
        parser.error("no command provided")
    command = args.command.replace("-", "_")
    func = getattr(commands, command)
    func(args)
