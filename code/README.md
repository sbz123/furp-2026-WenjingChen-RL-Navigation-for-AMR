# Historical Code

This directory retains the training, ablation, scenario-test, evaluation, and
figure-generation scripts used during the project. It is preserved for
traceability, not as the primary runnable interface.

Use the repository-root commands instead:

```bash
python scripts/verify_archive.py
python scripts/run_stps_v2.py --smoke
python scripts/run_stps_v2.py --hard-only
```

The current supported final runtime is self-contained under `runtime/` and the
frozen policies are under `artifacts/checkpoints/`. Many historical scripts in
this directory intentionally retain their original `~/DRL-robot-navigation-IR-SIM`
paths so their provenance remains visible.

`evaluation/`, `figure_generation/`, and `training_and_ablation/` map to the
final poster claims and earlier experimental branches. `WenjingChen/` preserves
the final Downloads/poster snapshot. See `REPRODUCIBILITY.md` for the supported
scope and known limits.
