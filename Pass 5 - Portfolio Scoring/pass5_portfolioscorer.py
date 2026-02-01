import json
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

PASS4_OUTPUT = BASE_DIR / "Pass 4 - Regime Mapping" / "outputs" / "factor_tilt_latest.json"
MACRO_DATA_PATH = BASE_DIR / "Pass 2 - Macro State Vector" / "macro_data.csv"

def load_macro_factor_weights():
    with open(PASS4_OUTPUT, "r") as f:
        data = json.load(f)
    return data["factor_weights"], data["active_regimes"]

def load_macro_data():
    """Load macro data CSV and return as DataFrame."""
    df = pd.read_csv(str(MACRO_DATA_PATH))
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df

def get_available_dates():
    """Get list of available dates from macro data."""
    df = load_macro_data()
    dates = sorted(df['DATE'].dt.strftime('%Y-%m-%d').tolist())
    return dates

def get_macro_conditions_for_date(target_date):
    """
    Look up macro conditions for a specific date and return normalized scores.
    Returns dict with inflation_score, growth_score, macro_score.
    """
    df = load_macro_data()
    target_date = pd.to_datetime(target_date)
    
    # Find closest date in data
    df['date_diff'] = (df['DATE'] - target_date).abs()
    closest_row = df.loc[df['date_diff'].idxmin()]
    
    # Normalize macro indicators to -1 to 1 scale
    # Higher CPI = higher inflation (more negative score)
    inflation_score = -1.0 if closest_row['CPI'] > 210 else (0.0 if closest_row['CPI'] > 180 else 0.5)
    
    # Higher unemployment or lower GDP growth = more negative growth score
    growth_score = -1.0 if closest_row.get('UnemploymentRate', 5) > 7 else (0.5 if closest_row.get('UnemploymentRate', 5) < 4 else 0.0)
    
    # VIX as proxy for liquidity (higher VIX = tighter liquidity = more negative)
    vix = closest_row.get('VIX', 20)
    macro_score = -1.0 if vix > 30 else (0.5 if vix < 15 else 0.0)
    
    return {
        "inflation_score": inflation_score,
        "growth_score": growth_score,
        "macro_score": macro_score,
        "date_used": closest_row['DATE'].strftime("%Y-%m-%d")
    }

def prompt_target_date(available_dates):
    """Prompt user to select a target date."""
    print("\n" + "="*50)
    print("SELECT TARGET DATE")
    print("="*50)
    print("\nAvailable dates range from:")
    print(f"  {available_dates[0]} to {available_dates[-1]}")
    print("\nEnter a date (YYYY-MM-DD):")
    
    while True:
        date_input = input("Target date: ").strip()
        
        # Check if date exists in data
        if date_input in available_dates:
            return date_input
        
        # Try to find closest match
        try:
            input_date = pd.to_datetime(date_input)
            closest = min(available_dates, key=lambda d: abs((pd.to_datetime(d) - input_date).days))
            print(f"Date not found. Closest available: {closest}")
            confirm = input("Use this date? (y/n): ").strip().lower()
            if confirm == 'y':
                return closest
        except:
            pass
        
        print(f"Invalid date. Please use format YYYY-MM-DD.\n")

def get_timestamp():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def load_investor_profiles():
    path = Path(__file__).parent / "investor_profiles.json"
    with open(path, "r") as f:
        return json.load(f)

def load_candidate_portfolios():
    path = Path(__file__).parent / "candidate_portfolios.json"
    with open(path, "r") as f:
        return json.load(f)

def prompt_investor_type(available_types):
    """Prompt user to select an investor type."""
    print("\n" + "="*50)
    print("PORTFOLIO RECOMMENDATION SYSTEM")
    print("="*50)
    print("\nAvailable Investor Types:")
    for i, inv_type in enumerate(available_types, 1):
        print(f"  {i}. {inv_type}")
    print()
    
    while True:
        choice = input("Select investor type (enter number or name): ").strip()
        
        # Try to match by number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_types):
                return available_types[idx]
        
        # Try to match by name (case-insensitive)
        for inv_type in available_types:
            if choice.lower() == inv_type.lower():
                return inv_type
        
        print(f"Invalid selection. Please choose 1-{len(available_types)} or enter a valid name.\n")

def macro_alignment_score(portfolio, macro_weights):
    score = 0.0
    for factor, weight in portfolio.items():
        score += weight * macro_weights.get(factor, 0)
    return min(score, 1.0)

def investor_alignment_score(portfolio, preferred_factors):
    score = 0.0
    for factor in preferred_factors:
        score += portfolio.get(factor, 0)
    return min(score, 1.0)

def final_portfolio_score(portfolio, macro_weights, investor_profile):
    macro_score = macro_alignment_score(portfolio, macro_weights)
    investor_score = investor_alignment_score(
        portfolio,
        investor_profile["preferred_factors"]
    )

    final_score = (
        investor_profile["macro_weight"] * macro_score +
        investor_profile["investor_weight"] * investor_score
    )

    return final_score, macro_score, investor_score

