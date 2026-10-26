from cache.exceptions import CacheKeyNotFoundError, NodeUnavailableError


class CacheCoordinator:

    def __init__(self, nodes, hashing, health, replication, monitoring):
        self.nodes = nodes
        self.hashing = hashing
        self.health = health
        self.replication = replication
        self.monitoring = monitoring
        self.replication_factor = 1

    def configure_replication_factor(self, factor): #update and validate the backup rep
        if not isinstance(factor, int) or isinstance(factor, bool) or factor < 0:
            raise ValueError("replication factor must be a non-negative integer")
        if factor >= len(self.nodes):
            raise ValueError("replication factor must be smaller than node count")
        self.replication_factor = factor

    def _ordered_nodes(self, key): #return all the node ordered by hashing
        return self.hashing.get_nodes_for_key(key, count=len(self.nodes))

    def _primary_and_replicas(self, key): #figure out the replica and original node
        ordered = self._ordered_nodes(key)
        if not ordered:
            raise NodeUnavailableError("No cache nodes are configured.")
        return ordered[0], ordered[1:1 + self.replication_factor], ordered

    def put(self, key, value): #add healthy node and control eviction tracking of node
        if not key:
            raise ValueError("key cannot be empty")
        self.monitoring.increment("put_requests")
        primary, replicas, ordered = self._primary_and_replicas(key)
        healthy = [node for node in ordered if self.health.is_healthy(node)]
        if not healthy:
            raise NodeUnavailableError("All cache nodes are unavailable.")
        if not self.health.is_healthy(primary):
            primary = healthy[0]
            replicas = [node for node in ordered if node != primary][:self.replication_factor]
        evicted = self.nodes[primary].put(key, value)
        if evicted is not None:
            self.monitoring.increment("evictions")
            self.monitoring.log(f"LRU evicted {evicted!r} from {primary}")
        replicas_written = self.replication.replicate(key, value, replicas, primary)
        self.monitoring.log(f"PUT key={key!r}, primary={primary}, replicas={replicas_written}")
        return f"Stored {key!r} on {primary}; successful replicas: {replicas_written}"

    def get(self, key): # to get node miss or hit
        self.monitoring.increment("get_requests")
        primary, _, ordered = self._primary_and_replicas(key)
        for node_id in [primary] + [n for n in ordered if n != primary]:
            if not self.health.is_healthy(node_id):
                continue
            value = self.nodes[node_id].get(key)
            if value is not None:
                self.monitoring.increment("cache_hits")
                return {
                    "value": value, "node": node_id,
                    "source": "primary" if node_id == primary else "fallback/replica"
                }
        self.monitoring.increment("cache_misses")
        raise CacheKeyNotFoundError(f"Key {key!r} was not found on any healthy node.")

    def delete(self, key):  # removes the key from all healthy nodes
        self.monitoring.increment("delete_requests")
        _, _, ordered = self._primary_and_replicas(key)
        deleted = []
        for node_id in ordered:
            if self.health.is_healthy(node_id) and self.nodes[node_id].delete(key):
                deleted.append(node_id)
        self.monitoring.log(f"DELETE key={key!r}, nodes={deleted}")
        if not deleted:
            raise CacheKeyNotFoundError(f"Key {key!r} was not found on healthy nodes.")
        return f"Deleted {key!r} from: {deleted}"

    def status(self):
        return {"operations": self.monitoring.status(), "nodes": self.nodes_status()}

    def nodes_status(self):
        return {
            node_id: {**node.status(), "healthy": self.health.is_healthy(node_id)}
            for node_id, node in self.nodes.items()
        }
