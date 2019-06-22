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
markets.add_argument("--exchange", "-e", nargs="*", choices=ExchangeListener.registered())

fetch_prices = subparsers.add_parser("fetch-prices", help="fetches the latest USD price for each coin in antalla db")

norm_volume = subparsers.add_parser("norm-volume", help="normalises the traded 24h volume for each market in USD")
norm_volume.add_argument("--exchange", "-e", nargs="*", choices=ExchangeListener.registered())

def run():
    args = vars(parser.parse_args())

    log_level = logging.DEBUG if args["debug"] else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    if not args["command"]:
        parser.error("no command provided")
    command = args["command"].replace("-", "_")
    func = getattr(commands, command)
    func(args)


    