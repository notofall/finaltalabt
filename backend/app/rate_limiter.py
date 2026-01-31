"""
Rate Limiting Middleware
تحديد معدل الطلبات للحماية من إساءة الاستخدام
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10  # Max requests in 1 second
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Store: {ip: [(timestamp, count), ...]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.second_requests: Dict[str, list] = defaultdict(list)
    
    def _cleanup_old_requests(self, requests_list: list, window_seconds: int) -> list:
        """Remove requests older than the window"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [req for req in requests_list if req > cutoff]
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, str]:
        """
        Check if request is allowed based on rate limits.
        Returns (is_allowed, reason_if_blocked)
        """
        current_time = time.time()
        
        # Cleanup old requests
        self.second_requests[client_ip] = self._cleanup_old_requests(
            self.second_requests[client_ip], 1
        )
        self.minute_requests[client_ip] = self._cleanup_old_requests(
            self.minute_requests[client_ip], 60
        )
        self.hour_requests[client_ip] = self._cleanup_old_requests(
            self.hour_requests[client_ip], 3600
        )
        
        # Check burst limit (per second)
        if len(self.second_requests[client_ip]) >= self.burst_limit:
            return False, "طلبات كثيرة جداً. انتظر ثانية واحدة"
        
        # Check per-minute limit
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            return False, "تجاوزت الحد المسموح من الطلبات. انتظر دقيقة"
        
        # Check per-hour limit
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            return False, "تجاوزت الحد المسموح من الطلبات. انتظر ساعة"
        
        # Record this request
        self.second_requests[client_ip].append(current_time)
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
        
        return True, ""
    
    def get_remaining(self, client_ip: str) -> Dict[str, int]:
        """Get remaining requests for each window"""
        return {
            "second": max(0, self.burst_limit - len(self.second_requests.get(client_ip, []))),
            "minute": max(0, self.requests_per_minute - len(self.minute_requests.get(client_ip, []))),
            "hour": max(0, self.requests_per_hour - len(self.hour_requests.get(client_ip, [])))
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Usage in main.py:
        from app.rate_limiter import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)
    """
    
    # Endpoints to exclude from rate limiting
    EXCLUDED_PATHS = {
        "/health",
        "/api/v2/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    # Stricter limits for sensitive endpoints
    SENSITIVE_PATHS = {
        "/api/v2/auth/login": (10, 100),  # 10/min, 100/hour
        "/api/v2/auth/register": (5, 50),
        "/api/v2/auth/forgot-password": (5, 20),
    }
    
    def __init__(self, app, requests_per_minute: int = 120, requests_per_hour: int = 2000):
        super().__init__(app)
        self.default_limiter = RateLimiter(requests_per_minute, requests_per_hour)
        self.sensitive_limiters: Dict[str, RateLimiter] = {}
        
        # Create limiters for sensitive paths
        for path, (rpm, rph) in self.SENSITIVE_PATHS.items():
            self.sensitive_limiters[path] = RateLimiter(rpm, rph, burst_limit=5)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip excluded paths
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # Use sensitive limiter if applicable
        limiter = self.sensitive_limiters.get(path, self.default_limiter)
        
        is_allowed, reason = limiter.is_allowed(client_ip)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=reason,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        remaining = limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["hour"])
        
        return response


# Standalone rate limiter instance for manual use
rate_limiter = RateLimiter()

def check_rate_limit(client_ip: str) -> None:
    """
    Manual rate limit check for use in specific endpoints.
    
    Usage:
        from app.rate_limiter import check_rate_limit
        
        @router.post("/sensitive-action")
        async def sensitive_action(request: Request):
            check_rate_limit(request.client.host)
            ...
    """
    is_allowed, reason = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason
        )
