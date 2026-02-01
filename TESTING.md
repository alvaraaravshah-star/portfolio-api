# 🧪 Testing Guide - Macro Portfolio Engine

This guide will help you test the website and verify all functionality works correctly.

## ✅ Initial Setup Verification

### 1. Check the Server is Running
```bash
curl -s http://localhost:5001/api/config | jq .
```

You should see:
```json
{
  "investor_types": ["Conservative", "Balanced", "Aggressive"],
  "portfolio_types": ["Defensive Portfolio", "Balanced Portfolio", "Growth Portfolio"],
  "factors": ["Value", "Quality", "Momentum"]
}
```

### 2. Check the Website Loads
Open http://localhost:5001 in your browser. You should see:
- Title: "📊 Macro Portfolio Engine"
- A questionnaire panel on the left
- Input fields for investor type and macro sliders

## 🧪 Test Scenarios

### Test 1: Conservative Investor in Normal Times
**Objective**: Verify conservative investor gets defensive portfolio

1. Open http://localhost:5001
2. Select: **Conservative**
3. Set all sliders to **0.0**
4. Click **Run Portfolio Analysis**

**Expected Results**:
- Active Regimes: "Neutral"
- Selected Portfolio: "Defensive Portfolio"
- Highest allocation to: Quality factor
- ETF: QUAL should appear in allocation

---

### Test 2: Aggressive Investor in Growth Period
**Objective**: Verify aggressive investor gets growth-focused portfolio

1. Reset the page (click Start Over or F5)
2. Select: **Aggressive**
3. Set:
   - Inflation Score: **0.5**
   - Growth Score: **0.5**
   - Macro Score: **0.2**
4. Click **Run Portfolio Analysis**

**Expected Results**:
- Active Regimes: "Neutral" (no extreme scores)
- Selected Portfolio: "Balanced Portfolio" or "Growth Portfolio"
- Higher allocation to: Momentum factor
- ETF: MTUM should appear

---

### Test 3: Tight Liquidity Detection
**Objective**: Verify regime detection works correctly

1. Reset the page
2. Select: **Balanced**
3. Set:
   - Inflation Score: **0.0**
   - Growth Score: **0.0**
   - Macro Score: **-0.8** (very negative = tight liquidity)
4. Click **Run Portfolio Analysis**

**Expected Results**:
- Active Regimes: **"Tight_Liquidity"**
- Higher allocation to: Quality factor
- Portfolio Score should be high

---

### Test 4: High Inflation Scenario
**Objective**: Verify inflation regime triggers

1. Reset the page
2. Select: **Aggressive**
3. Set:
   - Inflation Score: **-0.8** (negative = high inflation)
   - Growth Score: **0.0**
   - Macro Score: **0.0**
4. Click **Run Portfolio Analysis**

**Expected Results**:
- Active Regimes: **"High_Inflation"**
- Factor weights favor: Value
- Portfolio allocation includes Value ETFs (VTV, IVE)

---

### Test 5: Weak Growth + Tight Liquidity
**Objective**: Verify multiple regimes trigger together

1. Reset the page
2. Select: **Conservative**
3. Set:
   - Inflation Score: **0.0**
   - Growth Score: **-0.7**
   - Macro Score: **-0.6**
4. Click **Run Portfolio Analysis**

**Expected Results**:
- Active Regimes: **"Weak_Growth"** AND **"Tight_Liquidity"**
- Selected Portfolio: "Defensive Portfolio"
- Strong Quality emphasis
- Portfolio Score > 80%

---

## 📊 Visual Checklist

### Pass 4 Results (Regime Detection)
- ✅ Shows current date
- ✅ Lists active regimes (or "Neutral")
- ✅ Shows all three macro scores
- ✅ Regimes formatted as clickable-looking tags

### Pass 5 Results (Portfolio Scoring)
- ✅ Displays portfolio name (Defensive/Balanced/Growth)
- ✅ Shows three score cards: Overall, Macro Alignment, Investor Fit
- ✅ Each score is a percentage 0-100%
- ✅ Shows factor allocation (Quality, Value, Momentum)
- ✅ Allocations sum to 100%

### Pass 6 Results (Asset Construction)
- ✅ Shows specific ETF symbols (VTV, QUAL, MTUM, etc.)
- ✅ Shows allocation percentage for each ETF
- ✅ Factor to ETF mapping is clear
- ✅ All percentages sum to 100%

### Explanation
- ✅ Contains human-readable explanation
- ✅ Mentions specific factors and ETFs
- ✅ Explains why portfolio was chosen

---

## 🔧 API Testing

Test the backend directly with curl:

### Test Config Endpoint
```bash
curl http://localhost:5001/api/config | jq .
```

### Test Run Engine Endpoint
```bash
curl -X POST http://localhost:5001/api/run-engine \
  -H "Content-Type: application/json" \
  -d '{
    "investor_type": "Conservative",
    "macro_conditions": {
      "inflation_score": 0.0,
      "growth_score": 0.0,
      "macro_score": 0.0
    }
  }' | jq .
```

Expected: Full JSON response with pass4_output, pass5_output, pass6_output

### Test with Extreme Values
```bash
curl -X POST http://localhost:5001/api/run-engine \
  -H "Content-Type: application/json" \
  -d '{
    "investor_type": "Aggressive",
    "macro_conditions": {
      "inflation_score": -1.0,
      "growth_score": -1.0,
      "macro_score": -1.0
    }
  }' | jq .
```

Expected: Multiple active regimes triggered

---

## 🐛 Debugging Tips

### If page doesn't load:
1. Check browser console (F12)
2. Check server logs for errors
3. Verify http://localhost:5001 is correct

### If sliders don't work:
1. Check browser console for JS errors
2. Verify app.js is loading
3. Check style.css for CSS errors

### If run-engine button doesn't work:
1. Verify you selected an investor type
2. Check browser Network tab (F12)
3. Look for 400/500 error in response

### If results don't display:
1. Check browser console for JS errors
2. Verify response JSON from API
3. Check app.js rendering logic

---

## ✨ Performance Notes

- Initial load: ~1-2 seconds
- Run engine: ~500ms-1s (depending on system)
- No data stored between sessions
- Each run is independent calculation

---

## 📝 Sign-Off Checklist

- [ ] Website loads at http://localhost:5001
- [ ] Questionnaire panel displays correctly
- [ ] Sliders work and update values
- [ ] Run button triggers calculation
- [ ] Results panel shows all outputs
- [ ] Pass 4 results display regimes
- [ ] Pass 5 results display portfolio & scores
- [ ] Pass 6 results display ETF allocation
- [ ] Start Over button resets everything
- [ ] API endpoint works with curl
- [ ] No JavaScript errors in console
- [ ] No server errors in logs
- [ ] Responsive on mobile (narrow viewport)
- [ ] All test scenarios produce expected results

---

## 🚀 What's Next?

After testing:
1. Refine UI based on user feedback
2. Add more customization options
3. Integrate live macro data from FRED
4. Add portfolio performance metrics
5. Create multi-factor optimizer
