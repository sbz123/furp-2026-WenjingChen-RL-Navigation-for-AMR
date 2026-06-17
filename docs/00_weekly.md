# Weekly Progress Log

> Update this file **every week**. Add a new entry at the top for each week.
> This is the first thing we check during review. Keep it honest and specific — it also feeds your attendance record (Rule 1).

**How to use:** copy the *Week template* block below for each new week. Newest week goes at the top.

---

## Week template — copy me

### Week N — YYYY-MM-DD

**Attended this week's meeting:** Yes / No (if No, did you email leave? Yes / No)

**Progress this week**
- _What did you actually do / finish?_

**Challenges & blockers**
- _What got in the way? What are you stuck on?_

**Next steps**
- _What will you do next week?_

**Hours spent (optional):** _e.g. 6h_

**Links (optional):** _commits, notebooks, docs, datasets..._

---

<!-- =================  YOUR ENTRIES BELOW  ================= -->


### Week 2 — 2026-06-15

**Attended this week's meeting:** Yes

**Progress this week**

- Started Habitat PPO PointNav training (official baseline):
  - Algorithm: PPO, Scene: van-gogh-room
  - update 0: success = 0.000
  - update ~650: success first appears (0.333)
  - update ~12000: success ≈ 0.85, SPL ≈ 0.65
- Fixed PyTorch 2.6 checkpoint compatibility issue
  (added weights_only=False in ddp_utils.py line 224)
  to enable resume training without deleting checkpoints.
- Generated training curve with moving average (plot_training.py).
- Ran reward shaping experiments (3 variants, see below).
- Generated success and failure episode videos, converted to GIF.
- Installed NeuPAN (TRO 2025) in separate conda environment,
  ran 3 scenarios for comparison with PPO baseline.

**Training curve analysis**

![Training curve baseline](../src/training_curve.png)

Three distinct phases observed:

1. Learning phase (update 0-2000): success rises from 0 to ~0.75,
   agent transitions from random exploration to goal-directed navigation.
2. Convergence phase (update 2000-12000): moving average stabilizes
   at ~0.85 success, ~0.65 SPL.
3. Fluctuation: large variance caused by scene switching in dataset,
   not a training failure.

Reward moving average stays near 0 despite high success rate,
meaning most reward comes from the sparse success bonus.
This motivates the reward shaping experiments below.

**Reward shaping experiments**

| Experiment | Penalty | Result |
|---|---|---|
| Baseline | none | SR ~0.85, SPL ~0.65, converges fast |
| Experiment 1 | -0.5 | Failed: reward stuck at -0.015, success = 0 |
| Experiment 2 | -0.1 | Learning but slow: SR ~0.6 at update 10000 |

![Comparison curve](../src/comparison_curve.png)

The comparison clearly shows penalty -0.5 completely fails
(flat red line at 0), while penalty -0.1 learns slowly
(blue line lags ~3000 updates behind baseline).
Neither variant beats the baseline, which is itself a finding:
naive collision penalties hurt more than they help.

**Experiment 1 analysis (penalty = -0.5):**
Penalty too large relative to distance reward signal.
Negative reward dominated, agent learned to stay still
rather than explore. Classic reward shaping failure:
too strong a penalty prevents exploration entirely.

**Experiment 2 analysis (penalty = -0.1):**
Agent can learn but convergence is ~3x slower than baseline.
Suggests collision penalty changes exploration behavior,
making the agent more cautious at the cost of learning speed.

**Key finding:**
Reward shaping is a double-edged sword.
Too strong → training fails.
Too weak → no effect.
Careful tuning is required.

**Deeper analysis:**

The baseline reward function is sparse:
most of the learning signal comes from the +2.5 success bonus,
which the agent only receives at the very end of an episode.
This explains why early training (update 0-650) shows zero success —
the agent never reaches the goal by chance, so it receives
no positive feedback.

Adding collision penalty was intended to provide denser signal,
but introduced a new problem: the penalty dominates early training
when the agent has not yet learned to navigate,
causing it to avoid movement altogether (penalty -0.5 case)
or move very cautiously (penalty -0.1 case).

This reveals a fundamental tension in reward design:
- Dense rewards help learning speed but can distort behavior.
- Sparse rewards preserve correct behavior but slow learning.