def generate_macro_reasoning(active_regimes, macro_weights):
    """Generate deterministic macro reasoning based on regimes and factors."""
    reasoning = []
    
    regime_factor_mapping = {
        "High Inflation": ["Value", "Real Assets"],
        "Tight Liquidity": ["Quality", "Defensive"],
        "Stagflation": ["Commodities", "Value"],
        "Low Growth": ["Quality", "Dividend"],
        "Rising Rates": ["Value"],
        "Falling Rates": ["Growth", "Duration"]
    }
    
    for regime in active_regimes:
        factors = regime_factor_mapping.get(regime, [])
        top_factor = max(macro_weights.items(), key=lambda x: x[1])[0]
        if factors:
            reasoning.append(f"{regime} historically favors {factors[0]}")
    
    return reasoning

def generate_investor_reasoning(investor_type, portfolio_name, preferred_factors, portfolio_allocations):
    """Generate deterministic investor reasoning."""
    reasoning = []
    
    type_descriptions = {
        "Aggressive": "seek growth and momentum exposure",
        "Balanced": "prefer diversification across multiple factors",
        "Defensive": "prioritize stability and capital preservation"
    }
    
    description = type_descriptions.get(investor_type, "follow their risk profile")
    reasoning.append(f"{investor_type} investors {description}")
    
    momentum_exposure = portfolio_allocations.get("Momentum", 0)
    if momentum_exposure > 0.25:
        reasoning.append(f"Portfolio includes moderate Momentum exposure ({momentum_exposure:.0%})")
    else:
        reasoning.append(f"Portfolio avoids excessive Momentum exposure")
    
    return reasoning

def generate_explanation(investor_type, active_regimes, macro_weights, macro_reasoning, 
                        investor_reasoning, portfolio_name):
    """Generate the explanation section."""
    
    summary_map = {
        "Defensive Tilt": "This portfolio aligns with current macro conditions while emphasizing quality and defensive factors.",
        "Balanced Growth": "This portfolio balances growth potential with current macro headwinds, suitable for moderate risk tolerance.",
        "Aggressive Growth": "This portfolio maximizes growth exposure while considering macro regime signals.",
        "Value Focus": "This portfolio concentrates on value factors, historically effective in inflationary environments.",
    }
    
    summary = summary_map.get(portfolio_name, 
                             f"This portfolio aligns with current macro conditions while respecting the {investor_type} investor's risk tolerance.")
    
    return {
        "macro_reasoning": macro_reasoning,
        "investor_reasoning": investor_reasoning,
        "summary": summary
    }

def build_output_json(investor_type, macro_weights, active_regimes, ranked_portfolios, 
                      portfolio_details, investor_profiles):
    """Build the complete structured JSON output."""
    
    investor = investor_profiles[investor_type]
    best_portfolio = ranked_portfolios[0]
    
    macro_reasoning = generate_macro_reasoning(active_regimes, macro_weights)
    investor_reasoning = generate_investor_reasoning(investor_type, best_portfolio["portfolio"], 
                                                     investor["preferred_factors"], 
                                                     portfolio_details[best_portfolio["portfolio"]])
    explanation = generate_explanation(investor_type, active_regimes, macro_weights,
                                      macro_reasoning, investor_reasoning, best_portfolio["portfolio"])
    
    output = {
        "metadata": {
            "generated_at": get_timestamp(),
            "investor_type": investor_type,
            "macro_source": "pass4",
            "active_regimes": active_regimes
        },
        "macro_factor_weights": macro_weights,
        "ranked_portfolios": ranked_portfolios,
        "recommended_portfolio": {
            "name": best_portfolio["portfolio"],
            "confidence": round(best_portfolio["total_score"], 2)
        },
        "explanation": explanation
    }
    
    return output

if __name__ == "__main__":
    # Load data
    investors = load_investor_profiles()
    portfolios = load_candidate_portfolios()
    available_dates = get_available_dates()
    
    # Prompt user for target date
    target_date = prompt_target_date(available_dates)
    print(f"\nSelected date: {target_date}")
    
    # Get macro conditions for that date
    macro_conditions = get_macro_conditions_for_date(target_date)
    print(f"Using date: {macro_conditions['date_used']}")
    print(f"Macro conditions: Inflation={macro_conditions['inflation_score']}, Growth={macro_conditions['growth_score']}, Liquidity={macro_conditions['macro_score']}")
    print("="*50 + "\n")
    
    # For now, use pre-computed macro weights from Pass 4
    # In a full integration, would map date to regimes and compute weights
    macro_weights, regimes = load_macro_factor_weights()
    
    # Prompt user for investor type
    available_types = list(investors.keys())
    investor_type = prompt_investor_type(available_types)
    
    print(f"Selected: {investor_type}")
    print("="*50 + "\n")
    
    investor = investors[investor_type]

    results = []
    portfolio_details = {}

    for name, portfolio in portfolios.items():
        total_score, macro_score, investor_score = final_portfolio_score(portfolio, macro_weights, investor)
        portfolio_details[name] = portfolio
        results.append({
            "portfolio": name,
            "total_score": round(total_score, 2),
            "macro_score": round(macro_score, 2),
            "investor_score": round(investor_score, 2)
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    # Generate the structured output JSON
    output_json = build_output_json(investor_type, macro_weights, regimes, results, 
                                   portfolio_details, investors)
    
    # Create outputs directory if it doesn't exist
    output_dir = BASE_DIR / "Pass 5 - Portfolio Scoring" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write JSON to file
    output_file = output_dir / "portfolio_recommendation_latest.json"
    with open(output_file, "w") as f:
        json.dump(output_json, f, indent=2)
    
    print(f"Portfolio recommendation saved to {output_file}")