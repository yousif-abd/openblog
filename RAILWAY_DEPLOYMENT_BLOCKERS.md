# Railway Deployment Blockers Summary

## Overview
This document summarizes all blockers encountered while deploying OpenBlog to Railway and the attempted solutions.

## Main Issue
Railway keeps ignoring our start command configuration and tries to run `uvicorn` directly instead of `python3 -m uvicorn`, causing `uvicorn: command not found` errors.

---

## Blocker #1: Railway Dashboard Override
**Problem:** Railway dashboard had a manual start command override (`uvicorn`) that took precedence over all config files.

**Symptoms:**
- API showed correct start command: `python -m uvicorn service.api:app --host 0.0.0.0 --port $PORT`
- But logs showed: `/bin/bash: line 1: uvicorn: command not found`
- Railway was executing `uvicorn` directly, ignoring:
  - `railway.json`
  - `Procfile`
  - `nixpacks.toml`
  - `start.sh`

**Solution:** User manually cleared the dashboard start command field.

**Status:** ✅ Resolved (but issue persisted)

---

## Blocker #2: Nixpacks Auto-Detection Override
**Problem:** Railway's Nixpacks build system auto-detects FastAPI and generates its own start command, overriding our configs.

**Symptoms:**
- Build logs showed: `║ start │ uvicorn service.api:app --host 0.0.0.0 --port $PORT`
- Nixpacks detected FastAPI and generated: `uvicorn service.api:app` (without `python -m`)
- Our `nixpacks.toml [start] cmd` was ignored
- Our `railway.json` startCommand was ignored

**Attempted Solutions:**
1. ✅ Created `nixpacks.toml` with explicit `[start] cmd = "python3 -m uvicorn..."`
2. ✅ Created `railway.json` with `deploy.startCommand`
3. ✅ Created `Procfile` with `web: python3 -m uvicorn...`
4. ✅ Created `start.sh` wrapper script
5. ✅ Added explicit `nixpacksPlan` in `railway.json`
6. ✅ Deleted and recreated service (fresh start)

**Status:** ❌ Still blocking - Nixpacks auto-detection persists

---

## Blocker #3: Dockerfile ENTRYPOINT Variable Expansion
**Problem:** When switching to Dockerfile to bypass Nixpacks, PORT environment variable wasn't expanding correctly.

**Symptoms:**
- Error: `Invalid value for '--port': '$PORT' is not a valid integer`
- Dockerfile CMD with `${PORT:-8000}` wasn't expanding
- ENTRYPOINT script wasn't executing properly

**Attempted Solutions:**
1. ✅ Created `entrypoint.sh` script
2. ✅ Used shell form CMD: `CMD python3 -m uvicorn... --port ${PORT:-8000}`
3. ✅ Used ENTRYPOINT: `ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]`
4. ✅ Set startCommand in `railway.json` with shell wrapper: `/bin/sh -c "exec python3 -m uvicorn... --port $PORT"`

**Status:** ⚠️ Partially resolved - Dockerfile created but app still returns 502

---

## Blocker #4: Railway CLI Session Expiration
**Problem:** Railway CLI authentication expired, preventing log access and manual deployment triggers.

**Symptoms:**
- `railway logs` returns: "Unauthorized. Please login with `railway login`"
- Cannot check deployment logs via CLI
- Cannot manually trigger deployments

**Solution:** Requires user to re-authenticate or check dashboard manually.

**Status:** ⚠️ Blocking further CLI troubleshooting

---

## Blocker #5: Deployment Shows Success But App Returns 502
**Problem:** Latest deployment shows SUCCESS status, but app returns 502 "Application failed to respond".

**Symptoms:**
- Deployment status: `SUCCESS` (00903525-3c2c-4915-9104-5cdb5941c6f3)
- App health endpoint: `502 Application failed to respond`
- Cannot access logs to diagnose (CLI expired)

**Possible Causes:**
1. App crashing on startup (import errors, missing dependencies)
2. App not listening on correct port
3. Start command still not working correctly
4. Environment variables not set correctly

**Status:** ❌ Blocking - Need logs to diagnose

---

## Current Configuration Files

