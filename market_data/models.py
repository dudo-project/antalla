from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .db import Base

class Coin(Base):
    __tablename__ = 'coins'
    symbol = Column(String, primary_key=True)
    name = Column(String)

class Exchange(Base):
    __tablename__ = 'exchanges'
    name = Column(String)
    id = Column(Integer, primary_key=True)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    from_sym_id = Column(String,ForeignKey("coins.symbol"), nullable=False)
    from_sym = relationship("Coin", foreign_keys=[from_sym_id])
    to_sym_id = Column(String, ForeignKey("coins.symbol"), nullable=False)
    to_sym = relationship("Coin", foreign_keys=[to_sym_id])
    exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=False)
    exchange = relationship("Exchange")
    amount = Column(Float, nullable=False)
    gas_fee = Column(Float, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    user = Column(String)
    
