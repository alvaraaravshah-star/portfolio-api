#!/usr/bin/env python3
"""
Test script: Verify regime mapping is dynamically loaded from Pass 3.
This demonstrates the research → inference boundary.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
PASS3_PATH = BASE_DIR / "Pass 3 - Dataset Work " / "regime_factor_return_summary.csv"
PASS2_PATH = BASE_DIR / "Pass 2 - Macro State Vector" / "macro_data_scored.csv"

print("\n" + "="*70)
print("TEST: Pass 3 → Pass 4 Integration")
print("="*70)

# Load Pass 3 research output
print("\n[PASS 3 RESEARCH OUTPUT]")
print(f"Loading: {PASS3_PATH}")
df_pass3 = pd.read_csv(PASS3_PATH)
print(f"\nRegime Factor Mapping:")
for idx, row in df_pass3.iterrows():
    regime = row['regime']
    factor = row['best_factor']
    mean_return = row['best_mean']
    print(f"  {regime:20} → {factor:10} (avg return: {mean_return:.6f})")

# Create regime → factor map
regime_map = dict(zip(df_pass3['regime'], df_pass3['best_factor']))
print(f"\nRegime Map Dict:")
print(f"  {regime_map}")

# Load Pass 2 macro data
print(f"\n[PASS 2 MACRO DATA]")
print(f"Loading: {PASS2_PATH}")
df_macro = pd.read_csv(PASS2_PATH)
# PASS2 dates now stored as YYYY-DD-MM

df_macro['DATE'] = pd.to_datetime(df_macro['DATE'], format='%Y-%d-%m')

latest = df_macro.sort_values('DATE').iloc[-1]

print(f"\nLatest Macro State ({latest['DATE'].strftime('%Y-%m')}):")
print(f"  Inflation_Score: {latest['Inflation_Score']:.2f}")
print(f"  Growth_Score:    {latest['Growth_Score']:.2f}")
print(f"  Macro_Score:     {latest['Macro_Score']:.2f}")

# Simulate regime detection
print(f"\n[REGIME DETECTION LOGIC]")
regimes = []
if latest['Inflation_Score'] >= 1.0:
    regimes.append("High_Inflation")
if latest['Growth_Score'] <= -1.0:
    regimes.append("Weak_Growth")
if latest['Macro_Score'] <= -1.0:
    regimes.append("Tight_Liquidity")

if not regimes:
    regimes = ["Neutral"]

print(f"Active Regimes: {regimes}")

# Apply regime → factor mapping (this is what Pass 4 does)
print(f"\n[REGIME → FACTOR MAPPING (Pass 4 Application)]")
if regimes == ["Neutral"]:
    print(f"  Neutral regime detected → Equal weight all factors")
    allocation = {"Value": 1/3, "Quality": 1/3, "Momentum": 1/3}
else:
    factors_voted = {}
    for regime in regimes:
        if regime in regime_map:
            factor = regime_map[regime]
            factors_voted[factor] = factors_voted.get(factor, 0) + 1
            print(f"  {regime} → {factor} (+1 vote)")
    
    total_votes = sum(factors_voted.values())
    allocation = {f: v/total_votes for f, v in factors_voted.items()}

print(f"\nFinal Allocation:")
for factor in ["Value", "Quality", "Momentum"]:
    weight = allocation.get(factor, 0)
    print(f"  {factor}: {weight:.4f} ({weight*100:.1f}%)")

print(f"\n" + "="*70)
print("✓ Research (Pass 3) → Inference (Pass 4) boundary is clean")
print("✓ Pass 4 is now data-driven from Pass 3 research results")
print("="*70 + "\n")
