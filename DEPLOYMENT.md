# 🚀 Deployment & Production Guide

This guide explains how to run the Macro Engine website in production or make it available to others.

## 🏠 Local Development (Current Setup)

Currently running at: **http://localhost:5001**

### Start Development Server
```bash
cd /Users/aravshah/Documents/macro\ engine\ -\ interactive\ version/
python3 web_app.py
```

### Access from Other Devices on Same Network
If you want to access the website from another computer on the same network:

1. Find your machine's IP address:
   ```bash
   ifconfig | grep inet
   ```
   Look for `inet 192.168.x.x` or `inet 10.x.x.x`

2. Access from another device:
   ```
   http://YOUR_IP:5001
   ```

---

## 🐳 Docker Deployment

To containerize for easy deployment:

### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY web_app.py .
COPY web/ ./web/
COPY Pass*/ ./

# Expose port
EXPOSE 5001

# Run
CMD ["python3", "web_app.py"]
```

### 2. Build Image
```bash
docker build -t macro-engine:latest .
```

### 3. Run Container
```bash
docker run -p 5001:5001 macro-engine:latest
```

---

## ☁️ Cloud Deployment Options

### Option 1: Heroku
```bash
# Create app
heroku create macro-portfolio-engine

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Option 2: AWS EC2
```bash
# SSH into instance
ssh -i key.pem ec2-user@your-instance-ip

# Install Python
sudo yum install python3 python3-pip

# Clone/copy code
git clone <your-repo>

# Install dependencies
pip3 install -r requirements.txt

# Run with Gunicorn
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web_app:app
```

### Option 3: DigitalOcean App Platform
1. Connect GitHub repo
2. Set command: `python3 web_app.py`
3. Set PORT environment variable to 5001
4. Deploy

### Option 4: Vercel (if converting to Next.js)
```bash
npm install -g vercel
vercel --prod
```

---

## 🔒 Production Hardening

### 1. Use WSGI Server (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web_app:app
```

### 2. Update Flask Settings
```python
# web_app.py
app = Flask(__name__, template_folder='web', static_folder='web/static')
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False
```

### 3. Add Rate Limiting
```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(app)

@app.route('/api/run-engine', methods=['POST'])
@limiter.limit("30 per minute")
def run_engine():
    # ... rest of code
```

### 4. Add HTTPS/SSL
Use nginx reverse proxy with Let's Encrypt:
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

### 5. Environment Variables
```python
import os

DEBUG = os.getenv('DEBUG', 'False') == 'True'
FLASK_PORT = os.getenv('PORT', 5001)
```

---

## 🔄 Continuous Deployment

### GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          ssh -i $DEPLOY_KEY user@server "cd /app && git pull && pip install -r requirements.txt && systemctl restart macro-engine"
```

---

## 📊 Monitoring & Logging

### Application Logging
```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

### Health Check Endpoint
```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200
```

Monitor with:
```bash
curl http://localhost:5001/health
```

---

## 🚀 Scaling Considerations

### For More Traffic:
1. Use Gunicorn with multiple workers
2. Add Redis caching for results
3. Add Nginx reverse proxy
4. Load balance across multiple instances
5. Use CDN for static files

### Example Nginx Config
```nginx
upstream macro_engine {
    server localhost:5001;
    server localhost:5002;
    server localhost:5003;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://macro_engine;
    }
}
```

---

## 📱 Mobile App Considerations

Current website is responsive. To create native apps:

### React Native
```bash
npx create-react-native-app macro-engine-app
# Then reuse the API calls from web version
```

### Flutter
```dart
// Similar API calls to web version
```

---

## 🔄 Backup & Recovery

### Backup Configuration
```bash
# Backup Pass data
tar -czf macro-engine-backup.tar.gz \
  "Pass 4 - Regime Mapping/" \
  "Pass 5 - Portfolio Scoring/" \
  "Pass 6 - Portfolio Construction/"

# Store in S3
aws s3 cp macro-engine-backup.tar.gz s3://your-bucket/
```

### Recovery
```bash
aws s3 cp s3://your-bucket/macro-engine-backup.tar.gz .
tar -xzf macro-engine-backup.tar.gz
```

---

## 📈 Analytics Integration

Add Google Analytics:
```html
<!-- In web/index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
```

Track portfolio recommendations:
```javascript
// In web/static/app.js
gtag('event', 'portfolio_generated', {
  investor_type: investorType,
  portfolio: pass5.selected_portfolio,
  score: pass5.portfolio_score
});
```

---

## 🔐 Security Checklist

- [ ] HTTPS enabled
- [ ] CSRF protection
- [ ] Input validation
- [ ] SQL injection prevention (N/A - no DB)
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Environment variables for secrets
- [ ] Regular dependency updates
- [ ] Security headers set
- [ ] Logging & monitoring active

### Security Headers
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

## 📞 Support & Maintenance

### Troubleshooting
- Check logs: `tail -f app.log`
- Verify connectivity: `curl http://localhost:5001/health`
- Monitor resources: `top`, `iostat`

### Regular Maintenance
- Update dependencies monthly: `pip list --outdated`
- Review logs for errors
- Monitor performance metrics
- Test disaster recovery

---

## 🎯 Success Metrics

Track these KPIs:
- Page load time < 2s
- API response time < 1s
- 99.9% uptime
- < 1% error rate
- User retention > 60%

---

## 📝 Support Contact

For deployment issues:
1. Check logs first
2. Review this guide
3. Check Flask documentation
4. Test API directly with curl

---

Last Updated: January 25, 2026
