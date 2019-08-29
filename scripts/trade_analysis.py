import numpy as np
import pandas as pd
#import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter 
from matplotlib.ticker import PercentFormatter
import logging

from datetime import datetime
from antalla.db import session
from antalla import models

def get_exchange_trades(buy_sym_id, sell_sym_id, exchange): 
    query = ("select exchange_trade_id, name, timestamp, trade_type, buy_sym_id, sell_sym_id, price,"+
    " size from trades inner join exchanges on exchanges.id = trades.exchange_id" +
    " where name = '" + exchange.lower() +"' and buy_sym_id = '" + buy_sym_id.upper() + 
    "' and sell_sym_id = '" + sell_sym_id.upper() + "' order by timestamp asc")
    print(query)
    return session.execute(query)

def parse_raw_trades(raw_trades):
    trades = []
    for trade in list(raw_trades):
        trades.append(dict(
            exchange=trade[1],
            timestamp=trade[2],
            type=trade[3],
            buy_sym_id=trade[4],
            sell_sym_id=trade[5],
            price=trade[6],
            size=trade[7],
            volume=float(trade[6]*trade[7])
        ))
    return trades

def plot_hourly_trade_vol(buy_sym_id, sell_sym_id, exchanges):
    t = []
    formatter = DateFormatter('%Y-%m-%d %H:%M')
    fig, ax = plt.subplots()
    for exchange in exchanges:
        raw_trades = get_exchange_trades(buy_sym_id, sell_sym_id, exchange)
        parsed_trades = parse_raw_trades(raw_trades)
        plot_individual_trades(parsed_trades, ax, exchange)
    ax.set(xlabel="Timestamp", ylabel="Trade volume ("+buy_sym_id+")",
            title="Sum of Trade Volume Per Hour: "+buy_sym_id+"-"+sell_sym_id)
    ax.xaxis.set_major_formatter(formatter)
    ax.grid()
    ax.legend()
    plt.xticks(rotation="vertical")
    plt.show()
    
def plot_individual_trades(all_trades, ax, exchange):
    trades = list(filter(lambda x: x["exchange"] == exchange, all_trades))
    times = list(map(lambda x: x["timestamp"], trades))
    volumes = list(map(lambda x: x["volume"], trades))
    df = pd.DataFrame()
    df["timestamp"] =  pd.to_datetime(times)
    df["volumes"] = volumes
    df.index = df["timestamp"]
    df_bins = df.resample('H').sum()
    ax.plot(df_bins.index, df_bins["volumes"], label=exchange, linewidth=2)
    
def parse_market(raw_market, sym_1, sym_2):
    """
    >>> raw_market = 'BTCETH'
    >>> parse_market(raw_market, 'ETH', 'BTC')
    ('BTC', 'ETH')
    >>> parse_market("QTMBTC", 'QTM', 'BTC')
    ('QTM', 'BTC')
    
    """
    if sym_1 not in raw_market or sym_2 not in raw_market:
        return None
    elif raw_market[0:len(sym_1)] == sym_1:
        return (sym_1, sym_2)
    else:
        return (sym_2, sym_1) 

def is_original_market(buy_sym_id, sell_sym_id, exchange):
    query = (
        "select name, first_coin_id, second_coin_id, original_name from exchange_markets inner join exchanges on exchanges.id" +
        " = exchange_markets.exchange_id where name = '" + exchange.lower() + "'"
    )
    all_markets = session.execute(query)
    for row in list(all_markets):
        if row[1] == buy_sym_id and row[2] == sell_sym_id:
            market = parse_market(row[3], buy_sym_id, sell_sym_id)
            return market
        elif row[1] == sell_sym_id and row[2] == buy_sym_id:
            market = parse_market(row[3], sell_sym_id, buy_sym_id)
            return market
    return None

def invert_trades(raw_trades):
    trades = []
    for trade in list(raw_trades):
        modified_trade = dict(
            exchange=trade[1],
            timestamp=trade[2],
            )
        if trade[3] == "sell":
            modified_trade["type"]="sell"
        else:
            modified_trade["type"]="buy"
        modified_trade["buy_sym_id"]=trade[5]
        modified_trade["sell_sym_id"]=trade[4]
        price = float(1.0/trade[6])
        modified_trade["price"]=price
        modified_trade["size"]=float((trade[6]*trade[7])*(float(1.0/trade[6])))*trade[6]
        modified_trade["volume"]=float((trade[6]*trade[7])*(float(1.0/trade[6])))
        trades.append(modified_trade)
    return trades

