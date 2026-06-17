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
### Week 2 — 2026-06-17

**Attended this week's meeting:** Yes

**Progress this week**

- Started Habitat PPO PointNav training (official baseline):
  - Algorithm: PPO, Scene: van-gogh-room
  - update 0: success = 0.000
  - update ~650: success first appears (0.333)
  - update ~12000: success ≈ 0.85, SPL ≈ 0.65
- Fixed PyTorch 2.6 checkpoint issue (weights_only=False).
- Generated training curve with moving average (plot_training.py).
- Ran reward shaping experiments (3 variants, see below).

**Training curve analysis**

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

**Challenges & blockers**

- Hydra curly braces syntax error: resolved by hardcoding data path.
- PyTorch 2.6 checkpoint load failure: resolved by weights_only=False.
- Collision penalty -0.5 killed learning: identified and documented
  as a failed experiment, reduced to -0.1.

**Next steps**

- Read PPO paper and reward shaping literature.
- Consider potential-based reward shaping as next improvement.
- Run penalty -0.1 experiment to full convergence.

**Hours spent:** 

**Links:**
- [Training curve (baseline)](../src/training_curve.png)
- [Comparison curve](../src/comparison_curve.png)
- [Training log baseline](../src/training_log_baseline.txt)
- [Plot script](../src/plot_training.py)

   
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
