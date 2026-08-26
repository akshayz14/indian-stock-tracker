from flask import Flask, render_template, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Asset, DailyPrice, Suggestion, MutualFundAsset, MutualFundSuggestion, get_session, get_mutual_fund_session, get_mutual_fund_engine
import datetime
from functools import wraps
from nsetools import Nse  # Import NSE class
import requests
import json
import os
from datetime import datetime, timedelta
from stock_search_service import StockSearchService

# In-memory cache for searched stock 60-day price history (TTL: 1 hour)
search_history_cache = {}
SEARCH_HISTORY_CACHE_DURATION = timedelta(hours=1)

app = Flask(__name__)


@app.template_filter('ddmmmyyyy')
def format_date_ddmmmyyyy(value):
    """Format a date as dd-mm-yyyy string."""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    try:
        return value.strftime('%d-%m-%Y')
    except Exception:
        return str(value)


def get_db_session():
    """Get a database session"""
    return get_session()

def login_required(f):
    """Decorator to ensure database is accessible"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            session = get_db_session()
            # Simple database connection test
            session.execute(text("SELECT 1"))
            session.close()
            return f(*args, **kwargs)
        except Exception as e:
            return f"Database connection error: {str(e)}", 500
    return decorated_function

# Initialize mutual funds database on startup
def init_mutual_funds_db():
    """Initialize the mutual funds database and create tables if they don't exist."""
    try:
        engine = get_mutual_fund_engine()
        from models import Base
        Base.metadata.create_all(engine)
        print("Mutual funds database tables initialized successfully.")
    except Exception as e:
        print(f"Warning: Could not initialize mutual funds database: {e}")

# Run initialization on import
init_mutual_funds_db()

@app.route('/')
@login_required
def index():
    """Main dashboard showing overview of database"""
    session = get_db_session()
    try:
        stats = {
            'total_assets': session.query(Asset).count(),
            'total_stocks': session.query(Asset).filter(Asset.type == 'equity').count(),
            'total_prices': session.query(DailyPrice).count(),
            'total_suggestions': session.query(Suggestion).count(),
            'latest_date': session.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()[0] if session.query(DailyPrice).first() else None
        }
        return render_template('index.html', stats=stats, active='home')
    finally:
        session.close()

