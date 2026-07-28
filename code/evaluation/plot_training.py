import re
import matplotlib.pyplot as plt
import numpy as np

updates, success_rates, spls, rewards = [], [], [], []

with open("training_log.txt", "r") as f:
    lines = f.readlines()

current_update = None
for line in lines:
    u = re.search(r"update:\s*(\d+)", line)
    if u:
        current_update = int(u.group(1))
    if "Average window size" in line and current_update is not None:
        s = re.search(r"success:\s*([0-9.]+)", line)
        p = re.search(r"spl:\s*([0-9.]+)", line)
        r = re.search(r"reward:\s*([0-9.]+)", line)
        if s and p and r:
            updates.append(current_update)
            success_rates.append(float(s.group(1)))
            spls.append(float(p.group(1)))
            rewards.append(float(r.group(1)))

def moving_avg(data, window=100):
    return np.convolve(data, np.ones(window)/window, mode='valid')

fig, axes = plt.subplots(3, 1, figsize=(10, 12))

axes[0].plot(updates, success_rates, color='green', alpha=0.3, label='Raw')
axes[0].plot(updates[99:], moving_avg(success_rates), color='green', linewidth=2, label='Moving Avg')
axes[0].set_title("Success Rate")
axes[0].set_xlabel("Updates")
axes[0].set_ylabel("Success Rate")
axes[0].set_ylim(0, 1.1)
axes[0].legend()
axes[0].grid(True)

axes[1].plot(updates, spls, color='blue', alpha=0.3, label='Raw')
axes[1].plot(updates[99:], moving_avg(spls), color='blue', linewidth=2, label='Moving Avg')
axes[1].set_title("SPL")
axes[1].set_xlabel("Updates")
axes[1].set_ylabel("SPL")
axes[1].set_ylim(0, 1.1)
axes[1].legend()
axes[1].grid(True)

axes[2].plot(updates, rewards, color='orange', alpha=0.3, label='Raw')
axes[2].plot(updates[99:], moving_avg(rewards), color='orange', linewidth=2, label='Moving Avg')
axes[2].set_title("Reward")
axes[2].set_xlabel("Updates")
axes[2].set_ylabel("Reward")
axes[2].legend()
axes[2].grid(True)

plt.tight_layout()
plt.savefig("training_curve.png", dpi=150)
print("Done!")
