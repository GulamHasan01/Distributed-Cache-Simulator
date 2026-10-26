import hashlib
from bisect import bisect


class ConsistentHashing:
    #Hash ring with virtual nodes and deterministic SHA-256 positions.
    def __init__(self, virtual_nodes=100):
        if not isinstance(virtual_nodes, int) or isinstance(virtual_nodes, bool) or virtual_nodes < 1:
            raise ValueError("virtual_nodes must be a positive integer")
        self.virtual_nodes = virtual_nodes
        self._ring = {}
        self._positions = []

    @staticmethod
    def _hash(value):
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)

    def add_node(self, node_id):
        if not node_id:
            raise ValueError("node_id cannot be empty")
        for index in range(self.virtual_nodes):
            self._ring[self._hash(f"{node_id}#{index}")] = node_id
        self._positions = sorted(self._ring)

    def remove_node(self, node_id):
        for position in [p for p, owner in self._ring.items() if owner == node_id]:
            del self._ring[position]
        self._positions = sorted(self._ring)

    def get_node(self, key):
        nodes = self.get_nodes_for_key(key, 1)
        return nodes[0] if nodes else None

    def get_nodes_for_key(self, key, count=None):
        if not self._positions:
            return []
        wanted = count if count is not None else len(set(self._ring.values()))
        if wanted <= 0:
            return []
        start = self._hash(key)
        index = bisect(self._positions, start)
        ordered = self._positions[index:] + self._positions[:index]
        result, seen = [], set()
        for position in ordered:
            node_id = self._ring[position]
            if node_id not in seen:
                result.append(node_id)
                seen.add(node_id)
                if len(result) >= wanted:
                    break
        return result

    def nodes(self):
        return sorted(set(self._ring.values()))
