from cache.exceptions import NodeUnavailableError


class NodeHealthManager:
    def __init__(self, node_ids):
        self._health = {node_id: True for node_id in node_ids}

    def mark_unavailable(self, node_id):
        if node_id not in self._health:
            raise ValueError(f"Unknown node: {node_id}")
        self._health[node_id] = False

    def mark_healthy(self, node_id):
        if node_id not in self._health:
            raise ValueError(f"Unknown node: {node_id}")
        self._health[node_id] = True

    def is_healthy(self, node_id):
        return self._health.get(node_id, False)

    def healthy_nodes(self):
        return [node for node, healthy in self._health.items() if healthy]

    def require_healthy(self, node_id):
        if not self.is_healthy(node_id):
            raise NodeUnavailableError(f"Node {node_id} is unavailable.")

    def status(self):
        return dict(self._health)
