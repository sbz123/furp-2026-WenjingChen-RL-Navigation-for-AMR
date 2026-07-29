# Final Checkpoints

`cnntd3_final/` contains the 12 files needed to load the three frozen CNNTD3
policies used in the final evaluation:

- `CNNTD3_*`: baseline policy
- `CNNTD3_v7_finetune_best_*`: STPS precision policy
- `CNNTD3_improved_*`: STPS exploration policy

Each policy includes actor, actor-target, critic, and critic-target weights
because the original loader requires all four files. Verify their SHA-256
hashes with:

```bash
python scripts/verify_archive.py
```
