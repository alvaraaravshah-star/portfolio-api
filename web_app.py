"""
Macro Engine Web App
Simple Flask backend to expose the macro engine as an API
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Setup path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "Pass 4 - Regime Mapping" / "outputs"))
sys.path.insert(0, str(BASE_DIR / "Pass 5 - Portfolio Scoring"))
sys.path.insert(0, str(BASE_DIR / "Pass 6 - Portfolio Construction"))

from pass4_regime_mapper import load_macro_state, detect_active_regimes, load_regime_factor_map, ACTIVE_FACTORS
import pass5_portfolioscorer as p5
import pass6_portfolio_constructor as p6

app = Flask(__name__, template_folder='web', static_folder='web/static')
CORS(app)

# Load configuration once
INVESTOR_PROFILES = p5.load_investor_profiles()
CANDIDATE_PORTFOLIOS = p5.load_candidate_portfolios()
ASSET_UNIVERSE = p6.load_asset_universe()
PORTFOLIO_BLUEPRINTS = p6.load_portfolio_blueprints()

def get_macro_factor_weights(active_regimes):
    """Generate factor weights based on active regimes."""
    regime_factor_map, _ = load_regime_factor_map()
    
    # Initialize all factors to neutral weight
    factor_weights = {factor: 0.0 for factor in ACTIVE_FACTORS}
    
    # If neutral, equal weight
    if active_regimes == ["Neutral"]:
        equal_weight = 1.0 / len(ACTIVE_FACTORS)
        for factor in ACTIVE_FACTORS:
            factor_weights[factor] = equal_weight
    else:
        # Accumulate weights from active regimes
        regime_factor_count = {}
        for regime in active_regimes:
            factor = regime_factor_map.get(regime, "Quality")
            regime_factor_count[factor] = regime_factor_count.get(factor, 0) + 1
        
        # Distribute weight
        total_regimes = len(active_regimes)
        for factor in ACTIVE_FACTORS:
            factor_weights[factor] = regime_factor_count.get(factor, 0) / total_regimes
    
    return factor_weights

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Return configuration (dates, investor types, portfolio options, etc)."""
    # available_dates are in YYYY-DD-MM format; frontend will convert to iso (YYYY-MM-DD)
    available_dates = p5.get_available_dates()
    return jsonify({
        "available_dates": available_dates,
        "investor_types": list(INVESTOR_PROFILES.keys()),
        "portfolio_types": list(CANDIDATE_PORTFOLIOS.keys()),
        "factors": ACTIVE_FACTORS
    })

@app.route('/api/run-engine', methods=['POST'])
def run_engine():
    """
    Run the full macro engine pipeline.
    
    Input JSON:
    {
        "target_date": "2020-31-03",
        "investor_type": "Conservative"
    }
    """
    try:
        data = request.json
        
        # Extract inputs
        target_date = data.get("target_date")
        investor_type = data.get("investor_type")
        
        # Validate
        if not target_date:
            return jsonify({"error": "Missing target_date"}), 400
        if not investor_type or investor_type not in INVESTOR_PROFILES:
            return jsonify({"error": "Invalid investor type"}), 400
        
        # Get macro conditions for the target date
        macro_conditions = p5.get_macro_conditions_for_date(target_date)
        
        # Create macro state from date-based conditions
        macro_state = {
            "DATE": macro_conditions['date_used'],
            "Inflation_Score": macro_conditions.get("inflation_score", 0.0),
            "Growth_Score": macro_conditions.get("growth_score", 0.0),
            "Macro_Score": macro_conditions.get("macro_score", 0.0)
        }
        
        # PASS 4: Detect regimes
        active_regimes, regime_strength = detect_active_regimes(macro_state)
        macro_factor_weights = get_macro_factor_weights(active_regimes)
        
        # PASS 5: Score portfolios and select best
        investor_profile = INVESTOR_PROFILES[investor_type]
        portfolio_scores = {}
        
        for portfolio_name, portfolio_allocation in CANDIDATE_PORTFOLIOS.items():
            final_score, macro_score, investor_score = p5.final_portfolio_score(
                portfolio_allocation,
                macro_factor_weights,
                investor_profile
            )
            portfolio_scores[portfolio_name] = {
                "final_score": final_score,
                "macro_score": macro_score,
                "investor_score": investor_score,
                "allocation": portfolio_allocation
            }
        
        # Select best portfolio
        best_portfolio_name = max(portfolio_scores.keys(), key=lambda k: portfolio_scores[k]["final_score"])
        best_portfolio_allocation = CANDIDATE_PORTFOLIOS[best_portfolio_name]
        
        # PASS 6: Construct asset-level allocation
        asset_allocation, factor_to_etf = p6.construct_asset_allocation(
            best_portfolio_allocation,
            ASSET_UNIVERSE
        )
        
        # Generate explainability
        explainability_rule = p6.generate_explainability_rule(
            best_portfolio_allocation,
            factor_to_etf
        )
        
        return jsonify({
            "status": "success",
            "pass4_output": {
                "macro_state": macro_state,
                "active_regimes": active_regimes,
                "regime_strength": regime_strength,
                "factor_weights": macro_factor_weights
            },
            "pass5_output": {
                "investor_type": investor_type,
                "selected_portfolio": best_portfolio_name,
                "portfolio_score": portfolio_scores[best_portfolio_name]["final_score"],
                "macro_score": portfolio_scores[best_portfolio_name]["macro_score"],
                "investor_score": portfolio_scores[best_portfolio_name]["investor_score"],
                "all_portfolios": portfolio_scores,
                "factor_allocation": best_portfolio_allocation
            },
            "pass6_output": {
                "recommended_portfolio": best_portfolio_name,
                "asset_allocation": asset_allocation,
                "factor_to_etf_mapping": factor_to_etf,
                "explainability_rule": explainability_rule
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-latest-macro', methods=['GET'])
def get_latest_macro():
    """Get the latest macro state from saved data."""
    try:
        macro_state = load_macro_state()
        active_regimes, regime_strength = detect_active_regimes(macro_state)
        
        return jsonify({
            "macro_state": macro_state,
            "active_regimes": active_regimes,
            "regime_strength": regime_strength
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
