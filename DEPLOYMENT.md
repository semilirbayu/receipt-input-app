# Deployment Guide: Receipt Processing Web App on Render

This guide provides step-by-step instructions for deploying your receipt processing application to [Render.com](https://render.com/).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Render Account Setup](#render-account-setup)
4. [Service Configuration](#service-configuration)
5. [Environment Variables](#environment-variables)
6. [Google Cloud Console Setup](#google-cloud-console-setup)
7. [Deploy to Render](#deploy-to-render)
8. [Post-Deployment Testing](#post-deployment-testing)
9. [Monitoring & Logs](#monitoring--logs)
10. [Troubleshooting](#troubleshooting)
11. [Production Optimizations](#production-optimizations)

---

## Prerequisites

Before deploying, ensure you have:

- [ ] GitHub account with your code pushed to a repository
- [ ] Google Cloud project with Sheets API enabled
- [ ] Google OAuth2 credentials (Client ID and Secret)
- [ ] Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- [ ] All tests passing locally (`pytest` runs successfully)
- [ ] Application runs locally without errors

---

## Pre-Deployment Checklist

### Step 1: Verify Local Application

```bash
# Navigate to project directory
cd /path/to/receipt-input-app

# Activate virtual environment
source venv/bin/activate

# Run application
uvicorn frontend.src.main:app --reload --port 8000
```

Visit `http://localhost:8000` and verify:
- ✅ Upload page loads
- ✅ OAuth flow works
- ✅ Receipt upload and extraction works
- ✅ Data saves to Google Sheets

### Step 2: Verify Tests Pass

```bash
# Run all tests
pytest

# Expected: 91%+ tests passing (63/69)
```

### Step 3: Commit All Changes

```bash
# Ensure all code is committed
git status

# If you have uncommitted changes:
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## Render Account Setup

### Step 1: Create Render Account

1. Go to **https://render.com/**
2. Click **"Get Started"**
3. Sign up with **GitHub** (recommended for auto-deploy)
4. Authorize Render to access your GitHub repositories

### Step 2: Connect Repository

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Find `receipt-input-app` in the list
4. Click **"Connect"**

> **Note:** If you don't see your repository, click **"Configure account"** to grant Render access.

---

## Service Configuration

### Basic Settings

Configure your web service with these settings:

| Setting | Value |
|---------|-------|
| **Name** | `receipt-input-app` (or your custom name) |
| **Region** | `Singapore` (or closest: Oregon, Frankfurt) |
| **Branch** | `main` |
| **Root Directory** | _(leave blank)_ |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn frontend.src.main:app --host 0.0.0.0 --port $PORT` |

### Plan Selection

| Plan | Price | Features | Recommendation |
|------|-------|----------|----------------|
| **Free** | $0/mo | Cold starts after inactivity, 750 hours/mo | Testing only |
| **Starter** | $7/mo | No cold starts, always on | **Recommended for production** |
| **Standard** | $25/mo | More resources, faster | High-traffic applications |

---

## Environment Variables

In the Render dashboard, scroll to **"Environment Variables"** and add the following:

### Required Variables

#### 1. Python Configuration

```bash
PYTHON_VERSION
3.11.0
```

#### 2. Google OAuth2 Credentials

```bash
GOOGLE_CLIENT_ID
your-actual-client-id.apps.googleusercontent.com

GOOGLE_CLIENT_SECRET
your-actual-client-secret
```

**Where to get these:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services → Credentials**
3. Copy your OAuth 2.0 Client ID and Secret

#### 3. OAuth Redirect URI

```bash
REDIRECT_URI
https://your-app-name.onrender.com/api/v1/auth/callback
```

**⚠️ CRITICAL:** Replace `your-app-name` with your actual Render URL!

Render assigns a URL like:
- `https://receipt-input-app.onrender.com` (free tier)
- `https://receipt-input-app-xyz.onrender.com` (if name is taken)

You'll see the exact URL in the Render dashboard after creation.

#### 4. Application Secret Key

```bash
SECRET_KEY
your-generated-64-character-hex-string
```

**Generate the secret key:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64-character string) and paste as the value.

#### 5. Upload Configuration

```bash
UPLOAD_DIR
shared/uploads

MAX_FILE_SIZE_MB
5
```

#### 6. Gemini API Key

```bash
GEMINI_API_KEY
your-gemini-api-key-here
```

**Where to get this:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy the generated key

#### 7. CORS Security

```bash
ALLOWED_ORIGINS
https://your-app-name.onrender.com,http://localhost:8000
```

**⚠️ IMPORTANT:** Replace `your-app-name` with your actual Render domain!

This restricts which domains can call your API. The localhost entry allows local development.

---

## Google Cloud Console Setup

### Step 1: Add Render Redirect URI

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services → Credentials**
3. Click on your **OAuth 2.0 Client ID**
4. Under **"Authorized redirect URIs"**, click **"Add URI"**
5. Add your production redirect URI:
   ```
   https://your-app-name.onrender.com/api/v1/auth/callback
   ```
6. Click **"Save"**

### Step 2: Verify Sheets API Enabled

1. Navigate to **APIs & Services → Library**
2. Search for **"Google Sheets API"**
3. Should show **"Manage"** button (if enabled) or **"Enable"** button (click it!)

---

## Deploy to Render

### Method 1: Initial Deployment via Dashboard

1. After configuring all settings above, scroll to bottom
2. Click **"Create Web Service"**
3. Render will:
   - Clone your repository
   - Install dependencies (`pip install -r requirements.txt`)
   - Start your application
4. Watch the deployment logs in real-time

**Expected Timeline:**
- Build phase: 2-4 minutes
- Total deployment: 3-5 minutes

**Successful deployment shows:**
```
==> Build successful 🎉
==> Starting service...
INFO - Application startup: initializing cleanup scheduler
INFO - Uvicorn running on http://0.0.0.0:10000
```

### Method 2: Auto-Deploy via Git Push (After Initial Setup)

Once deployed, Render automatically redeploys on every push to `main`:

```bash
# Make code changes
git add .
git commit -m "Update feature X"
git push origin main

# Render auto-detects the push and redeploys!
```

---

## Post-Deployment Testing

### Step 1: Verify Health Endpoint

```bash
# Replace with your actual Render URL
curl https://receipt-input-app.onrender.com/health

# Expected response:
{"status":"healthy"}
```

### Step 2: Test OAuth Flow

1. Visit: `https://your-app-name.onrender.com/`
2. Click **"Connect to Google Sheets"** (or go to `/api/v1/auth/login`)
3. Should redirect to Google login
4. Sign in with your Google account
5. Grant permissions
6. Should redirect back to your app

**If OAuth fails:**
- Check Render logs (Dashboard → Logs tab)
- Verify `REDIRECT_URI` exactly matches Google Cloud Console
- Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct

### Step 3: Test Receipt Upload

1. After authenticating, go to homepage
2. Upload a receipt image
3. Wait for extraction (should complete in <5 seconds)
4. Review extracted data

**Verify Gemini is working:**
- Check API response includes `"extraction_method": "gemini"`
- If shows `"tesseract_fallback"`, check `GEMINI_API_KEY` in Render

### Step 4: Test Column Configuration

1. Navigate to `/column-config`
2. Set column mappings:
   - Date → A
   - Description → B
   - Price → C
3. Click **"Save Column Mappings"**
4. Upload receipt and save to Google Sheets
5. Verify data appears in correct columns

---

## Monitoring & Logs

### View Real-Time Logs

In Render dashboard:
1. Click on your service
2. Go to **"Logs"** tab
3. Watch for errors or issues

**Common log entries:**
```
INFO - Application startup: initializing cleanup scheduler
INFO - Creating required directories if they don't exist
INFO - Uvicorn running on http://0.0.0.0:10000
INFO - Started server process [1]
```

### Enable Log Retention

Render free tier keeps logs for 7 days. For production:

1. Go to **Settings → Advanced**
2. Enable **"Persistent Logs"** (Starter plan required)

### Health Check Configuration

Render automatically pings your `/health` endpoint.

**To configure:**
- Settings → Health Check Path: `/health`
- Grace Period: 30 seconds
- Interval: 30 seconds

If health checks fail 3+ times, you'll receive an alert.

---

## Troubleshooting

### Issue 1: OAuth Redirect Fails

**Symptoms:** After Google login, you see "redirect_uri_mismatch" error

**Solution:**
1. Check Render environment variable `REDIRECT_URI`
2. Ensure it exactly matches Google Cloud Console (including trailing `/callback`)
3. Common mistake: Using `http://` instead of `https://`

### Issue 2: Gemini API Not Working

**Symptoms:** All extractions show `"extraction_method": "tesseract_fallback"`

**Solution:**
1. Check `GEMINI_API_KEY` in Render environment variables
2. Verify API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Check Gemini API free tier limits (15 req/min, 1500 req/day)
4. Review logs for error messages

### Issue 3: Application Crashes on Startup

**Symptoms:** Render shows "Service Unavailable" or "502 Bad Gateway"

**Solution:**
1. Check **Logs** tab for error messages
2. Common issues:
   - Missing environment variables
   - Import errors (missing dependencies in `requirements.txt`)
   - Port binding issues (ensure using `--host 0.0.0.0 --port $PORT`)

### Issue 4: Files Lost After Restart

**Symptoms:** User preferences or metrics reset to empty

**Solution:**
Render's filesystem is **ephemeral** - files are lost on restart!

**Short-term fix:**
- Upgrade to Starter plan ($7/mo)
- Add persistent disk:
  ```yaml
  disks:
    - name: receipt-storage
      mountPath: /opt/render/project/src/shared
      sizeGB: 1
  ```

**Long-term fix:**
- Migrate to PostgreSQL for user preferences
- Use Redis for sessions
- See [Production Optimizations](#production-optimizations)

### Issue 5: CORS Errors

**Symptoms:** Browser console shows "blocked by CORS policy"

**Solution:**
1. Check `ALLOWED_ORIGINS` environment variable
2. Ensure it includes your Render domain:
   ```
   https://your-app-name.onrender.com,http://localhost:8000
   ```
3. Verify no trailing slashes or extra spaces

---

## Production Optimizations

### 1. Persistent Storage (Starter Plan Required)

**Problem:** Render's filesystem is ephemeral - all files lost on restart

**Solution:** Add a persistent disk

1. In Render dashboard, go to **Settings → Disks**
2. Click **"Add Disk"**
3. Configure:
   - Name: `receipt-storage`
   - Mount Path: `/opt/render/project/src/shared`
   - Size: `1 GB` (free with Starter plan)
4. Click **"Create"**

This persists `shared/user_preferences.json` and `shared/extraction_metrics.json`.

### 2. Database Migration (Recommended for Production)

**Current limitations:**
- JSON file-based storage (lost on restart without persistent disk)
- No multi-user support
- No transaction safety

**Recommended migration:**

1. **Add PostgreSQL:**
   ```bash
   # In Render dashboard:
   # New → PostgreSQL → Free tier (1GB, 90-day expiry)
   ```

2. **Migrate user preferences:**
   - Store OAuth tokens, spreadsheet IDs, column mappings in DB
   - Update `backend/src/models/user_preference.py` to use SQLAlchemy

3. **Migrate metrics:**
   - Store extraction metrics in PostgreSQL
   - Better querying, aggregation, and reporting

### 3. Session Storage Upgrade

**Current:** In-memory sessions (lost on restart)

**Recommended:** Redis-backed sessions

```python
# Add to requirements.txt
redis
aioredis

# Update frontend/src/main.py
from starlette.middleware.sessions import SessionMiddleware
from redis import Redis

redis_client = Redis.from_url(os.getenv("REDIS_URL"))
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session",
    max_age=7 * 24 * 60 * 60,  # 7 days
    same_site="lax",
    https_only=True
)
```

### 4. Enable HTTPS Redirects

Render provides HTTPS automatically, but ensure all traffic uses it:

```python
# Add to frontend/src/main.py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

Set in Render:
```bash
ENVIRONMENT
production
```

### 5. Rate Limiting

Protect your Gemini API quota:

```python
# Add to requirements.txt
slowapi

# Add to frontend/src/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Update upload endpoint
@app.post("/api/v1/upload")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def upload_receipt(...):
    ...
```

### 6. Monitoring & Alerts

**Add error tracking:**

```bash
# Add to requirements.txt
sentry-sdk

# Add to frontend/src/main.py
import sentry_sdk

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0
    )
```

**Set up alerts:**
- Render Dashboard → Settings → Notifications
- Enable email alerts for:
  - Failed deployments
  - Health check failures
  - High memory usage

---

## Deployment Checklist

Before going live, verify:

### Configuration
- [ ] All environment variables set in Render
- [ ] Google OAuth redirect URI updated in Cloud Console
- [ ] Gemini API key is valid
- [ ] `ALLOWED_ORIGINS` includes production domain
- [ ] `SECRET_KEY` is randomly generated (64 characters)

### Code
- [ ] All tests passing (`pytest`)
- [ ] Application runs locally without errors
- [ ] All changes committed and pushed to `main`

### Render Setup
- [ ] Web service created and deployed
- [ ] Logs show successful startup
- [ ] Health check returns `{"status": "healthy"}`

### Testing
- [ ] OAuth flow works end-to-end
- [ ] Receipt upload and extraction works
- [ ] Gemini extraction method confirmed
- [ ] Data saves to Google Sheets correctly
- [ ] Column mappings persist after save

### Production Readiness
- [ ] Persistent disk configured (Starter plan)
- [ ] Error tracking enabled (Sentry)
- [ ] Monitoring and alerts configured
- [ ] HTTPS redirect enabled

---

## Additional Resources

- **Render Documentation:** https://render.com/docs
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Google Cloud Console:** https://console.cloud.google.com/
- **Google AI Studio:** https://makersuite.google.com/app/apikey

---

## Support

For deployment issues:
1. Check Render logs first (Dashboard → Logs)
2. Review this troubleshooting guide
3. Consult Render documentation
4. Open an issue in your GitHub repository

---

**Deployment Date:** [Add date when deployed]
**Production URL:** [Add your Render URL here]
**Deployed By:** [Your name]
