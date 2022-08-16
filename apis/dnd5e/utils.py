from functools import wraps


def populated(func):
    @wraps(func)
    async def decorator(self, *args, **kwargs):
        await self.endpoints
        return await func(self, *args, **kwargs)
    return decorator


def with_resource_cache(func):
    @wraps(func)
    async def decorator(self, *args, **kwargs):
        await self.resource_cache
        return await func(self, *args, **kwargs)
    return decorator
