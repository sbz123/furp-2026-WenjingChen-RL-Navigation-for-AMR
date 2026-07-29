#!/usr/bin/env python3
"""Repository-relative, headless reproduction of the final STPS v2 evaluation."""

from __future__ import annotations

import argparse
from collections import deque
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = REPO_ROOT / "runtime" / "robot_nav"
CHECKPOINT_DIR = REPO_ROOT / "artifacts" / "checkpoints" / "cnntd3_final"
OUTPUT_DIR = REPO_ROOT / "artifacts" / "reproduced"

os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(RUNTIME_ROOT))

# The archived checkpoints are loaded only for CPU inference.
_torch_load = torch.load


def cpu_torch_load(*args, **kwargs):
    kwargs.setdefault("map_location", torch.device("cpu"))
    return _torch_load(*args, **kwargs)


torch.load = cpu_torch_load

from robot_nav.SIM_ENV.sim import SIM
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3


DEVICE = torch.device("cpu")
STALL_WINDOW = 20
STALL_DIST = 0.15
BASE_ESCAPE_STEPS = 120
PROGRESS_DIST = 0.5
OSC_WINDOW = 12
OSC_REVERSAL_THRESH = 5
OSC_MIN_STEPS = 8
SEEDS = [42, 123, 2026]

WORLD_DIR = RUNTIME_ROOT / "robot_nav" / "worlds"
SCENARIOS = {
    "S1_U_trap": {
        "world": WORLD_DIR / "u_trap_world.yaml",
        "base_xy": [7.5, 5.0],
        "goal": [[9.0], [5.0], [0.0]],
        "max_steps": 500,
    },
    "S2_Double_U": {
        "world": WORLD_DIR / "double_u_world.yaml",
        "base_xy": [5.0, 5.0],
        "goal": [[9.0], [5.0], [0.0]],
        "max_steps": 500,
    },
    "S3_Narrow_door": {
        "world": WORLD_DIR / "narrow_door_world.yaml",
        "base_xy": [2.0, 5.0],
        "goal": [[8.0], [5.0], [0.0]],
        "max_steps": 500,
    },
    "S5_Corridor": {
        "world": WORLD_DIR / "symmetric_corridor_world.yaml",
        "base_xy": [1.0, 5.0],
        "goal": [[9.0], [5.0], [0.0]],
        "max_steps": 500,
    },
}


def make_configs(base_xy: list[float], seed: int, n: int = 12) -> list[list[list[float]]]:
    rng = np.random.default_rng(seed)
    headings = [0.0, 1.57, 3.14, -1.57]
    configs = []
    for index in range(n):
        heading = headings[index % 4] + rng.uniform(-0.4, 0.4)
        x = base_xy[0] + rng.uniform(-0.3, 0.3)
        y = base_xy[1] + rng.uniform(-0.3, 0.3)
        configs.append(
            [
                [x],
                [y],
                [heading],
            ]
        )
    return configs


def detect_oscillation(position_history: deque[np.ndarray]) -> bool:
    if len(position_history) < OSC_WINDOW:
        return False
    recent = list(position_history)[-OSC_WINDOW:]
    reversals = 0
    previous_delta = None
    for index in range(1, len(recent)):
        delta = recent[index] - recent[index - 1]
        if previous_delta is not None and np.dot(delta, previous_delta) < 0:
            reversals += 1
        previous_delta = delta
    return reversals >= OSC_REVERSAL_THRESH


def load_model(prefix: str) -> CNNTD3:
    model = CNNTD3(
        state_dim=185,
        action_dim=2,
        max_action=1,
        device=DEVICE,
        load_model=False,
        model_name=prefix,
    )
    model.load(prefix, CHECKPOINT_DIR)
    model.actor.eval()
    return model


def end_simulation(sim: SIM) -> None:
    sim.env.end()
    # IR-SIM creates a Matplotlib figure even with plotting disabled.
    try:
        import matplotlib.pyplot as plt

        plt.close("all")
    except ImportError:
        pass


