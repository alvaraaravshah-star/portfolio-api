"""
Pass 4: Regime Mapping
Converts macro state vector into regime-based factor weights.
"""

import pandas as pd
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ============================================================================
# PROJECT ROOT & RELATIVE PATHS (FIX 1)
# ============================================================================
# Note: This file is now in Pass 4 - Regime Mapping/outputs/
# Go up 3 levels to reach project root
BASE_DIR = Path(__file__).resolve().parents[2]
MACRO_DATA_PATH = BASE_DIR / "Pass 2 - Macro State Vector" / "macro_data_scored.csv"
OUTPUT_DIR = BASE_DIR / "Pass 4 - Regime Mapping" / "outputs"


# ============================================================================
# STEP 2: REGIME RULES (LOCKED IN)
# These rules must match Pass 3 exactly. Do not modify thresholds.
# ============================================================================
# High_Inflation    → Inflation_Score ≥ +1
# Weak_Growth       → Growth_Score ≤ -1
# Tight_Liquidity   → Macro_Score ≤ -1
# ============================================================================

# ============================================================================
# ACTIVE FACTORS (FIX 2 - v1)
# ============================================================================
# Only available factors. LowVol pending.
# This ensures Neutral weighting applies only to active factors.
ACTIVE_FACTORS = ["Value", "Quality", "Momentum"]


# ============================================================================
# STEP 3: REGIME → FACTOR LOOKUP TABLE (DYNAMIC FROM PASS 3)
# ============================================================================
def load_regime_factor_map():
    """
    Load regime → best_factor mapping from Pass 3 research output.
    This creates a clean research → inference boundary:
    - Pass 3 (research) defines what works historically
    - Pass 4 (inference) applies it today
    
    Returns: (regime_map dict, source string)
    source = "pass3" or "fallback"
    """
    # Note: Directory name has trailing space (unusual but intentional)
    pass3_path = BASE_DIR / "Pass 3 - Dataset Work " / "regime_factor_return_summary.csv"
    
    if not pass3_path.exists():
        print(f"⚠ CRITICAL: {pass3_path} not found.")
        print(f"  Falling back to hard-coded mapping (NOT research-based).")
        print(f"  This should only happen during development.")
        fallback_map = {
            "High_Inflation": "Value",
            "Weak_Growth": "Value",
            "Tight_Liquidity": "Quality"
        }
        return fallback_map, "fallback"
    
    df = pd.read_csv(pass3_path)
    
    # Create mapping: regime (with underscores) → best_factor
    regime_map = dict(zip(df['regime'], df['best_factor']))
    
    print(f"✓ Loaded regime mapping from Pass 3:")
    for regime, factor in regime_map.items():
        print(f"  {regime} → {factor}")
    
    return regime_map, "pass3"


# Dynamically load mapping at module initialization
REGIME_FACTOR_MAP, MAPPING_SOURCE = load_regime_factor_map()


# ============================================================================
# STEP 4: LOAD MACRO STATE
# ============================================================================
def load_macro_state(target_date=None):
    """
    Load macro_data_scored.csv.
    If target_date (YYYY-DD-MM) is provided, return that date.
    Otherwise, return latest.
    """
    df = pd.read_csv(MACRO_DATA_PATH)
    # dates in CSV now encoded as YYYY-DD-MM
    df['DATE'] = pd.to_datetime(df['DATE'], format='%Y-%d-%m')

    if target_date:
        # Parse user input as YYYY-DD-MM and convert to date for comparison
        target_date = pd.to_datetime(target_date, format='%Y-%d-%m')
        row = df[df['DATE'].dt.date == target_date.date()]

        if row.empty:
            raise ValueError(f"No data for date {target_date.strftime('%Y-%d-%m')}")
        
        selected_row = row.iloc[0]
    else:
        selected_row = df.sort_values('DATE').iloc[-1]

    return {
        "DATE": selected_row['DATE'].strftime("%Y-%d-%m"),
        "Inflation_Score": selected_row['Inflation_Score'],
        "Growth_Score": selected_row['Growth_Score'],
        "Macro_Score": selected_row['Macro_Score']
    }


# ============================================================================
# STEP 5: DETECT ACTIVE REGIMES
# ============================================================================
def detect_active_regimes(macro_state):
    """
    Check each regime rule. Append triggered regimes to list.
    If no regimes trigger, return ["Neutral"].
    Returns: (active_regimes, regime_strength dict)
    Regime names use underscores to match Pass 3 output.
    """
    active_regimes = []
    regime_strength = {}  # UPGRADE 1: Track strength/confidence of each regime
    
    # Rule 1: High Inflation
    if macro_state['Inflation_Score'] <= -0.5:
        active_regimes.append("High_Inflation")
        regime_strength["High_Inflation"] = macro_state['Inflation_Score'] - 1.0
    
    # Rule 2: Weak Growth
    if macro_state['Growth_Score'] <= -0.5:
        active_regimes.append("Weak_Growth")
        regime_strength["Weak_Growth"] = abs(macro_state['Growth_Score'] + 1.0)
    
    # Rule 3: Tight Liquidity
    if macro_state['Macro_Score'] <= -0.5:
        active_regimes.append("Tight_Liquidity")
        regime_strength["Tight_Liquidity"] = abs(macro_state['Macro_Score'] + 1.0)
    
    # If no regimes triggered
    if len(active_regimes) == 0:
        active_regimes = ["Neutral"]
    
    return active_regimes, regime_strength


