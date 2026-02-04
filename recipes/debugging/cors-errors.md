# CORS Errors: Diagnosis and Fixes

CORS (Cross-Origin Resource Sharing) errors are common when your frontend tries to call an API on a different domain. This guide helps diagnose and fix them.

## Quick Diagnosis

```bash
# Check CORS headers for a URL
bin/vibe cors-check https://api.example.com/endpoint

# Test with specific origin
bin/vibe cors-check https://api.example.com/endpoint -o http://localhost:3000

# Test POST with Authorization header
bin/vibe cors-check https://api.example.com/endpoint -m POST -H Authorization
```

## Common Error Messages

### "No 'Access-Control-Allow-Origin' header"

**Cause:** Server doesn't include CORS headers in response.

**Fix:** Add CORS headers to your server (see framework-specific fixes below).

### "Origin 'X' is not allowed by Access-Control-Allow-Origin"

**Cause:** Server allows different origins than your request.

**Fix:** Add your origin to the allowed list, or use `*` for development.

### "Method 'X' is not allowed by Access-Control-Allow-Methods"

**Cause:** Server doesn't allow the HTTP method you're using.

**Fix:** Add the method to `Access-Control-Allow-Methods`.

### "Request header 'X' is not allowed by Access-Control-Allow-Headers"

**Cause:** You're sending a header that the server doesn't allow.

**Fix:** Add the header to `Access-Control-Allow-Headers`.

## Framework-Specific Fixes

### Next.js (API Routes)

```typescript
// pages/api/example.ts or app/api/example/route.ts
export async function GET(request: Request) {
  return new Response(JSON.stringify({ data: 'hello' }), {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

// Handle preflight
export async function OPTIONS(request: Request) {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
```

### Next.js (next.config.js)

```javascript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ];
  },
};
```

### FastAPI

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Express.js

```javascript
const cors = require('cors');
const app = require('express')();

// Simple usage (allow all)
app.use(cors());

// Or with options
app.use(cors({
  origin: 'http://localhost:3000',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}));
```

### Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]

# Development
CORS_ALLOW_ALL_ORIGINS = True

# Production
CORS_ALLOWED_ORIGINS = [
    "https://yourfrontend.com",
]
```

### Flask

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins

# Or with options
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})
```

### Go (net/http)

```go
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusOK)
            return
        }

        next.ServeHTTP(w, r)
    })
}
```

### Rust (Actix-web)

```rust
use actix_cors::Cors;
use actix_web::{App, HttpServer};

HttpServer::new(|| {
    let cors = Cors::default()
        .allow_any_origin()
        .allow_any_method()
        .allow_any_header();

    App::new()
        .wrap(cors)
        // ... routes
})
```

## Local Development Patterns

### Proxy Through Frontend Dev Server

Instead of enabling CORS, proxy API requests through your dev server:

**Next.js (next.config.js):**
```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};
```

**Vite (vite.config.ts):**
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### Browser Extensions (Development Only)

For quick testing, browser extensions can disable CORS:
- Chrome: "CORS Unblock" or "Allow CORS"
- Firefox: "CORS Everywhere"

**Warning:** Only use these for local development, never in production.

## Production Considerations

1. **Never use `*` with credentials:** If you need `credentials: true`, you must specify exact origins.

2. **Use environment variables for origins:**
   ```javascript
   origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000']
   ```

3. **Be specific about allowed headers:** Only allow headers your API actually uses.

4. **Set appropriate Max-Age:** Cache preflight responses:
   ```
   Access-Control-Max-Age: 86400
   ```

5. **Consider security:** CORS is a security feature. Overly permissive settings can expose your API.

## Debugging Checklist

- [ ] Is the server running and reachable?
- [ ] Are CORS headers in the response? (Check Network tab)
- [ ] Is OPTIONS (preflight) request handled?
- [ ] Is your origin in the allowed list?
- [ ] Are all required headers allowed?
- [ ] Is the HTTP method allowed?
- [ ] If using credentials, is `Allow-Credentials: true` set?
- [ ] Is CORS middleware early enough in the chain?
