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
    industry = Column(String)
    type = Column(String, nullable=False, default='equity')
    
    # Fundamental data fields
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    forward_pe = Column(Float)
    eps = Column(Float)
    book_value = Column(Float)
    price_to_book = Column(Float)
    dividend_yield = Column(Float)
    dividend_rate = Column(Float)
    beta = Column(Float)
    profit_margin = Column(Float)
    operating_margin = Column(Float)
    return_on_equity = Column(Float)
    return_on_assets = Column(Float)
    total_revenue = Column(Float)
    total_debt = Column(Float)
    total_cash = Column(Float)
    debt_to_equity = Column(Float)
    shares_outstanding = Column(Float)
    float_shares = Column(Float)
    website = Column(String)
    country = Column(String)
    currency = Column(String)
    last_updated = Column(String)  # timestamp of last data update
    
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

class MutualFundAsset(Base):
    __tablename__ = 'mutual_fund_assets'
    id = Column(Integer, primary_key=True)
    scheme_code = Column(String, unique=True, nullable=False)
    scheme_name = Column(String)
    fund_house = Column(String)
    type = Column(String)  # Will store category like 'large_cap', etc.
    
    suggestions = relationship('MutualFundSuggestion', back_populates='asset')

class MutualFundSuggestion(Base):
    __tablename__ = 'mutual_fund_suggestions'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('mutual_fund_assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    score = Column(Float, nullable=False)
    reasoning = Column(String)
    
    asset = relationship('MutualFundAsset', back_populates='suggestions')

def get_engine(db_path='sqlite:///stocks.db'):
    return create_engine(db_path, echo=False)

def _add_missing_columns(engine):
    """Add any columns from the Asset model that are missing from the assets table."""
    from sqlalchemy import inspect, text

    # Get existing column names from the assets table
    inspector = inspect(engine)
    # If the table doesn't exist yet, there are no existing columns to compare against
    if not inspector.has_table('assets'):
        return

    existing_cols = set(c['name'] for c in inspector.get_columns('assets'))

    # Define all columns from the Asset model (those NOT already present)
    # and their SQL types, matching the model definitions
    model_columns = {
        'industry': 'TEXT',
        'market_cap': 'REAL',
        'pe_ratio': 'REAL',
        'forward_pe': 'REAL',
        'eps': 'REAL',
        'book_value': 'REAL',
        'price_to_book': 'REAL',
        'dividend_yield': 'REAL',
        'dividend_rate': 'REAL',
        'beta': 'REAL',
        'profit_margin': 'REAL',
        'operating_margin': 'REAL',
        'return_on_equity': 'REAL',
        'return_on_assets': 'REAL',
        'total_revenue': 'REAL',
        'total_debt': 'REAL',
        'total_cash': 'REAL',
        'debt_to_equity': 'REAL',
        'shares_outstanding': 'REAL',
        'float_shares': 'REAL',
        'website': 'TEXT',
        'country': 'TEXT',
        'currency': 'TEXT',
        'last_updated': 'TEXT',
    }

    # Build ALTER TABLE statements for any missing columns
    with engine.begin() as conn:
        for col_name, col_type in model_columns.items():
            if col_name not in existing_cols:
                conn.execute(text(f'ALTER TABLE assets ADD COLUMN "{col_name}" {col_type}'))

def init_db():
    engine = get_engine()
    # Create all tables first (handles initial schema creation)
    Base.metadata.create_all(engine)
    # Then add any missing columns from model updates
    _add_missing_columns(engine)
    return engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def get_mutual_fund_engine(db_path='sqlite:///mutual_funds.db'):
    return create_engine(db_path, echo=False)

def get_mutual_fund_session():
    engine = get_mutual_fund_engine()
    Session = sessionmaker(bind=engine)
    return Session()