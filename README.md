## Project Info

| Field | Your entry |
|---|---|
| Student name(s) | Wenjing Chen |
| Project title | End-to-End Navigation for an AMR with Reinforcement Learning |
| Project tag | RL-Navigation-for-AMR |
| Track | Research |
| Supervising faculty | Tianxiang Cui|
| Project lead | Fuhua Jia|
| Team or individual | Team |
| Cited paper being replicated |  |

**One-line summary:** This project implements and evaluates an end-to-end reinforcement learning navigation policy for an AMR in Habitat simulator, focusing on how reward design and state representation affect navigation performance.




## Environment
- [x] Python environment created
  - conda env `neupan`: Python 3.10
  - conda env `habitat`: Habitat 0.3.3 + Habitat-Baselines
- [x] Dependencies installed without conflicts
  - PyTorch (CUDA enabled, RTX 5060 Laptop GPU, 8GB VRAM)
  - IR-SIM (irsim)
  - NumPy
  - Habitat 0.3.3 + Habitat-Baselines (separate conda env)
  - NeuPAN (in neupan conda env)
  - ROS 2 Humble (installed on system, not used in current project)
- [x] Project folder structure understood
  - Project path: `~/DRL-robot-navigation-IR-SIM/`
  - Models: `robot_nav/models/` (CNNTD3, RCPG, TD3, DDPG, PPO, SAC, HCM, MARL)
  - World files: `robot_nav/worlds/`
  - Training scripts: `robot_nav/rl_train.py`, `robot_nav/rnn_train.py`
  - Test scripts: `robot_nav/rl_test.py`, `robot_nav/rnn_test.py`

## Smoke test
- [x] Smoke test command executed
- [x] No runtime crash
- [x] Output evidence attached

**Smoke test results:**

| Test | Status | Notes |
|---|---|---|
| CNNTD3 checkpoint load | ✅ Pass | Loaded from `robot_nav/models/CNNTD3/checkpoint/` |
| RCPG checkpoint load | ✅ Pass | Loaded from `robot_nav/models/RCPG/checkpoint/` (GRU) |
| IR-SIM environment launch | ✅ Pass | `eval_world.yaml` loaded, step_time=0.3s |
| Habitat import | ✅ Pass | Habitat 0.3.3, Habitat-Baselines OK |
| GPU detection | ✅ Pass | NVIDIA RTX 5060 Laptop GPU, 8151 MiB, driver 595.71.05 |
| NeuPAN environment | ✅ Pass | neupan conda env functional |
****

![environment](../src/environment.png)
[smoke test](../src/smoke_test.sh),
