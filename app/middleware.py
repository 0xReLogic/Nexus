from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import redis
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class RateLimiter:
    def __init__(self):
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_available = True
        except:
            self.redis_client = None
            self.redis_available = False
            # Fallback to in-memory storage
            self.memory_store: Dict[str, Dict] = {}
    
    async def check_rate_limit(self, request: Request, max_requests: int = 10, window_seconds: int = 60):
        """Check if client has exceeded rate limit"""
        client_ip = request.client.host
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        if self.redis_available and self.redis_client:
            try:
                # Use Redis for distributed rate limiting
                key = f"rate_limit:{client_ip}"
                pipe = self.redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                # Add current request
                pipe.zadd(key, {str(current_time): current_time})
                # Count requests in window
                pipe.zcard(key)
                # Set expiration
                pipe.expire(key, window_seconds)
                
                results = pipe.execute()
                request_count = results[2]
                
                if request_count > max_requests:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                    )
            except redis.RedisError:
                # Fallback to memory storage if Redis fails
                self._check_memory_rate_limit(client_ip, current_time, window_start, max_requests)
        else:
            # Use in-memory storage
            self._check_memory_rate_limit(client_ip, current_time, window_start, max_requests)
    
    def _check_memory_rate_limit(self, client_ip: str, current_time: int, window_start: int, max_requests: int):
        """Fallback rate limiting using memory"""
        if client_ip not in self.memory_store:
            self.memory_store[client_ip] = {"requests": []}
        
        # Clean old requests
        self.memory_store[client_ip]["requests"] = [
            req_time for req_time in self.memory_store[client_ip]["requests"]
            if req_time > window_start
        ]
        
        # Add current request
        self.memory_store[client_ip]["requests"].append(current_time)
        
        if len(self.memory_store[client_ip]["requests"]) > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_requests} requests per minute."
            )

# Global rate limiter instance
rate_limiter = RateLimiter()
