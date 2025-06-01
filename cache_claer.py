from diskcache import Cache

cache = Cache("./.cache")
cache.clear()
print("✅ Cache cleared.")