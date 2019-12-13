import hashlib
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from .db import Base as AbstractBase


class Base(AbstractBase):
    __abstract__ = True

    @classmethod
    def index_elements(cls):
        return [v.name for v in cls.__table__.primary_key]


class BelongsToOrder:
    @declared_attr
    def exchange_id(cls):
        return Column(Integer, ForeignKey("exchanges.id"), nullable=False)

    @declared_attr
    def exchange(cls):
        return relationship("Exchange", foreign_keys=[cls.exchange_id])

    @declared_attr
    def exchange_order_id(cls):
        return Column(String, nullable=False)

    @declared_attr
    def order(cls):
        return relationship(
            "Order",
            foreign_keys=[cls.exchange_id, cls.exchange_order_id],
            viewonly=True
        )

    @declared_attr
    def __table_args__(cls):
        idx_name = f"{cls.__name__}-exchange-id-exchange-order-id-idx"
        return (
            ForeignKeyConstraint(
                ["exchange_id", "exchange_order_id"],
                ["orders.exchange_id", "orders.exchange_order_id"],
            ),
            Index(idx_name, "exchange_id", "exchange_order_id"),
        )


class Coin(Base):
    __tablename__ = "coins"
    symbol = Column(String, primary_key=True)
    name = Column(String)
    price_usd = Column(Float)
    last_price_updated = Column(DateTime)

    def __repr__(self):
        return f"Coin(symbol='{self.symbol}')"

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol


class Exchange(Base):
    __tablename__ = "exchanges"
    name = Column(String)
    id = Column(Integer, primary_key=True)
    markets = relationship("ExchangeMarket", back_populates="exchange")
    markets_with_data = relationship("ExchangeMarket",
        primaryjoin="and_(Exchange.id == ExchangeMarket.exchange_id, ExchangeMarket.agg_orders_count > 0)")

    def __repr__(self):
        return f"Exchange(name='{self.name}')"

    def to_dict(self, include_markets=False):
        result = dict(id=self.id, name=self.name)
        if include_markets:
            result["markets"] = [market.to_dict() for market in self.markets_with_data]
        return result


class Order(Base):
    __tablename__ = "orders"

    exchange_id = Column(Integer, ForeignKey("exchanges.id"), primary_key=True)
    exchange_order_id = Column(String, primary_key=True)

    timestamp = Column(DateTime, index=True)
    filled_at = Column(DateTime)
    expiry = Column(DateTime)
    cancelled_at = Column(DateTime, index=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange = relationship("Exchange")
    sizes = relationship("OrderSize", back_populates="order")
    gas_fee = Column(Float) 
    user = Column(String)
    side = Column(String)
    price = Column(Float, nullable=False)
    last_updated = Column(DateTime)
    order_type = Column(String)
    funds = relationship("MarketOrderFunds", back_populates="order")

    def __repr__(self):
        return f"Order(exchange_id={self.exchange_id}, exchange_order_id='{self.exchange_order_id}')"


class MarketOrderFunds(BelongsToOrder, Base):
    __tablename__ = "market_order_funds"

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, nullable=False)
    funds = Column(Float, nullable=False)

    def __repr__(self):
        return f"MarketOrderFunds(id={self.id})"


class OrderSize(BelongsToOrder, Base):
    __tablename__ = "order_sizes"

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, nullable=False)
    size = Column(Float, nullable=False)

    def __repr__(self):
        return f"OrderSize(id={self.id})"


class Trade(Base):
    __tablename__ = "trades"

    exchange_trade_id = Column(String, primary_key=True)
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, primary_key=True)

    exchange = relationship("Exchange")

    timestamp = Column(DateTime, nullable=False, index=True)
    trade_type = Column(String)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    maker = Column(String)
    taker = Column(String)
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    total = Column(Float)
    buyer_fee = Column(Float)
    seller_fee = Column(Float)
    gas_fee = Column(Float)
    exchange_order_id = Column(String, index=True)
    maker_order_id = Column(String, index=True)
    taker_order_id = Column(String, index=True)

    def __repr__(self):
        return f"Trade(id={self.exchange_trade_id})"


class AggOrder(Base):
    __tablename__ = "aggregate_orders"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash_id = self.pk_hash()
        self.first_coin_id, self.second_coin_id = self.buy_sym_id, self.sell_sym_id
        if self.first_coin_id > self.second_coin_id:
            self.first_coin_id, self.second_coin_id = self.second_coin_id, self.first_coin_id

    def pk_hash(self):
        pk = f"{self.last_update_id}{self.exchange_id}{self.order_type}{self.price}".encode("utf-8")
        hash_obj = hashlib.sha256(pk)
        return hash_obj.hexdigest()
    
    hash_id = Column(String, primary_key=True)
    last_update_id = Column(Integer)
    timestamp = Column(DateTime, index=True, nullable=False)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])

    first_coin_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    second_coin_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)

    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange")
    # exchange_market = relationship("ExchangeMarket", foreign_keys=[first_coin_id, second_coin_id, exchange_id])
    order_type = Column(String, nullable=False)
    price = Column(Float, nullable=False, index=True)
    size = Column(Float, nullable=False)

    __table_args__ = (
        Index("latest_orders_index",
            "order_type", "price", "last_update_id", "exchange_id", unique=True),
        Index("market_orders_index", "first_coin_id", "second_coin_id", "exchange_id"),
        ForeignKeyConstraint(["first_coin_id", "second_coin_id", "exchange_id"],
                             ["exchange_markets.first_coin_id", "exchange_markets.second_coin_id", "exchange_markets.exchange_id"])
    )

    @classmethod
    def index_elements(cls):
        return ["order_type", "price", "last_update_id", "exchange_id"]

    def __repr__(self):
        return f"AggOrder(id={self.hash_id})"

