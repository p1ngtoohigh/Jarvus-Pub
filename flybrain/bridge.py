"""HYDRA Fly Brain — read-only bridge for REAL Eon/FlyWire spike exports.

Reads genuine simulation output (Parquet) and exposes bounded, neuron-identified
telemetry on localhost. Never fabricates spike activity or modifies biological
connectome weights. It is an integration component, not the neural simulator.
Dependencies: pip install fastapi uvicorn pyarrow
Usage: python flybrain/bridge.py --spikes /path/to/real/spikes.parquet
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from collections import Counter, deque
from pathlib import Path
from typing import Any

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None

class SpikeBridge:
    def __init__(self, path: Path, max_events: int = 25000):
        self.path = path
        self.max_events = max_events
        self.events: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {"connected": False, "source": str(path), "mode": "offline"}
        self._lock = threading.Lock()

    def load(self) -> dict[str, Any]:
        if pq is None:
            raise RuntimeError("pyarrow required: pip install pyarrow")
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        file = pq.ParquetFile(self.path)
        columns = set(file.schema.names)
        time_key = "time_ms" if "time_ms" in columns else "t" if "t" in columns else None
        neuron_key = "flywire_id" if "flywire_id" in columns else "neuron_index" if "neuron_index" in columns else None
        if not time_key or not neuron_key:
            raise ValueError("Expected time_ms (or t) and flywire_id (or neuron_index)")
        recent: deque[dict[str, Any]] = deque(maxlen=self.max_events)
        total = 0
        for batch in file.iter_batches(batch_size=32768, columns=[time_key, neuron_key]):
            times = batch.column(0).to_pylist()
            neurons = batch.column(1).to_pylist()
            for t, n in zip(times, neurons):
                if t is None or n is None:
                    continue
                recent.append({"time": float(t), "neuron_id": str(n)})
                total += 1
        rows = sorted(recent, key=lambda x: x["time"])
        info = {
            "connected": True,
            "source": str(self.path.resolve()),
            "mode": "recorded_neural_spikes",
            "time_unit": "ms" if time_key == "time_ms" else "upstream_t_check_units",
            "neuron_id_type": neuron_key,
            "spikes_in_file": total,
            "spikes_retained": len(rows),
            "read_at_unix": time.time(),
            "simulation_live": False,
            "learning_verified": False,
            "connectome_modified": False,
        }
        with self._lock:
            self.events = rows
            self.metadata = info
        return info

    def snapshot(self, last_n: int = 250) -> dict[str, Any]:
        last_n = max(0, min(int(last_n), 2000))
        with self._lock:
            rows = list(self.events[-last_n:]) if last_n else []
            meta = dict(self.metadata)
        counts = Counter(x["neuron_id"] for x in rows)
        return {
            "metadata": meta,
            "events": rows,
            "active_neuron_ids": len(counts),
            "top_firing_neurons": [{"neuron_id": key, "spikes": val} for key, val in counts.most_common(25)],
            "learning": {"verified": False, "new_synapses": None, "reason": "Spike recording alone cannot prove learning or synapse formation"},
        }

def make_app(bridge: SpikeBridge):
    from fastapi import FastAPI, HTTPException
    app = FastAPI(title="HYDRA Fly Brain Telemetry", docs_url=None, redoc_url=None)
    @app.get("/health")
    def health():
        return bridge.snapshot(0)["metadata"]
    @app.get("/api/brain")
    def brain(limit: int = 250):
        return bridge.snapshot(limit)
    @app.post("/reload")
    def reload():
        # Deliberately excluded: no unauthenticated control endpoint.
        raise HTTPException(403, "Reload is only available through local process restart")
    return app

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spikes", required=True, type=Path, help="Genuine Eon/FlyWire simulation spike parquet")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8891)
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        parser.error("For safety this bridge binds only to loopback. Use authenticated access for remote viewing.")
    bridge = SpikeBridge(args.spikes)
    print(json.dumps(bridge.load(), indent=2))
    import uvicorn
    uvicorn.run(make_app(bridge), host=args.host, port=args.port)

if __name__ == "__main__":
    main()
