import sys, os, numpy as np, torch, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
from robot_nav.SIM_ENV.sim import SIM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
               device=device, load_model=True, model_name="CNNTD3")

def run_test(scene_name, world_file, test_cases, max_steps=300):
    sim = SIM(world_file=world_file)
    results = []
    total_goal, total_col = 0, 0
    print(f"\n{'='*50}")
    print(f"{scene_name}")
    print('='*50)
    for idx, (robot_state, robot_goal) in enumerate(test_cases):
        for rep in range(3):
            scan,dist,cos,sin,col,goal,a,r = sim.reset(
                robot_state=robot_state, robot_goal=robot_goal, random_obstacles=False)
            done, steps = False, 0
            while not done and steps < max_steps:
                s,_ = model.prepare_state(scan,dist,cos,sin,col,goal,a)
                act = model.get_action(np.array(s), False)
                scan,dist,cos,sin,col,goal,a,r = sim.step(
                    lin_velocity=(act[0]+1)/4, ang_velocity=act[1])
                steps += 1
                done = col or goal
            outcome = "goal" if goal else ("collision" if col else "timeout")
            total_goal += int(goal); total_col += int(col)
            print(f"  case={idx} rep={rep} | theta={robot_state[2][0]:.2f} "
                  f"start=({robot_state[0][0]:.1f},{robot_state[1][0]:.1f}) "
                  f"steps={steps:>3} | {outcome}")
            results.append({"scene": scene_name, "case": idx, "rep": rep,
                           "outcome": outcome, "steps": steps})
    n = len(results)
    print(f"\n  SR={total_goal/n*100:.1f}%  CR={total_col/n*100:.1f}%  "
          f"TR={(n-total_goal-total_col)/n*100:.1f}%")
    return results

# ── S5 对称长走廊 ──
s5_cases = [
    ([[1.0],[5.0],[0.0]],   [[9.0],[5.0],[0]]),  # 正中，朝右
    ([[1.0],[5.0],[1.57]],  [[9.0],[5.0],[0]]),  # 正中，朝上
    ([[1.0],[5.0],[-1.57]], [[9.0],[5.0],[0]]),  # 正中，朝下
    ([[1.0],[5.0],[3.14]],  [[9.0],[5.0],[0]]),  # 正中，朝左（背对goal）
    ([[1.0],[5.1],[0.0]],   [[9.0],[5.0],[0]]),  # 轻微偏上0.1
    ([[1.0],[4.9],[0.0]],   [[9.0],[5.0],[0]]),  # 轻微偏下0.1
]

# ── S2 双U陷阱 ──
s2_cases = [
    ([[5.0],[5.0],[0.0]],   [[9.0],[5.0],[0]]),  # 正中，朝右
    ([[5.0],[5.0],[1.57]],  [[9.0],[5.0],[0]]),  # 朝上（易误入上方U）
    ([[5.0],[5.0],[-1.57]], [[9.0],[5.0],[0]]),  # 朝下（易误入下方U）
    ([[5.0],[5.0],[3.14]],  [[9.0],[5.0],[0]]),  # 朝左
    ([[5.0],[6.0],[1.57]],  [[9.0],[5.0],[0]]),  # 偏上，朝上，极易入上U
    ([[5.0],[4.0],[-1.57]], [[9.0],[5.0],[0]]),  # 偏下，朝下，极易入下U
]

all_results = []
all_results += run_test("S5 对称长走廊",
                        "robot_nav/worlds/symmetric_corridor_world.yaml",
                        s5_cases, max_steps=300)
all_results += run_test("S2 双U陷阱",
                        "robot_nav/worlds/double_u_world.yaml",
                        s2_cases, max_steps=300)

with open("s5_s2_results.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=all_results[0].keys())
    w.writeheader(); w.writerows(all_results)
print("\n结果保存到 s5_s2_results.csv")
