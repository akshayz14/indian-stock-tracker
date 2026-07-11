from flask import Flask, render_template, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Stock, DailyPrice, Suggestion, get_session
import datetime
from functools import wraps

app = Flask(__name__)

def get_db_session():
    """Get a database session"""
    return get_session()

def login_required(f):
    """Decorator to ensure database is accessible"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            session = get_db_session()
            # Test connection
            session.execute(text("SELECT 1"))
            session.close()
            return f(*args, **kwargs)
        except Exception as e:
            return f"Database connection error: {str(e)}", 500
    return decorated_function

@app.route('/')
@login_required
def index():
    """Main dashboard showing overview of database"""
    session = get_db_session()
    try:
        stats = {
            'total_stocks': session.query(Stock).count(),
            'total_prices': session.query(DailyPrice).count(),
            'total_suggestions': session.query(Suggestion).count(),
            'latest_date': session.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()[0] if session.query(DailyPrice).first() else None
        }
        return render_template('index.html', stats=stats)
    finally:
        session.close()

@app.route('/stocks')
@login_required
def stocks():
    """Display all stocks"""
    session = get_db_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        stocks_query = session.query(Stock)
        total = stocks_query.count()
        stocks = stocks_query.order_by(Stock.symbol).offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('stocks.html', 
                             stocks=stocks, 
                             page=page, 
                             per_page=per_page,
                             total=total,
                             has_next=page * per_page < total,
                             has_prev=page > 1)
    finally:
        session.close()

@app.route('/stocks/<int:stock_id>')
@login_required
def stock_detail(stock_id):
    """Display details for a specific stock"""
    session = get_db_session()
    try:
        stock = session.query(Stock).get(stock_id)
        if not stock:
            return "Stock not found", 404
            
        # Get recent prices
        recent_prices = session.query(DailyPrice).filter_by(stock_id=stock_id).order_by(DailyPrice.date.desc()).limit(10).all()
        
        # Get suggestions for this stock
        suggestions = session.query(Suggestion).filter_by(stock_id=stock_id).order_by(Suggestion.date.desc()).limit(5).all()
        
        return render_template('stock_detail.html', 
                             stock=stock, 
                             recent_prices=recent_prices,
                             suggestions=suggestions)
    finally:
        session.close()

@app.route('/prices')
@login_required
def prices():
    """Display daily prices with filtering"""
    session = get_db_session()
    try:
        # Get filter parameters
        stock_id = request.args.get('stock_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = session.query(DailyPrice, Stock).join(Stock, DailyPrice.stock_id == Stock.id)
        
        if stock_id:
            query = query.filter(DailyPrice.stock_id == stock_id)
        if start_date:
            query = query.filter(DailyPrice.date >= datetime.datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(DailyPrice.date <= datetime.datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Get all stocks for filter dropdown
        stocks = session.query(Stock).order_by(Stock.symbol).all()
        
        # Paginate
        page = request.args.get('page', 1, type=int)
        per_page = 20
        total = query.count()
        prices = query.order_by(DailyPrice.date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('prices.html',
                             prices=prices,
                             stocks=stocks,
                             page=page,
                             per_page=per_page,
                             total=total,
                             has_next=page * per_page < total,
                             has_prev=page > 1,
                             start_date=start_date,
                             end_date=end_date)
    finally:
        session.close()

@app.route('/suggestions')
@login_required
def suggestions():
    """Display suggestions with filtering"""
    session = get_db_session()
    try:
        # Get filter parameters
        stock_id = request.args.get('stock_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = session.query(Suggestion, Stock).join(Stock, Suggestion.stock_id == Stock.id)
        
        if stock_id:
            query = query.filter(Suggestion.stock_id == stock_id)
        if start_date:
            query = query.filter(Suggestion.date >= datetime.datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Suggestion.date <= datetime.datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Get all stocks for filter dropdown
        stocks = session.query(Stock).order_by(Stock.symbol).all()
        
        # Paginate
        page = request.args.get('page', 1, type=int)
        per_page = 20
        total = query.count()
        suggestions = query.order_by(Suggestion.date.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return render_template('suggestions.html',
                             suggestions=suggestions,
                             stocks=stocks,
                             page=page,
                             per_page=per_page,
                             total=total,
                             has_next=page * per_page < total,
                             has_prev=page > 1,
                             start_date=start_date,
                             end_date=end_date)
    finally:
        session.close()

@app.route('/api/stocks')
@login_required
def api_stocks():
    """API endpoint to get stocks as JSON"""
    session = get_db_session()
    try:
        stocks = session.query(Stock).order_by(Stock.symbol).all()
        return jsonify([{
            'id': stock.id,
            'symbol': stock.symbol,
            'name': stock.name,
            'exchange': stock.exchange,
            'sector': stock.sector
        } for stock in stocks])
    finally:
        session.close()

@app.route('/api/prices')
@login_required
def api_prices():
    """API endpoint to get prices as JSON"""
    session = get_db_session()
    try:
        stock_id = request.args.get('stock_id', type=int)
        days = request.args.get('days', type=int, default=30)
        
        query = session.query(DailyPrice, Stock).join(Stock, DailyPrice.stock_id == Stock.id)
        if stock_id:
            query = query.filter(DailyPrice.stock_id == stock_id)
        
        prices = query.order_by(DailyPrice.date.desc()).limit(days).all()
        
        return jsonify([{
            'date': price[0].date.isoformat(),
            'stock_symbol': price[1].symbol,
            'open': price[0].open,
            'high': price[0].high,
            'low': price[0].low,
            'close': price[0].close,
            'volume': price[0].volume,
            'adj_close': price[0].adj_close
        } for price in prices])
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
