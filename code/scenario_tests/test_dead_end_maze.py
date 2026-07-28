import sys, os, numpy as np, torch, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
from robot_nav.SIM_ENV.sim import SIM

WORLD_FILE = "robot_nav/worlds/dead_end_maze_world.yaml"
MAX_STEPS  = 500   # 迷宫给更多步数

# 不同朝向起点，goal固定在右侧
TEST_CASES = [
    # agent在左侧，朝右正对死路走廊上方入口
    ([[1.5],[8.0],[0.0]],    [[9.0],[6.0],[0]]),  # 起点正对上死路，goal在中间走廊出口
    ([[1.5],[8.0],[1.57]],   [[9.0],[6.0],[0]]),  # 朝上
    ([[1.5],[8.0],[-1.57]],  [[9.0],[6.0],[0]]),  # 朝下
    ([[1.5],[8.0],[3.14]],   [[9.0],[6.0],[0]]),  # 朝左
    ([[1.5],[2.0],[0.0]],    [[9.0],[6.0],[0]]),  # 起点在下方，正对下死路
    ([[1.5],[6.0],[0.0]],    [[9.0],[6.0],[0]]),  # 起点正对中间走廊（相对容易）
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
               device=device, load_model=True, model_name="CNNTD3")
sim = SIM(world_file=WORLD_FILE)

results = []
total_goal, total_col = 0, 0
print("="*50)
print("S4 死路迷宫测试")
print("="*50)

for idx, (robot_state, robot_goal) in enumerate(TEST_CASES):
    for rep in range(3):
        latest_scan, distance, cos, sin, collision, goal, a, reward = sim.reset(
            robot_state=robot_state, robot_goal=robot_goal, random_obstacles=False)
        done, steps, ep_reward = False, 0, 0.0
        while not done and steps < MAX_STEPS:
            state, _ = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
            action = model.get_action(np.array(state), False)
            a_in = [(action[0]+1)/4, action[1]]
            latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(
                lin_velocity=a_in[0], ang_velocity=a_in[1])
            ep_reward += reward; steps += 1
            done = collision or goal
        outcome = "goal" if goal else ("collision" if collision else "timeout")
        total_goal += int(goal); total_col += int(collision)
        print(f"case={idx} rep={rep} theta={robot_state[2][0]:.2f} steps={steps:>3} | {outcome}")
        results.append({"case": idx, "rep": rep, "theta": robot_state[2][0],
                        "steps": steps, "outcome": outcome, "reward": round(ep_reward,2)})

n = len(results)
print(f"\nSR={total_goal/n*100:.1f}%  CR={total_col/n*100:.1f}%  TR={(n-total_goal-total_col)/n*100:.1f}%")
with open("dead_end_maze_results.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys()); w.writeheader(); w.writerows(results)
print("结果保存到 dead_end_maze_results.csv")
