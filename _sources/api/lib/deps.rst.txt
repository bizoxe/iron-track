Module Dependencies
===================

.. autofunction:: app.lib.deps.get_redis_client

.. data:: app.lib.deps.RedisClientDep
   :type: Annotated[Redis, Depends(get_redis_client)]

   FastAPI dependency for injecting the Redis client instance.
