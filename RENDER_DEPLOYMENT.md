# Macro Engine API - Render Deployment Guide

## Quick Deploy to Render

### Prerequisites
- GitHub account with the repository pushed
- Render account (free tier available)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Add FastAPI macro engine with Render deployment config"

# Add remote and push (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/macro-engine.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `macro-engine-api`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api_server:app --host 0.0.0.0`
   - **Plan**: Free (or upgrade as needed)

5. Click "Create Web Service"

### Step 3: Access Your API

Once deployed, your API will be available at:
- `https://macro-engine-api.onrender.com`
- API Docs: `https://macro-engine-api.onrender.com/docs`

### Important Notes

#### File Paths
The API expects these files to be present:
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
