# Graph/UI Chart Implementation Plan

## Library Choice: Chart.js
- Lightweight, pure JavaScript CDN
- Supports line, candlestick, bar, pie charts
- Interactive tooltips, responsive design
- Easy Jinja2 template integration

## Implementation Steps

### Step 1: Add Chart.js CDN to base.html
- Include Chart.js in head section
- Add chart container divs where needed

### Step 2: Modify flask_app.py routes
- `/stocks/<int:asset_id>`: Pass 60 days price data
- `/mutual-funds/<scheme_code>`: Already passes nav_history
- `/suggestions`: Add aggregated score stats

### Step 3: Add charts to templates
- stock_detail.html: Price line chart + volume bar chart
- mutual_fund_detail.html: NAV history line chart
- index.html: Dashboard overview charts
- suggestions.html: Score distribution histogram
- gainers_losers.html: Top gainers/losers bar chart

### Step 4: CSS styling
- Add chart container styles
- Responsive design

## TDD Approach
1. Write tests for data structure
2. Implement chart rendering
3. Verify charts render correctly
4. Test with sample data