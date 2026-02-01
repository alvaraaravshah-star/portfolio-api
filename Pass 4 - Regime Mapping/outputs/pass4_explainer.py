"""
Pass 4 Explainer: Regime → Explanation Layer
Converts factor_tilt_latest.json into plain-English explanations.
This is why Alvara is explainable.
"""

import json
import os
from pathlib import Path


# ============================================================================
# PROJECT ROOT & RELATIVE PATHS (FIX 1)
# ============================================================================
# Note: This file is now in Pass 4 - Regime Mapping/outputs/
# Go up 3 levels to reach project root
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "Pass 4 - Regime Mapping" / "outputs"
JSON_PATH = OUTPUT_DIR / "factor_tilt_latest.json"


# ============================================================================
# REGIME EXPLANATION TEMPLATES
# ============================================================================
REGIME_EXPLANATIONS = {
    "High_Inflation": (
        "Inflation is elevated (Inflation_Score ≥ +1). "
        "Historically, Value factors perform well in high-inflation environments "
        "as real asset owners are compensated for currency debasement."
    ),
    "Weak_Growth": (
        "Growth is weakening (Growth_Score ≤ -1). "
        "In low-growth environments, Quality factors (stable earnings, strong balance sheets) "
        "typically provide defensive characteristics."
    ),
    "Tight_Liquidity": (
        "Liquidity conditions are tight (Macro_Score ≤ -1). "
        "Quality factors tend to outperform as markets favor low-volatility, "
        "financially stable companies."
    ),
    "Neutral": (
        "Macro conditions are balanced and neutral. "
        "No single regime is dominant, so we apply equal weights across all factors."
    )
}


# ============================================================================
# LOAD FACTOR TILT OUTPUT
# ============================================================================
def load_factor_tilt_output():
    """
    Load factor_tilt_latest.json from Pass 4 - Regime Mapping/outputs/
    """
    if not JSON_PATH.exists():
        print(f"✗ Error: {JSON_PATH} not found.")
        print("  Run pass4_regime_mapper.py first to generate this file.")
        return None
    
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    return data


# ============================================================================
# GENERATE EXPLANATION
# ============================================================================
def generate_explanation(factor_tilt_data):
    """
    Take factor_tilt_latest.json and generate plain-English explanation.
    """
    if not factor_tilt_data:
        return None
    
    date = factor_tilt_data['date']
    active_regimes = factor_tilt_data['active_regimes']
    factor_weights = factor_tilt_data['factor_weights']
    
    # Build explanation
    explanation_lines = []
    explanation_lines.append(f"As of {date}:")
    explanation_lines.append("")
    
    # Regime explanations
    for regime in active_regimes:
        if regime in REGIME_EXPLANATIONS:
            explanation_lines.append(f"• {REGIME_EXPLANATIONS[regime]}")
    
    explanation_lines.append("")
    
    # Factor weights explanation
    explanation_lines.append("Factor Allocation:")
    for factor, weight in sorted(factor_weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0:
            pct = weight * 100
            explanation_lines.append(f"  {factor}: {pct:.1f}%")
    
    full_explanation = "\n".join(explanation_lines)
    return full_explanation


# ============================================================================
# SAVE EXPLANATION OUTPUT
# ============================================================================
def save_explanation_output(explanation_text):
    """
    Save explanation to a text file for review.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = OUTPUT_DIR / "regime_explanation.txt"
    
    with open(output_path, 'w') as f:
        f.write(explanation_text)
    
    print(f"✓ Saved explanation to: {output_path}")
    return output_path


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("PASS 4 EXPLAINER: Regime → Explanation")
    print("="*70 + "\n")
    
    # Load factor tilt output
    factor_tilt_data = load_factor_tilt_output()
    
    if factor_tilt_data:
        # Generate explanation
        explanation = generate_explanation(factor_tilt_data)
        
        print(explanation)
        print("")
        
        # Save explanation
        save_explanation_output(explanation)
    else:
        print("Explanation generation failed. Please run pass4_regime_mapper.py first.")
    
    print("\n" + "="*70 + "\n")
