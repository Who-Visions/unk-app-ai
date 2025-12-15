# FastAPI & CORS Middleware Implementation

**Status**: ✅ Already Implemented  
**Project**: Unk Agent API  
**File**: `deploy.py`

---

## 🎯 Current Implementation

Your `deploy.py` already has a **production-ready FastAPI application** with **CORS middleware** properly configured.

### ✅ CORS Middleware Configuration

```python
# Lines 122-130 in deploy.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ENV == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Processing-Time"]
)
```

### 🌐 Allowed Origins

```python
# Lines 61-69
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://aiwithdav3.com",
    "https://www.aiwithdav3.com",
    "https://whovisions.com",
    "https://www.whovisions.com",
    # Add your Vercel/Netlify domains here
]
```

### 🔧 Environment-Based Behavior

| Environment | CORS Origins | Behavior |
|------------|-------------|----------|
| **Development** | `["*"]` (all origins) | Permissive - allows all origins for testing |
| **Production** | `ALLOWED_ORIGINS` list | Restrictive - only whitelisted domains |

---

## 🚀 FastAPI Features Implemented

### 1. **Lifecycle Management** (Lines 83-106)
- Startup/shutdown hooks with `lifespan` async context manager
- Firebase Admin SDK initialization
- Structured logging

### 2. **CORS Configuration** (Lines 122-130)
- ✅ Wildcard origins in development
- ✅ Whitelist in production
- ✅ Credentials enabled
- ✅ All standard HTTP methods
- ✅ Custom headers exposed

### 3. **Request Middleware** (Lines 280-299)
- Request ID generation (UUID)
- Processing time tracking
- Custom headers: `X-Request-ID`, `X-Processing-Time`
- Automatic request logging

### 4. **Authentication** (Lines 195-273)
- Firebase/OIDC token verification
- Dev token backdoor for testing
- Optional authentication dependency
- User context extraction with subscription tiers

### 5. **Error Handling** (Lines 798-822)
- HTTP exception handler
- General exception handler
- Environment-aware error messages

### 6. **API Endpoints**
- `GET /` - Root
- `GET /health` - Health check
- `GET /.well-known/agent.json` - A2A Identity Card
- `GET /models` - List cognitive modes
- `GET /models/{mode}` - Model details
- `POST /chat` - Primary chat endpoint
- `POST /chat/route` - Auto-routed chat
- `GET /usage` - User usage stats
- `GET /pricing/spikes` - Price spike detection
- `GET /pricing/history` - Price history
- `GET /pricing/trends` - Price trends
- `POST /pricing/record` - Record price snapshot

---

## 🔥 Enhancement Options

If you want to enhance your current implementation, here are some options:

### 1. **Dynamic Origin Management**

```python
# Add to deploy.py - allows dynamically adding origins without redeployment
from typing import List
import re

def validate_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Custom origin validator with pattern matching."""
    for allowed in allowed_origins:
        if allowed == "*":
            return True
        if allowed == origin:
            return True
        # Support wildcard subdomains: *.aiwithdav3.com
        if allowed.startswith("*."):
            pattern = allowed.replace("*.", r".*\.")
            if re.match(pattern + "$", origin):
                return True
    return False

# Custom CORS middleware configuration
from fastapi.middleware.cors import CORSMiddleware as BaseCORSMiddleware

class DynamicCORSMiddleware(BaseCORSMiddleware):
    def is_allowed_origin(self, origin: str) -> bool:
        return validate_origin(origin, self.allow_origins)
```

### 2. **CORS Preflight Optimization**

```python
# Add OPTIONS handler for preflight caching
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests with caching."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Max-Age": "86400",  # Cache for 24 hours
        }
    )
```

### 3. **Security Headers Middleware**

```python
# Add security headers to all responses
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 4. **Rate Limiting Middleware**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("60/minute")  # 60 requests per minute
async def chat(request: Request, chat_request: ChatRequest, ...):
    # existing implementation
    pass
```

