import sys, os, numpy as np, torch, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
from robot_nav.SIM_ENV.sim import SIM

WORLD_FILE = "robot_nav/worlds/narrow_door_world.yaml"
MAX_STEPS  = 300

TEST_CASES = [
    ([[2.0],[5.0],[0.0]],   [[8.0],[5.0],[0]]),  # 正对门洞中心
    ([[2.0],[5.0],[0.3]],   [[8.0],[5.0],[0]]),  # 轻微偏上
    ([[2.0],[5.0],[-0.3]],  [[8.0],[5.0],[0]]),  # 轻微偏下
    ([[2.0],[6.0],[0.0]],   [[8.0],[5.0],[0]]),  # 起点偏上1格
    ([[2.0],[4.0],[0.0]],   [[8.0],[5.0],[0]]),  # 起点偏下1格
    ([[2.0],[7.0],[0.0]],   [[8.0],[5.0],[0]]),  # 起点偏上2格
    ([[2.0],[3.0],[0.0]],   [[8.0],[5.0],[0]]),  # 起点偏下2格
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
               device=device, load_model=True, model_name="CNNTD3")
sim = SIM(world_file=WORLD_FILE)

results = []
total_goal, total_col = 0, 0
print("="*50)
print("S3 窄门测试（门宽0.7m，robot直径0.4m）")
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
        start_y = robot_state[1][0]
        print(f"case={idx} rep={rep} start_y={start_y:.1f} steps={steps:>3} | {outcome}")
        results.append({"case": idx, "rep": rep, "start_y": start_y,
                        "steps": steps, "outcome": outcome, "reward": round(ep_reward,2)})

n = len(results)
print(f"\nSR={total_goal/n*100:.1f}%  CR={total_col/n*100:.1f}%  TR={(n-total_goal-total_col)/n*100:.1f}%")
with open("narrow_door_results.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys()); w.writeheader(); w.writerows(results)
print("结果保存到 narrow_door_results.csv")
