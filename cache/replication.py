from cache.exceptions import NodeUnavailableError


class ReplicationManager:
    def __init__(self, nodes, health, monitoring):
        self.nodes = nodes
        self.health = health
        self.monitoring = monitoring

    def replicate(self, key, value, replica_node_ids, primary_node_id):
        successful = []
        for node_id in replica_node_ids:
            if node_id == primary_node_id:
                continue
            if not self.health.is_healthy(node_id):
                self.monitoring.increment("replication_failures")
                self.monitoring.log(f"Replica {node_id} unavailable for {key!r}")
                continue
            try:
                evicted = self.nodes[node_id].put(key, value)
                if evicted is not None:
                    self.monitoring.increment("evictions")
                successful.append(node_id)
                self.monitoring.increment("replication_successes")
            except (KeyError, ValueError, NodeUnavailableError):
                self.monitoring.increment("replication_failures")
        return successful

    def delete_replicas(self, key, replica_node_ids, primary_node_id):
        deleted = []
        for node_id in replica_node_ids:
            if node_id != primary_node_id and self.health.is_healthy(node_id):
                if self.nodes[node_id].delete(key):
                    deleted.append(node_id)
        return deleted
