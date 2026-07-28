import numpy as np
import sys, os
import time
import csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_nav.SIM_ENV.sim import SIM
from neupan.neupan import neupan

# ============ 配置 ============
PLANNER_YAML = "/home/ubuntu22/NeuPAN/example/standard_eval/diff/planner.yaml"

SCENARIOS = {
    "Standard": {
        "world": "robot_nav/worlds/eval_world.yaml",
        "states": None,
        "goals": None,
    },
    "S1_U_trap": {
        "world": "robot_nav/worlds/u_trap_world.yaml",
        "states": [
            np.array([[7.5],[5.0],[0.0]]),
            np.array([[7.5],[5.0],[1.57]]),
            np.array([[7.5],[5.0],[3.14]]),
            np.array([[7.5],[5.0],[-1.57]]),
        ],
        "goals": np.array([[9.0],[5.0],[0]]),
    },
    "S2_Double_U": {
        "world": "robot_nav/worlds/double_u_world.yaml",
        "states": None,
        "goals": None,
    },
    "S3_Narrow_door": {
        "world": "robot_nav/worlds/narrow_door_world.yaml",
        "states": None,
        "goals": None,
    },
    "S5_Symmetric": {
        "world": "robot_nav/worlds/symmetric_corridor_world.yaml",
        "states": None,
        "goals": None,
    },
}

NUM_EPISODES = 2         # 先跑 2 轮测试
MAX_STEPS = 500

def evaluate_scenario(name, config, num_episodes, max_steps):
    world_file = config["world"]
    states_list = config["states"]
    goals = config["goals"]
    
    print(f"\n{'='*60}")
    print(f"评测场景: {name}")
    print(f"World: {world_file}")
    print(f"{'='*60}")
    
    results = []
    
    for ep in range(num_episodes):
        sim = SIM(world_file=world_file)
        planner = neupan.init_from_yaml(PLANNER_YAML)
        
        if states_list is not None:
            robot_state = states_list[ep % len(states_list)]
        else:
            robot_state = None
        
        if goals is not None:
            robot_goal = goals
        else:
            robot_goal = None
        
        latest_scan, distance, cos, sin, collision, goal, a, reward = sim.reset(
            robot_state=robot_state,
            robot_goal=robot_goal
        )
        
        state = sim.env.robot.state
        start = np.array([[state[0,0]], [state[1,0]], [state[2,0]]])
        if robot_goal is None:
            goal_arr = sim.robot_goal
        else:
            goal_arr = robot_goal
        
        planner.reset()
        planner.update_initial_path_from_goal(start, goal_arr)
        
        step = 0
        collision_flag = False
        goal_flag = False
        total_compute_time = 0.0
        
        for step in range(max_steps):
            state = sim.env.robot.state
            x, y, theta = state[0,0], state[1,0], state[2,0]
            cur = np.array([[x], [y], [theta]])
            
            scan_dict = {
                'ranges': latest_scan.tolist() if hasattr(latest_scan, 'tolist') else list(latest_scan),
                'angle_min': -np.pi,
                'angle_max': np.pi,
                'range_max': 7.0,
                'range_min': 0.0,
            }
            
            t_start = time.time()
            points = planner.scan_to_point(cur, scan_dict)
            action, info = planner.forward(cur, points)
            compute_time = time.time() - t_start
            total_compute_time += compute_time
            
            v, w = action[0,0], action[1,0]
            
            latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(
                lin_velocity=v, ang_velocity=w
            )
            
            if collision:
                collision_flag = True
                break
            if goal:
                goal_flag = True
                break
        
        success = goal_flag and not collision_flag
        timeout = not goal_flag and not collision_flag and step >= max_steps - 1
        
        results.append({
            'episode': ep,
            'success': success,
            'collision': collision_flag,
            'timeout': timeout,
            'steps': step + 1,
            'avg_compute_ms': (total_compute_time / (step + 1)) * 1000 if step > 0 else 0,
        })
        
        if (ep + 1) % 1 == 0:
            sr = np.mean([r['success'] for r in results])
            print(f"  Ep {ep+1}/{num_episodes}: {'✅' if success else '❌'}, SR={sr:.1%}")
    
    sr = np.mean([r['success'] for r in results])
    cr = np.mean([r['collision'] for r in results])
    tr = np.mean([r['timeout'] for r in results])
    avg_steps = np.mean([r['steps'] for r in results])
    avg_time = np.mean([r['avg_compute_ms'] for r in results])
    
    print(f"\n  ✅ SR: {sr:.2%} | ❌ CR: {cr:.2%} | ⏰ TR: {tr:.2%}")
    print(f"  📏 平均步数: {avg_steps:.1f} | ⚡ 决策时间: {avg_time:.2f} ms")
    
    return {
        'scenario': name,
        'SR': sr,
        'CR': cr,
        'TR': tr,
        'Avg steps': avg_steps,
        'Avg compute ms': avg_time,
    }

if __name__ == "__main__":
    all_results = []
    
    for name, config in SCENARIOS.items():
        result = evaluate_scenario(name, config, NUM_EPISODES, MAX_STEPS)
        all_results.append(result)
    
    csv_file = "neupan_full_benchmark_results.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['scenario', 'SR', 'CR', 'TR', 'Avg steps', 'Avg compute ms'])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n{'='*60}")
    print("全量评测完成！结果:", csv_file)
    print(f"{'='*60}")
    
    print("\n场景              | SR      | CR      | TR      | 平均步数 | 决策时间(ms)")
    print("-" * 80)
    for r in all_results:
        print(f"{r['scenario']:<18} | {r['SR']:.2%}   | {r['CR']:.2%}   | {r['TR']:.2%}   | {r['Avg steps']:.1f}     | {r['Avg compute ms']:.2f}")
