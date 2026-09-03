# Landing Page Redesign Design Spec

## Overview

Redesign the entire Indian Stock Tracker web UI to match the visual language and layout of the Figma "Fintech Stock-Analysis Dashboard" reference. This redesign covers all pages (Dashboard, Stocks, Mutual Funds, etc.) with a modern, professional fintech aesthetic including dark/light theme switching.

## Goals

- Modernize the UI to match the Figma reference design
- Implement dark/light theme toggle
- Improve information density and visual hierarchy
- Make the app feel like a professional trading/research terminal
- Use demo data for now, with the data shape ready for real data integration later

## Non-Goals

- Migrating to React/frontend framework (keeping Flask + Jinja2)
- Building real data pipelines (using demo data)
- Adding authentication or user accounts
- Mobile-specific layouts (responsive improvements are in-scope but desktop-first)
- Adding new features beyond the Figma reference

## User Experience

### Target User
Individual retail investors in India who want a clean, data-dense research interface for NSE/BSE stocks and mutual funds.

### Primary Use Cases
1. **Dashboard view**: Get market overview at a glance (indices, top movers, sector performance)
2. **Stock research**: Browse stock cards by index (Nifty 50, Bank, IT, Sensex), view stock details
3. **Watch list**: Quick access to tracked stocks
4. **Mutual funds**: Browse and research mutual funds
5. **Theme preference**: Switch between light and dark mode based on preference/time of day

## Design System

### Color Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | `#f0f4f8` | `#090c14` | Page background |
| `--foreground` | `#0d1117` | `#e8edf5` | Primary text |
| `--card` | `#ffffff` | `#111827` | Card backgrounds |
| `--card-foreground` | `#0d1117` | `#e8edf5` | Card text |
| `--primary` | `#2563eb` | `#3b82f6` | Primary actions, brand |
| `--primary-foreground` | `#ffffff` | `#ffffff` | Text on primary |
| `--secondary` | `#e8edf3` | `#1a2235` | Secondary buttons |
| `--muted` | `#eef2f7` | `#141c2e` | Muted backgrounds |
| `--muted-foreground` | `#6b7280` | `#64748b` | Secondary text |
| `--border` | `rgba(0,0,0,0.08)` | `rgba(255,255,255,0.07)` | Borders |
| `--up` | `#16a34a` | `#22c55e` | Positive change |
| `--down` | `#dc2626` | `#ef4444` | Negative change |
| `--radius` | `10px` | `10px` | Border radius |

### Typography
- **Body font**: `DM Sans` (Google Fonts) — 300, 400, 500, 600, 700
- **Monospace font**: `JetBrains Mono` (Google Fonts) — 400, 500, 600 — for numbers, prices
- **Sizes**: 10px (micro), 12px (small), 14px (base), 16px (lg), 20px (2xl)

### Spacing & Layout
- Border radius: 10px (default), 8px (small), 12px (large)
- Card padding: 16px–20px
- Max content width: 1600px
- Grid gap: 16px–24px


## Architecture

### Technology Stack
- **Backend**: Flask + Jinja2 (existing, unchanged)
- **Styling**: Tailwind CSS v4 via CDN + custom CSS variables for theme tokens
- **Charts**: Chart.js (existing)
- **Icons**: Lucide icons via CDN
- **Fonts**: Google Fonts (DM Sans, JetBrains Mono)
- **JavaScript**: Vanilla JS for theme toggle and minor interactions
- **No build step required** — all CSS/JS via CDN

### File Structure
```
templates/: base.html, index.html, stocks.html, stock_detail.html, prices.html, suggestions.html, gainers_losers.html, mutual_funds.html, mutual_fund_detail.html, top_mutual_funds.html, search.html, error.html
static/: style.css (rewritten), demo_data.js (new), chart-helpers.js (new)
flask_app.py: Minor updates for demo data and theme context
```

### Theme System
- CSS custom properties on `:root` (light) and `.dark` (dark)
- Toggle in TopNav adds/removes `.dark` class on `<html>`
- Preference in `localStorage` key `theme`
- All colors via `var(--token)`

### Demo Data Module
- File: `static/demo_data.js` exports `window.DEMO_DATA`
- Stocks (50+ Indian stocks), indices (Nifty 50, Bank, IT, Sensex), sectors, gainers, losers, watchlist, funds
- Data shape mirrors real API responses (ready for future integration)
## Features

