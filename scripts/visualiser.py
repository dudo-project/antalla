import numpy as np 
from matplotlib import pyplot as plt 
import pandas as pd 

from matplotlib.dates import DateFormatter 
from matplotlib.ticker import PercentFormatter
import logging

from datetime import datetime
from antalla.db import session
from antalla import models

class Visualiser:

    def plot_trade_size_cdf(self, exchange, buy_sym_id, sell_sym_id):
        result = session.execute(
            """
            select timestamp, buy_sym_id, sell_sym_id, price, size, timestamp from trades inner join exchanges ex on trades.exchange_id=ex.id \
                where buy_sym_id= :buy_sym_id and sell_sym_id= :sell_sym_id and ex.name = :exchange
            """, {"exchange": exchange, "buy_sym_id": buy_sym_id, "sell_sym_id": sell_sym_id}
        )
        trades = []
        for row in list(result):
            trades.append(dict(
                timestamp=row["timestamp"],
                buy_sym_id=row["buy_sym_id"],
                sell_sym_id=row["sell_sym_id"],
                size=row["size"],
                price=["price"]
            ))
        trade_sizes = list(map(lambda x: x["size"], trades))
        ser = pd.Series(trade_sizes)
        ser.hist(cumulative=True, bins=100, density=1)
        plt.title("Trade Size CDF: "+ exchange + " (" + buy_sym_id + "-" + sell_sym_id + ")")      
        plt.xlabel("Trade Size ("+sell_sym_id+")")
        plt.ylabel("F(x)")
        plt.show()

visualiser = Visualiser()
visualiser.plot_trade_size_cdf("binance", "ETH", "BTC")

