# AMR Reinforcement Learning Navigation With Policy Switching

This repository is the final reproducibility archive for Wenjing Chen's 2026
FURP research project on autonomous mobile robot (AMR) navigation with
reinforcement learning.

The main idea is simple: instead of training a new complex neural network, the
project uses two already trained navigation policies and a transparent
`if/else` runtime supervisor to decide which policy should control the robot.

By default, the robot uses a precision-oriented policy for normal navigation.
When the robot appears stuck, oscillates back and forth, or stops making useful
progress toward the goal, the supervisor switches to an exploration-oriented
policy. After the exploration policy helps the robot move away from the local
trap, the supervisor switches back to the precision policy.

## Project Goal

End-to-end reinforcement learning policies can work well in standard navigation
scenes, but a single policy may fail in structured local-minimum cases. One
important example is a U-trap: the goal direction points through a wall, so a
reactive policy can keep pushing toward the blocked direction instead of moving
away first and escaping.

This project studies that failure mode and implements **Stall-Triggered Policy
Switching (STPS v2)** as a lightweight recovery mechanism for AMR navigation in
IR-SIM.

## Method

The system uses two frozen CNNTD3 policies:

| Policy | Role |
|---|---|
| Precision policy | Used for normal navigation, corridor following, and narrow-door alignment. |
| Exploration policy | Used temporarily when the robot is stuck or oscillating. |

The switching logic is rule-based and interpretable:

```python
if stalled or oscillating:
    active_policy = exploration_policy
elif exploration_has_made_progress:
    active_policy = precision_policy
else:
    active_policy = current_policy
```

A stall is detected when the robot's displacement over a recent time window is
smaller than a threshold. Oscillation is detected when the recent movement
direction reverses repeatedly. Once the exploration policy is active, it remains
active until the robot has moved far enough away from the stuck position, or
until a maximum recovery duration is reached.

The final STPS v2 parameters are:

| Parameter | Value |
|---|---:|
| Stall window | 20 steps |
| Stall displacement threshold | 0.15 m |
| Base exploration duration | 120 steps |
| Escape progress threshold | 0.5 m |
| Oscillation window | 12 steps |
| Oscillation reversal threshold | 5 |
| Repeated-stall exploration duration | Up to 240 steps |

This method does not train a new switching network. The two component policies
are frozen, and the supervisor is a small `if/else` controller placed above
them. This makes the behavior easier to inspect and explain than an additional
learned model.

## Evaluation

The final evaluation uses IR-SIM hard scenarios:

| Scenario | What it tests |
|---|---|
| U-trap | Whether the robot can escape a local minimum. |
| Double-U | Whether the robot can avoid entering the wrong concave region. |
| Narrow door | Whether the robot preserves precision in tight passages. |
| Symmetric corridor | Whether the robot remains stable in corridor navigation. |

The hard-scenario protocol uses 3 seeds x 12 perturbed starts per scenario.
The standard environment uses an independent 100-episode evaluation.

Final archived result summary:

| Method | Standard | U-trap | Double-U | Narrow Door | Corridor | Scenario Avg. |
|---|---:|---:|---:|---:|---:|---:|
| CNNTD3 baseline | 87% | 0 +/- 0% | 69 +/- 4% | 100 +/- 0% | 100 +/- 0% | 67% |
| NeuPAN | 0% | 0 +/- 0% | 0 +/- 0% | 0 +/- 0% | 0 +/- 0% | 0% |
| STPS v2 | 88% | 75 +/- 7% | 100 +/- 0% | 100 +/- 0% | 100 +/- 0% | 94% |

The NeuPAN result should be read only as a result for this compact benchmark
and tested planner configuration. It is not a general claim that NeuPAN fails.

## Reproducibility

Create the supported environment:

```bash
conda env create -f environment/final-stps.yml
conda activate final-stps
```

Verify archived files and checkpoint hashes:

```bash
python scripts/verify_archive.py
```

Run a headless smoke test:

```bash
python scripts/run_stps_v2.py --smoke
```

Re-run the fixed-input STPS hard-scenario evaluation:

```bash
python scripts/run_stps_v2.py --hard-only
```

Important files:

| Path | Meaning |
|---|---|
| `src/results/final/` | Canonical saved final results used in the poster/report. |
| `artifacts/checkpoints/cnntd3_final/` | Frozen CNNTD3 checkpoint files. |
| `runtime/robot_nav/` | Minimal vendored runtime needed by the final STPS runner. |
| `artifacts/SHA256SUMS.txt` | SHA-256 manifest for result and model verification. |
| `REPRODUCIBILITY.md` | Full environment, protocol, and verification notes. |

The archive has been verified on July 29, 2026. The independent rerun matches
Double-U, narrow-door, and corridor exactly. U-trap differs by one start in one
seed group: the archived result is 75.0%, while the rerun is 72.2%. Both the
canonical result and the rerun result are preserved for transparency.

## Repository Structure

```text
artifacts/       Frozen checkpoints, hashes, and reproduced run output
code/            Historical training, evaluation, ablation, and poster scripts
environment/     Conda environment file and source-machine environment snapshots
runtime/         Minimal robot_nav runtime for the final STPS evaluation
scripts/         Current verification and reproduction entry points
src/results/     Canonical saved final results
docs/            Project notes, final materials, and figures
```

## Limitations

- The policy switch thresholds are manually designed.
- The final claim is mainly validated in IR-SIM, not on a real robot.
- Exact bit-for-bit retraining of every historical policy is not claimed.
- The standard-environment random seed was not fully recovered, so that result
  is preserved as archived evidence rather than a bit-for-bit rerun target.
- NeuPAN experiments are retained as comparison and exploration, but should not
  be overclaimed beyond this benchmark configuration.

## Team and Roles

| Person | Role |
|---|---|
| Wenjing Chen | Project lead; model training, STPS switching logic, evaluation, result organization, and documentation. |
| Tianxiang Cui | Faculty supervision. |
| Fuhua Jia | Project guidance and research support. |
