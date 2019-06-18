from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .db import Base


class Coin(Base):
    __tablename__ = "coins"
    symbol = Column(String, primary_key=True)
    name = Column(String)


class Exchange(Base):
    __tablename__ = "exchanges"
    name = Column(String)
    id = Column(Integer, primary_key=True)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    filled_at = Column(DateTime)
    expiry = Column(DateTime)
    cancelled_at = Column(DateTime, index=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange")
    quantity = Column(Float)
    gas_fee = Column(Float)
    user = Column(String)
    side = Column(String)
    price = Column(Float, nullable=False)
    remaining_size = Column(Float)
    exchange_order_id = Column(String, index=True, nullable=False)
    last_updated = Column(DateTime)
    order_type = Column(String)
    funds = Column(Float)


class Trade(Base):
    __tablename__ = "trades"
    timestamp = Column(DateTime, nullable=False, index=True)
    trade_type = Column(String)
    id = Column(Integer, primary_key=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange")
    maker = Column(String)
    taker = Column(String)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    total = Column(Float)
    buyer_fee = Column(Float)
    seller_fee = Column(Float)
    gas_fee = Column(Float)
    exchange_order_id = Column(String, index=True, unique=True)
    maker_order_id = Column(String, index=True)
    taker_order_id = Column(String, index=True)


class AggOrder(Base):
    __tablename__ = "aggregate_orders"
    id = Column(Integer, primary_key=True)
    last_update_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, index=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False, index=True)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False, index=True)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False, index=True)
    exchange = relationship("Exchange")
    order_type = Column(String, nullable=False)
    price = Column(Float, nullable=False, index=True)
    quantity = Column(Float, nullable=False)

    