### F1: Top Navigation Bar (all pages)
- Logo "StockTracker" with colored dot
- Nav links: Dashboard, Stocks, Prices, Suggestions, Gainers & Losers, Mutual Funds, Search
- Global search bar (right-aligned)
- Theme toggle (sun/moon icon, Lucide)
- User avatar placeholder
- Sticky positioning, subtle border-bottom, light shadow

### F2: Sidebar (all pages)
- Two sections: "Explore" and "Data"
- Explore: Dashboard, Stocks, Prices, Suggestions, Gainers & Losers, Mutual Funds
- Data: API endpoints
- Active state: primary background, white text
- Hover: muted background
- Width: 220px, sticky positioning

### F3: Dashboard Page (`/`)
- **Stat cards row**: Tracked Stocks, Price Records, Suggestions, Latest Data
- **Price chart card**: Area chart with timeframe selector (1D, 1W, 1M, 3M, 1Y), gradient fill
- **Watch list card**: 4–5 stocks with price + change %
- **Stock grid sections**: Nifty 50, Nifty Bank, Nifty IT, Sensex — each as a card grid (4 columns) showing top stocks with: symbol, name, price, change %, recommendation badge
- **Sector performance**: Horizontal row of sector chips, color-coded by performance
- **Top gainers & losers**: Two-column layout, top 5 each
- **Footer**: Data timestamp, copyright

### F4: Stock Detail Page (`/stocks/<symbol>`)
- Large stock header: symbol, name, current price, recommendation badge
- Stats grid: Open, High, Low, Volume, Mkt Cap, P/E, P/B, Dividend, 52W High, 52W Low, Sector, Exchange
- Price chart (line/area)
- Recommendation target shown

### F5: Theme Toggle
- Sun/moon icon button in TopNav
## Components

### Reusable Component Classes (in `static/style.css`)
- `.topnav` — Top navigation bar
- `.sidebar` — Left sidebar
- `.content` — Main content wrapper
- `.card` — Bordered card container
- `.stat` — Stat card (label + value)
- `.btn`, `.btn-secondary` — Buttons
- `.stock-card` — Stock grid card
- `.rec-badge` — Recommendation badge (Buy/Hold/Sell)
- `.change-chip` — Price change indicator (green/red)
- `.sector-chip` — Sector performance chip
- `.data-table` — Table styling
- `.page-head` — Page title + subtitle

## Data Model

### Demo Stock Object
```js
{ symbol: "RELIANCE", name: "Reliance Industries", price: 2847.35, change: 42.15, changePct: 1.50, volume: "12.4M", mktCap: "19.2L Cr", pe: 24.8, pb: 2.3, div: 0.4, week52H: 3024.90, week52L: 2220.30, sector: "Energy", exchange: "NSE", recommendation: "Buy", target: 3200 }
```

### Index Object
```js
{ name: "NIFTY 50", value: 24847.30, change: 124.50, changePct: 0.50 }
```

### Sector Object
```js
{ name: "Banking", pct: 1.24 }
```

## Technical Decisions
1. **CDN-based Tailwind** over build-step: Simpler, no tooling changes
2. **CSS variables for theming** over Tailwind dark: More explicit, works without JIT
3. **Keep Chart.js**: Already integrated
4. **Demo data in JS, not Flask**: Easier to swap later
5. **Lucide icons**: Used in Figma reference
6. **localStorage for theme**: Standard pattern

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Tailwind CDN slower than build-time | Acceptable for prototype |
| Demo data doesn't match real structure | Design objects to mirror API responses |
| Theme flash on page load | Inline script in `<head>` reads localStorage before paint |
| Flask routes/data passing breaks | Keep existing route signatures |

## Open Questions
None — all design decisions confirmed with user.

## Next Steps
1. Write implementation plan using `writing-plans` skill
2. Implement files: base.html → style.css → index.html → other pages
3. Add demo_data.js
4. Test in browser, verify theme toggle, verify all pages render
- Click toggles `.dark` class on `<html>`
- Persists to `localStorage` key `theme`
- On page load, reads `localStorage` and applies theme before render (no flash)

### F6: Demo Data Display
- All stock grids, cards, and lists populated from `demo_data.js`
- Realistic Indian stock names (RELIANCE, TCS, HDFCBANK, etc.)
- Realistic price ranges and change values
- Static for now; structured to mirror real API responses
- Tagged: `// TODO: Replace with real data source when available`
- Page padding: 20px horizontal