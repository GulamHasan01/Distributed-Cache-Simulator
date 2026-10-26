import json
import shlex
import sys
from pathlib import Path

from cache.cache_node import CacheNode
from cache.cache_coordinator import CacheCoordinator
from cache.consistent_hashing import ConsistentHashing
from cache.exceptions import CacheError
from cache.monitoring import Monitoring
from cache.node_health import NodeHealthManager
from cache.replication import ReplicationManager


def load_config(path):  # config loader , readand cheak the cluster config provided 
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON configuration: {exc}") from exc
    nodes = config.get("nodes")
    if not isinstance(nodes, list) or not nodes or any(not isinstance(n, str) or not n for n in nodes):
        raise ValueError("'nodes' must be a non-empty list of node IDs.")
    if len(set(nodes)) != len(nodes):
        raise ValueError("Node IDs must be unique.")
    for name, minimum in (("cache_capacity", 1), ("virtual_nodes", 1), ("replication_factor", 0)):
        value = config.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise ValueError(f"'{name}' must be an integer >= {minimum}.")
    if config["replication_factor"] >= len(nodes):
        raise ValueError("'replication_factor' must be smaller than the number of nodes.")
    return config


def build_coordinator(config): #get all the dependencies and inject it and also wire them in configuration

    nodes = {node_id: CacheNode(node_id, config["cache_capacity"]) for node_id in config["nodes"]}
    hashing = ConsistentHashing(config["virtual_nodes"])
    for node_id in nodes:
        hashing.add_node(node_id)
    health = NodeHealthManager(nodes.keys())
    monitoring = Monitoring(config.get("logging_level", "INFO"))
    replication = ReplicationManager(nodes, health, monitoring)
    coordinator = CacheCoordinator(nodes, hashing, health, replication, monitoring)
    coordinator.configure_replication_factor(config["replication_factor"])
    return coordinator


def help_text(): #command for operate the cache
    print("""Commands:
  PUT <key> <value>   Store a value
  GET <key>           Retrieve a value
  DELETE <key>        Delete a key and available replicas
  STATUS              Show metrics and node details
  NODES               Show node health and cache contents
  FAIL <node-id>      Simulate node failure
  RECOVER <node-id>   Mark a node healthy again
  HELP                Show commands
  EXIT                Quit
Use quotes for values containing spaces, e.g. PUT greeting "hello world".
""")


def run_cli(coordinator): # to run the cli in lop

    print("Distributed Cache Simulator (single-process simulation)")
    help_text()
    while True:
        try:
            raw = input("cache> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not raw:
            continue
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            print(f"Invalid syntax: {exc}")
            continue
        command = parts[0].upper()
        try:
            if command == "EXIT" and len(parts) == 1:
                print("Goodbye.")
                break
            elif command == "HELP" and len(parts) == 1:
                help_text()
            elif command == "PUT" and len(parts) >= 3:
                print(coordinator.put(parts[1], " ".join(parts[2:])))
            elif command == "GET" and len(parts) == 2:
                result = coordinator.get(parts[1])
                print(f"{result['value']!r} (node={result['node']}, source={result['source']})")
            elif command == "DELETE" and len(parts) == 2:
                print(coordinator.delete(parts[1]))
            elif command == "STATUS" and len(parts) == 1:
                print(json.dumps(coordinator.status(), indent=2))
            elif command == "NODES" and len(parts) == 1:
                print(json.dumps(coordinator.nodes_status(), indent=2))
            elif command == "FAIL" and len(parts) == 2:
                coordinator.health.mark_unavailable(parts[1])
                print(f"{parts[1]} marked unavailable.")
            elif command == "RECOVER" and len(parts) == 2:
                coordinator.health.mark_healthy(parts[1])
                print(f"{parts[1]} marked healthy. Data is not automatically repaired.")
            else:
                print("Invalid command or arguments. Type HELP.")
        except (CacheError, ValueError, KeyError) as exc:
            print(f"Error: {exc}")


def main():
    try:
        config = load_config(Path(__file__).with_name("config.json"))
        run_cli(build_coordinator(config))
        return 0
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