A better approach (future work) would be potential-based reward
shaping, which provides dense guidance while mathematically
guaranteeing the optimal policy is unchanged.

**Success Cases**

| | |
|:---:|:---|
| ![success_1](../src/success_1.gif) | **Case 1: Near-optimal navigation (SPL=0.99)** <br> Start: distance=1.98m → End: success=1, SPL=0.99 <br> Agent moves directly toward goal with minimal turns. <br> SPL=0.99 means path was almost identical to shortest path. <br> Represents the best-case behavior of the trained policy. |
| ![success_2](../src/success_2.gif) | **Case 2: Medium distance success (SPL=0.96)** <br> Start: distance=4.82m → End: success=1, SPL=0.96 <br> Longer episode, agent maintains goal-directed movement. <br> Confirms policy generalizes across different starting distances. |
| ![success_3](../src/success_3.gif) | **Case 3: van-gogh-room success (SPL=0.98)** <br> Start: distance=2.12m → End: success=1, SPL=0.98 <br> Simple room layout allows agent to find efficient path. <br> Training scene — policy performs best in familiar environments. |

---

**Failure Cases**

| | |
|:---:|:---|
| ![failure_1](../src/failure_1.gif) | **Case 1: Wall-stuck failure** <br> Start: distance=3.92m → End: distance=5.28m (got further away) <br> Agent spawns facing a wall, depth camera sees only darkness. <br> Repeatedly collides, moves away from goal instead of toward it. <br> **Root cause:** no obstacle avoidance or recovery strategy. |
| ![failure_2](../src/failure_2.gif) | **Case 2: Long-distance failure** <br> Start: distance=11.81m → End: distance=11.81m (no movement) <br> Goal far outside training distribution, agent barely moves. <br> **Root cause:** policy not generalized to long-horizon tasks. <br> **Proposed fix:** curriculum learning. |
| ![failure_3](../src/failure_3.gif) | **Case 3: Immediate termination** <br> Duration: 0.2s, episode ends almost instantly. <br> Goal distance: 12.32m — beyond policy capability. <br> **Root cause:** episode difficulty exceeds policy capability. <br> Suggests evaluation set contains unsolvable episodes, inflating failure rate. |


**NeuPAN comparison study**

NeuPAN (TRO 2025) is a model-based neural planner that directly
maps obstacle point clouds to control actions via MPC optimization.
Installed in a separate conda environment (Python 3.10) to avoid
dependency conflicts with Habitat.

| Scenario | Result | Notes |
|---|---|---|
| corridor (static obstacles) | ✅ Success | Smooth wave path, 20.4s |
| dyna_obs (dynamic obstacles) | ❌ Failed | Moving obstacles too fast |
| non_obs (non-convex obstacles) | ✅ Success | Handles irregular shapes |


| | |
|:---:|:---|
| ![neupan_corridor](../src/neupan_corridor.gif) | **Corridor navigation** <br> Robot navigates through corridor with static obstacles. <br> Green wave trajectory shows real-time path adjustment. <br> Forward execution time: **0.083ms** per step. <br> Successfully reaches goal in 20.4s. |
| ![neupan_dyna_obs](../src/neupan_dyna_obs.gif) | **Dynamic obstacles (failed)** <br> Moving circular obstacles cross the robot path. <br> Robot collides and fails to reach goal. <br> **Root cause:** MPC prediction horizon insufficient <br> for fast-moving obstacles. Known NeuPAN limitation. |
| ![neupan_non_obs](../src/neupan_non_obs.gif) | **Non-convex obstacles** <br> Irregular-shaped obstacles scattered in environment. <br> Robot successfully navigates around all obstacles. <br> Point-level constraints handle arbitrary shapes without <br> requiring explicit shape models. |

**PPO vs NeuPAN comparison:**

| Aspect | PPO (this project) | NeuPAN |
|---|---|---|
| Method | Reinforcement Learning | MPC + Neural Network |
| Static obstacles | ⚠️ Sometimes wall-stuck | ✅ Handles well |
| Dynamic obstacles | ❌ Not tested | ⚠️ Struggles |
| Non-convex obstacles | ❌ Not tested | ✅ Handles well |
| Training time | Hours (12000+ updates) | 1-2h (DUNE model only) |
| Inference speed | ~ms | **0.083ms** |
| Map required | Yes (Habitat scene) | ❌ Map-free |
| Generalization | Limited to training scenes | Any environment |

