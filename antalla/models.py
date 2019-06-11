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
    buy_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False)
    buy_sym = relationship("Coin", foreign_keys=[buy_sym_id])
    sell_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False)
    sell_sym = relationship("Coin", foreign_keys=[sell_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    exchange = relationship("Exchange")
    amount_buy = Column(Float, nullable=False)
    amount_sell = Column(Float, nullable=False)
    gas_fee = Column(Float)
    cancelled_at = Column(DateTime)
    user = Column(String)
    exchange_order_id = Column(String)
    
