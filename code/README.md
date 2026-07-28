# Poster Code Package

This folder is a cleaned copy of the code used to support the final STPS poster.

The original working experiment directory is:

```text
~/DRL-robot-navigation-IR-SIM
```

Most scripts still assume that directory layout, saved model checkpoints, and the `robot_nav` Python package exist there. This folder is mainly for submission, review, and traceability.

## Folder Structure

```text
code/
  evaluation/
    eval_unified.py
    eval_stps_v2.py
    eval_expanded.py
    eval_diagnose.py
    eval_final.py
    evidence.py
    script1_full_comparison.py
    script3_stps_v3.py
    final_evaluate_all.py
    plot_training.py
    ddp_utils.py
  figure_generation/
    generate_case_figures.py
    plot_final_bars.py
    gen_screenshots.py
    gen_screenshots_clean.py
  training_and_ablation/
    rl_train.py
    rnn_train.py
    rl_train_curriculum_only.py
    rl_train_improved.py
    rl_train_v2.py
    rl_train_v2_continue.py
    rl_train_v2_continue_v2.py
    rl_train_cnntd3_v4_improved.py
    script2_train_utrap.py
  scenario_tests/
    test_u_trap_cnntd3.py
    test_narrow_door.py
    test_s5_s2.py
    test_rcpg_hard_scenarios.py
    test_improved_hard_scenarios.py
    test_curriculum_only.py
    test_dead_end_maze.py
    test_neupan_full_benchmark.py
  neupan_delay_exploratory/
    test_neupan_*.py
  downloads_final_snapshot/
    stps_evaluation/
    training_ablation/
    scenario_tests/
    neupan_delay/
    configs/
    real_robot_ros/
    model_files/
  worlds/
    robot_world.yaml
    u_trap_world.yaml
    double_u_world.yaml
    narrow_door_world.yaml
    symmetric_corridor_world.yaml
    dead_end_maze_world.yaml
  dependencies_snapshot/
    robot_nav/
```

## Poster Mapping

| Poster content | Supporting code |
|---|---|
| Main result table: CNNTD3 vs NeuPAN vs STPS | `evaluation/eval_unified.py` |
| STPS v2 method and result | `evaluation/eval_stps_v2.py` |
| STPS v3 negative result | `evaluation/script3_stps_v3.py` |
| Full RL metrics: SR, collision, reward, path length, efficiency | `evaluation/evidence.py` |
| Precision/exploration conflict and ablation | `evaluation/eval_expanded.py`, `scenario_tests/test_curriculum_only.py`, `scenario_tests/test_improved_hard_scenarios.py` |
| U-trap diagnosis and sensitivity | `evaluation/eval_diagnose.py` |
| Six case figures | `figure_generation/generate_case_figures.py` |
| Success-rate bar charts | `figure_generation/plot_final_bars.py` |
| Training curves | `evaluation/plot_training.py`, training logs in the original experiment directory |
| NeuPAN / delay exploratory results | `neupan_delay_exploratory/` |

## Key Commands

Run the final unified comparison:

```bash
conda activate neupan
cd ~/DRL-robot-navigation-IR-SIM
python eval_unified.py
```

Run STPS v2 evaluation:

```bash
conda activate neupan
cd ~/DRL-robot-navigation-IR-SIM
python eval_stps_v2.py
```

Run full RL metrics on the standard environment:

```bash
conda activate neupan
cd ~/DRL-robot-navigation-IR-SIM
python evidence.py
```

Generate case figures:

```bash
conda activate neupan
cd ~/DRL-robot-navigation-IR-SIM
python ~/furp-2026-WenjingChen-RL-Navigation-for-AMR/code/figure_generation/generate_case_figures.py
```

Generate bar charts:

```bash
cd ~/furp-2026-WenjingChen-RL-Navigation-for-AMR
python code/figure_generation/plot_final_bars.py
```

## Important Notes

- Model checkpoints are not copied here. The scripts expect checkpoints under `~/DRL-robot-navigation-IR-SIM/models/CNNTD3/checkpoint` or `~/DRL-robot-navigation-IR-SIM/robot_nav/models/CNNTD3/checkpoint`.
- `dependencies_snapshot/` is a lightweight copy of key source files for review. It is not a full standalone package.
- `downloads_final_snapshot/` preserves useful STPS-related files found in `~/Downloads`, including final test scripts that were not originally in the repo. Some of these files contain old `/root/DRL-robot-navigation-IR-SIM` paths and may need path edits before running.
- The poster figures and final data are collected separately in `poster_assets/`.
- NeuPAN delay experiments are exploratory and should not be presented as the final contribution.
