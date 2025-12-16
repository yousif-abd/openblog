# OpenBlog API Documentation

## 📚 Interactive API Docs

Once deployed, your FastAPI app automatically provides interactive documentation:

### **Swagger UI (Recommended)**
```
https://openblog-production.up.railway.app/docs
```
- Interactive API explorer
- Try endpoints directly from browser
- See request/response schemas
- Test API calls

### **ReDoc (Alternative)**
```
https://openblog-production.up.railway.app/redoc
```
- Clean, readable documentation
- Better for sharing with non-technical users

### **OpenAPI JSON Schema**
```
https://openblog-production.up.railway.app/openapi.json
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

Currently, the API doesn't require authentication, but you may want to add:
- API keys
- Bearer tokens
- Rate limiting (already configured: 10 requests/minute)

---

## 📝 Example Request

```bash
curl -X POST "https://openblog-production.up.railway.app/write" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI automation",
    "company_url": "https://example.com"
  }'
```

---

**Note**: Replace `openblog-production.up.railway.app` with your actual domain once deployed!

