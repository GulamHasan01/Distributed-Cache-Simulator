# Distributed Cache Simulator — Core Python

This learning project simulates in-memory cache nodes, LRU eviction, consistent hashing,
manual node health, replication, logging, and a terminal interface. All nodes run in
one Python process. It is not a production distributed system and does not use real
network communication or durable storage.

## Requirements
Python 3.10+ recommended. No third-party packages are needed.

## Run (Windows PowerShell)
```powershell
python --version
python main.py
```

## Commands
- `PUT <key> <value>`
- `GET <key>`
- `DELETE <key>`
- `STATUS`
- `NODES`
- `FAIL <node-id>`
- `RECOVER <node-id>`
- `HELP`
- `EXIT`

Use quotes for values with spaces: `PUT greeting "hello world"`.

## Run tests
```powershell
python -m unittest discover -s tests -v
```

## Components
- `CacheNode`: in-memory key-value storage.
- `LRUCache`: bounded storage and least-recently-used eviction.
- `ConsistentHashing`: SHA-256 hash ring with virtual nodes.
- `CacheCoordinator`: request routing and operation orchestration.
- `NodeHealthManager`: manual healthy/unavailable flags, not real heartbeats.
- `ReplicationManager`: best-effort replica writes.
- `Monitoring`: counters and standard-library logging.

## Limitations
Data disappears when the process exits. Nodes are simulated, not separate servers.
Replication is best-effort; unavailable replicas are not repaired automatically.
Recovering a node does not restore missing data. LRU eviction can remove replica data.
The simulator does not implement transactions, authentication, durable storage, or
strong consistency. Failover checks other healthy nodes, and fallback copies can be stale.
