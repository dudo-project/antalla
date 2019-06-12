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
    timestamp = Column(DateTime)
    filled_at = Column(DateTime)
    expiry = Column(DateTime)
    cancelled_at = Column(DateTime)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    exchange = relationship("Exchange")
    amount_buy = Column(Float, nullable=False)
    amount_sell = Column(Float, nullable=False)
    gas_fee = Column(Float)
    user = Column(String)
    exchange_order_id = Column(String)
    
class Trade(Base):
    __tablename__ = "trades"
    timestamp = Column(DateTime, nullable=False)
    trade_type = Column(String, nullable=False)
    id = Column(Integer, primary_key=True)
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    exchange = relationship("Exchange")
    maker = Column(String, nullable=False)
    taker = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    total = Column(Float)
    buyer_fee = Column(Float)
    seller_fee = Column(Float)
    gas_fee = Column(Float)
    order_hash = Column(String)