# ============================================================================
# STEP 6: CONVERT REGIMES → FACTOR VOTES
# ============================================================================
def convert_regimes_to_votes(active_regimes):
    """
    For each active regime, look up preferred factor and add one vote.
    Returns factor_votes dict.
    
    ISSUE 3 NOTE: Currently each regime gets 1 vote regardless of strength.
    Future enhancement: Weight votes by regime_strength for stronger signals.
    """
    # Initialize vote counter for active factors only (FIX 2)
    factor_votes = {f: 0 for f in ACTIVE_FACTORS}
    
    # If Neutral, don't add any votes (will result in equal weighting)
    if active_regimes == ["Neutral"]:
        return factor_votes
    
    # Add one vote for each active regime
    for regime in active_regimes:
        if regime in REGIME_FACTOR_MAP:
            factor = REGIME_FACTOR_MAP[regime]
            factor_votes[factor] += 1
    
    return factor_votes


# ============================================================================
# STEP 7: NORMALIZE VOTES INTO FACTOR WEIGHTS
# ============================================================================
def normalize_votes_to_weights(factor_votes, active_regimes):
    """
    Convert votes to weights: weight = votes / total_votes
    If Neutral, return equal weights.
    """
    # Initialize with active factors only (FIX 2)
    factor_weights = {f: 0.0 for f in ACTIVE_FACTORS}
    
    # If Neutral, equal weight across active factors
    if active_regimes == ["Neutral"]:
        equal_weight = 1.0 / len(ACTIVE_FACTORS)
        for f in ACTIVE_FACTORS:
            factor_weights[f] = equal_weight
        return factor_weights
    
    # Otherwise, normalize votes
    total_votes = sum(factor_votes.values())
    
    if total_votes > 0:
        for factor in factor_votes:
            factor_weights[factor] = factor_votes[factor] / total_votes
    
    return factor_weights


# ============================================================================
# STEP 8: SAVE MACHINE-READABLE OUTPUT
# ============================================================================
def save_factor_tilt_output(macro_state, active_regimes, factor_weights, regime_strength):
    """
    Write JSON to: Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json
    
    ISSUE 2 FIX: Include source field to indicate whether mapping came from
    Pass 3 research or hard-coded fallback.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # UPGRADE 2: Add timestamp metadata
    # ISSUE 2 FIX: Add source field to track data lineage
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date": macro_state['DATE'],
        "source": MAPPING_SOURCE,  # "pass3" or "fallback"
        "active_regimes": active_regimes,
        "regime_strength": regime_strength,
        "factor_weights": factor_weights
    }
    
    output_path = OUTPUT_DIR / "factor_tilt_latest.json"
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved factor tilt output to: {output_path}")
    if MAPPING_SOURCE == "fallback":
        print(f"⚠ NOTE: Using fallback mapping (not research-based)")
    return output


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("PASS 4: REGIME MAPPING")
    print("="*70)
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Pass 4: Regime Mapping - Convert macro state vector into regime-based factor weights."
    )
    parser.add_argument(
        "--target-date",
        required=True,
        type=str,
        help="Target date in YYYY-MM-DD format (e.g., 2009-01-04)"
    )
    args = parser.parse_args()
    
    # Validate and convert date
    try:
        target_date = pd.to_datetime(args.target_date, format='%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError as e:
        parser.error(f"Invalid date format. Expected YYYY-MM-DD, got '{args.target_date}': {e}")
    
    # STEP 4: Load macro state with validated date
    macro_state = load_macro_state(target_date)
    print(f"\n[STEP 4] Latest Macro State:")
    print(f"  DATE:             {macro_state['DATE']}")
    print(f"  Inflation_Score:  {macro_state['Inflation_Score']:.2f}")
    print(f"  Growth_Score:     {macro_state['Growth_Score']:.2f}")
    print(f"  Macro_Score:      {macro_state['Macro_Score']:.2f}")
    
    # STEP 5: Detect active regimes
    active_regimes, regime_strength = detect_active_regimes(macro_state)
    print(f"\n[STEP 5] Active Regimes Detected:")
    print(f"  {active_regimes}")
    if regime_strength:
        print(f"  Strength: {regime_strength}")
    
    # STEP 6: Convert regimes to votes
    factor_votes = convert_regimes_to_votes(active_regimes)
    print(f"\n[STEP 6] Factor Votes:")
    for factor, votes in factor_votes.items():
        if votes > 0:
            print(f"  {factor}: {votes}")
    
    # STEP 7: Normalize votes to weights
    factor_weights = normalize_votes_to_weights(factor_votes, active_regimes)
    print(f"\n[STEP 7] Normalized Factor Weights (FIX 3 - all factors):")
    for factor, weight in factor_weights.items():
        print(f"  {factor}: {weight:.4f}")
    
    # STEP 8: Save output
    print(f"\n[STEP 8] Saving Output...")
    save_factor_tilt_output(macro_state, active_regimes, factor_weights, regime_strength)
    
    print("\n" + "="*70)
    print("REGIME MAPPING COMPLETE")
    print("="*70 + "\n")

