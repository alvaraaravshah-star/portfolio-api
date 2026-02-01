# Setup Instructions for Render Deployment

## Quick Start to Deploy

### 1. Initialize Git Repository
```bash
cd "/Users/aravshah/Documents/macro engine - interactive version"
git init
git add .
git commit -m "Initial commit: FastAPI macro engine"
```

### 2. Create GitHub Repository
- Go to https://github.com/new
- Create a new repository (e.g., `macro-engine-api`)
- Do NOT initialize with README, .gitignore, or license
- Copy the remote URL

### 3. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/macro-engine-api.git
git branch -M main
git push -u origin main
```

### 4. Connect to Render
1. Visit https://dashboard.render.com
2. Sign up / Log in with GitHub
3. Click "New +" button
4. Select "Web Service"
5. Connect your GitHub account and select `macro-engine-api` repository
6. Configure:
   - **Name**: `macro-engine-api`
   - **Environment**: Python 3
   - **Build Command**: Leave empty (auto-detected)
   - **Start Command**: Leave empty (auto-detected from Procfile)
   - **Plan**: Free (starts at $7/month for production)
7. Click "Create Web Service"

### 5. View Your Live API
Once deployed, visit:
- https://YOUR_SERVICE_NAME.onrender.com (replace with your service name)
- https://YOUR_SERVICE_NAME.onrender.com/docs (Swagger UI)

## Files Created for Deployment

- **render.yaml** - Render deployment configuration
- **Procfile** - Process file for Render
- **runtime.txt** - Python version specification
- **.gitignore** - Git ignore patterns
- **.github/workflows/deploy.yml** - GitHub Actions for auto-deployment
- **RENDER_DEPLOYMENT.md** - Detailed deployment guide

## Environment Setup (GitHub Secrets)

For GitHub Actions auto-deployment (optional):
1. In GitHub: Settings → Secrets and variables → Actions
2. Add new secret: `RENDER_DEPLOY_HOOK`
3. Value: Get from Render → Web Service → Settings → Deploy Hook

## Important Considerations

### Data Files
The API requires these JSON files in your repository:
- Pass 4: `Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json`
- Pass 5: `Pass 5 - Portfolio Scoring/investor_profiles.json`
- Pass 6: `Pass 6 - Portfolio Construction/outputs/portfolio_execution_latest.json`

Make sure to commit these files to GitHub.

### Free Tier Limitations
- Spins down after 15 minutes of inactivity (restart takes 30-60s)
- 0.5 CPU and 512MB RAM
- Good for development/testing

### Production Deployment
For production, upgrade to Starter ($7/month):
- Always-on service
- Better performance
- Reserved resources

## Testing Locally First

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn api_server:app --reload

# Test in another terminal
python api_client.py

# Or use curl
curl http://localhost:8000/docs
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| 404 on data files | Commit JSON files to GitHub, check paths in api_server.py |
| Build fails | Check `requirements.txt` syntax, ensure all packages are pip-installable |
| Service crashes | Check Render logs, verify memory usage, check for file path issues |
| Cold starts slow | Normal on free tier, upgrade for always-on |

## Custom Domain (Optional)

Add custom domain in Render dashboard:
1. Web Service → Settings → Custom Domain
2. Add your domain
3. Update DNS CNAME record

## Monitoring

- **Logs**: Render Dashboard → Web Service → Logs
- **Metrics**: Render Dashboard → Web Service → Metrics
- **Alerts**: Render Dashboard → Web Service → Settings → Alert Email