def run_stps(
    precision_model: CNNTD3,
    exploration_model: CNNTD3,
    world: Path,
    robot_state: list[list[float]],
    robot_goal: list[list[float]],
    max_steps: int,
) -> tuple[str, int]:
    sim = SIM(world_file=str(world), disable_plotting=True)
    scan, distance, cos, sin, collision, goal, action, _ = sim.reset(
        robot_state=robot_state,
        robot_goal=robot_goal,
        random_obstacles=False,
    )
    previous_action = [0.0, 0.0]
    positions: deque[np.ndarray] = deque(maxlen=max(STALL_WINDOW, OSC_WINDOW + 2))
    mode = "precision"
    escape_steps = BASE_ESCAPE_STEPS
    escape_count = 0
    escape_start = None
    switches = 0
    precision_steps = 0

    for _ in range(max_steps):
        state = sim.env.get_robot_state()
        position = np.array([state[0].item(), state[1].item()])
        positions.append(position)

        if mode == "precision":
            precision_steps += 1
            stalled = (
                len(positions) >= STALL_WINDOW
                and np.linalg.norm(positions[-1] - positions[-STALL_WINDOW]) < STALL_DIST
            )
            oscillating = precision_steps > OSC_MIN_STEPS and detect_oscillation(positions)
            if stalled or oscillating:
                mode = "exploration"
                escape_count = 0
                escape_start = position.copy()
                switches += 1
                precision_steps = 0
                positions.clear()
                if switches > 1:
                    escape_steps = min(BASE_ESCAPE_STEPS * 2, 240)
        else:
            escape_count += 1
            escaped_distance = np.linalg.norm(position - escape_start)
            if (
                escape_count >= escape_steps and escaped_distance > PROGRESS_DIST
            ) or escape_count >= escape_steps * 3:
                mode = "precision"
                precision_steps = 0
                positions.clear()

        model = precision_model if mode == "precision" else exploration_model
        policy_state, _ = model.prepare_state(
            scan, distance, cos, sin, collision, goal, previous_action
        )
        action = model.get_action(np.array(policy_state), False)
        previous_action = list(action)
        linear_velocity = float(np.clip((action[0] + 1) / 4, 0, 0.5))
        angular_velocity = float(np.clip(action[1], -1, 1))
        scan, distance, cos, sin, collision, goal, action, _ = sim.step(
            linear_velocity, angular_velocity
        )
        if goal:
            end_simulation(sim)
            return "goal", switches
        if collision:
            end_simulation(sim)
            return "collision", switches

    end_simulation(sim)
    return "timeout", switches


def smoke_test(precision_model: CNNTD3, exploration_model: CNNTD3) -> int:
    scenario = SCENARIOS["S1_U_trap"]
    start = make_configs(scenario["base_xy"], SEEDS[0], n=1)[0]
    outcome, switches = run_stps(
        precision_model,
        exploration_model,
        scenario["world"],
        start,
        scenario["goal"],
        max_steps=5,
    )
    print(f"Smoke test completed: outcome={outcome}, switches={switches}, steps<=5")
    return 0


def hard_scenario_evaluation(
    precision_model: CNNTD3, exploration_model: CNNTD3
) -> dict[str, dict[str, object]]:
    results = {}
    for name, scenario in SCENARIOS.items():
        seed_success_rates = []
        for seed in SEEDS:
            starts = make_configs(scenario["base_xy"], seed)
            successes = 0
            for start in starts:
                outcome, _ = run_stps(
                    precision_model,
                    exploration_model,
                    scenario["world"],
                    start,
                    scenario["goal"],
                    scenario["max_steps"],
                )
                successes += outcome == "goal"
            seed_success_rates.append(successes / len(starts))

        mean = float(np.mean(seed_success_rates))
        std = float(np.std(seed_success_rates))
        results[name] = {
            "mean": round(mean, 3),
            "std": round(std, 3),
            "seeds": seed_success_rates,
        }
        print(
            f"{name}: {mean:.0%} +/- {std:.0%} "
            f"({[f'{value:.0%}' for value in seed_success_rates]})"
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Load all runtime artifacts and take five simulation steps.")
    parser.add_argument("--hard-only", action="store_true", help="Run the four deterministic hard scenarios.")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "stps_v2_hard_reproduction.json",
        help="Output JSON path for --hard-only.",
    )
    args = parser.parse_args()

    if not CHECKPOINT_DIR.is_dir():
        parser.error(f"Missing checkpoint directory: {CHECKPOINT_DIR}")
    if not args.smoke and not args.hard_only:
        parser.error("Choose --smoke or --hard-only.")

    started = time.time()
    with tempfile.TemporaryDirectory(prefix="final-stps-") as temporary_directory:
        original_directory = Path.cwd()
        os.chdir(temporary_directory)
        try:
            precision_model = load_model("CNNTD3_v7_finetune_best")
            exploration_model = load_model("CNNTD3_improved")
            print("Loaded frozen precision and exploration policies on CPU.")

            if args.smoke:
                return smoke_test(precision_model, exploration_model)

            results = hard_scenario_evaluation(precision_model, exploration_model)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(results, indent=2) + "\n", encoding="utf-8"
            )
            elapsed_minutes = (time.time() - started) / 60
            print(
                f"Saved {args.output.relative_to(REPO_ROOT)} "
                f"in {elapsed_minutes:.1f} minutes."
            )
            return 0
        finally:
            os.chdir(original_directory)


if __name__ == "__main__":
    sys.exit(main())
