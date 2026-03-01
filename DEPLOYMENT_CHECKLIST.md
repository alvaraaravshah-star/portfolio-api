# FastAPI Refactoring - Deployment Checklist

## Pre-Deployment: Local Testing

### ✅ Environment Setup
- [ ] Python 3.7+ installed
- [ ] Virtual environment created (if needed)
- [ ] `pip install -r requirements.txt` executed successfully
- [ ] All dependencies installed (fastapi, uvicorn, pandas, numpy, etc.)

### ✅ Project Structure
- [ ] `api_server_refactored.py` exists
- [ ] `services/` directory with `pipeline.py` and `validation.py`
- [ ] `routers/` directory with `recommendations.py`
- [ ] All Pass 4, 5, 6 scripts in their original locations
- [ ] Output directories exist:
  - [ ] `Pass 4 - Regime Mapping/outputs/`
  - [ ] `Pass 5 - Portfolio Scoring/outputs/`
  - [ ] `Pass 6 - Portfolio Construction/outputs/`

### ✅ Local Testing
- [ ] Start API server: `python api_server_refactored.py`
- [ ] API responds on http://localhost:10000
- [ ] Health check works: GET http://localhost:10000/health
- [ ] API docs load: http://localhost:10000/docs
- [ ] Run integration tests: `python test_api.py`

### ✅ Manual Endpoint Testing

**Test Pass 4:**
```bash
curl -X POST http://localhost:10000/recommend/start \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04"}'
```
- [ ] Response status 200
- [ ] Response has "status": "success"
- [ ] Response has "stage": "pass4"

**Test Pass 5:**
```bash
curl -X POST http://localhost:10000/recommend/investor \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04", "investor_type": "Balanced"}'
```
- [ ] Response status 200
- [ ] Response has "status": "success"
- [ ] Response has "stage": "pass5"

**Test Pass 6:**
```bash
curl -X POST http://localhost:10000/recommend/final \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04", "investor_type": "Balanced"}'
```
- [ ] Response status 200
- [ ] Response has "status": "success"
- [ ] Response has "stage": "pass6"

### ✅ Error Handling Testing
- [ ] Invalid date format: `{"target_date": "invalid"}` → 400 Bad Request
- [ ] Invalid investor type: `{"investor_type": "InvalidType"}` → 400 Bad Request
- [ ] Missing field: `{}` → 422 Unprocessable Entity

### ✅ Output File Verification
After each pass runs successfully:
- [ ] `Pass 4 - Regime Mapping/outputs/factor_tilt_latest.json` exists
- [ ] `Pass 5 - Portfolio Scoring/outputs/portfolio_recommendation_latest.json` exists
- [ ] `Pass 6 - Portfolio Construction/outputs/portfolio_execution_latest.json` exists
- [ ] Output files are valid JSON (parseable)

### ✅ Logging
- [ ] Check `logs/api.log` exists (if enabled)
- [ ] Log entries show Pass 4, 5, 6 execution traces
- [ ] Error logs are detailed and helpful

---

## Pre-Deployment: Code Review

### ✅ Code Quality
- [ ] No syntax errors: `python -m py_compile api_server_refactored.py`
- [ ] No obvious bugs in services/routers
- [ ] Type hints are correct
- [ ] Error messages are user-friendly

### ✅ Configuration
- [ ] CORS origins are appropriate (["*"] for testing, ["yourdomain.com"] for prod)
- [ ] Port is configurable or documented
- [ ] Timeout values are reasonable (300s = 5 minutes)
- [ ] Logging level is appropriate for environment

### ✅ Documentation
- [ ] README or REFACTORING_GUIDE.md reviewed
- [ ] API endpoints documented
- [ ] Error codes documented
- [ ] Example requests/responses provided

---

## Deployment: Render/Railway/Cloud

### ✅ Update Deployment Config

**For Render:**
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `python api_server_refactored.py`
- [ ] Ensure PORT environment variable not needed (hardcoded to 10000) OR update app
- [ ] Set timeout to at least 300 seconds (for Pass execution)

**For Railway/Other:**
- [ ] Update start command in deployment config
- [ ] Ensure all dependencies in requirements.txt
- [ ] Check environment variables if needed
- [ ] Verify port configuration

### ✅ Pre-Deployment Verification
- [ ] All files committed to git
- [ ] requirements.txt up-to-date
- [ ] No hardcoded paths or credentials
- [ ] No large files being deployed unnecessarily

### ✅ Deploy
- [ ] Push code to repository
- [ ] Monitor deployment logs for errors
- [ ] Wait for build to complete
- [ ] Verify server starts without errors

### ✅ Post-Deployment Testing

**Test Health Check:**
```bash
curl https://yourdomain.com/health
```
- [ ] Response status 200
- [ ] Service is "healthy"

**Test Pass 4 on Production:**
```bash
curl -X POST https://yourdomain.com/recommend/start \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04"}'
```
- [ ] Response status 200
- [ ] No errors in server logs

