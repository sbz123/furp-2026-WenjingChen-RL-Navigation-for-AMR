# Code Manifest For Final Poster

Use this file when deciding what to cite or mention in the poster/report.

## Final Mainline Code

| Purpose | Primary file | Output / evidence |
|---|---|---|
| Unified final comparison | `evaluation/eval_unified.py` | `unified_comparison.json` |
| STPS v2 final method | `evaluation/eval_stps_v2.py` | `stps_v2_results.json` |
| Full RL metrics | `evaluation/evidence.py` | `full_rl_metrics.json` |
| Case figures | `figure_generation/generate_case_figures.py` | `docs/img/cases/*.png` |
| Bar charts | `figure_generation/plot_final_bars.py` | `docs/img/final_success_rate_*.png` |

## Ablation / Negative Results

| Claim | Code |
|---|---|
| Exploration helps U-trap but hurts narrow door | `evaluation/eval_expanded.py`, `scenario_tests/test_improved_hard_scenarios.py` |
| Annealing recovers precision but loses U-trap | `downloads_final_snapshot/training_ablation/rl_train_v6_anneal.py`, `downloads_final_snapshot/training_ablation/rl_train_v7_finetune.py`, `downloads_final_snapshot/stps_evaluation/eval_v7.py` |
| STPS v3 added complexity but no gain | `evaluation/script3_stps_v3.py` |
| U-trap sensitivity / diagnosis | `evaluation/eval_diagnose.py`, `downloads_final_snapshot/stps_evaluation/eval_stps_sensitivity.py` |
| RCPG comparison | `scenario_tests/test_rcpg_hard_scenarios.py` |

## Exploratory Code

| Branch | Code |
|---|---|
| NeuPAN compact-scene comparison | `scenario_tests/test_neupan_full_benchmark.py`, `downloads_final_snapshot/stps_evaluation/eval_neupan.py` |
| NeuPAN observation/inference delay | `neupan_delay_exploratory/`, `downloads_final_snapshot/neupan_delay/` |
| Real-robot / ROS node attempts | `downloads_final_snapshot/real_robot_ros/` |

## What To Mention In The Poster

Mention these:

- `eval_unified.py` for the final table.
- `eval_stps_v2.py` for the STPS method.
- `generate_case_figures.py` for the 3 success + 3 failure cases.
- `evidence.py` for supplementary RL metrics.

Do not over-emphasize these:

- NeuPAN delay experiments.
- Real-robot ROS node variants.
- Early failed architecture/training branches.

## Runnable Path Note

Most scripts were developed for:

```text
~/DRL-robot-navigation-IR-SIM
```

Some downloaded scripts still use:

```text
/root/DRL-robot-navigation-IR-SIM
```

If running downloaded scripts directly, replace `/root/DRL-robot-navigation-IR-SIM` with `~/DRL-robot-navigation-IR-SIM`.

