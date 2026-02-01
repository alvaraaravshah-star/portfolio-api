# 🌐 Macro Portfolio Engine - Web Version

A simple, usable web interface for the Macro Engine. The website asks users questions and displays personalized portfolio recommendations based on their risk profile and current macro conditions.

## ✨ Live Demo

**The website is running at: http://localhost:5001**

## 🚀 Quick Start

### Option A: Using the Startup Script (Recommended)

```bash
cd /Users/aravshah/Documents/macro\ engine\ -\ interactive\ version/
chmod +x start.sh
./start.sh
```

Then open your browser to: **http://localhost:5001**

### Option B: Manual Setup

```bash
cd /Users/aravshah/Documents/macro\ engine\ -\ interactive\ version/

# Install dependencies
pip install -r requirements.txt

# Run the server
python3 web_app.py
```

Then open: **http://localhost:5001**

## 🎯 How It Works

The website combines all 6 passes of the macro engine in a simple 3-step flow:

### Step 1: User Input (Questionnaire)
- **Investor Type**: Conservative, Balanced, or Aggressive
- **Macro Conditions**: Three sliders to set current market state
  - Inflation Score (-1 to +1)
  - Growth Score (-1 to +1)
  - Liquidity/Macro Score (-1 to +1)

### Step 2: Backend Processing
When you click "Run Portfolio Analysis", the engine:

1. **Pass 4 - Regime Detection**: Converts macro scores into market regimes
   - High Inflation, Weak Growth, Tight Liquidity, etc.
   - Generates factor weights based on what regimes suggest

2. **Pass 5 - Portfolio Scoring**: Selects the best portfolio
   - Scores all candidate portfolios (Defensive, Balanced, Growth)
   - Weighs macro alignment vs. investor preference
   - Returns the recommended portfolio and its factor allocation

3. **Pass 6 - Asset Construction**: Converts factors to investable assets
   - Maps factors (Quality, Value, Momentum) to ETFs
   - Returns concrete allocation percentages for ETFs like VTV, QUAL, MTUM
   - Generates explainability reasoning

### Step 3: Display Results
The website shows:
- 📍 Current market regime (regimes detected, scores)
- 🎯 Recommended portfolio (name, scores, factor breakdown)
- 💼 Asset allocation (specific ETFs and %s)
- 💡 Explanation (why this portfolio makes sense)

## 📁 Project Structure

```
macro engine - interactive version/
├── web_app.py                    # Flask backend API
├── requirements.txt               # Python dependencies
├── start.sh                       # Startup script
├── README.md                      # This file
└── web/
    ├── index.html               # Main page (HTML)
    └── static/
        ├── style.css            # Styling
        └── app.js               # Frontend logic
├── Pass 1 - FETCH/              # Data fetching (not used by web)
├── Pass 2 - Macro State Vector/  # Macro scoring
├── Pass 3 - Dataset Work/        # Historical analysis
├── Pass 4 - Regime Mapping/      # Regime detection
├── Pass 5 - Portfolio Scoring/   # Portfolio selection
└── Pass 6 - Portfolio Construction/  # Asset allocation
```

## 🔧 API Endpoints

### `GET /api/config`
Returns available investor types, portfolio types, and factors
```json
{
  "investor_types": ["Conservative", "Balanced", "Aggressive"],
  "portfolio_types": ["Defensive Portfolio", "Balanced Portfolio", "Growth Portfolio"],
  "factors": ["Value", "Quality", "Momentum"]
}
```

### `POST /api/run-engine`
Runs the full pipeline and returns results

**Request:**
```json
{
  "investor_type": "Conservative",
  "macro_conditions": {
    "inflation_score": 0.5,
    "growth_score": -0.2,
    "macro_score": 0.1
  }
}
```

