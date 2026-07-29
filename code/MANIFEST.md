# Historical Code Manifest

## Supported Final Reproduction

| Purpose | Current entry point | Inputs | Output |
|---|---|---|---|
| Archive integrity | `scripts/verify_archive.py` | `artifacts/SHA256SUMS.txt` | Pass/fail report |
| Runtime smoke test | `scripts/run_stps_v2.py --smoke` | Vendored runtime and frozen STPS policies | Headless five-step run |
| Final hard scenarios | `scripts/run_stps_v2.py --hard-only` | Four worlds, seeds 42/123/2026, frozen STPS policies | `artifacts/reproduced/stps_v2_hard_reproduction.json` |

## Poster Evidence

| Poster content | Historical source | Canonical saved evidence |
|---|---|---|
| Three-method hard-scenario comparison | `evaluation/eval_unified.py` | `src/results/final/unified_comparison.json` |
| STPS v2 method | `evaluation/eval_stps_v2.py` | `src/results/final/stps_v2_results.json` |
| Standard-environment supplementary metrics | `evaluation/evidence.py` | `src/results/final/full_rl_metrics.json` |
| Case figures | `figure_generation/generate_case_figures.py` | `docs/img/cases/` |
| Bar charts | `figure_generation/plot_final_bars.py` | `docs/img/final_success_rate_*.svg` |

## Historical / Exploratory Branches

- `training_and_ablation/`: reward, curriculum, finetuning, and U-trap
  specialist experiments.
- `scenario_tests/`: diagnosis and model comparisons.
- `neupan_delay_exploratory/`: NeuPAN delay work, not a final claim.
- `WenjingChen/`: final Downloads, poster, real-robot, and NeuPAN snapshots.

These files are deliberately retained but are not supported one-command
workflows because some depend on the original external directory layout,
unarchived replay buffers, or optional NeuPAN/ROS tooling.
