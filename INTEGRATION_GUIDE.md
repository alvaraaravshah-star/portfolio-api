# Complete API + Web App Integration Guide

## Overview

Your macro engine has three main components:
- **Pass 4**: Regime detection (macro_engine_api.egg-info/outputs/factor_tilt_latest.json)
- **Pass 5**: Portfolio scoring & selection (investor_profiles.json, candidate_portfolios.json)
- **Pass 6**: Asset construction (asset_universe.json → ETF allocation)

This guide connects them all through a **FastAPI** server with a simple frontend.

---

## Architecture

```
┌─────────────────┐
│   Web Frontend  │ (HTML/JS in /web)
└────────┬────────┘
         │ HTTP requests
         ▼
┌─────────────────────────────────────┐
│   FastAPI Server (api_server.py)    │
│  ┌─────────────────────────────────┐│
│  │ /recommend endpoint             ││ Runs Pass 5 + Pass 6 logic
│  │ /available-dates, etc.          ││
│  └─────────────────────────────────┘│
└────────┬────────────────────────────┘
         │ Loads data from
         ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Pass 4 JSON   │ │   Pass 5 JSON   │ │   Pass 6 JSON   │
│  factor_tilt    │ │ investor profs  │ │  asset universe │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Local Development (Your Machine)

### 1. Install Dependencies
```bash
cd "/Users/aravshah/Documents/macro engine - interactive version"
python3 -m pip install -r requirements.txt
```

**Requirements:**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==1.10.15
```

### 2. Start the API Server
```bash
python3 -m uvicorn api_server:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 3. Access the Web App
Open in your browser:
```
http://localhost:8000/web/simple.html
```

### 4. Test the Flow
1. Select a **Target date**
2. Choose an **Investor type** (Conservative, Balanced, Aggressive)
3. Click **"Get Recommendation"**
4. See JSON response showing:
   - Selected portfolio
   - Factor weights
   - ETF allocations
   - Investor preferences

### 5. Test the API Directly
```bash
# Get available dates
curl http://localhost:8000/available-dates

# Get investor types
curl http://localhost:8000/available-investor-types

# Get recommendation
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"target_date":"01-04-2009","investor_type":"Conservative"}'
```

---

## Production Deployment (Render)

### Prerequisites
- [Render account](https://dashboard.render.com)
- [GitHub account](https://github.com) with your repo pushed
- Render CLI installed: `brew install render`

### Step 1: Verify Docker Setup (Already Done)

Your `Dockerfile` specifies **Python 3.11-slim** (stable, no compilation issues):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh","-c","uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Your `render.yaml` points to it:

```yaml
services:
  - type: web
    name: macro-engine-api
    env: docker
    plan: free
    dockerfilePath: Dockerfile
```

### Step 2: Verify All Files Are Committed

```bash
cd "/Users/aravshah/Documents/macro engine - interactive version"

# Check that all required files are in git
git ls-files | grep -E "(api_server\.py|Dockerfile|requirements\.txt|web/)"
```

Expected output:
```
Dockerfile
api_server.py
requirements.txt
web/simple.html
web/static/simple.js
```

### Step 3: Push Latest Changes

```bash
git add .
git commit -m "Add CORS support and finalize API"
git push origin main
```

### Step 4: Deploy to Render

**Option A: Via Render Dashboard (Recommended)**

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. **Connect GitHub** (if not already connected)
4. Select your **portfolio-api** repository
5. Configure:
   - **Name**: `macro-engine-api`
   - **Environment**: Docker
   - **Build Command**: (leave blank, Dockerfile handles it)
   - **Start Command**: (leave blank, Dockerfile handles it)
   - **Plan**: Free tier (or upgrade if needed)
6. Click **"Create Web Service"**

Render will:
- Clone your GitHub repo
- Build Docker image (Python 3.11 + dependencies)
- Deploy to `https://macro-engine-api.onrender.com`

**Option B: Via Render CLI**

```bash
render login
render deploy --name macro-engine-api
```

### Step 5: Monitor Deployment

```bash
render logs macro-engine-api --deploy --tail
```

Look for:
```
==> Build successful 🎉
==> Deploying...
==> Running 'uvicorn api_server:app --host 0.0.0.0'
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Test Your Deployed API

```bash
# Replace with your actual Render service URL
SERVICE_URL="https://macro-engine-api.onrender.com"

