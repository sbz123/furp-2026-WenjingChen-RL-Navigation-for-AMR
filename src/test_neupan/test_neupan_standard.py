"""NeuPAN 标准环境评测 - 用和 CNNTD3 相同的 10 个起点/终点"""
import sys
sys.path.insert(0, '/home/ubuntu22/NeuPAN')
from neupan import neupan
import irsim
import numpy as np
import yaml

# 加载和 CNNTD3 相同的评测点
with open("/home/ubuntu22/DRL-robot-navigation-IR-SIM/robot_nav/eval_points.yaml") as f:
    points = yaml.safe_load(f)

robot_poses = points["robot"]["poses"]
robot_goals = points["robot"]["goals"]

env_file = "standard_eval/diff/env.yaml"
planner_file = "standard_eval/diff/planner.yaml"

goals_reached = 0
collisions = 0
total = len(robot_poses)

print(f"Testing NeuPAN on {total} scenarios (same as CNNTD3 eval)")
print("=" * 60)

for idx in range(total):
    # 提取起点和终点
    sx = robot_poses[idx][0][0]
    sy = robot_poses[idx][1][0]
    sth = robot_poses[idx][2][0]
    gx = robot_goals[idx][0][0]
    gy = robot_goals[idx][1][0]

    env = irsim.make(env_file, display=False, save_ani=False)

    # 设置 robot 起点
    env.robot.set_state(np.array([[sx],[sy],[sth]]), init=True)
    env.robot.set_goal(np.array([[gx],[gy],[0]]), init=True)
    env.reset()

    # 初始化 planner，设置 waypoints
    planner = neupan.init_from_yaml(planner_file)
    planner.update_initial_path_from_waypoints([
        np.array([sx, sy, sth]).reshape(3, 1),
        np.array([gx, gy, 0]).reshape(3, 1)
    ])

    arrived = False
    stopped = False
    max_steps = 500

    for step in range(max_steps):
        robot_state = env.get_robot_state()
        lidar_scan = env.get_lidar_scan()
        points_obs = planner.scan_to_point(robot_state, lidar_scan)
        action, info = planner(robot_state, points_obs, None)

        if info["arrive"]:
            arrived = True
            break
        if info["stop"]:
            stopped = True

        env.step(action)

        if env.done():
            break

    outcome = "GOAL" if arrived else ("STOPPED" if stopped else "timeout")
    if arrived:
        goals_reached += 1
    print(f"  Case {idx+1}/{total} | start=({sx:.0f},{sy:.0f}) goal=({gx:.0f},{gy:.0f}) | {outcome}")

    env.end(0)

sr = goals_reached / total * 100
print(f"\n{'=' * 60}")
print(f"NeuPAN Standard Environment Results:")
print(f"  SR = {sr:.1f}%  ({goals_reached}/{total})")
print(f"{'=' * 60}")
