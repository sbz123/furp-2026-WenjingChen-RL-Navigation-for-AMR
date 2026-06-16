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
### Week 1 — 2026-06-6

**Attended this week's meeting:** Yes

**Progress this week**
- Completed end-to-end evaluation of a pretrained PointNav baseline model
  (trained for 64,512,768 steps) in the `van-gogh-room` test scene.
- Achieved **Success Rate: 1.0000** and **SPL: 0.9523** on the test episode.
- Generated first-person navigation video.
- Read the Habitat PointNav paper (Savva et al., ICCV 2019).
- Installed Habitat-Lab + habitat-baselines on Ubuntu 22.04 (RTX 5060 GPU).
- Ran PPO PointNav training from scratch (~261,000 steps).
- Self-trained baseline results: SR=0.88, SPL=0.80, Distance to goal=0.15m
- Generated success demo (SPL=0.98) and failure demo (Distance=2.13m).
- Selected paper to reproduce: DD-PPO (Wijmans et al., ICLR 2020).
- Studied core concepts: PointNav, reward shaping, PPO, NeuPAN.

**Challenges & blockers**
- `ModuleNotFoundError` on first run: resolved by setting PYTHONPATH.
- Hydra config conflicts: resolved by switching to `ppo_pointnav_example.yaml`.
- Model weight key mismatch: resolved by writing `fix_checkpoint.py`.
- Training instability: success rate dropped from 88% to 0% on scene change.
- PyTorch 2.6 checkpoint compatibility issue with `weights_only=True`.

**Next steps**
- Install ROS2 Humble, run TurtleSim.
- Analyze success and failure cases in detail.
- Plot training curves.

**Hours spent (optional):** 

**Links (optional):**
- [Success navigation demo](../src/success_navigation.gif)
- [Failure navigation demo](../src/failure_navigation.gif)




