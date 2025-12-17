# OpenBlog API Documentation

## 📚 Interactive API Docs

Once deployed, your FastAPI app automatically provides interactive documentation:

### **Swagger UI (Recommended)**
```
https://openblog-service.up.railway.app/docs
```
- Interactive API explorer
- Try endpoints directly from browser
- See request/response schemas
- Test API calls

### **ReDoc (Alternative)**
```
https://openblog-service.up.railway.app/redoc
```
- Clean, readable documentation
- Better for sharing with non-technical users

### **OpenAPI JSON Schema**
```
https://openblog-service.up.railway.app/openapi.json
```
- Machine-readable API specification
- Can import into Postman, Insomnia, etc.

---

## 🔌 Available Endpoints

### Health & Status
- `GET /health` - Health check endpoint
- `GET /debug/env` - Debug environment variables

### Blog Generation
- `POST /write` - Generate blog article (synchronous)
- `POST /write-async` - Generate blog article (asynchronous)
- `POST /refresh` - Refresh/update existing content

### Job Management
- `GET /jobs` - List all jobs
- `GET /jobs/{job_id}/status` - Get job status
- `POST /jobs/{job_id}/cancel` - Cancel a job
- `GET /jobs/stats` - Get job statistics
- `GET /jobs/errors` - Get error summary

### Image & Graphics
- `POST /generate-image` - Generate blog image
- `POST /generate-graphics` - Generate HTML graphics
- `POST /generate-graphics-config` - Generate graphics config

### Translation
- `POST /translate` - Translate content

---

## 📖 How to Use

1. **For Developers**: Use `/docs` endpoint
   - Open in browser
   - Click "Try it out" on any endpoint
   - Fill in parameters
   - Execute and see response

2. **For API Clients**: Use `/openapi.json`
   - Download the OpenAPI spec
   - Import into Postman/Insomnia
   - Generate client SDKs

3. **For Documentation**: Share `/redoc` link
   - Clean, readable format
   - Perfect for non-technical users

---

## 🔐 Authentication

**⚠️ IMPORTANT: API Keys Required**

All endpoints (except `/health` and `/debug/env`) require authentication via API key.

### Setting Up API Keys

1. **Generate Keys**:
   ```bash
   python3 generate_api_key.py
   ```

2. **Set Environment Variable**:
   ```bash
   export OPENBLOG_API_KEYS="ob_prod_7Zq3Am6qgCXPuFFppDswxRyTQwHBBnp6,ob_staging_biqTvDNCYoRgAUViyuibojKVKyntE9Zk"
   ```

3. **Deploy with Keys** (Railway/Vercel):
   - Add `OPENBLOG_API_KEYS` to environment variables
   - Comma-separated for multiple keys

### Using API Keys

**Method 1: Authorization Header (Recommended)**
```bash
curl -H "Authorization: Bearer ob_prod_7Zq3Am6qgCXPuFFppDswxRyTQwHBBnp6" \
     https://openblog-service.up.railway.app/write
```

**Method 2: X-API-Key Header**
```bash
curl -H "X-API-Key: ob_prod_7Zq3Am6qgCXPuFFppDswxRyTQwHBBnp6" \
     https://openblog-service.up.railway.app/write
```

### Security Features
- ✅ Cryptographically secure keys (256-bit entropy)
- ✅ Multiple keys supported (prod/staging/dev)
- ✅ Rate limiting (10 requests/minute) 
- ✅ CORS protection
- ✅ Backward compatibility (if no keys set, API stays open)

---

## 📝 Example Request

```bash
curl -X POST "https://openblog-service.up.railway.app/write" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{
    "primary_keyword": "AI automation",
    "company_url": "https://example.com"
  }'
```

**⚠️ Replace `YOUR_API_KEY_HERE` with your actual API key**

---

**Live API**: `https://openblog-service.up.railway.app` is the correct production URL.