# Test health endpoint
curl ${SERVICE_URL}/health

# Test recommendation endpoint
curl -X POST ${SERVICE_URL}/recommend \
  -H "Content-Type: application/json" \
  -d '{"target_date":"01-04-2009","investor_type":"Conservative"}'

# Open web app in browser
open "${SERVICE_URL}/web/simple.html"
```

### Step 7: Update Frontend URL (if needed)

If your frontend is deployed separately, update the API base URL in `web/static/simple.js`:

```javascript
const API_BASE = "https://macro-engine-api.onrender.com";  // Change this

async function loadOptions(){
  try{
    const d = await fetch(`${API_BASE}/available-dates`);
    // ... rest of code
  }
}
```

Then redeploy the frontend.

---

## Troubleshooting

### API Errors on Render

**Check logs:**
```bash
render logs macro-engine-api --tail
```

**Common issues:**

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed; check `requirements.txt` is committed |
| `No such file or directory: Pass 4 - Regime Mapping/...` | Data files missing from repo; run `git add "Pass 4 - Regime Mapping/"` |
| `Connection refused` | API not running; check start command in Render dashboard |
| `404 Not Found` | API running but endpoint wrong; verify URL matches `available-dates`, `recommend`, etc. |

### Frontend Issues

**API not responding from browser:**
- Check CORS headers: `curl -i http://localhost:8000/health` should show `Access-Control-Allow-Origin: *`
- Open browser DevTools (F12) → Network tab → see if requests are being blocked

**Data not loading:**
- Check browser console for JavaScript errors
- Verify `simple.js` is fetching from correct base URL
- Test API directly: `curl http://localhost:8000/available-dates`

---

## File Structure for Deployment

```
repository-root/
├── api_server.py                          # FastAPI app
├── Dockerfile                             # Container definition
├── render.yaml                            # Render config
├── requirements.txt                       # Python dependencies
├── web/
│   ├── simple.html                        # Frontend
│   └── static/
│       └── simple.js                      # API client
├── Pass 4 - Regime Mapping/
│   └── outputs/
│       └── factor_tilt_latest.json        # Regime data
├── Pass 5 - Portfolio Scoring/
│   ├── investor_profiles.json             # Investor profiles
│   └── candidate_portfolios.json          # Portfolio options
└── Pass 6 - Portfolio Construction/
    ├── asset_universe.json                # Factor → ETF mapping
    └── outputs/
        └── portfolio_execution_latest.json
```

**All of these must be in your GitHub repository for Render to access them.**

---

## Environment Variables (Optional)

If you want to customize behavior, add environment variables in Render dashboard:

1. Go to Web Service → Settings
2. Add environment variable:
   - **Key**: `PORT`
   - **Value**: `8000`

In your code (optional):
```python
import os
PORT = int(os.getenv("PORT", "8000"))
```

---

## Final Checklist

- [ ] All files committed to GitHub (`git status` shows nothing)
- [ ] `requirements.txt` lists: fastapi, uvicorn, pydantic
- [ ] `Dockerfile` uses `python:3.11-slim`
- [ ] `render.yaml` has `env: docker`
- [ ] Data files exist:
  - `Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json`
  - `Pass 5 - Portfolio Scoring/investor_profiles.json` + `candidate_portfolios.json`
  - `Pass 6 - Portfolio Construction/asset_universe.json`
- [ ] Frontend files in `/web`:
  - `simple.html`
  - `static/simple.js`
- [ ] API responds locally: `curl http://localhost:8000/health`
- [ ] Frontend works locally: `http://localhost:8000/web/simple.html`
- [ ] Render deployment shows "Build successful 🎉"
- [ ] Render service running: `https://macro-engine-api.onrender.com/health` returns JSON

---

## Next Steps

1. **Test locally** (see "Local Development" section)
2. **Deploy to Render** (see "Production Deployment" section)
3. **Monitor logs** for any errors
4. **Share your API URL** with users: `https://macro-engine-api.onrender.com/web/simple.html`

---

## Support

For issues:
- Check Render logs: `render logs macro-engine-api --tail`
- Check API directly: `curl -i https://macro-engine-api.onrender.com/health`
- Check browser console (F12) for frontend errors
- Review FastAPI docs: `https://macro-engine-api.onrender.com/docs`
