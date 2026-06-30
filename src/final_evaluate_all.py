"""
最终 Evaluate：所有训练好的模型 × 泛化场景 + 4个特殊场景
"""
import sys, numpy as np, torch
from pathlib import Path
sys.path.insert(0, 'robot_nav')
from SIM_ENV.sim import SIM
from models.CNNTD3.CNNTD3 import CNNTD3
from models.RCPG.RCPG import RCPG

device = torch.device('cpu')

CNNTD3_MODELS = [
    'CNNTD3', 'CNNTD3_v2', 'CNNTD3_improved', 'CNNTD3_v3',
    'CNNTD3_v4_improved_best', 'CNNTD3_curriculum_only',
]
CNNTD3_DIR = Path('robot_nav/models/CNNTD3/checkpoint')

GENERALIZATION_TRIALS = 20

SPECIAL_SCENARIOS = {
    'S1_U_trap': {
        'world': 'robot_nav/worlds/u_trap_world.yaml',
        'cases': [
            ([[7.5],[5.0],[0.0]],  [[9.0],[5.0],[0]]),
            ([[7.5],[5.0],[1.57]], [[9.0],[5.0],[0]]),
            ([[7.5],[5.0],[3.14]], [[9.0],[5.0],[0]]),
            ([[7.5],[5.0],[-1.57]],[[9.0],[5.0],[0]]),
        ], 'max_steps': 300,
    },
    'S2_Double_U': {
        'world': 'robot_nav/worlds/double_u_world.yaml',
        'cases': [
            ([[5.0],[5.0],[0.0]],  [[9.0],[5.0],[0]]),
            ([[5.0],[5.0],[1.57]], [[9.0],[5.0],[0]]),
            ([[5.0],[5.0],[3.14]], [[9.0],[5.0],[0]]),
            ([[5.0],[5.0],[-1.57]],[[9.0],[5.0],[0]]),
        ], 'max_steps': 300,
    },
    'S3_Narrow_door': {
        'world': 'robot_nav/worlds/narrow_door_world.yaml',
        'cases': [
            ([[2.0],[5.0],[0.0]],  [[8.0],[5.0],[0]]),
            ([[2.0],[5.0],[0.3]],  [[8.0],[5.0],[0]]),
            ([[2.0],[5.0],[-0.3]], [[8.0],[5.0],[0]]),
            ([[2.0],[6.0],[0.0]],  [[8.0],[5.0],[0]]),
        ], 'max_steps': 300,
    },
    'S5_Corridor': {
        'world': 'robot_nav/worlds/symmetric_corridor_world.yaml',
        'cases': [
            ([[1.0],[5.0],[0.0]],  [[9.0],[5.0],[0]]),
            ([[1.0],[5.0],[1.57]], [[9.0],[5.0],[0]]),
            ([[1.0],[5.0],[3.14]], [[9.0],[5.0],[0]]),
            ([[1.0],[5.0],[-1.57]],[[9.0],[5.0],[0]]),
        ], 'max_steps': 300,
    },
}


def run_episode_cnntd3(model, world, robot_state, robot_goal, max_steps, random_obs):
    sim = SIM(world_file=world, disable_plotting=True)
    if robot_state is not None:
        scan,dist,cos,sin,col,goal,a,r = sim.reset(
            robot_state=robot_state, robot_goal=robot_goal, random_obstacles=False)
    else:
        scan,dist,cos,sin,col,goal,a,r = sim.reset(random_obstacles=random_obs)
    prev = [0.0, 0.0]
    success = False
    for step in range(max_steps):
        state,_ = model.prepare_state(scan,dist,cos,sin,col,goal,prev)
        action = model.get_action(np.array(state), False)
        prev = list(action)
        lin = float(np.clip((action[0]+1)/4, 0, 0.5))
        ang = float(np.clip(action[1], -1, 1))
        scan,dist,cos,sin,col,goal,a,r = sim.step(lin, ang)
        if goal: success = True; break
        if col: break
    sim.env.end()
    return success


def run_episode_rcpg(model, world, robot_state, robot_goal, max_steps, random_obs):
    sim = SIM(world_file=world, disable_plotting=True)
    if robot_state is not None:
        scan,dist,cos,sin,col,goal,a,r = sim.reset(
            robot_state=robot_state, robot_goal=robot_goal, random_obstacles=False)
    else:
        scan,dist,cos,sin,col,goal,a,r = sim.reset(random_obstacles=random_obs)
    success = False
    history = []
    for step in range(max_steps):
        state, _ = model.prepare_state(scan, dist, cos, sin, col, goal, [0.0, 0.0])
        history.append(state)
        if len(history) > 10:
            history.pop(0)
        seq = history + [history[-1]] * (10 - len(history))
        action = model.get_action(np.array(seq), False)
        lin = float(np.clip((action[0]+1)/4, 0, 0.5))
        ang = float(np.clip(action[1], -1, 1))
        scan,dist,cos,sin,col,goal,a,r = sim.step(lin, ang)
        if goal: success = True; break
        if col: break
    sim.env.end()
    return success


def evaluate_model(model_name, run_fn, model):
    print(f"\n{'='*60}\n{model_name}\n{'='*60}")
    results = {}

    success_count = 0
    for trial in range(GENERALIZATION_TRIALS):
        success = run_fn(model, 'robot_nav/worlds/robot_world.yaml', None, None, 300, True)
        if success: success_count += 1
    gen_sr = success_count / GENERALIZATION_TRIALS
    results['generalization'] = gen_sr
    print(f"  泛化(标准环境,随机,{GENERALIZATION_TRIALS}次): SR={gen_sr:.0%}")

    for scene_name, cfg in SPECIAL_SCENARIOS.items():
        total, success_count = 0, 0
        for robot_state, robot_goal in cfg['cases']:
            for rep in range(3):
                success = run_fn(model, cfg['world'], robot_state, robot_goal, cfg['max_steps'], False)
                if success: success_count += 1
                total += 1
        sr = success_count / total
        results[scene_name] = sr
        print(f"  {scene_name:<18}: {success_count}/{total} = {sr:.0%}")

    return results


all_results = {}

for model_name in CNNTD3_MODELS:
    try:
        model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
                       device=device, load_model=True,
                       model_name=model_name, load_directory=CNNTD3_DIR)
        model.actor.eval()
        all_results[model_name] = evaluate_model(model_name, run_episode_cnntd3, model)
    except Exception as e:
        print(f"\n跳过 {model_name}（不存在）: {e}")

try:
    rcpg_model = RCPG(state_dim=185, action_dim=2, max_action=1,
                      device=device, load_model=True, rnn='gru')
    all_results['RCPG'] = evaluate_model('RCPG', run_episode_rcpg, rcpg_model)
except Exception as e:
    print(f"\n跳过 RCPG: {e}")

print(f"\n{'='*85}")
print(f"{'模型':<28} {'泛化':>8} {'U-trap':>8} {'Double-U':>10} {'窄门':>8} {'走廊':>8}")
print(f"{'-'*85}")
for model_name, r in all_results.items():
    print(f"{model_name:<28} "
          f"{r.get('generalization',0):>7.0%} "
          f"{r.get('S1_U_trap',0):>7.0%} "
          f"{r.get('S2_Double_U',0):>9.0%} "
          f"{r.get('S3_Narrow_door',0):>7.0%} "
          f"{r.get('S5_Corridor',0):>7.0%}")
print(f"{'='*85}")

import json
with open('final_evaluate_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print("\n结果已保存到 final_evaluate_results.json")
