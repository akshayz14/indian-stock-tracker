// Demo data for Indian Stock Tracker
// TODO: Replace with real data sources when available
window.DEMO_DATA = {
  indices: [
    { name: "NIFTY 50", value: 24847.30, change: 124.50, changePct: 0.50 },
    { name: "NIFTY BANK", value: 52341.20, change: -89.30, changePct: -0.17 },
    { name: "NIFTY IT", value: 36892.10, change: 234.60, changePct: 0.64 },
    { name: "SENSEX", value: 82156.80, change: -45.20, changePct: -0.05 }
  ],

  stocks: [
    { symbol: "RELIANCE", name: "Reliance Industries", price: 2847.35, change: 42.15, changePct: 1.50, volume: "12.4M", mktCap: "19.2L Cr", pe: 24.8, pb: 2.3, div: 0.4, week52H: 3024.90, week52L: 2220.30, sector: "Energy", exchange: "NSE", recommendation: "Buy", target: 3200 },
    { symbol: "TCS", name: "Tata Consultancy Services", price: 3912.60, change: -28.40, changePct: -0.72, volume: "3.1M", mktCap: "14.2L Cr", pe: 31.4, pb: 13.2, div: 1.6, week52H: 4256.00, week52L: 3400.10, sector: "IT", exchange: "NSE", recommendation: "Hold", target: 4100 },
    { symbol: "HDFCBANK", name: "HDFC Bank", price: 1724.80, change: 18.95, changePct: 1.11, volume: "8.7M", mktCap: "13.1L Cr", pe: 19.2, pb: 2.8, div: 1.2, week52H: 1880.00, week52L: 1363.55, sector: "Banking", exchange: "NSE", recommendation: "Buy", target: 1950 },
    { symbol: "INFY", name: "Infosys", price: 1847.25, change: -14.70, changePct: -0.79, volume: "4.2M", mktCap: "7.7L Cr", pe: 28.6, pb: 8.4, div: 2.1, week52H: 2082.40, week52L: 1358.35, sector: "IT", exchange: "NSE", recommendation: "Hold", target: 1920 },
    { symbol: "ICICIBANK", name: "ICICI Bank", price: 1312.45, change: 22.30, changePct: 1.73, volume: "9.8M", mktCap: "9.2L Cr", pe: 17.8, pb: 2.6, div: 0.8, week52H: 1388.55, week52L: 1006.70, sector: "Banking", exchange: "NSE", recommendation: "Buy", target: 1550 },
    { symbol: "HINDUNILVR", name: "Hindustan Unilever", price: 2398.10, change: -31.55, changePct: -1.30, volume: "1.8M", mktCap: "5.6L Cr", pe: 56.2, pb: 12.1, div: 1.9, week52H: 2700.00, week52L: 2172.00, sector: "FMCG", exchange: "NSE", recommendation: "Sell", target: 2200 }
  ],

  sectors: [
    { name: "Banking", pct: 1.24 },
    { name: "IT", pct: -0.91 },
    { name: "FMCG", pct: -0.48 },
    { name: "Auto", pct: 0.34 },
    { name: "Energy", pct: 1.50 },
    { name: "Pharma", pct: 1.12 }
  ],

  gainers: [
    { symbol: "BAJFINANCE", name: "Bajaj Finance", price: 7248.15, changePct: 2.21 },
    { symbol: "BHARTIARTL", name: "Bharti Airtel", price: 1623.45, changePct: 2.02 },
    { symbol: "SUNPHARMA", name: "Sun Pharmaceutical", price: 1682.45, changePct: 1.75 }
  ],

  losers: [
    { symbol: "WIPRO", name: "Wipro", price: 547.80, changePct: -1.47 },
    { symbol: "TATAMOTORS", name: "Tata Motors", price: 985.40, changePct: -1.52 },
    { symbol: "BPCL", name: "Bharat Petroleum", price: 628.70, changePct: -1.32 }
  ],

  watchlist: [
    { symbol: "RELIANCE", name: "Reliance Industries", sector: "Energy", price: 2847.35, changePct: 1.50 },
    { symbol: "TCS", name: "Tata Consultancy Services", sector: "IT", price: 3912.60, changePct: -0.72 },
    { symbol: "HDFCBANK", name: "HDFC Bank", sector: "Banking", price: 1724.80, changePct: 1.11 },
    { symbol: "INFY", name: "Infosys", sector: "IT", price: 1847.25, changePct: -0.79 }
  ],

  funds: [
    { scheme_name: "HDFC Top 100 Fund", scheme_code: "HDFC_T100", fund_house: "HDFC Mutual Fund", category: "Large Cap", type: "Equity", nav: 845.67, nav_change: 12.34, nav_changePct: 1.48, score: 0.8745 }
  ]
};