**Response:**
```json
{
  "status": "success",
  "pass4_output": {
    "macro_state": { ... },
    "active_regimes": ["Tight_Liquidity"],
    "factor_weights": { "Value": 0.2, "Quality": 0.5, "Momentum": 0.3 }
  },
  "pass5_output": {
    "investor_type": "Conservative",
    "selected_portfolio": "Defensive Portfolio",
    "portfolio_score": 0.85,
    "macro_score": 0.92,
    "investor_score": 0.78
  },
  "pass6_output": {
    "asset_allocation": {
      "QUAL": 0.35,
      "VTV": 0.40,
      "MTUM": 0.25
    },
    "factor_to_etf_mapping": {
      "Quality": "QUAL",
      "Value": "VTV",
      "Momentum": "MTUM"
    }
  }
}
```

### `GET /api/get-latest-macro`
Gets the most recent macro state from saved data

## 🎨 Features

- ✅ **Simple & Clean UI**: Questionnaire → Results flow
- ✅ **Interactive Sliders**: Adjust macro conditions in real-time
- ✅ **Responsive Design**: Works on desktop, tablet, mobile
- ✅ **No Data Storage**: Test usability without database
- ✅ **Full Explainability**: Shows the "why" at each step
- ✅ **Live ETF Allocation**: Concrete investment recommendations
- ✅ **Running Live**: Already started at http://localhost:5001

## 🧪 Test Scenarios

Try these to test different paths:

### Scenario 1: Conservative Investor, Normal Times
- Investor Type: **Conservative**
- Inflation Score: **0.0**
- Growth Score: **0.0**
- Macro Score: **0.0**
- **Result**: Defensive portfolio with heavy quality emphasis

### Scenario 2: Aggressive Investor, High Growth
- Investor Type: **Aggressive**
- Inflation Score: **0.5**
- Growth Score: **0.5**
- Macro Score: **0.2**
- **Result**: Growth portfolio with momentum emphasis

### Scenario 3: Balanced Investor, Tight Liquidity
- Investor Type: **Balanced**
- Inflation Score: **-0.3**
- Growth Score: **-0.5**
- Macro Score: **-0.7**
- **Result**: Quality-focused defensive portfolio

### Scenario 4: Aggressive Investor, High Inflation
- Investor Type: **Aggressive**
- Inflation Score: **-0.8** (high inflation)
- Growth Score: **0.2**
- Macro Score: **0.3**
- **Result**: Value-focused portfolio with momentum

## 📊 Customization

To modify the engine behavior, edit:
- **Investor profiles**: [Pass 5 - Portfolio Scoring/investor_profiles.json](Pass%205%20-%20Portfolio%20Scoring/investor_profiles.json)
- **Candidate portfolios**: [Pass 5 - Portfolio Scoring/candidate_portfolios.json](Pass%205%20-%20Portfolio%20Scoring/candidate_portfolios.json)
- **Asset universe**: [Pass 6 - Portfolio Construction/asset_universe.json](Pass%206%20-%20Portfolio%20Construction/asset_universe.json)
- **Regime rules**: Edit [Pass 4 - Regime Mapping/outputs/pass4_regime_mapper.py](Pass%204%20-%20Regime%20Mapping/outputs/pass4_regime_mapper.py)

## 📱 Usability Testing

The website is designed for simple usability testing:

1. **Zero Complexity**: Just select investor type and adjust 3 sliders
2. **Instant Feedback**: Click one button to get full recommendations
3. **Clear Output**: Results shown in easy-to-understand sections
4. **No Login**: Works immediately without authentication
5. **No Data Saved**: Each session is independent (perfect for testing)

## ⚠️ Known Limitations

- No historical data persistence (results are computed on-the-fly)
- Macro conditions are manually entered sliders (not pulling live data)
- No backtesting or performance metrics
- Simple regime detection (not ML-based)
- Single-threaded development server (not for production)

## 🚀 Future Enhancements

- [ ] Pull live macro data from FRED API
- [ ] Add historical portfolio performance charts
- [ ] Multi-factor optimization
- [ ] Backtesting engine
- [ ] User accounts and favorites
- [ ] Mobile app version
- [ ] WebSocket real-time updates
- [ ] Export recommendations as PDF

## 🛑 Stopping the Server

Press **Ctrl+C** in the terminal where the server is running.

## 📝 License

Internal use only.