**Test All Three Passes:**
- [ ] POST /recommend/start → 200 OK
- [ ] POST /recommend/investor → 200 OK
- [ ] POST /recommend/final → 200 OK

**Test Error Handling:**
- [ ] Invalid input → 400 Bad Request
- [ ] Missing field → 422 Unprocessable Entity

### ✅ Monitor Logs
- [ ] Check production logs for errors
- [ ] Look for missing dependencies errors
- [ ] Verify Pass scripts execute successfully
- [ ] Check for timeout issues

---

## Post-Deployment: Frontend Updates

### ✅ Update Frontend API Calls

**Old Endpoint Structure (if applicable):**
```javascript
POST /recommend
```

**New Endpoint Structure:**
```javascript
// Stage 1
POST /recommend/start

// Stage 2
POST /recommend/investor

// Stage 3
POST /recommend/final
```

### ✅ Error Handling
- [ ] Handle 400 Bad Request (invalid input)
- [ ] Handle 422 Unprocessable Entity (missing field)
- [ ] Handle 500 Internal Server Error (execution failure)
- [ ] Display user-friendly error messages

### ✅ UI Updates
- [ ] Show progress through three stages
- [ ] Display error messages from API
- [ ] Handle long execution times gracefully
- [ ] Show loading indicators during execution

---

## Production Monitoring

### ✅ Set Up Monitoring
- [ ] Monitor API uptime
- [ ] Track response times
- [ ] Log errors and exceptions
- [ ] Set up alerts for failures

### ✅ Check Regularly
- [ ] [ ] Daily: Review error logs for issues
- [ ] [ ] Weekly: Check performance metrics
- [ ] [ ] Weekly: Verify all endpoints functioning
- [ ] [ ] Monthly: Review and optimize

### ✅ Performance Tuning
If experiencing issues:
- [ ] Check subprocess execution times
- [ ] Increase timeout if needed: 300s → 600s
- [ ] Increase workers if high load: 4 → 8
- [ ] Consider caching Pass 4 output by date

---

## Rollback Plan

If something goes wrong in production:

### ✅ Quick Rollback
1. [ ] Revert to previous deployment version
2. [ ] Update start command back to: `python api_server.py`
3. [ ] Redeploy
4. [ ] Verify API is back online

### ✅ Investigate
1. [ ] Check deployment logs for errors
2. [ ] Review recent code changes
3. [ ] Check server resources (CPU, memory)
4. [ ] Verify all data files are accessible

### ✅ Debug Steps
1. [ ] SSH into server (if possible)
2. [ ] Check logs: `tail -f logs/api.log`
3. [ ] Test Pass scripts manually
4. [ ] Verify output files are being created
5. [ ] Check Python version and dependencies

---

## Issue Resolution Guide

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No module named 'pandas'" | Missing dependency | `pip install -r requirements.txt` |
| "Pass 4 did not generate output" | Script failure | Check subprocess logs, run script manually |
| "Invalid date format" | Wrong format | Use YYYY-DD-MM (e.g., 2009-01-04) |
| "Pass 5 fails after Pass 4" | Output file missing | Verify Pass 4 creates factor_tilt_latest.json |
| "Connection refused" | Server not running | Start with `python api_server_refactored.py` |
| "Timeout" | Subprocess takes too long | Increase timeout in services/pipeline.py |
| "Port already in use" | Port 10000 taken | Change port or kill process using it |

---

## Documentation & References

- **API_README.py** - Complete API documentation
- **REFACTORING_GUIDE.md** - Technical architecture guide
- **REFACTORING_SUMMARY.md** - What changed and why
- **ARCHITECTURE.md** - System architecture diagrams
- **test_api.py** - Example API calls and testing

---

## Sign-Off

- [ ] Local testing passed
- [ ] Code review completed
- [ ] Pre-deployment verification done
- [ ] Deployment executed successfully
- [ ] Post-deployment testing passed
- [ ] Production monitoring set up
- [ ] Documentation updated
- [ ] Team notified of deployment

**Deployment Date:** ___________  
**Deployed By:** ___________  
**Notes:** _________________________________________________________________

---

## Quick Command Reference

```bash
# Local Testing
python api_server_refactored.py
python test_api.py

# Check Health
curl http://localhost:10000/health

# Test Pass 4
curl -X POST http://localhost:10000/recommend/start \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04"}'

# Test Pass 5
curl -X POST http://localhost:10000/recommend/investor \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04", "investor_type": "Balanced"}'

# Test Pass 6
curl -X POST http://localhost:10000/recommend/final \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2009-01-04", "investor_type": "Balanced"}'

# Production (Gunicorn)
gunicorn api_server_refactored:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:10000 \
  --timeout 300

# Docker
docker build -t macro-engine .
docker run -p 10000:10000 macro-engine

# View Logs
tail -f logs/api.log

# Install Dependencies
pip install -r requirements.txt
```