### `railway.json`
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "/bin/sh -c \"exec python3 -m uvicorn service.api:app --host 0.0.0.0 --port $PORT\""
  }
}
```

### `Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
# ... install dependencies ...
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
```

### `entrypoint.sh`
```bash
#!/bin/bash
set -e
exec python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}
```

### `Procfile`
```
web: python3 -m uvicorn service.api:app --host 0.0.0.0 --port $PORT
```

### `nixpacks.toml`
```toml
[start]
cmd = "python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}"
```

---

## Root Cause Analysis

### Why Railway Ignores Our Configs

1. **Nixpacks Auto-Detection Priority:**
   - Railway's Nixpacks has built-in detection for FastAPI
   - When it detects FastAPI, it generates: `uvicorn main:app` (assumes uvicorn in PATH)
   - This auto-generated command takes precedence over config files
   - According to Railway docs, `railway.json` should have highest priority, but in practice Nixpacks auto-detection wins

2. **Dashboard Override:**
   - Manual dashboard settings override Config as Code (`railway.json`)
   - Even after clearing, Railway may cache the old setting

3. **Build Plan Caching:**
   - Railway may cache Nixpacks build plans
   - Fresh service should clear cache, but auto-detection still occurs

---

## Attempted Solutions Timeline

1. ✅ Updated `Procfile` and `nixpacks.toml` with `python -m uvicorn`
2. ✅ Created `railway.json` with Config as Code
3. ✅ Created `start.sh` wrapper script
4. ✅ Cleared dashboard start command manually
5. ✅ Deleted and recreated service
6. ✅ Added explicit `nixpacksPlan` in `railway.json`
7. ✅ Switched to Dockerfile builder
8. ✅ Created `entrypoint.sh` script
9. ✅ Set startCommand in `railway.json` with shell wrapper

**Result:** Still seeing `uvicorn: command not found` or `502` errors

---

## Next Steps / Recommendations

### Immediate Actions Needed:
1. **Check Railway Dashboard Logs:**
   - Go to: https://railway.com/project/2f0cb32f-0508-43e1-85ec-1dd4075e4b4d/service/bc3664df-2ba4-4967-bb16-81207ff4d569
   - Check "Deploy Logs" for latest deployment
   - Look for:
     - What command Railway actually executed
     - Any startup errors
     - Port binding issues
     - Import errors

2. **Verify GitHub Connection:**
   - Ensure service is connected to GitHub repo for auto-deploy
   - Or manually trigger deployment after fixes

3. **Alternative Solutions to Try:**
   - **Option A:** Use Railway's `railway.toml` instead of `railway.json` (if supported)
   - **Option B:** Install uvicorn globally in Dockerfile: `RUN pip install uvicorn && ln -s $(which uvicorn) /usr/local/bin/uvicorn`
   - **Option C:** Use a different deployment platform (Render, Fly.io, etc.)
   - **Option D:** Contact Railway support about Nixpacks auto-detection override issue

### If Dockerfile Approach Works:
- Ensure `railway.json` startCommand is being used (not Dockerfile ENTRYPOINT)
- Or ensure Dockerfile ENTRYPOINT properly expands PORT variable
- Test locally: `docker build -t test . && docker run -e PORT=8000 -p 8000:8000 test`

---

## Service Information

- **Service ID:** `bc3664df-2ba4-4967-bb16-81207ff4d569`
- **Project ID:** `2f0cb32f-0508-43e1-85ec-1dd4075e4b4d`
- **Environment:** `production` (16814626-e3de-44d4-a766-664cba18d92c)
- **Domain:** `https://openblog-production.up.railway.app`
- **Dashboard:** https://railway.com/project/2f0cb32f-0508-43e1-85ec-1dd4075e4b4d/service/bc3664df-2ba4-4967-bb16-81207ff4d569

---

## Environment Variables Set

- ✅ `GEMINI_API_KEY` = `***GEMINI-API-KEY-REMOVED***`
- ✅ `SERPER_API_KEY` = `***SERPER-API-KEY-REMOVED***`

---

## Files Created/Modified

### Created:
- `Dockerfile` - Docker build configuration
- `entrypoint.sh` - Startup script for Docker
- `start.sh` - Alternative startup script (not currently used)
- `railway.json` - Railway Config as Code
- `.railwayignore` - Ignore patterns for Railway

### Modified:
- `Procfile` - Updated start command
- `nixpacks.toml` - Updated start command
- `.gitignore` - Added exception for `railway.json`

---

## Key Learnings

1. **Railway's Nixpacks auto-detection is very aggressive** - It overrides config files when it detects frameworks
2. **Dashboard settings take precedence** - Even over Config as Code (`railway.json`)
3. **Dockerfile approach bypasses Nixpacks** - But requires proper PORT variable handling
4. **Railway CLI sessions expire** - Need to re-authenticate periodically
5. **Fresh service doesn't always clear cache** - Nixpacks still auto-detects even on new services

---

## References

- Railway Docs: https://docs.railway.app
- Railway Config as Code: https://docs.railway.app/reference/config-as-code
- Nixpacks Docs: https://nixpacks.com/docs
- FastAPI Deployment: https://docs.railway.app/guides/fastapi

---

*Last Updated: 2025-12-16*
*Status: Blocked - Need dashboard logs to diagnose 502 error*

