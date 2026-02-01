"""
Pass 6 - Portfolio Construction

Purpose:
- Load macro-aware factor tilts from Pass 5
- Map factors to investable ETFs via asset_universe
- Construct execution-ready asset-level allocations
- Generate explainable portfolio output

No optimization, backtest, or ML. Pure deterministic construction.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def load_pass5_recommendation() -> Dict[str, Any]:
    """Load the portfolio recommendation from Pass 5."""
    # Use absolute path by going up from current script location
    current_file = Path(__file__).resolve()
    workspace_root = current_file.parent.parent
    pass5_path = workspace_root / "Pass 5 - Portfolio Scoring" / "outputs" / "portfolio_recommendation_latest.json"
    
    if not pass5_path.exists():
        raise FileNotFoundError(f"Pass 5 output not found at {pass5_path}")
    
    with open(pass5_path, 'r') as f:
        return json.load(f)


def load_asset_universe() -> Dict[str, list]:
    """Load the asset universe mapping factors to ETFs."""
    universe_path = Path(__file__).parent / "asset_universe.json"
    
    with open(universe_path, 'r') as f:
        return json.load(f)


def load_portfolio_blueprints() -> Dict[str, Dict[str, float]]:
    """Load portfolio blueprint allocations."""
    blueprints_path = Path(__file__).parent / "portfolio_blueprints.json"
    
    with open(blueprints_path, 'r') as f:
        return json.load(f)


def select_asset_for_factor(factor: str, asset_universe: Dict[str, list]) -> str:
    """
    Select a default asset (ETF) for a given factor.
    
    Rule: Select the first ETF in the factor's asset list (deterministic, explainable).
    """
    if factor not in asset_universe:
        raise ValueError(f"Factor '{factor}' not found in asset universe")
    
    etfs = asset_universe[factor]
    if not etfs:
        raise ValueError(f"No ETFs available for factor '{factor}'")
    
    return etfs[0]


def construct_asset_allocation(
    factor_weights: Dict[str, float],
    asset_universe: Dict[str, list]
) -> tuple:
    """
    Construct final asset-level allocation from factor weights.
    
    Logic:
    1. For each factor in recommended portfolio, select an ETF
    2. Assign that ETF the weight of its factor (defensive: aggregate if same ETF)
    3. Verify weights sum to 1
    
    Returns:
        (asset_allocation, factor_to_etf) tuple for explainability
    """
    asset_allocation = {}
    factor_to_etf = {}  # Track factor -> ETF mapping for explanation
    
    for factor, weight in factor_weights.items():
        selected_etf = select_asset_for_factor(factor, asset_universe)
        factor_to_etf[factor] = selected_etf
        # Defensive: aggregate if same ETF appears twice
        asset_allocation[selected_etf] = asset_allocation.get(selected_etf, 0) + weight
    
    # Verify weights sum to 1
    total_weight = sum(asset_allocation.values())
    if not (0.999 <= total_weight <= 1.001):  # Allow small floating point error
        raise ValueError(f"Asset allocation weights do not sum to 1: {total_weight}")
    
    return asset_allocation, factor_to_etf


def generate_explainability_rule(
    factor_weights: Dict[str, float],
    factor_to_etf: Dict[str, str]
) -> str:
    """Generate a deterministic explanation referencing factor, asset, and reason.
    
    Uses explicit factor->ETF mapping for guaranteed correctness.
    """
    explanations = []
    
    for factor, weight in factor_weights.items():
        selected_etf = factor_to_etf[factor]
        percentage = round(weight * 100, 1)
        explanations.append(
            f"This portfolio allocates {percentage}% to {factor} via {selected_etf} because {factor} is favored under the current macro regime."
        )
    
    return " ".join(explanations)


def construct_portfolio_execution() -> Dict[str, Any]:
    """
    Main orchestration function.
    
    Workflow:
    1. Load Pass 5 recommendation (single source of truth)
    2. Load asset universe and blueprints
    3. Select assets for each factor
    4. Construct asset-level allocation
    5. Generate execution-ready output with explanation
    """
    # Load dependencies
    pass5_output = load_pass5_recommendation()
    asset_universe = load_asset_universe()
    portfolio_blueprints = load_portfolio_blueprints()
    
    # Extract from Pass 5 (single source of truth)
    recommended_portfolio_name = pass5_output.get("recommended_portfolio", {}).get("name")
    macro_factor_weights = pass5_output.get("macro_factor_weights", {})
    macro_reasoning = pass5_output.get("explanation", {}).get("macro_reasoning", [])
    investor_reasoning = pass5_output.get("explanation", {}).get("investor_reasoning", [])
    summary = pass5_output.get("explanation", {}).get("summary", "")
    investor_type = pass5_output.get("metadata", {}).get("investor_type", "")
    
    if not recommended_portfolio_name:
        raise ValueError("No recommended portfolio name found in Pass 5 output")
    
    # Load portfolio blueprint (this is the actual allocation source)
    if recommended_portfolio_name not in portfolio_blueprints:
        raise ValueError(f"Recommended portfolio '{recommended_portfolio_name}' not found in blueprints")
    
    factor_weights = portfolio_blueprints[recommended_portfolio_name]
    
    if not factor_weights:
        raise ValueError(f"No factor weights found for portfolio '{recommended_portfolio_name}'")
    
    # Construct asset allocation
    asset_allocation, factor_to_etf = construct_asset_allocation(factor_weights, asset_universe)
    
    # Generate explanation
    construction_explanation = generate_explainability_rule(
        factor_weights,
        factor_to_etf
    )
    
    # Build execution output
    execution_output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "investor_type": investor_type,
            "source": "pass6",
            "pass5_reference": recommended_portfolio_name
        },
        "portfolio": {
            "name": recommended_portfolio_name,
            "assets": asset_allocation
        },
        "explanation": {
            "macro": "; ".join(macro_reasoning) if macro_reasoning else "Macro conditions inform factor selection",
            "investor": "; ".join(investor_reasoning) if investor_reasoning else investor_type,
            "construction": construction_explanation
        }
    }
    
    return execution_output


def save_execution_output(execution_output: Dict[str, Any]) -> None:
    """Save execution-ready output to JSON."""
    output_path = Path(__file__).parent / "outputs" / "portfolio_execution_latest.json"
    
    with open(output_path, 'w') as f:
        json.dump(execution_output, f, indent=2)
    
    print(f"✓ Portfolio execution output saved to {output_path}")


def main():
    """Execute Pass 6 pipeline."""
    try:
        print("=" * 70)
        print("Pass 6 - Portfolio Construction")
        print("=" * 70)
        
        execution_output = construct_portfolio_execution()
        
        print("\n📊 Portfolio Construction Complete")
        print(f"   Portfolio: {execution_output['portfolio']['name']}")
        print(f"   Assets: {list(execution_output['portfolio']['assets'].keys())}")
        print(f"   Generated: {execution_output['metadata']['generated_at']}")
        
        print("\n📋 Asset Allocation:")
        for asset, weight in execution_output['portfolio']['assets'].items():
            print(f"   {asset}: {weight*100:.1f}%")
        
        print("\n📝 Explanation:")
        print(f"   {execution_output['explanation']['construction']}")
        
        save_execution_output(execution_output)
        
        print("\n" + "=" * 70)
        print("✅ Pass 6 Complete - Portfolio is execution-ready")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Pass 6 Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
