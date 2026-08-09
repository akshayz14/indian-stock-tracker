from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    exchange = Column(String)  # NSE, BSE, etc.
    sector = Column(String)
    type = Column(String, nullable=False, default='equity')
    
    prices = relationship('DailyPrice', back_populates='asset')
    suggestions = relationship('Suggestion', back_populates='asset')

class DailyPrice(Base):
    __tablename__ = 'daily_prices'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(Float)
    
    asset = relationship('Asset', back_populates='prices')

class Suggestion(Base):
    __tablename__ = 'suggestions'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    score = Column(Float, nullable=False)
    reasoning = Column(String)
    
    asset = relationship('Asset', back_populates='suggestions')

def get_engine(db_path='sqlite:///stocks.db'):
    return create_engine(db_path, echo=False)

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()