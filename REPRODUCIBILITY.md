# Reproducibility Protocol

## Scope

This archive supports three distinct tasks:

| Task | Status | Entry point |
|---|---|---|
| Verify the final saved evidence and model files | Fully reproducible | `python scripts/verify_archive.py` |
| Re-run the final STPS v2 hard-scenario evaluation | Executable with fixed inputs; one U-trap trial differs from the saved result | `python scripts/run_stps_v2.py --hard-only` |
| Reproduce the archived three-method table including NeuPAN | Conditionally reproducible | See "Optional NeuPAN Baseline" |
| Re-train every historical policy bit-for-bit | Not claimed | Historical scripts are retained in `code/` |

The published hard-scenario protocol uses four fixed worlds, three start-state
seeds (`42`, `123`, and `2026`), and 12 perturbed starts per seed.
The standard-environment 100-episode value is preserved as evidence, but its
original Python random seed was not recorded. It should therefore be treated as
an independently sampled reported metric, not a bit-for-bit rerun target.

## Environment

The final evaluation was archived from the `neupan` Conda environment on
July 29, 2026:

| Item | Archived value |
|---|---|
| OS | Linux 6.8.0-136-generic x86_64, glibc 2.35 |
| Python | 3.10.20 |
| PyTorch | 2.12.0+cu130 |
| NumPy | 2.2.6 |
| IR-SIM | 2.7.5 |
| Matplotlib | 3.10.7 |
| PyYAML | 6.0.3 |
| CUDA reported by PyTorch | 13.0 |

The original project recorded an NVIDIA RTX 5060 Laptop GPU. The final
evaluation entry point uses CPU inference and does not require a GPU or display.
It has been set up for headless execution.

Create a practical environment with:

```bash
conda env create -f environment/final-stps.yml
conda activate final-stps
```

For forensic reconstruction of the exact machine environment, use:

- `environment/neupan-conda-linux-64-2026-07-29.txt`
- `environment/neupan-pip-freeze-2026-07-29.txt`

The full Pip snapshot includes unrelated ROS and development packages installed
on the source machine. The smaller `final-stps.yml` is the supported runtime
environment.

## Frozen Runtime and Weights

`runtime/robot_nav/` is the minimal source snapshot used by the current final
evaluation. It contains the IR-SIM wrapper, CNNTD3 implementation, auxiliary
imports, and exactly the five worlds used by the final scripts.

It was derived from the local final working tree based on:

```text
https://github.com/reiniscimurs/DRL-robot-navigation-IR-SIM
commit 31e1a4d511bb607e6ea38f4f8fccc842fbc7dd77
```

The archived `SIM_ENV/sim.py` includes the final local distance-shaping reward
change. That source change is retained in the runtime snapshot and is therefore
part of the reproducibility boundary.

The three frozen policies below are complete CNNTD3 checkpoints: actor,
actor-target, critic, and critic-target files are all included.

| Role | Checkpoint prefix |
|---|---|
| Baseline CNNTD3 | `CNNTD3` |
| STPS precision policy | `CNNTD3_v7_finetune_best` |
| STPS exploration policy | `CNNTD3_improved` |

Their SHA-256 hashes, together with canonical final JSON results, are recorded
in `artifacts/SHA256SUMS.txt`. Run `python scripts/verify_archive.py` before
using the archive.

## Final Evaluation Protocol

### STPS v2

The supported runner is repository-relative and contains no absolute paths:

```bash
python scripts/run_stps_v2.py --hard-only
```

STPS v2 uses the following frozen parameters:

| Parameter | Value |
|---|---:|
| Stall window | 20 steps |
| Stall displacement threshold | 0.15 m |
| Escape-policy base duration | 120 steps |
| Escape progress threshold | 0.5 m |
| Oscillation window | 12 steps |
| Oscillation reversal threshold | 5 |
| Repeated-stall escape duration | 240 steps maximum |

The runner evaluates:

| Scenario | Start position | Goal | Step limit |
|---|---|---|---:|
| U-trap | (7.5, 5.0) | (9.0, 5.0) | 500 |
| Double-U | (5.0, 5.0) | (9.0, 5.0) | 500 |
| Narrow door | (2.0, 5.0) | (8.0, 5.0) | 500 |
| Symmetric corridor | (1.0, 5.0) | (9.0, 5.0) | 500 |

### Saved Final Results

The canonical poster evidence is under `src/results/final/`. In particular,
`unified_comparison.json` is the three-method hard-scenario comparison and
`final_results_table.md` is the report-ready summary.

The final hard-scenario average is computed across four scenario means:

| Method | Scenario average |
|---|---:|
| CNNTD3 baseline | 67% |
| STPS v2 | 94% |

NeuPAN's 0% result applies only to the archived compact 10 x 10 m benchmark
and tested planner configuration. It must not be generalized as a failure of
NeuPAN outside this configuration.

### Verification Status on July 29, 2026

The archived artifacts, checkpoint hashes, runtime loading, and headless IR-SIM
smoke test were verified on the environment listed above. A complete fixed-input
STPS rerun was also performed and saved at:

```text
artifacts/reproduced/stps_v2_hard_reproduction.json
```

The rerun matched Double-U, narrow-door, and corridor results exactly. For
U-trap it produced `72.2% +/- 7.9%` with seed rates `66.7%, 66.7%, 83.3%`,
while the archived final result is `75.0% +/- 6.8%` with seed rates `66.7%,
75.0%, 83.3%`. This is a one-start difference in the seed-123 group.

The exact source of that residual discrepancy was not recoverable from the
retained artifacts. The archive therefore preserves both the original reported
result and the independently rerun result, rather than replacing one with the
other or claiming an exact rerun that was not observed.

## Optional NeuPAN Baseline

The archived three-method comparison also needs NeuPAN and its specific planner
YAML. These were not vendored because they are a separate research codebase and
have their own broader dependency surface.

The recorded dependency is:

```text
https://github.com/hanruihua/NeuPAN
commit 579e7afa239cd7ff61f7f63fbd4aaaecbb136d3b
planner: example/standard_eval/diff/planner.yaml
```

The historical unified script is `code/evaluation/eval_unified.py`. It still
uses the original external directory layout and is retained as provenance, not
as the supported one-command workflow.

## Historical Training and Ablations

`code/training_and_ablation/`, `code/scenario_tests/`, and
`code/WenjingChen/` preserve the work leading to the final method. They include
exploration-reward, curriculum, finetuning, RCPG, NeuPAN-delay, and real-robot
experiments.

Exact re-training is not claimed because the complete training seed schedule,
all replay buffers, and every intermediate data artifact were not retained.
The final frozen policies and the deterministic hard-scenario evaluation are
the reproducibility target for this archive.
