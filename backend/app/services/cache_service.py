"""Cache service for storing temporary data."""
from typing import Optional, Any, Dict
import json
import time
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheService:
    """In-memory cache service (can be extended to Redis)."""
    
    def __init__(self):
        """Initialize cache service."""
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.enabled = settings.CACHE_ENABLED
        self.ttl = settings.CACHE_TTL
        logger.info(f"Initialized cache service (enabled: {self.enabled})")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # Check if expired
        if time.time() > expiry:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        if not self.enabled:
            return
        
        ttl = ttl or self.ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str):
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache service instance
cache_service = CacheService()

