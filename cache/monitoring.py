import logging


class Monitoring:
    #Small in-memory counters and standard-library logging.
    def __init__(self, logging_level="INFO"):
        level = getattr(logging, str(logging_level).upper(), logging.INFO)
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
        self.logger = logging.getLogger("distributed_cache")
        self.counters = {
            "get_requests": 0, "put_requests": 0, "delete_requests": 0,
            "cache_hits": 0, "cache_misses": 0, "evictions": 0,
            "replication_successes": 0, "replication_failures": 0
        }

    def increment(self, name, amount=1):
        if name not in self.counters:
            raise KeyError(f"Unknown metric: {name}")
        self.counters[name] += amount

    def log(self, message):
        self.logger.info(message)

    def status(self):
        return dict(self.counters)
