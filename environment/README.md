# Environment Files

`final-stps.yml` is the supported environment for the archived final STPS v2
runtime. It is intentionally small and does not install ROS, Habitat, Isaac
Sim, or NeuPAN.

```bash
conda env create -f environment/final-stps.yml
conda activate final-stps
python scripts/run_stps_v2.py --smoke
```

`neupan-conda-linux-64-2026-07-29.txt` and
`neupan-pip-freeze-2026-07-29.txt` are exact snapshots of the source machine's
`neupan` environment, captured on July 29, 2026. They document the full
historical environment, including unrelated system-level ROS tooling, and are
not the recommended installation path for this compact archive.
