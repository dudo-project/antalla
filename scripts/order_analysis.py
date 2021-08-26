import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import PercentFormatter
import matplotlib.style as style
import logging

from datetime import datetime
from antalla.db import session
from antalla import models

sns.set_style("darkgrid")


def query_orders(buy_sym_id, sell_sym_id):
    query = f"""select e.name, o.exchange_order_id, o.timestamp, o.filled_at, o.expiry,
                       o.cancelled_at, o.buy_sym_id, o.sell_sym_id, o.user, o.price
                from {models.Order.__tablename__} o
        inner join {models.Exchange.__tablename__} e on e.id = o.exchange_id
        where buy_sym_id = '{buy_sym_id.upper()}' and
        sell_sym_id = '{sell_sym_id.upper()}'
        order by timestamp asc"""
    return session.execute(query)


def parse_orders(raw_orders):
    orders = []
    for order in raw_orders:
        new_order = dict(
            exchange=order[0],
            exchange_order_id=order[1],
            timestamp=order[2],
            filled_at=order[3],
            exipry=order[4],
            cancelled_at=order[5],
            buy_sym_id=order[6],
            sell_sym_id=order[7],
            user=order[8],
            price=order[9],
        )
        # check if order has been cancelled (for DEXs, e.g. IDEX: regardless whether it has been filled)
        if order[5] != None:
            new_order["order_time"] = order[5] - order[2]
        # check if order has been filled and not been cancelled
        elif order[3] != None:
            new_order["order_time"] = order[3] - order[2]
        else:
            new_order["order_time"] = None
        orders.append(new_order)
    return orders


def get_times(orders):
    fill_times = []
    cancel_times = []
    for order in orders:
        if order["cancelled_at"] is not None:
            cancel_times.append(order["order_time"])
        elif order["filled_at"] is not None and order["cancelled_at"] is None:
            fill_times.append(order["order_time"])
    return dict(fill_times=fill_times, cancel_times=cancel_times)


def plot_order_time_densities(buy_sym_id, sell_sym_id, exchange):
    # get times until filled and cancelled
    raw_orders = query_orders(buy_sym_id, sell_sym_id)
    parsed_orders = parse_orders(raw_orders)
    filtered_orders = list(filter(lambda x: x["exchange"] == exchange, parsed_orders))
    times = get_times(filtered_orders)
    df = pd.DataFrame()
    df["cancel_times"] = times["cancel_times"]
    cancels = df["cancel_times"].dt.total_seconds() / 60
    df["fill_times"] = pd.Series(times["fill_times"])
    fills = df["fill_times"].dt.total_seconds() / 60

    style.use("seaborn")
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.hist(cancels, bins=40, log=True)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Number of orders cancelled")
    ax1.set_title(
        exchange
        + ": Time until order is cancelled ("
        + buy_sym_id
        + "-"
        + sell_sym_id
        + ")"
    )
    ax2.hist(fills, bins=40, log=True)
    ax2.set_ylabel("Number of orders filled")
    ax2.set_xlabel("Time (s)")
    ax2.set_title(
        exchange
        + ": Time until order is filled ("
        + buy_sym_id
        + "-"
        + sell_sym_id
        + ")"
    )
    plt.show()


"""
Basic histogram for comparing the time until an order is cancelled vs the time until an order is filled

Examples:
    > plot_order_time_densities("ETH", "BTC","coinbase")
    > plot_order_time_densities("ETH", "USDC","coinbase")
    > plot_order_time_densities("USDC", "ETH","idex")
"""
