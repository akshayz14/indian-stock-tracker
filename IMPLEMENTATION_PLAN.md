# Graph/UI Chart Implementation Plan

**Status**: Completed (2026-08-30) → Enhanced (2026-09-03 with Landing Page Redesign)
**Related Spec**: `docs/superpowers/specs/2026-09-01-landing-page-redesign-design.md`

## Library Choice: Chart.js
- Lightweight, pure JavaScript CDN
- Supports line, candlestick, bar, pie charts
- Interactive tooltips, responsive design
- Easy Jinja2 template integration
- Works alongside Tailwind CSS v4 (CDN) for modern fintech look

## Implementation Steps

### Step 1: Add Chart.js CDN to base.html [DONE]
- Include Chart.js in head section
- Add chart container divs where needed
- Add Tailwind CSS v4 + Lucide icons CDN
- Add theme toggle with localStorage persistence

### Step 2: Modify flask_app.py routes
- `/stocks/<int:asset_id>`: Pass 60 days price data [DONE]
- `/mutual-funds/<scheme_code>`: Already passes nav_history [DONE]
- `/suggestions`: Add aggregated score stats [DONE]
- `/`: Dashboard passes demo_data context [DONE]
- `/gainers-losers`: Top gainers/losers [DONE]

### Step 3: Add charts to templates
- stock_detail.html: Price line chart + volume bar chart [DONE]
  - AutoSkip disabled when <= 30 data points (last tick always visible)
- mutual_fund_detail.html: NAV history line chart [DONE]
- index.html: Dashboard overview charts (market performance, top gainers, sector) [DONE]
- suggestions.html: Score distribution histogram [DONE]
- gainers_losers.html: Top gainers/losers bar chart [DONE]

### Step 4: CSS styling [DONE]
- Add chart container styles
- Responsive design
- Theme-aware colors (light/dark mode)
- Design tokens for consistency (cards, buttons, badges)

## TDD Approach
1. Write tests for data structure
2. Implement chart rendering
3. Verify charts render correctly
4. Test with sample data

## Demo Data Integration
- `static/demo_data.js` provides structured data mirroring real API response shape
- All stock grids, cards, and lists populated from demo data
- Tagged: `// TODO: Replace with real data source when available`
- Realistic Indian stock names (RELIANCE, TCS, HDFCBANK, etc.)

## Theme Toggle
- Sun/moon button in TopNav
- Toggles `.dark` class on `<html>`
- Persists to `localStorage` key `theme`
- Inline script in `<head>` reads localStorage before paint (no flash)

## Pages with Charts
| Page | Charts |
|------|--------|
| `/` (Dashboard) | Market performance area chart, top gainers/losers bars, sector chips |
| `/stocks/<id>` | Price line + volume bar |
| `/mutual-funds/<code>` | NAV history line |
| `/suggestions` | Score distribution histogram |
| `/gainers-losers` | Top gainers/losers horizontal bars |

## Dependencies Added
- Tailwind CSS v4 (CDN)
- Lucide icons (CDN)
- Chart.js (CDN)
- Google Fonts: DM Sans, JetBrains Mono

## Date
- Initial Plan: 2026-08-27
- Last Updated: 2026-09-03 (Landing Page Redesign)