# Vendored Runtime

This is the smallest `robot_nav` source snapshot required to run the archived
STPS v2 hard-scenario evaluation. It includes the final IR-SIM wrapper,
CNNTD3 code, import-time dependencies, and five YAML worlds.

Source lineage:

```text
https://github.com/reiniscimurs/DRL-robot-navigation-IR-SIM
base commit: 31e1a4d511bb607e6ea38f4f8fccc842fbc7dd77
```

The final local `SIM_ENV/sim.py` reward implementation includes distance
shaping and is intentionally preserved here. Checkpoints are not stored in
this directory; they live in `artifacts/checkpoints/cnntd3_final/`.
