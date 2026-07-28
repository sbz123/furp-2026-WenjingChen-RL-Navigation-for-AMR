"""CNNTD3_curriculum_only 困难场景测试"""
import sys, os, numpy as np, torch, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
from robot_nav.SIM_ENV.sim import SIM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
               device=device, load_model=True, model_name="CNNTD3_curriculum_only")

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

PREV = {"S1_U_trap":("0%","0%"),"S2_double_U":("33%","0%"),"S3_narrow_door":("4.8%","90.5%"),
        "S4_dead_end_maze":("67%","0%"),"S5_symmetric_corridor":("83%","100%")}

all_results = []
summary = {}
for name, cfg in SCENARIOS.items():
    print(f"\n{'='*60}\n  {name}\n{'='*60}")
    sim = SIM(world_file=cfg["world"])
    tg, tc, n = 0, 0, 0
    for idx, (rs, rg) in enumerate(cfg["cases"]):
        for rep in range(3):
            scan,dist,cos,sin,col,goal,a,r = sim.reset(robot_state=rs,robot_goal=rg,random_obstacles=False)
            done, steps = False, 0
            while not done and steps < cfg["max_steps"]:
                state,_ = model.prepare_state(scan,dist,cos,sin,col,goal,a)
                action = model.get_action(np.array(state), False)
                a_in = [(action[0]+1)/4, action[1]]
                scan,dist,cos,sin,col,goal,a,r = sim.step(lin_velocity=a_in[0],ang_velocity=a_in[1])
                steps+=1; done=col or goal
            outcome="goal" if goal else ("collision" if col else "timeout")
            tg+=int(goal); tc+=int(col); n+=1
            print(f"  case={idx} rep={rep} | theta={rs[2][0]:>6.2f} | steps={steps:>3} | {outcome}")
            all_results.append({"scene":name,"case":idx,"rep":rep,"theta":rs[2][0],"steps":steps,"outcome":outcome})
    sr=tg/n*100; cr=tc/n*100; tr=(n-tg-tc)/n*100
    summary[name]=f"{sr:.1f}%"
    c,r = PREV.get(name,("?","?"))
    print(f"\n  Improved: SR={sr:.1f}%  CR={cr:.1f}%  TR={tr:.1f}%")
    print(f"  CNNTD3:   SR={c}")
    print(f"  RCPG:     SR={r}")

print(f"\n{'='*70}\n  三方对比\n{'='*70}")
print(f"  {'场景':<26} {'Improved':<12} {'CNNTD3':<12} {'RCPG':<12}")
print(f"  {'-'*62}")
for s in SCENARIOS:
    c,r = PREV.get(s,("?","?"))
    print(f"  {s:<26} {summary[s]:<12} {c:<12} {r:<12}")
print(f"{'='*70}")

with open("improved_hard_scenario_results.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=all_results[0].keys());w.writeheader();w.writerows(all_results)
print("结果保存到 improved_hard_scenario_results.csv")