@app.route('/stocks')
@login_required
def stocks():
    """Display all assets, with optional search by symbol/name and type filter"""
    session = get_db_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        q = request.args.get('q', '').strip()
        asset_type = request.args.get('type', 'equity')
        
        assets_query = session.query(Asset)
        if asset_type:
            assets_query = assets_query.filter(Asset.type == asset_type)
        if q:
            like = f"%{q}%"
            assets_query = assets_query.filter(
                (Asset.symbol.ilike(like)) | (Asset.name.ilike(like))
            )
        total = assets_query.count()
        assets = assets_query.order_by(Asset.symbol).offset((page - 1) * per_page).limit(per_page).all()
        
        # Add latest price to each asset
        for asset in assets:
            latest_price = (
                session.query(DailyPrice)
                .filter(DailyPrice.asset_id == asset.id)
                .order_by(DailyPrice.date.desc())
                .first()
            )
            asset.latest_price = latest_price.close if latest_price is not None else 0.0
            
        total_pages = max(1, (total + per_page - 1) // per_page)
        
        return render_template('stocks.html',
            stocks=assets,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            q=q,
            has_next=page < total_pages,
            has_prev=page > 1,
            asset_type=asset_type,
            active='stocks')
    finally:
        session.close()

def get_price_history(asset_id, show_latest_days=60):
    """Get price history for an asset, optionally limiting to latest N days.
    
    Returns a list of dicts for JSON compatibility, or DailyPrice objects 
    if show_latest_days is None (for maximum flexibility).
    """
    session = get_db_session()
    try:
        # Get full price history from database
        price_history = session.query(DailyPrice).filter_by(asset_id=asset_id).order_by(DailyPrice.date.asc()).all()
        
        # If we want latest N days, slice the most recent records
        if show_latest_days and price_history:
            # Take the most recent show_latest_days records
            price_history = price_history[-show_latest_days:]
        
        # Convert to dicts for JSON serialization compatibility
        # This ensures the data can be passed to templates and APIs without
        # "Object of type DailyPrice is not JSON serializable" errors
        result = []
        for price in price_history:
            result.append({
                'date': price.date.isoformat() if price.date else None,
                'open': price.open,
                'high': price.high,
                'low': price.low,
                'close': price.close,
                'adj_close': price.adj_close,
                'volume': price.volume
            })
        return result
    finally:
        session.close()


@app.route('/stocks/<int:asset_id>')
@login_required
def stock_detail(asset_id):
    """Display details for a specific asset"""
    session = get_db_session()
    try:
        asset = session.query(Asset).get(asset_id)
        if not asset:
            return "Asset not found", 404
        
        # Check for history view mode: ?history=latest60 or ?history=all
        history_mode = request.args.get('history', 'latest60')
        if history_mode == 'all':
            show_latest_days = None  # Show all data
        else:
            show_latest_days = 60  # Show latest 60 days
        
        # Get recent prices (last 10 for table)
        recent_prices = session.query(DailyPrice).filter_by(asset_id=asset_id).order_by(DailyPrice.date.desc()).limit(10).all()
        
        # Get full price history for charts (controlled by show_latest_days param)
        price_history = get_price_history(asset_id, show_latest_days=show_latest_days)
        
        # Get suggestions for this asset
        suggestions = session.query(Suggestion).filter_by(asset_id=asset_id).order_by(Suggestion.date.desc()).limit(5).all()
        
        return render_template('stock_detail.html',
            stock=asset,
            recent_prices=recent_prices,
            price_history=price_history,
            suggestions=suggestions,
            active='stocks',
            history_mode=history_mode)
    finally:
        session.close()

@app.route('/prices')
@login_required
def prices():
    """Display daily prices with filtering"""
    session = get_db_session()
    try:
        # Get filter parameters
        asset_id = request.args.get('asset_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        asset_type = request.args.get('type', None)
        
        query = session.query(DailyPrice, Asset).join(Asset, DailyPrice.asset_id == Asset.id)
        
        if asset_id:
            query = query.filter(DailyPrice.asset_id == asset_id)
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        else:
            # Default to stocks only (exclude mutual funds, which have NAV-only rows)
            query = query.filter(Asset.type != 'mutual_fund')
        if start_date:
            query = query.filter(DailyPrice.date >= datetime.datetime.strptime(start_date, '%d-%m-%Y').date())
        if end_date:
            query = query.filter(DailyPrice.date <= datetime.datetime.strptime(end_date, '%d-%m-%Y').date())
        
        # Get all assets for filter dropdown
        assets = session.query(Asset).order_by(Asset.symbol).all()
        
        # Paginate
        page = request.args.get('page', 1, type=int)
        per_page = 20
        total = query.count()
        prices = query.order_by(DailyPrice.date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = max(1, (total + per_page - 1) // per_page)
        return render_template('prices.html',
            prices=prices,
            stocks=assets,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            start_date=start_date,
            end_date=end_date,
            asset_type=asset_type,
            active='prices')
    finally:
        session.close()

@app.route('/suggestions')
@login_required
def suggestions():
    """Display suggestions with filtering"""
    session = get_db_session()
    try:
        # Get filter parameters
        asset_id = request.args.get('asset_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        asset_type = request.args.get('type', None)
        
        query = session.query(Suggestion, Asset).join(Asset, Suggestion.asset_id == Asset.id)
        
        if asset_id:
            query = query.filter(Suggestion.asset_id == asset_id)
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        if start_date:
            query = query.filter(Suggestion.date >= datetime.datetime.strptime(start_date, '%d-%m-%Y').date())
        if end_date:
            query = query.filter(Suggestion.date <= datetime.datetime.strptime(end_date, '%d-%m-%Y').date())
        
        # Get all assets for filter dropdown
        assets = session.query(Asset).order_by(Asset.symbol).all()
        
        # Paginate
        page = request.args.get('page', 1, type=int)
        per_page = 20
        total = query.count()
        suggestions = query.order_by(Suggestion.date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = max(1, (total + per_page - 1) // per_page)
        # Compute score distribution for chart
        score_labels = []
        score_counts = []
        if suggestions:
            scores = [s[0].score for s in suggestions if s[0].score is not None]
            if scores:
                # Simple binning for chart
                bins = [0, 20, 40, 60, 80, 100]
                for i in range(len(bins)-1):
                    count = sum(1 for s in scores if bins[i] <= s < bins[i+1])
                    score_labels.append(f"{bins[i]}-{bins[i+1]}")
                    score_counts.append(count)
        
        return render_template('suggestions.html',
            suggestions=suggestions,
            stocks=assets,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            start_date=start_date,
            end_date=end_date,
            asset_type=asset_type,
            score_labels=score_labels,
            score_counts=score_counts,
            active='suggestions')
    finally:
        session.close()

@app.route('/api/stocks')
@login_required
def api_stocks():
    """API endpoint to get assets as JSON"""
    session = get_db_session()
    try:
        assets = session.query(Asset).order_by(Asset.symbol).all()
        return jsonify([{
            'id': asset.id,
            'symbol': asset.symbol,
            'name': asset.name,
            'exchange': asset.exchange,
            'sector': asset.sector,
            'type': asset.type
        } for asset in assets])
    finally:
        session.close()

@app.route('/api/prices')
@login_required
def api_prices():
    """API endpoint to get prices as JSON"""
    session = get_db_session()
    try:
        asset_id = request.args.get('asset_id', type=int)
        days = request.args.get('days', type=int, default=30)
        
        query = session.query(DailyPrice, Asset).join(Asset, DailyPrice.asset_id == Asset.id)
        if asset_id:
            query = query.filter(DailyPrice.asset_id == asset_id)
        
        prices = query.order_by(DailyPrice.date.desc()).limit(days).all()
        
        return jsonify([{
            'date': price[0].date.isoformat(),
            'asset_symbol': price[1].symbol,
            'open': price[0].open,
            'high': price[0].high,
            'low': price[0].low,
            'close': price[0].close,
            'volume': price[0].volume,
            'adj_close': price[0].adj_close
        } for price in prices])
    finally:
        session.close()

@app.route('/gainers-losers')
@login_required
def gainers_losers():
    """Display top gainers and losers from NSE"""
    nse = Nse()  # Initialize NSE client
    # Look up asset IDs from the database by symbol so we can link to detail pages.
    # NSE returns bare symbols (e.g. KOTAKBANK) but the DB stores them with a
    # .NS suffix (e.g. KOTAKBANK.NS), so try both forms.
    session = get_db_session()
    try:
        gainers_raw = nse.get_top_gainers()[:15]
        losers_raw = nse.get_top_losers()[:15]
        symbols = [s['symbol'] for s in gainers_raw] + [s['symbol'] for s in losers_raw]
        # Try both the bare symbol and the .NS-suffixed form
        variants = []
        for s in symbols:
            variants.append(s)
            if not s.endswith('.NS'):
                variants.append(s + '.NS')
        assets = session.query(Asset).filter(Asset.symbol.in_(variants)).all()
        # Build a lookup that accepts either form
        symbol_to_id = {}
        for a in assets:
            symbol_to_id[a.symbol] = a.id
            if a.symbol.endswith('.NS'):
                symbol_to_id[a.symbol[:-3]] = a.id
    finally:
        session.close()
    
    # Format gainers and losers data for template
    gainers_data = []
    for stock in gainers_raw:
        gainers_data.append({
            'symbol': stock['symbol'],
            'ltp': stock['ltp'],
            'change': stock['net_price'],
            'pChange': stock['perChange'],
            'id': symbol_to_id.get(stock['symbol'])
        })
    
    losers_data = []
    for stock in losers_raw:
        losers_data.append({
            'symbol': stock['symbol'],
            'ltp': stock['ltp'],
            'change': stock['net_price'],
            'pChange': stock['perChange'],
            'id': symbol_to_id.get(stock['symbol'])
        })
    
    return render_template('gainers_losers.html',
        gainers=gainers_data,
        losers=losers_data,
        active='gainers_losers')

@app.route('/search')
@login_required
def search():
    """Search stocks page with autocomplete suggestions."""
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        service = StockSearchService()
        results = service.search_stocks(query, limit=20)
    
    return render_template('search.html',
        query=query,
        results=results,
        active='search')


@app.route('/mutual-funds')
@login_required
def mutual_funds():
    """Display mutual funds with category filtering."""
    # Use mutual fund database session for proper category filtering
    session = get_mutual_fund_session()
    try:
        # Get category filter from request, default to large-cap
        category = request.args.get('category', 'large-cap')
        
        # Build query with category filter
        query = session.query(MutualFundSuggestion, MutualFundAsset)
        query = query.join(MutualFundAsset, MutualFundSuggestion.asset_id == MutualFundAsset.id)
        
        # Apply category filter
        category_underscore = category.replace('-', '_')
        query = query.filter(MutualFundAsset.type == category_underscore)
        
        # Get top 50 by score
        top = query.order_by(MutualFundSuggestion.score.desc()).limit(50).all()
        
        # Prepare data for template - just asset info and suggestion score
        data = []
        for suggestion, asset in top:
            data.append({'asset': asset, 'suggestion': suggestion})
        
        return render_template('mutual_funds.html', assets=data, active='mutual_funds', category=category)
    finally:
        session.close()


@app.route('/top-mutual-funds')
@login_required
def top_mutual_funds():
    """Display top 50 mutual funds by score from stocks.db."""
    session = get_session()
    try:
        # Get top 50 mutual funds by score from stocks.db
        # Mutual funds are stored in the assets table with type='mutual_fund'
        top = (
            session.query(
                Asset,
                Suggestion
            )
            .join(Suggestion, Suggestion.asset_id == Asset.id)
            .filter(Asset.type == 'mutual_fund')
            .order_by(Suggestion.score.desc())
            .limit(50)
            .all()
        )
        
        # Prepare data for template - just asset info and suggestion score
        data = []
        for asset, suggestion in top:
            data.append({
                'asset': asset,
                'suggestion': suggestion
            })
        
        return render_template('top_mutual_funds.html', assets=data, active='top-mutual-funds')
    finally:
        session.close()

# Cache for mutual fund details to avoid repeated API calls
mf_cache = {}
CACHE_DURATION = timedelta(hours=1)  # Cache for 1 hour

def get_mutual_fund_details_from_api(scheme_code):
    """Fetch mutual fund details from API"""
    BASE_URL = "https://api.mfapi.in/mf"
    url = f"{BASE_URL}/{scheme_code}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") != "SUCCESS":
            raise Exception(f"API returned failure: {result}")
        
        meta = result["meta"]
        nav_history = result["data"]
        latest_nav = nav_history[0] if nav_history else None
        
        return {
            "scheme_code": meta.get("scheme_code"),
            "scheme_name": meta.get("scheme_name"),
            "fund_house": meta.get("fund_house"),
            "scheme_type": meta.get("scheme_type"),
            "scheme_category": meta.get("scheme_category"),
            "isin_growth": meta.get("isin_growth"),
            "isin_div_reinvestment": meta.get("isin_div_reinvestment"),
            "latest_nav": latest_nav["nav"] if latest_nav else None,
            "latest_nav_date": latest_nav["date"] if latest_nav else None,
            "nav_history": nav_history
        }
    except Exception as e:
        raise Exception(f"Failed to fetch mutual fund details: {str(e)}")

@app.route('/api/search')
@login_required
def api_search_stocks():
    """API endpoint to search stocks by name or symbol."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify([])
    
    service = StockSearchService()
    results = service.search_stocks(query, limit)
    return jsonify(results)


@app.route('/api/stock-details/<symbol>')
@login_required
def api_stock_details(symbol):
    """API endpoint to get stock details by symbol."""
    service = StockSearchService()
    details = service.get_stock_details(symbol)
    return jsonify(details)


@app.route('/api/stock-history/<symbol>')
@login_required
def api_stock_history(symbol):
    """API endpoint to get stock history by symbol."""
    service = StockSearchService()
    history = service.get_stock_history(symbol)
    return jsonify(history)


@app.route('/mutual-funds/<scheme_code>')
@login_required
def mutual_fund_detail(scheme_code):
    """Display details for a specific mutual fund with caching"""
    # Check cache first
    now = datetime.now()
    if scheme_code in mf_cache:
        cached_data, cached_time = mf_cache[scheme_code]
        if now - cached_time < CACHE_DURATION:
            # Return cached data
            return render_template('mutual_fund_detail.html', 
                                 fund=cached_data, 
                                 active='mutual_funds',
                                 from_cache=True)
    
    # Fetch from API if not in cache or cache expired
    try:
        fund_details = get_mutual_fund_details_from_api(scheme_code)
        # Update cache
        mf_cache[scheme_code] = (fund_details, now)
        
        return render_template('mutual_fund_detail.html', 
                             fund=fund_details, 
                             active='mutual_funds',
                             from_cache=False)
    except Exception as e:
        return f"Error fetching mutual fund details: {str(e)}", 500

@app.route("/stock/<symbol>")
@login_required
def stock_by_symbol(symbol):
    session = get_db_session()
    try:
        cache_symbol = symbol.upper().strip()
        
        # Check cache first (freshness: 1 hour)
        now = datetime.now()
        cached_price_history = None
        if cache_symbol in search_history_cache:
            cached_data, cached_time = search_history_cache[cache_symbol]
            if now - cached_time < SEARCH_HISTORY_CACHE_DURATION:
                cached_price_history = cached_data
        
        # First try exact match in DB
        asset = session.query(Asset).filter(Asset.symbol == symbol).first()
        if not asset and symbol.endswith('.BO'):
            asset = session.query(Asset).filter(Asset.symbol == symbol.replace('.BO', '.NS')).first()
        if not asset and not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            asset = session.query(Asset).filter(Asset.symbol == symbol + ".NS").first()
        
        # CASE 1: Asset found in DB (Nifty 50 or previously stored)
        if asset:
            history_mode = request.args.get('history', 'latest60')
            if history_mode == 'all':
                show_latest_days = None
            else:
                show_latest_days = 60
            
            # Use cache if fresh, otherwise DB
            if cached_price_history is not None:
                price_history = cached_price_history
            else:
                price_history = get_price_history(asset.id, show_latest_days=show_latest_days)
                search_history_cache[cache_symbol] = (price_history, now)
            
            recent_prices = list(reversed(price_history[-10:])) if len(price_history) >= 10 else list(reversed(price_history))
            suggestions = session.query(Suggestion).filter_by(asset_id=asset.id).order_by(Suggestion.date.desc()).limit(5).all()
            return render_template("stock_detail.html", stock=asset, recent_prices=recent_prices, price_history=price_history, suggestions=suggestions, active="stocks", history_mode=history_mode)
        
        # CASE 2: Asset not in DB (non-Nifty 50 stock) - NO DB writes
        history_mode = request.args.get('history', 'latest60')
        from data_sources import YFinanceSource
        yf_source = YFinanceSource()
        
        # Fetch asset info from Yahoo
        ohlcv = yf_source.fetch_latest(symbol)
        name = yf_source.fetch_name(symbol)
        if not ohlcv and (symbol.endswith('.NS') or symbol.endswith('.BO')):
            base_symbol = symbol.replace('.NS', '').replace('.BO', '')
            ohlcv = yf_source.fetch_latest(base_symbol)
            name = yf_source.fetch_name(base_symbol)
            if ohlcv and not name: name = base_symbol
        
        if not ohlcv or not name:
            return "Stock not found or data unavailable", 404
        
        exchange = 'NSE' if symbol.endswith('.NS') or not (symbol.endswith('.NS') or symbol.endswith('.BO')) else 'BSE'
        if symbol.endswith('.BO'): exchange = 'BSE'
        elif symbol.endswith('.NS'): exchange = 'NSE'
        
        # Create transient Asset (not added to session)
        asset = Asset(symbol=symbol, name=name, exchange=exchange, sector='Unknown', type='equity')
        
        # Get price history: cache or Yahoo
        if cached_price_history is not None:
            price_history_data = cached_price_history
        else:
            history_records = yf_source.fetch_history(symbol, limit=60)
            if not history_records and (symbol.endswith('.NS') or symbol.endswith('.BO')):
                base_symbol = symbol.replace('.NS', '').replace('.BO', '')
                history_records = yf_source.fetch_history(base_symbol, limit=60)
            if not history_records: return "No historical data available", 404
            price_history_data = []
            for rec in history_records:
                price_history_data.append(DailyPrice(date=rec.date, open=rec.open, high=rec.high, low=rec.low, close=rec.close, adj_close=rec.adj_close, volume=rec.volume))
            search_history_cache[cache_symbol] = (price_history_data, now)
        
        # Apply history mode
        if history_mode == 'all':
            show_latest_days = None
        else:
            show_latest_days = 60
        
        if show_latest_days is not None and len(price_history_data) > show_latest_days:
            price_history = list(price_history_data[-show_latest_days:])
        else:
            price_history = list(price_history_data)
        
        recent_prices = list(reversed(price_history[-10:])) if len(price_history) >= 10 else list(reversed(price_history))
        suggestions = []
        
        return render_template("stock_detail.html", stock=asset, recent_prices=recent_prices, price_history=price_history, suggestions=suggestions, active="stocks", history_mode=history_mode)
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

