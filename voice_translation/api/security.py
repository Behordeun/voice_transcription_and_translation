from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import re

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit = defaultdict(list)
        self.blocked_patterns = [
            r'\.git', r'\.env', r'\.aws', r'\.ssh', r'\.docker',
            r'admin', r'phpmyadmin', r'wp-admin', r'\.php$',
            r'\.\./|\.\.\\', r'etc/passwd', r'proc/self'
        ]
        self.pattern_regex = re.compile('|'.join(self.blocked_patterns), re.IGNORECASE)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        
        # Allow static files and root
        if path == "/" or path.startswith("/static/"):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            return response
        
        # Block suspicious paths
        if self.pattern_regex.search(path):
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden"}
            )
        
        # Rate limiting: 100 requests per minute per IP
        now = time.time()
        self.rate_limit[client_ip] = [t for t in self.rate_limit[client_ip] if now - t < 60]
        
        if len(self.rate_limit[client_ip]) >= 100:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        self.rate_limit[client_ip].append(now)
        
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        return response
