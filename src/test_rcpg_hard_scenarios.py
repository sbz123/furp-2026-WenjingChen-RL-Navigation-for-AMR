"""RCPG 困难场景全量测试"""
import sys, os, numpy as np, torch, csv
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from robot_nav.models.RCPG.RCPG import RCPG
from robot_nav.SIM_ENV.sim import SIM

HISTORY_LEN = 10
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = RCPG(state_dim=185, action_dim=2, max_action=1, device=device, load_model=True, rnn="gru")

SCENARIOS = {
    "S1_U_trap": {
        "world": "robot_nav/worlds/u_trap_world.yaml", "max_steps": 300,
        "cases": [
            ([[7.5],[5.0],[0.0]],[[9.0],[5.0],[0]]),([[7.5],[5.0],[1.57]],[[9.0],[5.0],[0]]),
            ([[7.5],[5.0],[3.14]],[[9.0],[5.0],[0]]),([[7.5],[5.0],[-1.57]],[[9.0],[5.0],[0]]),
            ([[7.5],[6.0],[0.0]],[[9.0],[5.0],[0]]),([[7.5],[4.0],[0.0]],[[9.0],[5.0],[0]]),
            ([[7.0],[5.0],[3.14]],[[9.0],[5.0],[0]]),([[7.5],[5.5],[1.57]],[[9.0],[5.0],[0]]),
            ([[7.5],[4.5],[-1.57]],[[9.0],[5.0],[0]]),([[7.0],[5.0],[2.0]],[[9.0],[5.0],[0]]),
        ],
    },
    "S2_double_U": {
        "world": "robot_nav/worlds/double_u_world.yaml", "max_steps": 300,
        "cases": [
            ([[5.0],[5.0],[0.0]],[[9.0],[5.0],[0]]),([[5.0],[5.0],[1.57]],[[9.0],[5.0],[0]]),
            ([[5.0],[5.0],[-1.57]],[[9.0],[5.0],[0]]),([[5.0],[5.0],[3.14]],[[9.0],[5.0],[0]]),
            ([[5.0],[6.0],[1.57]],[[9.0],[5.0],[0]]),([[5.0],[4.0],[-1.57]],[[9.0],[5.0],[0]]),
        ],
    },
    "S3_narrow_door": {
        "world": "robot_nav/worlds/narrow_door_world.yaml", "max_steps": 300,
        "cases": [
            ([[2.0],[5.0],[0.0]],[[8.0],[5.0],[0]]),([[2.0],[5.0],[0.3]],[[8.0],[5.0],[0]]),
            ([[2.0],[5.0],[-0.3]],[[8.0],[5.0],[0]]),([[2.0],[6.0],[0.0]],[[8.0],[5.0],[0]]),
            ([[2.0],[4.0],[0.0]],[[8.0],[5.0],[0]]),([[2.0],[7.0],[0.0]],[[8.0],[5.0],[0]]),
            ([[2.0],[3.0],[0.0]],[[8.0],[5.0],[0]]),
        ],
    },
    "S4_dead_end_maze": {
        "world": "robot_nav/worlds/dead_end_maze_world.yaml", "max_steps": 500,
        "cases": [
            ([[1.5],[8.0],[0.0]],[[9.0],[6.0],[0]]),([[1.5],[8.0],[1.57]],[[9.0],[6.0],[0]]),
            ([[1.5],[8.0],[-1.57]],[[9.0],[6.0],[0]]),([[1.5],[8.0],[3.14]],[[9.0],[6.0],[0]]),
            ([[1.5],[2.0],[0.0]],[[9.0],[6.0],[0]]),([[1.5],[6.0],[0.0]],[[9.0],[6.0],[0]]),
        ],
    },
    "S5_symmetric_corridor": {
        "world": "robot_nav/worlds/symmetric_corridor_world.yaml", "max_steps": 300,
        "cases": [
            ([[1.0],[5.0],[0.0]],[[9.0],[5.0],[0]]),([[1.0],[5.0],[1.57]],[[9.0],[5.0],[0]]),
            ([[1.0],[5.0],[-1.57]],[[9.0],[5.0],[0]]),([[1.0],[5.0],[3.14]],[[9.0],[5.0],[0]]),
            ([[1.0],[5.1],[0.0]],[[9.0],[5.0],[0]]),([[1.0],[4.9],[0.0]],[[9.0],[5.0],[0]]),
        ],
    },
}

CNNTD3_RESULTS = {
    "S1_U_trap": "0%", "S2_double_U": "33%", "S3_narrow_door": "4.8%",
    "S4_dead_end_maze": "67%", "S5_symmetric_corridor": "83%",
}

all_results = []
summary = {}
for scene_name, cfg in SCENARIOS.items():
    print(f"\n{'='*60}\n  {scene_name}\n{'='*60}")
    sim = SIM(world_file=cfg["world"])
    total_goal, total_col, n = 0, 0, 0
    for idx, (rs, rg) in enumerate(cfg["cases"]):
        for rep in range(3):
            sq = deque(maxlen=HISTORY_LEN)
            fill = True
            scan,dist,cos,sin,col,goal,a,r = sim.reset(robot_state=rs, robot_goal=rg, random_obstacles=False)
            done, steps = False, 0
            while not done and steps < cfg["max_steps"]:
                state, _ = model.prepare_state(scan,dist,cos,sin,col,goal,a)
                if fill:
                    sq.clear()
                    for _ in range(HISTORY_LEN): sq.append(state)
                    fill = False
                sq.append(state)
                action = model.get_action(np.array(sq), False)
                a_in = [(action[0]+1)/4, action[1]]
                scan,dist,cos,sin,col,goal,a,r = sim.step(lin_velocity=a_in[0], ang_velocity=a_in[1])
                steps += 1; done = col or goal
            outcome = "goal" if goal else ("collision" if col else "timeout")
            total_goal += int(goal); total_col += int(col); n += 1
            print(f"  case={idx} rep={rep} | theta={rs[2][0]:>6.2f} | steps={steps:>3} | {outcome}")
            all_results.append({"scene":scene_name,"case":idx,"rep":rep,"theta":rs[2][0],"steps":steps,"outcome":outcome})
    sr = total_goal/n*100; cr = total_col/n*100; tr = (n-total_goal-total_col)/n*100
    summary[scene_name] = f"{sr:.1f}%"
    print(f"\n  RCPG:   SR={sr:.1f}%  CR={cr:.1f}%  TR={tr:.1f}%")
    print(f"  CNNTD3: SR={CNNTD3_RESULTS.get(scene_name,'?')}")

print(f"\n{'='*70}\n  RCPG vs CNNTD3 全场景对比\n{'='*70}")
print(f"  {'场景':<26} {'RCPG SR':<12} {'CNNTD3 SR':<12}")
print(f"  {'-'*60}")
for s in SCENARIOS:
    print(f"  {s:<26} {summary[s]:<12} {CNNTD3_RESULTS.get(s,'?'):<12}")
print(f"{'='*70}")

with open("rcpg_hard_scenario_results.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=all_results[0].keys()); w.writeheader(); w.writerows(all_results)
print("结果保存到 rcpg_hard_scenario_results.csv")
