"""Cache manager for storing scraped data temporarily."""
import json
import hashlib
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

from config import settings
from logger import setup_logger

logger = setup_logger(__name__)


class CacheManager:
    """Manages file-based caching for scraped data."""
    
    def __init__(self, cache_dir: str = None, ttl: int = None):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files (default from settings)
            ttl: Time-to-live in seconds (default from settings)
        """
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.ttl = ttl or settings.cache_ttl
        self.enabled = settings.enable_cache
        
        # Create cache directory if it doesn't exist
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            logger.info(f"Cache initialized at {self.cache_dir} with TTL={self.ttl}s")
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL.
        
        Args:
            url: URL to cache
            
        Returns:
            MD5 hash of URL as cache key
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a cache key.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"
    
    async def get(self, url: str) -> Optional[dict]:
        """Get cached data for URL.
        
        Args:
            url: URL to lookup
            
        Returns:
            Cached data dict or None if not found/expired
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            async with aiofiles.open(cache_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                cache_data = json.loads(content)
            
            # Check if cache is expired
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_at > timedelta(seconds=self.ttl):
                logger.debug(f"Cache expired for {url}")
                await self.delete(url)
                return None
            
            logger.debug(f"Cache hit for {url}")
            return cache_data['data']
            
        except Exception as e:
            logger.warning(f"Cache read failed for {url}: {e}")
            return None
    
    async def set(self, url: str, data: Any) -> bool:
        """Store data in cache.
        
        Args:
            url: URL to cache
            data: Data to store
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'url': url,
                'cached_at': datetime.now().isoformat(),
                'data': data
            }
            
            async with aiofiles.open(cache_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(cache_data, ensure_ascii=False))
            
            logger.debug(f"Cached data for {url}")
            return True
            
        except Exception as e:
            logger.warning(f"Cache write failed for {url}: {e}")
            return False
    
    async def delete(self, url: str) -> bool:
        """Delete cached data for URL.
        
        Args:
            url: URL to delete from cache
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Deleted cache for {url}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for {url}: {e}")
            return False
    
    async def clear_all(self) -> int:
        """Clear all cached data.
        
        Returns:
            Number of files deleted
        """
        if not self.enabled:
            return 0
        
        count = 0
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
                count += 1
            logger.info(f"Cleared {count} cache files")
            return count
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return count
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        if not self.enabled:
            return {'enabled': False}
        
        cache_files = list(self.cache_dir.glob('*.json'))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'enabled': True,
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'ttl_seconds': self.ttl,
            'cache_dir': str(self.cache_dir)
        }