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

### Week 1 — 2026-06-06

**Attended this week's meeting:** Yes

**Progress this week**
- Completed end-to-end evaluation of a pretrained PointNav baseline model 
  (trained for 64,512,768 steps) in the `van-gogh-room` test scene.
- Achieved **Success Rate: 1.0000** and **SPL: 0.9523** on the test episode.
- Generated first-person navigation video.
- Read the Habitat PointNav paper (Savva et al., ICCV 2019) to understand 
  what the baseline is actually measuring.

**Challenges & blockers**
- `ModuleNotFoundError` on first run: resolved by explicitly setting 
  `PYTHONPATH=.:./habitat-lab:./habitat-baselines` before executing scripts.
- Hydra config conflicts in `ppo_pointnav.yaml`: `num_updates` and 
  `total_num_steps` were both set, and the full Gibson dataset (~tens of GB) 
  was unavailable. Resolved by switching to `ppo_pointnav_example.yaml` and 
  overriding the dataset path to the local `val/val.json.gz` (van-gogh-room, 
  2.6 MB).
- Model weight key mismatch (`RuntimeError: Error(s) in loading state_dict`): 
  the downloaded `gibson-rgbd-best.pth` was trained on an older architecture 
  with `actor_critic.` prefixes that the current codebase does not expect. 
  Resolved by writing `fix_checkpoint.py` to strip the prefix from all keys 
  and saving a clean `gibson-rgbd-fixed.pth`.

**Next steps**
- Search for more literature reviews to read.

**Hours spent (optional):**

**Links (optional):**


