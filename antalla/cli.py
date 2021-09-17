import argparse
import logging

from . import commands
from .exchange_listener import ExchangeListener
from . import settings

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


parser = argparse.ArgumentParser(prog="antalla")
parser.add_argument(
    "--debug", help="Enables debug mode", default=False, action="store_true"
)
subparsers = parser.add_subparsers(dest="command")
migrations_parser = subparsers.add_parser("migrations")

run_parser = subparsers.add_parser("run", help="Runs antalla to fetch data")
run_parser.add_argument("--exchange", nargs="*", choices=ExchangeListener.registered())
run_parser.add_argument(
    "--event-type",
    choices=["trade", "depth"],
    help="which event type to listen to; defaults to all events",
)
run_parser.add_argument(
    "--markets-files",
    help="files to use to select the markets for each exchange",
    nargs="*",
)

markets = subparsers.add_parser("markets")
markets.add_argument(
    "--exchange", "-e", nargs="*", choices=ExchangeListener.registered()
)

fetch_prices = subparsers.add_parser(
    "fetch-prices", help="fetches the latest USD price for each coin in antalla db"
)

norm_volume = subparsers.add_parser(
    "norm-volume", help="normalises the traded 24h volume for each market in USD"
)
norm_volume.add_argument(
    "--exchange", "-e", nargs="*", choices=ExchangeListener.registered()
)

init_data = subparsers.add_parser(
    "init-data", help="fetches exchange markets, traded volume and prices in USD"
)
init_data.add_argument(
    "--exchange", "-e", nargs="*", choices=ExchangeListener.registered()
)
init_data.add_argument(
    "--fetch-prices",
    default=False,
    action="store_true",
    help="Fetch prices for all curencies",
)

snapshots_parser = subparsers.add_parser("snapshot")
snapshots_parser.add_argument(
    "--exchange", nargs="*", choices=ExchangeListener.registered()
)
snapshots_parser.add_argument(
    "--depth",
    type=float,
    help="sets order book depth for orders to be included in snapshot, expressed in percentage relative to the mid price",
)
snapshots_parser.add_argument(
    "--quartile",
    action="store_true",
    help="includes orders ranging from upper quartile bids to lower quartile asks",
)

plot_order_book_parser = subparsers.add_parser(
    "plot-order-book", help="plot the order book"
)
plot_order_book_parser.add_argument("--exchange", choices=ExchangeListener.registered())
plot_order_book_parser.add_argument("--market", choices=settings.MARKETS)

ws_server_parser = subparsers.add_parser(
    "ws-server", help="start antalla websocket server"
)
ws_server_parser.add_argument(
    "--port", type=int, default=8765, help="port to run the server on"
)
ws_server_parser.add_argument("--host", default="0.0.0.0", help="host for the server")


def run():
    args, unkown_args = parser.parse_known_args()
    args = vars(args)

    log_level = logging.DEBUG if args["debug"] else logging.INFO
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    if not args["command"]:
        parser.error("no command provided")
    command = args["command"].replace("-", "_")
    if command != "migrations" and unkown_args:
        parser.error("unknown arguments: {0}".format(unkown_args))
    func = getattr(commands, command)
    func(args)
