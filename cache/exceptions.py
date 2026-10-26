class CacheError(Exception):
    """Base class for expected cache errors."""

class CacheKeyNotFoundError(CacheError):
    """A key was not found on any healthy node."""

class CacheCapacityError(CacheError):
    """A cache cannot accept a write."""

class NodeUnavailableError(CacheError):
    """No suitable healthy node is available."""

class ReplicationError(CacheError):
    """Replication failed."""
