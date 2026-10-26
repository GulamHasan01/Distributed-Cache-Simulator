from cache.eviction_policy import LRUCache


class CacheNode:
    def __init__(self, node_id, capacity):
        if not node_id:
            raise ValueError("node_id cannot be empty")
        self.node_id = node_id
        self._cache = LRUCache(capacity)
        self.hits = self.misses = self.writes = self.deletes = 0

    def get(self, key):
        value = self._cache.get(key)
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def put(self, key, value):
        if not key:
            raise ValueError("key cannot be empty")
        evicted = self._cache.put(key, value)
        self.writes += 1
        return evicted

    def delete(self, key):
        deleted = self._cache.delete(key)
        if deleted:
            self.deletes += 1
        return deleted

    def contains(self, key):
        return self._cache.contains(key)

    def status(self):
        return {
            "node_id": self.node_id, "entries": len(self._cache),
            "capacity": self._cache.capacity, "hits": self.hits,
            "misses": self.misses, "writes": self.writes,
            "deletes": self.deletes, "evictions": self._cache.evictions,
            "keys": [key for key, _ in self._cache.items()]
        }
