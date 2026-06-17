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

- Started Habitat PPO PointNav training from scratch (official baseline):
  - Scene: van-gogh-room
  - Algorithm: PPO
  - update 0: success = 0.000
  - update ~650: success first appears (0.333)
  - update ~5000: success = 0.75~0.88
  - update ~12000: moving average success ≈ 0.85, SPL ≈ 0.65
- Fixed PyTorch 2.6 checkpoint compatibility issue
  (added weights_only=False in ddp_utils.py line 224)
  to enable resume training without deleting checkpoints.
- Wrote plot_training.py to extract training log and generate
  training curve (Success Rate / SPL / Reward vs Updates).
  

**Challenges & blockers**

- Hydra config error with curly braces in data path:
  resolved by hardcoding train/train.json.gz path.
- PyTorch 2.6 breaking change caused checkpoint load failure:
  resolved by modifying ddp_utils.py weights_only=False.
- Success rate shows large fluctuations during training:
  identified as normal behavior caused by scene switching
  in the dataset, not a training failure.

**Next steps**

- Let training continue to 50000+ steps.
- Add collision penalty as an improvement experiment.
- Compare improved model vs baseline (SR, SPL, collision rate).

**Hours spent:** 

**Links:** 
- [Training log](../src/training_log.txt)
- [Plot script](../src/plot_training.py)
- [Training curve](../src/training_curve.png)

**Training curve analysis**

The training curve shows three distinct phases:

1. **Learning phase (update 0-2000):**
   Success rate rises rapidly from 0 to ~0.75.
   The agent transitions from random exploration
   to goal-directed navigation within ~2000 updates.

2. **Convergence phase (update 2000-12000):**
   Moving average success rate stabilizes at ~0.85.
   SPL stabilizes at ~0.65, indicating the agent not only
   reaches the goal but also takes reasonably efficient paths.

3. **Fluctuation analysis:**
   Raw success rate shows large variance throughout training.
   This is caused by scene switching in the dataset —
   when a harder scene is sampled, success temporarily drops,
   then recovers as the agent adapts.
   This suggests the baseline policy has limited
   generalization across scenes.

**Key observations:**
- Reward moving average stays near 0 despite high success rate,
  meaning most reward comes from the sparse success bonus.
  This is a known limitation of the default reward design
  and motivates the next experiment: adding a collision penalty
  to provide denser reward signal.
- Final baseline metrics (moving average):
  - Success Rate: ~0.85
  - SPL: ~0.65

 
          
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
