import pandas as pd
from pandas_datareader import data as pdr
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Time range
start_date = datetime(2000, 1, 1)
end_date = datetime.today()

print(f"Fetching data from {start_date.date()} to {end_date.date()}")
print("="*70)

# FRED series codes - all indicators needed for Pass 2
series = {
    # Growth Indicators
    "GDP": "GDP",                           # Gross Domestic Product (Quarterly)
    "UnemploymentRate": "UNRATE",           # Unemployment Rate (Monthly)
    
    # Inflation Indicators
    "CPI": "CPIAUCSL",                      # Consumer Price Index (Monthly)
    "PMI": "NAPM",                          # ISM Manufacturing PMI (Monthly, discontinued 2002)
    
    # Liquidity/Policy Indicators
    "FedFundsRate": "FEDFUNDS",            # Federal Funds Rate (Monthly)
    "Treasury10Y": "DGS10",                 # 10Y Treasury Yield (Daily)
    "Treasury2Y": "DGS2",                   # 2Y Treasury Yield (Daily)
    
    # Additional useful indicators (optional)
    "SP500": "SP500",                       # S&P 500 Index (Daily)
    "VIX": "VIXCLS",                        # CBOE Volatility Index (Daily)
}

# Alternative PMI/manufacturing indicators to try
pmi_alternatives = {
    "PMI_Production": "IPMAN",              # Industrial Production: Manufacturing Index
    "PMI_Capacity": "TCU",                  # Capacity Utilization: Manufacturing
    "PMI_Orders": "NEWORDER",               # New Orders for Manufacturing
}

data_dict = {}

# Fetch each series
for name, code in series.items():
    try:
        print(f"Fetching {name:25} (code: {code})...", end=" ")
        df = pdr.DataReader(code, "fred", start_date, end_date)
        data_dict[name] = df
        print(f"✓ ({len(df)} records)")
    except Exception as e:
        print(f"✗ Failed: {str(e)[:50]}")
        data_dict[name] = None

# Try alternative PMI sources if main one failed
if data_dict.get("PMI") is None:
    print("\nTrying alternative PMI sources...")
    for name, code in pmi_alternatives.items():
        try:
            print(f"Fetching {name:25} (code: {code})...", end=" ")
            df = pdr.DataReader(code, "fred", start_date, end_date)
            data_dict["PMI"] = df  # Use first successful alternative
            print(f"✓ ({len(df)} records)")
            break
        except Exception as e:
            print(f"✗ Failed: {str(e)[:50]}")

print("\n" + "="*70)
print("Combining data...")

# Combine all dataframes
combined_data = pd.DataFrame()
for name, df in data_dict.items():
    if df is not None:
        combined_data[name] = df.iloc[:, 0] if len(df.columns) == 1 else df.mean(axis=1)

# Reset index to make DATE a column
combined_data.reset_index(inplace=True)
combined_data.rename(columns={'index': 'DATE'}, inplace=True)

print(f"Combined dataset shape: {combined_data.shape}")
print(f"Date range: {combined_data['DATE'].min()} to {combined_data['DATE'].max()}")

# ============================================================================
# DATA FREQUENCY ALIGNMENT
# ============================================================================
print("\n" + "="*70)
print("Aligning data frequencies...")

# Since we have mixed frequencies (daily, monthly, quarterly), we need to align
# Strategy: Resample to QUARTERLY frequency (matches GDP)

# Set DATE as index for resampling
combined_data.set_index('DATE', inplace=True)

# Resample to quarterly, taking the last value in each quarter
quarterly_data = combined_data.resample('QE').last()

# For flow variables (GDP), we want the actual quarterly value
# For stock variables (rates, prices), last value is fine
# For PMI and other monthly indicators, we can take the average of the quarter
if 'PMI' in quarterly_data.columns:
    pmi_avg = combined_data['PMI'].resample('QE').mean()
    quarterly_data['PMI'] = pmi_avg

# Reset index to make DATE a column again
quarterly_data.reset_index(inplace=True)

# ============================================================================
# CALCULATE DERIVED METRICS
# ============================================================================
print("Calculating derived metrics...")

# Yield Curve spread
if 'Treasury10Y' in quarterly_data.columns and 'Treasury2Y' in quarterly_data.columns:
    quarterly_data['YieldCurve'] = quarterly_data['Treasury10Y'] - quarterly_data['Treasury2Y']
    print("✓ Yield Curve calculated")

# Forward fill any NaN values in yield data (common for weekends/holidays)
yield_cols = ['Treasury10Y', 'Treasury2Y', 'FedFundsRate']
for col in yield_cols:
    if col in quarterly_data.columns:
        quarterly_data[col] = quarterly_data[col].ffill()

# ============================================================================
# DATA QUALITY CHECKS
# ============================================================================
print("\n" + "="*70)
print("Data Quality Summary:")
print("="*70)

for col in quarterly_data.columns:
    if col != 'DATE':
        total_rows = len(quarterly_data)
        non_null = quarterly_data[col].notna().sum()
        pct_complete = (non_null / total_rows) * 100
        status = "✓" if pct_complete > 80 else "⚠" if pct_complete > 50 else "✗"
        print(f"{status} {col:20} {non_null:4}/{total_rows:4} ({pct_complete:5.1f}% complete)")

# ============================================================================
# SAVE FILES
# ============================================================================
print("\n" + "="*70)
print("Saving data...")

# Save quarterly data (for Pass 2 analysis)
quarterly_data.to_csv("macro_data.csv", index=False)
print(f"✓ Quarterly data saved to: macro_data.csv ({len(quarterly_data)} rows)")

# Also save monthly data for higher frequency analysis (optional)
monthly_data = combined_data.resample('ME').last()
monthly_data.reset_index(inplace=True)
monthly_data.to_csv("macro_data_monthly.csv", index=False)
print(f"✓ Monthly data saved to: macro_data_monthly.csv ({len(monthly_data)} rows)")

# ============================================================================
# PREVIEW
# ============================================================================
print("\n" + "="*70)
print("Preview of quarterly data (last 10 rows):")
print("="*70)
print(quarterly_data.tail(10).to_string(index=False))

print("\n" + "="*70)
print("✓ Data fetch complete!")
print("="*70)
print("\nNext steps:")
print("1. Review data quality warnings above")
print("2. Run the Pass 2 macro scoring script")
print("3. Check if PMI data is available (critical for inflation assessment)")
if data_dict.get("PMI") is None:
    print("\n⚠ WARNING: PMI data not available from FRED")
    print("   Consider manually downloading ISM PMI from: https://www.ismworld.org/")
    print("   Or use alternative manufacturing indicators")