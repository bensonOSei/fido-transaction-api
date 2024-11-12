from functools import wraps
from typing import Optional, Any, List, Union
import json
from fastapi import Request
from datetime import datetime
import hashlib
from enum import Enum

class CacheNamespace(str, Enum):
    TRANSACTION = "transaction"
    USER = "user"
    ANALYTICS = "analytics"
    SYSTEM = "system"

class CacheManager:
    """
    Generic cache manager for handling caching operations across different routes.
    """
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data before caching."""
        if hasattr(data, '__dict__'):  # SQLAlchemy model
            return {
                key: value for key, value in data.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {
                key: self._serialize_data(value)
                for key, value in data.items()
            }
        return data
        
    @staticmethod
    def _generate_cache_key(
        namespace: str,
        identifier: Optional[Union[int, str]] = None,
        params: Optional[dict] = None,
        prefix: Optional[str] = None
    ) -> str:
        """
        Generate a consistent cache key based on namespace, identifier, and parameters.
        
        Example outputs:
        - transaction:single:123
        - user:list:skip_0:limit_20:order_created_at
        - analytics:user:456:daily
        """
        key_parts = [namespace]
        
        if prefix:
            key_parts.append(prefix)
            
        if identifier is not None:
            key_parts.append(str(identifier))
            
        if params:
            # Sort params to ensure consistent key generation
            sorted_params = sorted(
                [(k, v) for k, v in params.items() if v is not None],
                key=lambda x: x[0]
            )
            param_parts = [f"{k}_{v}" for k, v in sorted_params]
            if param_parts:
                param_string = ":".join(param_parts)
                # If param string is very long, use a hash instead
                if len(param_string) > 100:
                    param_string = hashlib.md5(
                        param_string.encode()
                    ).hexdigest()
                key_parts.append(param_string)
        
        return ":".join(key_parts)
    
    async def get_cached(self, cache_key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    async def set_cached(
        self,
        cache_key: str,
        data: Any,
        expire: int = 300
    ) -> bool:
        """Set a value in cache."""
        try:
            serialized_data = self._serialize_data(data)
            await self.redis_client.set(
                cache_key,
                json.dumps(serialized_data, default=str),
                ex=expire
            )
            return True
        except Exception as e:
            print(f"Cache error: {str(e)}")  # For debugging
            return False
    
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching the given pattern.
        Returns the number of keys removed.
        """
        try:
            keys = []
            async for key in self.redis_client.scan_iter(pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    async def invalidate_by_namespace(
        self,
        namespace: str,
        identifier: Optional[Union[int, str]] = None
    ) -> int:
        """Invalidate all cache entries for a given namespace and optional identifier."""
        pattern = f"{namespace}:*"
        if identifier:
            pattern = f"{namespace}:*{identifier}*"
        return await self.invalidate_by_pattern(pattern)
    

def cache_route(
    namespace: Union[str, CacheNamespace],
    expire: int = 300,
    identifier_param: Optional[str] = None,
    include_params: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    invalidate_namespaces: Optional[List[Union[str, CacheNamespace]]] = None
):
    """
    Generic cache decorator for API routes.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):  # Explicitly add request parameter
            # Initialize cache manager
            cache_manager = CacheManager(request.app.state.redis_client)
            
            # Extract identifier if specified
            identifier = kwargs.get(identifier_param) if identifier_param else None
            
            # Build params dict for cache key
            cache_params = {}
            if include_params:
                cache_params.update({
                    param: kwargs.get(param)
                    for param in include_params
                    if param in kwargs
                })
            
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                namespace=namespace,
                identifier=identifier,
                params=cache_params,
                prefix=prefix
            )
            
            # Try to get cached response
            cached_response = await cache_manager.get_cached(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Execute function if cache miss
            response = await func(request, *args, **kwargs)
            
            # Don't cache error responses
            if isinstance(response, dict) and response.get('error'):
                return response
            
            # Cache the response
            await cache_manager.set_cached(cache_key, response, expire)
            
            # Invalidate related caches if specified
            if invalidate_namespaces and response:
                for ns in invalidate_namespaces:
                    await cache_manager.invalidate_by_namespace(
                        namespace=ns,
                        identifier=identifier
                    )
            
            return response
        return wrapper
    return decorator