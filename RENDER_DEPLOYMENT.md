# Deploy API + Frontend to Render (Complete Guide)

## Goal
Deploy your macro engine so it runs entirely on Render:
- **API** running at: `https://macro-engine-api.onrender.com`
- **Frontend** running at: `https://macro-engine-api.onrender.com/web/simple.html`

Both served from the same Render service.

---

## Architecture

```
Your GitHub Repo
    ↓
Render detects push
    ↓
Render builds Docker image (Python 3.11)
    ↓
Renders deploys single Web Service
    ↓
Service runs FastAPI + serves static files (/web)
    ↓
Users access: https://macro-engine-api.onrender.com/web/simple.html
    ↓
Frontend calls: https://macro-engine-api.onrender.com/recommend
```

---

## Prerequisites Checklist

Before deploying, ensure:

✅ Your GitHub repo has:
- `api_server.py` (with CORS enabled)
- `Dockerfile` (using Python 3.11-slim)
- `requirements.txt` (fastapi, uvicorn, pydantic)
- `render.yaml` (with `env: docker`)
- `web/simple.html`
- `web/static/simple.js`
- All Pass 4/5/6 JSON data files

Run this to verify:
```bash
cd "/Users/aravshah/Documents/macro engine - interactive version"
git status  # Should show "nothing to commit, working tree clean"
git ls-files | grep -E "(Dockerfile|api_server|requirements|web/)" # Should list all key files
```

---

## Step 1: Push Everything to GitHub

```bash
cd "/Users/aravshah/Documents/macro engine - interactive version"

# Check what's staged
git status

# Stage all changes
git add .

# Commit
git commit -m "Final deployment: API + frontend ready for Render"

# Push
git push origin main
```

**Verify it pushed:**
```bash
git log --oneline -1  # Should show your commit
```

