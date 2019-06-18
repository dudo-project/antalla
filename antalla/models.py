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
    sizes = relationship("OrderSize", back_populates="order")
    gas_fee = Column(Float) 
    user = Column(String)
    side = Column(String)
    price = Column(Float, nullable=False)
    exchange_order_id = Column(String, index=True, nullable=False)
    last_updated = Column(DateTime)
    order_type = Column(String)
    funds = relationship("MarketOrderFunds", back_populates="order")


class MarketOrderFunds(Base):
    __tablename__ = "market_order_funds"
    exchange_order_id = Column(String, ForeignKey("orders.exchange_order_id"), index=True, nullable=False)
    order = relationship("Order", foreign_keys=[exchange_order_id])
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    funds = Column(Float, nullable=False)
    

class OrderSize(Base):
    __tablename__ = "order_sizes"
    exchange_order_id = Column(String, ForeignKey("orders.exchange_order_id"), index=True, nullable=False)
    order = relationship("Order", foreign_keys=[exchange_order_id])
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    size = Column(Float, nullable=False)


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
    size = Column(Float, nullable=False)
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
    size = Column(Float, nullable=False)