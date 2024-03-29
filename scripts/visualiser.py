import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.integrate import cumtrapz
from scipy.stats import norm

from matplotlib.dates import DateFormatter
from matplotlib.ticker import PercentFormatter
from matplotlib.ticker import ScalarFormatter
import matplotlib.ticker as ticker
from collections import defaultdict
from scipy.stats.stats import pearsonr

from datetime import datetime
from antalla.db import session
from antalla import models

sns.set_style("darkgrid")


class Visualiser:
    def _get_all_trades(self, exchange, buy_sym_id, sell_sym_id):
        return session.execute(
            f"""
            select timestamp, buy_sym_id, sell_sym_id, price, size
            from {models.Trade.__tablename__} trades
            join {models.Exchange.__tablename__} ex on trades.exchange_id=ex.id
            where buy_sym_id= :buy_sym_id and sell_sym_id= :sell_sym_id and ex.name = :exchange 
            """,
            {
                "exchange": exchange.lower(),
                "buy_sym_id": buy_sym_id.upper(),
                "sell_sym_id": sell_sym_id.upper(),
            },
        )

    def plot_single_trade_size_cdf(self, exchange, buy_sym_id, sell_sym_id):
        # plot trade size cdf for one pair of given exchange
        result = self._get_all_trades(exchange, buy_sym_id, sell_sym_id)
        trades = []
        for row in list(result):
            trades.append(
                dict(
                    timestamp=row["timestamp"],
                    buy_sym_id=row["buy_sym_id"],
                    sell_sym_id=row["sell_sym_id"],
                    size=row["size"],
                    price=["price"],
                )
            )
        trade_sizes = list(map(lambda x: x["size"], trades))

        x = np.sort(trade_sizes)
        y = np.arange(len(x)) / float(len(x))

        f, ax = plt.subplots(figsize=(8, 8))
        plt.title(
            "Trade Size Empirical CDF: "
            + exchange
            + " ("
            + buy_sym_id
            + "-"
            + sell_sym_id
            + ")"
        )
        # ax = sns.kdeplot(trade_sizes, cumulative=True)
        ax.plot(x, y)
        ax.set_xlabel("Trade size (" + buy_sym_id + ")")
        ax.set_ylabel("Percentage of trades")
        ax.set_xscale("log")
        plt.show()

    def _get_all_associated_markets(self, exchange, symbol):
        return session.execute(
            f"""
            select original_name, quoted_volume_id buy_sym_id, first_coin_id, second_coin_id, ex.name
            from {models.ExchangeMarket.__tablename__} em
            inner join {models.Exchange.__tablename__} ex
            on ex.id = em.exchange_id where first_coin_id = :symbol or second_coin_id = :symbol and ex.name = :exchange
            """,
            {"symbol": symbol, "exchange": exchange},
        )

    def _normalise_trade_size(self, market_trades, symbol):
        norm_trades = []
        for trade in market_trades:
            norm_trade = dict(trade)
            if trade["buy_sym_id"] == symbol:
                trade_size = trade["size"]
            else:
                trade_size = trade["size"] * trade["price"]
            norm_trade["size"] = trade_size
            norm_trades.append(norm_trade)
        return norm_trades

    def plot_trade_size_cdf(self, exchanges, symbol):
        # plot trade size cdf for one coin (taking into account all markets) for a given exchange
        exchange_markets = defaultdict(list)
        for exchange in exchanges:
            result_proxy = self._get_all_associated_markets(exchange, symbol)
            result = list(result_proxy)
            if len(result) == 0:
                continue
            for row in result:
                buy_sym_id = row["buy_sym_id"]
                if row["buy_sym_id"] == row["first_coin_id"]:
                    sell_sym_id = row["second_coin_id"]
                else:
                    sell_sym_id = row["first_coin_id"]
                exchange_markets[exchange].append(
                    dict(buy_sym_id=buy_sym_id, sell_sym_id=sell_sym_id)
                )
        f, ax = plt.subplots(figsize=(8, 8))
        plt.title("Trade Size Emperical CDF (" + symbol + ")")
        for exchange in exchanges:
            all_trades = []
            for market in exchange_markets[exchange]:
                market_trades_proxy = self._get_all_trades(
                    exchange, market["buy_sym_id"], market["sell_sym_id"]
                )
                market_trades = list(market_trades_proxy)
                if len(market_trades) == 0:
                    continue
                market_trades = self._normalise_trade_size(market_trades, symbol)
                all_trades.extend(market_trades)
            x = np.sort([trade["size"] for trade in all_trades])
            y = np.arange(len(x)) / float(len(x))
            (line,) = ax.plot(x, y, label=exchange)
            line.set_label(exchange)
        ax.set_xscale("log")
        for axis in [ax.xaxis, ax.yaxis]:
            axis.set_major_formatter(
                ticker.FuncFormatter(lambda y, _: "{:g}".format(y))
            )
        ax.legend()
        ax.set_xlabel("Trade size (" + symbol + ")")
        ax.set_ylabel("Percentage of trades")
        plt.show()

    def plot_trade_size_hist(self, exchanges, symbol):
        exchange_markets = defaultdict(list)
        for exchange in exchanges:
            result_proxy = self._get_all_associated_markets(exchange, symbol)
            result = list(result_proxy)
            if len(result) == 0:
                continue
            for row in result:
                buy_sym_id = row["buy_sym_id"]
                if row["buy_sym_id"] == row["first_coin_id"]:
                    sell_sym_id = row["second_coin_id"]
                else:
                    sell_sym_id = row["first_coin_id"]
                exchange_markets[exchange].append(
                    dict(buy_sym_id=buy_sym_id, sell_sym_id=sell_sym_id)
                )
        jet = plt.get_cmap("jet")
        colors = iter(jet(np.linspace(0, 1, 10)))
        plt.figure(1)
        plt.title("Trade Sizes Histogram (" + symbol + ")")
        n = 311
        for exchange in exchanges:
            all_trades = []
            for market in exchange_markets[exchange]:
                market_trades_proxy = self._get_all_trades(
                    exchange, market["buy_sym_id"], market["sell_sym_id"]
                )
                market_trades = list(market_trades_proxy)
                if len(market_trades) == 0:
                    continue
                market_trades = self._normalise_trade_size(market_trades, symbol)
                all_trades.extend(market_trades)
            df = pd.DataFrame(all_trades)
            df.index = df["timestamp"]
            df_bins = df.resample("1T").sum()
            plt.subplot(n)
            # plt.bar(df_bins.index, df_bins["size"], width=0.001, label=exchange, color=next(colors))
            plt.plot(df_bins.index, df_bins["size"], label=exchange, color=next(colors))
            plt.ylabel("Total trade size (" + symbol + ")")
            n += 1
            # print(df_bins["size"].head())
            plt.legend()
        plt.xlabel("Timestamp")
        # plt.pause(0.05)
        # plt.clf()
        # plt.show()
        plt.savefig("trade_vol_hist.png")


visualiser = Visualiser()
# visualiser.plot_single_trade_size_cdf("binance", "ETH", "BTC")
exchanges = ["binance", "coinbase", "idex"]
# visualiser.plot_trade_size_cdf(exchanges, "ETH")
# exchanges = ["coinbase", "binance"]
visualiser.plot_trade_size_hist(exchanges, "ETH")

# while True:
#     try:
#         visualiser.plot_trade_size_hist(exchanges, "ETH")
#     except KeyboardInterrupt:
#         #logging.warning("KeybaordInterrupt - plotting order book for '{}'".format(args["market"]))
#         break