class Market(Base):
    __tablename__ = "markets"
    first_coin_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True)
    first_coin = relationship("Coin", foreign_keys=[first_coin_id])
    second_coin_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True)
    second_coin = relationship("Coin", foreign_keys=[second_coin_id])

    def __eq__(self, other):
        return (self.first_coin_id, self.second_coin_id) == (other.first_coin_id, other.second_coin_id)

    def __hash__(self):
        return hash((self.first_coin_id, self.second_coin_id))

    def __repr__(self):
        return f"Market(buy_sym_id='{self.first_coin_id}', sell_sym_id='{self.second_coin_id}')"

    def to_dict(self):
        return dict(
            first_coin=self.first_coin_id,
            second_coin=self.second_coin_id,
        )


class ExchangeMarket(Base):
    __tablename__ = "exchange_markets"
    volume_usd = Column(Float)
    quoted_volume = Column(Float, nullable=False)
    quoted_vol_timestamp = Column(DateTime)
    vol_usd_timestamp = Column(DateTime)
    quoted_volume_id = Column(String, ForeignKey("coins.symbol"), nullable=False)
    original_name = Column(String, nullable=False)

    agg_orders_count = Column(Integer, nullable=False, server_default="0")

    first_coin_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    second_coin_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)

    orders = relationship("AggOrder")

    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange", foreign_keys=[exchange_id])
    market = relationship("Market", foreign_keys=[first_coin_id, second_coin_id])

    __table_args__ = (
        PrimaryKeyConstraint("first_coin_id", "second_coin_id", "exchange_id"),
        ForeignKeyConstraint(
            ["first_coin_id", "second_coin_id"],
            ["markets.first_coin_id", "markets.second_coin_id"],
        ),
        Index("exchange-market-fk-idx", "first_coin_id", "second_coin_id")
    )

    def __eq__(self, other):
        return (self.first_coin_id, self.second_coin_id, self.exchange_id) == \
               (other.first_coin_id, other.second_coin_id, other.exchange_id)

    def __hash__(self):
        return hash((self.first_coin_id, self.second_coin_id, self.exchange_id))

    def to_dict(self):
        market = dict(
            quoted_volume=self.quoted_volume,
            quoted_vol_timestamp=self.quoted_vol_timestamp.isoformat(),
            quoted_volume_id=self.quoted_volume_id,
            name=self.name,
            original_name=self.original_name,
            first_coin=self.first_coin_id,
            second_coin=self.second_coin_id,
        )
        if self.volume_usd and self.vol_usd_timestamp:
            market["volume_usd"] = self.volume_usd
            market["vol_usd_timestamp"] = self.vol_usd_timestamp.isoformat()
        return market

    @property
    def name(self):
        original_name = self.original_name.replace("-", "").replace("_", "")
        first_coin, second_coin = self.first_coin_id, self.second_coin_id
        if first_coin + second_coin != original_name:
            first_coin, second_coin = second_coin, first_coin
        if first_coin + second_coin != original_name:
            raise ValueError("invalid coin names")
        return "{0}/{1}".format(first_coin, second_coin)

    def __repr__(self):
        return "ExchangeMarket(name='{0}', exchange_id={1})".format(self.name, self.exchange_id)


class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"
        
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    snapshot_type = Column(String, nullable=False, primary_key=True)
    mid_price_range = Column(Float, nullable=False, primary_key=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True, primary_key=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True, primary_key=True)
    exchange = relationship("Exchange", foreign_keys=[exchange_id])
    spread = Column(Float, nullable=False, index=True)
    bids_volume = Column(Float, nullable=False)
    asks_volume = Column(Float, nullable=False)
    bids_count = Column(Integer, nullable=False)
    asks_count = Column(Integer, nullable=False)
    bids_price_stddev = Column(Float, nullable=False)
    asks_price_stddev = Column(Float, nullable=False)
    bids_price_mean = Column(Float, nullable=False)
    asks_price_mean = Column(Float, nullable=False)
    min_ask_price = Column(Float, nullable=False)
    min_ask_size = Column(Float, nullable=False)
    max_bid_price = Column(Float, nullable=False)
    max_bid_size = Column(Float, nullable=False)
    bid_price_median = Column(Float, nullable=False)
    ask_price_median = Column(Float, nullable=False)
    

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)

    session_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    connection_event = Column(String, nullable=False)
    data_collected = Column(String, nullable=False)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange")
    