**Key insight:**
NeuPAN is faster and more generalizable for local obstacle
avoidance. PPO learns end-to-end from raw pixels without
manual constraint design, making it more flexible for
complex tasks. The ideal system combines both: NeuPAN for
local avoidance, RL for high-level goal understanding.

---
**What worked:**
- Baseline PPO learns PointNav (SR ~0.85, SPL ~0.65)
- Training curve shows clear 3-phase learning signal
- Reward shaping experiments reveal important trade-offs
- NeuPAN demonstrates superior obstacle handling (static/non-convex)


**What did not work:**
- Collision penalty -0.5: too strong, kills exploration
- Collision penalty -0.1: enables learning but 3x slower
- Neither penalty outperforms baseline
- NeuPAN fails on fast dynamic obstacles

**Challenges & blockers**

- Hydra curly braces syntax error: resolved by hardcoding data path.
- PyTorch 2.6 checkpoint load failure: resolved by weights_only=False.
- Collision penalty -0.5 killed learning: identified and documented
  as a failed experiment, reduced to -0.1.
- Success rate shows large fluctuations during training:
  identified as normal behavior caused by scene switching,
  not a training failure.
- NeuPAN dependency conflicts: resolved with separate conda env.


**Next steps**

1. **Implement potential-based reward shaping**
   F(s,s') = γΦ(s') - Φ(s), Φ = distance to goal.
   Mathematically guarantees optimal policy preserved.

2. **Fix stopping error**
   Add small reward for STOP when distance < 0.5m.

3. **Address long-distance failure**
   Curriculum learning: short distances first, increase gradually.

4. **Address wall-stuck failure**
   Delayed penalty: apply collision penalty only after
   agent has learned basic navigation.

5. **Read PPO and reward shaping papers**
   Schulman et al. 2017 (PPO), Ng et al. 1999 (reward shaping).


**Hours spent:** 

**Links:**
- [Training curve (baseline)](../src/training_curve.png)
- [Comparison curve](../src/comparison_curve.png)
- [Training log baseline](../src/training_log_baseline.txt)
- [Plot script](../src/plot_training.py)
- [Success case 1 SPL=0.99](../src/success_1.gif)
- [Success case 2 SPL=0.96](../src/success_2.gif)
- [Success case 3 SPL=0.98](../src/success_3.gif)
- [Failure case 1 wall stuck](../src/failure_1.gif)
- [Failure case 2 far goal](../src/failure_2.gif)
- [Failure case 3 episode terminated](../src/failure_3.gif)

   
### Week 1 — 2026-06-6

**Attended this week's meeting:** Yes

**Progress this week**
- Installed Habitat-Lab + habitat-baselines on Ubuntu 22.04 (RTX 5060, 8GB VRAM).
- Selected reproduction target: DD-PPO (Wijmans et al., ICLR 2020).
- Studied core concepts: PointNav task, reward shaping, PPO, NeuPAN.
- Installed ROS 2 Humble on native Ubuntu 22.04 dual-boot system.
- Ran TurtleSim to verify basic ROS 2 node and topic communication.
- Locally deployed Qwen VLM (4-bit quantized, ~988MB VRAM) and built
  a mini VLN pipeline:
  natural language instruction → Qwen parses coordinates
  → ROS 2 topic → TurtleSim executes.
  Tested "go to top right corner" → successfully navigated to (10.0, 10.0).

**Challenges & blockers**
- Training instability: SR dropped from 88% to 0% on scene switch (generalization issue).
- PyTorch 2.6 / Habitat checkpoint incompatibility (`weights_only=True`): fixed by patching `ppo_trainer.py`.
- conda Python 3.9 vs ROS2 Python 3.10 conflict: resolved by separating Qwen (conda) and ROS2 (system Python) into two processes communicating via file.

**Next steps**
- Analyze success and failure cases in detail.
- Plot training curves from log data.
- Run longer PPO training for stronger baseline.

**Hours spent (optional):** 

**Links (optional):**
- [Success navigation demo](../src/success_navigation.gif)
- [Failure navigation demo](../src/failure_navigation.gif)
- [Qwen + TurtleSim demo](../src/qwen_turtlesim.png)