def plot_volume_bar_chart(buy_sym_id, sell_sym_id, exchange, plot_id):
    # check if market is original market
    original_market = is_original_market(buy_sym_id, sell_sym_id, exchange)
    trades = []
    if original_market is None:
        return
    elif original_market[0] == sell_sym_id and original_market[1] == buy_sym_id:
        raw_trades = get_exchange_trades(sell_sym_id, buy_sym_id, exchange)
        trades = invert_trades(raw_trades)
    else:
        raw_trades = get_exchange_trades(buy_sym_id, sell_sym_id, exchange)
        trades = parse_raw_trades(raw_trades)

    times = list(map(lambda x: x["timestamp"], trades))
    volumes = list(map(lambda x: x["volume"], trades))
    prices = list(map(lambda x: x["price"], trades))
    sell_volume = list(map(lambda x: x["volume"] if x["type"] == "sell" else 0, trades))
    buy_volume = list(map(lambda x: x["volume"] if x["type"] == "buy" else 0, trades))
    
    sells = list(filter(lambda x: x["type"] == "sell", trades))
    sell_times = list(map(lambda x: x["timestamp"], sells))
    sell_prices = list(map(lambda x: x["price"], sells))

    buys = list(filter(lambda x: x["type"] == "buy", trades))
    buy_times = list(map(lambda x: x["timestamp"], buys))
    buy_prices = list(map(lambda x: x["price"], buys))

    fig, axs = plt.subplots(2, sharex=True)

    df = pd.DataFrame()
    df["timestamp"] =  pd.to_datetime(times)
    df["volumes"] = volumes
    df["prices"] = prices
    df["sell_volume"] = sell_volume
    df["buy_volume"] = buy_volume
    df.index = df["timestamp"]
    # bin trades in 1 hour bins
    df_bins = df.resample('30T').sum()
    
    p1 = axs[0].bar(df_bins.index, df_bins["sell_volume"], width=0.01, color="steelblue")
    p2 = axs[0].bar(df_bins.index, df_bins["buy_volume"], width=0.01, color="tomato")
   
    formatter = DateFormatter('%Y-%m-%d %H:%M')
    axs[0].set(title=exchange+": Traded Volume and Price per Hour: " + buy_sym_id + "-" + sell_sym_id)
    axs[0].xaxis.set_major_formatter(formatter)
    axs[0].set_ylabel("Total trade volume ("+buy_sym_id.upper()+")")
    axs[0].grid()
    axs[0].legend((p1[0], p2[0]), ("Sell volume", "Buy volume"))

    plt.xticks(rotation="vertical")
    plt.figure(plot_id)
    if len(sells) == 0 or len(buys) == 0:
        plt.xticks(rotation="vertical")
        plt.figure(plot_id)
        return
    df_sells = pd.DataFrame()
    df_sells["timestamp"] = sell_times
    df_sells["prices"] = sell_prices
    df_sells.index = df_sells["timestamp"]
    sell_bins = df_sells.resample('30T').mean().fillna(0)
    # avg sell price
    ps = axs[1].plot(sell_bins.index, sell_bins["prices"])
    df_buys = pd.DataFrame()
    df_buys["timestamp"] = buy_times
    df_buys["prices"] = buy_prices
    df_buys.index = df_buys["timestamp"]
    buy_bins = df_buys.resample('30T').mean().fillna(0)
    # avg buy price
    pb = axs[1].plot(buy_bins.index, buy_bins["prices"])
    axs[1].set(xlabel='Time')
    axs[1].xaxis.set_major_formatter(formatter)
    axs[1].grid()
    axs[1].legend((ps[0], pb[0]), ("Sell price", "Buy price"))
    axs[1].set_ylabel("Avg. price ("+buy_sym_id.upper()+")")    
    plt.xticks(rotation="vertical")
    plt.figure(plot_id)


"""
Here are some basic plots for analysing:
    - total trade volume
    - trade volume from sell trades
    - trade volume from buy trades
    - avg trade sell prices
    - avg trade buy prices

The 'plot_volume_bar_chart()' method provides an overview of the trade price developement and the trade volume.
However, for some exchanges (e.g. binance), no trade type (i.e. sell/buy) is given and hence no analysis with regards
to this variable can be performed.

Examples:
    > plot_hourly_trade_vol("ETH", "BTC", ["binance", "coinbase", "hitbtc"])
    > plot_volume_bar_chart("ETH", "BTC", "hitbtc", 0)
    > plot_volume_bar_chart("ETH", "BTC", "coinbase", 1)
    and add 'plt.show()'

"""

#plt.show()

