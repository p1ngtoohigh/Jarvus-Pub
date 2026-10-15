# HYDRA × Eon Fly Brain — real neural data integration

Upstream: https://github.com/eonsystemspbc/fly-brain

**Status: adapter committed, actual neural simulator not yet installed or connected.**
This repo is a static GitHub Pages interface; it cannot run a full FlyWire brain or access the Windows Jarvis runtime.

## Scientific model

The Eon project provides a whole-brain leaky integrate-and-fire network based on the FlyWire adult fruit-fly brain, with several execution backends. Its public README currently describes approximately 138k neurons and approximately 5 million model connections (not to be confused with the roughly 54.5 million individual synapses in the underlying FlyWire reconstruction). Do not conflate connectome synapses with model edges.

It exports per-neuron spike times as Parquet with `time_ms`, `neuron_index`, `flywire_id`, `trial` and `exp_name`. This adapter consumes *real* exported spikes and does not generate simulated spikes of its own.

## Windows machine installation (WSL2 Ubuntu recommended)

In WSL2, clone the scientific project and follow its pinned environment and CUDA guidance:

```bash
git clone https://github.com/eonsystemspbc/fly-brain.git
cd fly-brain
conda env create -f environment.yml
conda activate brain-fly
python main.py --brian2-cpu --t_run 0.1 --n_run 1 --no_log_file
```

The upstream environment can require Linux toolchains and significant memory. A CUDA GPU is recommended for fast runs. Confirm actual output file path from the upstream run.

In a separate Python environment install `fastapi uvicorn pyarrow`, then start the bridge:

```bash
python flybrain/bridge.py --spikes /absolute/path/to/actual/spikes.parquet
```

Local read-only endpoint: `http://127.0.0.1:8891/api/brain?limit=250`.

**Security:** binds to loopback only; do not port-forward it to the public Internet. Expose it to an authenticated iPhone UI through a user-approved, scoped private gateway. Never copy biological datasets, credentials, or private Jarvis runtime into the public GitHub Pages repository.

## What this currently proves

- Real spike recording loaded: bridge `metadata.connected=true`, `simulation_live=false`
- Specific neuron IDs and their spike counts: `top_firing_neurons`
- Evidence that the model has learned or created synapses: **not proven**; spike recordings alone are insufficient
- Jarvis movement governed by neural output: **not implemented**. Requires an explicit, tested sensory encoder and motor decoder, safety arbitration, and closed-loop experiment.
- Self-growing synaptic network: **not implemented**; baseline FlyWire connectivity must be immutable. If added later, store plasticity changes as versioned overlays, with evaluation and rollback.

## Next verified integration steps

1. Install and benchmark upstream Eon simulator on the Windows/WSL2 machine.
2. Confirm an actual exported spike Parquet and read it through this bridge.
3. Add a local authenticated event stream with bounded updates, neuron IDs, and time units.
4. Bind visual observatory to those genuine events; show *recorded* vs *live simulation* status.
5. Implement sensory encoding and motor output to drive Jarvis in a closed-loop simulation; test collision handling and task success.
6. Keep Jarvis's language reasoning, episodic memory, and tools as distinct modules; a fruit-fly LIF connectome is not a replacement for a language model.

License: Upstream Eon repository is GPL-2.0-or-later. Preserve its licensing and third-party notices when integrating code.