Go to [https://github.com/alvaraaravshah-star/portfolio-api](https://github.com/alvaraaravshah-star/portfolio-api) and verify you see:
- `Dockerfile`
- `api_server.py`
- `web/` folder
- All Pass 4/5/6 folders

---

## Step 2: Create Render Service

### Method A: Via Render Dashboard (Easiest)

1. **Login to Render**
   - Go to [https://dashboard.render.com](https://dashboard.render.com)
   - Sign in with GitHub

2. **Create New Web Service**
   - Click **"New +"** button (top right)
   - Select **"Web Service"**

3. **Connect GitHub Repository**
   - Click **"Connect GitHub"** (if not already connected)
   - Search for and select **`portfolio-api`** repository
   - Click **"Connect"**

4. **Configure Service**
   - **Name**: `macro-engine-api` (this becomes your domain)
   - **Environment**: Select **`Docker`** (NOT Python)
   - **Region**: Choose closest to you (default is fine)
   - **Branch**: `main`
   - **Build Command**: Leave empty (Dockerfile handles it)
   - **Start Command**: Leave empty (Dockerfile handles it)
   - **Plan**: Free tier (click "Free" under Instance Type)

5. **Deploy**
   - Click **"Create Web Service"**
   - Render starts building immediately

### Method B: Via Render CLI

```bash
# Login
render login

# Create service from repo
render services create \
  --name macro-engine-api \
  --type web \
  --repo alvaraaravshah-star/portfolio-api \
  --runtime docker
```

---

## Step 3: Monitor the Build

**Via Dashboard:**
1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click your service: **`macro-engine-api`**
3. Watch the **"Events"** feed for build progress

**Via CLI:**
```bash
render logs macro-engine-api --deploy --tail
```

**Expected build output:**
```
==> Building image...
==> Installing dependencies from requirements.txt...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pydantic-1.10.15
==> Build successful 🎉
==> Deploying...
==> Running 'uvicorn api_server:app --host 0.0.0.0'
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

---

## Step 4: Get Your Render URL

Once deployment completes (shows "Live" status):

1. In Render Dashboard, click your service
2. Look for the **URL** at the top: `https://macro-engine-api.onrender.com`
3. Copy this URL

**Your endpoints are now:**
- API health: `https://macro-engine-api.onrender.com/health`
- Available dates: `https://macro-engine-api.onrender.com/available-dates`
- Recommendation: `https://macro-engine-api.onrender.com/recommend`
- **Web Frontend**: `https://macro-engine-api.onrender.com/web/simple.html`

---

## Step 5: Test the API from Render

### Test 1: Health Check
```bash
curl https://macro-engine-api.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T19:00:00.123456",
  "data_files": {
    "pass4": true,
    "pass5": true,
    "pass6": true
  }
}
```

### Test 2: Get Available Dates
```bash
curl https://macro-engine-api.onrender.com/available-dates
```

**Expected response:**
```json
{
  "dates": ["2009-01-04"],
  "count": 1
}
```

### Test 3: Get Recommendation
```bash
curl -X POST https://macro-engine-api.onrender.com/recommend \
  -H "Content-Type: application/json" \
  -d '{"target_date":"2009-01-04","investor_type":"Conservative"}'
```

**Expected response:** Full portfolio recommendation JSON

---

## Step 6: Test the Frontend on Render

### Open in Browser

Go to:
```
https://macro-engine-api.onrender.com/web/simple.html
```

**You should see:**
- Dropdown with target date (2009-01-04)
- Dropdown with investor types (Conservative, Balanced, Aggressive)
- "Get Recommendation" button

### Test the Flow

1. **Select Conservative** from investor type dropdown
2. Click **"Get Recommendation"** button
3. Wait 2-3 seconds
4. You should see JSON response showing:
   ```json
   {
     "metadata": {
       "requested_investor_type": "Conservative",
       ...
     },
     "investor_profile": {
       "preferred_factors": ["Quality"],
       ...
     },
     ...
   }
   ```

5. **Try Aggressive** and click again - should show different investor profile

---

## Troubleshooting

### Service Status is "Failed"

**Check the logs:**
```bash
render logs macro-engine-api --deploy
```

**Common errors:**

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: fastapi` | `requirements.txt` not in repo or not committed. Check with `git ls-files requirements.txt` |
| `FileNotFoundError: Pass 4 - Regime Mapping/outputs/...` | Data files not in repo. Run `git add "Pass 4 - Regime Mapping/"` and push |
| `exec /bin/sh: no such file or directory` | `Dockerfile` has wrong line endings. On Mac, run `dos2unix Dockerfile` |
| `Connection refused` | Service crashed. Check logs for Python errors |

### Service is "Live" but API returns 500 errors

**Check logs:**
```bash
render logs macro-engine-api --tail
```

**Common causes:**
- Missing `candidate_portfolios.json` or `asset_universe.json` - ensure they're in repo
- Wrong Python syntax in `api_server.py` - check logs for traceback
- CORS issues - should show `Access-Control-Allow-Origin` in response headers

**Test locally to verify before deploying:**
```bash
python3 -m uvicorn api_server:app --port 8000
curl http://localhost:8000/health
```

### Frontend loads but "Get Recommendation" does nothing

**Check browser console (F12):**
1. Open your Render frontend: `https://macro-engine-api.onrender.com/web/simple.html`
2. Press **F12** to open DevTools
3. Click **Console** tab
4. Click "Get Recommendation" button
5. Look for error messages like:
   - `CORS error` → API not responding to requests (check API is running: `render logs macro-engine-api --tail`)
   - `TypeError: Cannot read property 'json'` → API returned error status code
   - `404 Not Found` → API endpoint URL wrong

**Fix CORS issues:**
Verify `api_server.py` has:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If you had to change it, commit and push:
```bash
git add api_server.py
git commit -m "Fix CORS middleware"
git push origin main
```

Render will auto-redeploy.

### "Free instance spinning down" message

This is normal on the free tier. Render stops your service after 15 minutes of inactivity. When you access it again, it takes 30-60 seconds to restart. No action needed.

To keep it running 24/7, upgrade to **Starter plan** ($7/month).

---

## Verify Everything is Working

Run this checklist:

```bash
# 1. Check Render service is running
curl -I https://macro-engine-api.onrender.com/health

# 2. Check API responds
curl https://macro-engine-api.onrender.com/available-investor-types

# 3. Check frontend loads
curl -s https://macro-engine-api.onrender.com/web/simple.html | head -5

# 4. Test full API call
curl -X POST https://macro-engine-api.onrender.com/recommend \
  -H "Content-Type: application/json" \
  -d '{"target_date":"2009-01-04","investor_type":"Balanced"}'
```

**All should return 200 status codes and JSON responses.**

---

## Share Your Live App

**Your app is now live at:**
```
https://macro-engine-api.onrender.com/web/simple.html
```

Share this URL with anyone to let them:
1. Choose a target date
2. Pick Conservative/Balanced/Aggressive
3. Get portfolio recommendations in real-time

---

## Update Code After Deployment

When you make changes locally:

```bash
# Make changes to api_server.py, web/simple.html, etc.

# Commit and push
git add .
git commit -m "Your change description"
git push origin main
```

**Render automatically redeploys** when you push to `main`. Watch the progress in Render Dashboard under "Events".

---

## Monitoring and Logs

**View live logs:**
```bash
render logs macro-engine-api --tail
```

**View deployment history:**
Go to Render Dashboard → macro-engine-api → Events

**View metrics:**
Go to Render Dashboard → macro-engine-api → Metrics

---

## Production Improvements

After verifying everything works, consider:

1. **Upgrade to Starter Plan ($7/month)**
   - Always-on (no spinning down)
   - Better performance
   - 2x CPU

2. **Add Custom Domain**
   - Settings → Custom Domain
   - Point your domain to Render

3. **Add Environment Variables**
   - Settings → Environment
   - Set API version, feature flags, etc.

4. **Enable Health Checks**
   - Settings → Health Check Path: `/health`
   - Render monitors and restarts if unhealthy

---

## Support

**If something fails:**

1. Check Render logs: `render logs macro-engine-api --tail`
2. Check GitHub repo has all files: `git ls-files`
3. Test locally: `python3 -m uvicorn api_server:app --port 8000`
4. Check browser console (F12) for frontend errors
5. Visit Render status page: https://status.render.com

**Get help:**
- Render docs: https://render.com/docs
- FastAPI docs: https://fastapi.tiangolo.com
- Your app docs: `https://macro-engine-api.onrender.com/docs` (auto-generated by FastAPI)

---

## Final Checklist

- [ ] GitHub repo pushed with all files
- [ ] Render service created successfully
- [ ] Service status shows "Live"
- [ ] `curl https://macro-engine-api.onrender.com/health` returns JSON
- [ ] Frontend loads: `https://macro-engine-api.onrender.com/web/simple.html`
- [ ] "Get Recommendation" button works
- [ ] Different investor types show different profiles
- [ ] Shared URL with team/users

✅ **You're done!** Your macro engine is live on Render.
- `Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json`
- `Pass 5 - Portfolio Scoring/investor_profiles.json`
- `Pass 6 - Portfolio Construction/outputs/portfolio_execution_latest.json`

**Note**: If using Render's free tier, data files need to be included in the repository or loaded from an external source.

#### Environment Variables (Optional)
If needed, add these in Render dashboard under Environment:
```
PORT=8000
PYTHON_VERSION=3.11
```

#### Cold Starts
Free tier services spin down after inactivity. First request may take 30-60 seconds.

#### Upgrading Plan
For production use, upgrade to Starter or Standard plan for:
- Always-on services
- Better performance
- Custom domains
- SSL certificate

### Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Start local server
python -m uvicorn api_server:app --reload

# In another terminal, test the API
python api_client.py
```

### Troubleshooting

**API returns 404 for data files:**
- Ensure all required JSON files are committed to GitHub
- Check file paths in `api_server.py`

**Build fails:**
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility

**Service crashes:**
- Check Render logs: Dashboard → Web Service → Logs
- Verify all data files are accessible
- Check for memory usage on free tier

### Auto-Deploy from GitHub

Every push to `main` branch will automatically trigger a new deployment. To disable:
- Render Dashboard → Web Service → Settings → Auto-Deploy: Off

### Custom Domain (Optional)

To use a custom domain:
1. Render Dashboard → Web Service → Settings
2. Add custom domain under "Custom Domain"
3. Update DNS records with provided CNAME
