import argparse
import logging

from . import commands
from .exchange_listener import ExchangeListener

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


parser = argparse.ArgumentParser(prog="antalla")
parser.add_argument("--debug", help="Enables debug mode",
                    default=False, action="store_true")
subparsers = parser.add_subparsers(dest="command")
init_db_parser = subparsers.add_parser("init-db")

run_parser = subparsers.add_parser("run")
run_parser.add_argument("--exchange", nargs="*", choices=ExchangeListener.registered())

markets = subparsers.add_parser("markets")
markets.add_argument("--exchange", nargs="*", choices=ExchangeListener.registered())


def run():
    args = vars(parser.parse_args())

    log_level = logging.DEBUG if args["debug"] else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    if not args["command"]:
        parser.error("no command provided")
    command = args["command"].replace("-", "_")
    func = getattr(commands, command)
    func(args)


    