### 5. **WebSocket CORS Support**

If you plan to add WebSocket support:

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    
    # Validate origin
    if ENV == "production" and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)  # Policy violation
        return
        
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
```

---

## 🧪 Testing CORS Configuration

### Test with cURL

```bash
# Test preflight request
curl -X OPTIONS http://localhost:8080/chat \
  -H "Origin: https://aiwithdav3.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -v

# Test actual request
curl -X POST http://localhost:8080/chat \
  -H "Origin: https://aiwithdav3.com" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev_token" \
  -d '{"message": "Hello", "mode": "default"}' \
  -v
```

### Test with JavaScript (Browser Console)

```javascript
// Test from browser console
fetch('http://localhost:8080/health', {
  method: 'GET',
  headers: {
    'Origin': 'https://aiwithdav3.com'
  },
  credentials: 'include'
})
.then(res => res.json())
.then(data => console.log('Success:', data))
.catch(err => console.error('Error:', err));
```

### Test with Python

```python
import requests

# Preflight
response = requests.options(
    'http://localhost:8080/chat',
    headers={
        'Origin': 'https://aiwithdav3.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
    }
)
print(f"Preflight Status: {response.status_code}")
print(f"CORS Headers: {dict(response.headers)}")

# Actual request
response = requests.post(
    'http://localhost:8080/chat',
    headers={
        'Origin': 'https://aiwithdav3.com',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev_token'
    },
    json={
        'message': 'Hello',
        'mode': 'default'
    }
)
print(f"Request Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 📝 Adding New Origins

To add new allowed origins for production deployment:

1. **Edit** `deploy.py` lines 61-69
2. **Add** your new origin to the `ALLOWED_ORIGINS` list:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://aiwithdav3.com",
    "https://www.aiwithdav3.com",
    "https://whovisions.com",
    "https://www.whovisions.com",
    # Netlify deployments
    "https://unk-agent.netlify.app",
    "https://unk-agent-preview.netlify.app",
    # Vercel deployments
    "https://unk-agent.vercel.app",
    "https://unk-agent-preview.vercel.app",
]
```

3. **Alternatively**, use environment variables:

```python
import os
import json

# In deploy.py
ALLOWED_ORIGINS_ENV = os.environ.get("ALLOWED_ORIGINS", "[]")
ALLOWED_ORIGINS_EXTRA = json.loads(ALLOWED_ORIGINS_ENV)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://aiwithdav3.com",
    "https://www.aiwithdav3.com",
    "https://whovisions.com",
    "https://www.whovisions.com",
] + ALLOWED_ORIGINS_EXTRA
```

Then set environment variable:
```bash
export ALLOWED_ORIGINS='["https://my-new-domain.com"]'
```

---

## 🚦 Running the Server

### Development Mode

```bash
# Install dependencies
pip install fastapi uvicorn python-multipart

# Run with auto-reload
python deploy.py
```

### Production Mode

```bash
# Set environment
export ENV=production
export PORT=8080
export GOOGLE_CLOUD_PROJECT=unk-app-480102
export GCP_LOCATION=us-central1

# Run
python deploy.py
```

### Docker (Cloud Run)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV ENV=production

CMD ["python", "deploy.py"]
```

---

## ✅ Summary

Your FastAPI + CORS implementation is **already production-ready** with:

- ✅ Proper CORS middleware configuration
- ✅ Environment-based origin whitelisting  
- ✅ Credentials support enabled
- ✅ All HTTP methods allowed
- ✅ Custom headers exposed
- ✅ Request tracking middleware
- ✅ Authentication integration
- ✅ Error handling
- ✅ Health checks
- ✅ A2A Identity Card endpoint

**No additional work needed** unless you want to implement the enhancement options above!

---

*Who Visions LLC - AI with Dav3*  
*Instagram: [@aiwithdav3](https://instagram.com/aiwithdav3)*  
*YouTube: [youtube.com/aiwithdav3](https://youtube.com/aiwithdav3)*
