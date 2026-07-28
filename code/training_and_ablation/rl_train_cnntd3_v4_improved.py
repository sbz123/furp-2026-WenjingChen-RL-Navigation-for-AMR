"""
Improved CNNTD3 training script.
- longer default training (max_epochs=120)
- separate eval SIM instance
- saves best checkpoint by eval SR and periodic saves
- fixes outcome logging bug
"""
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
import argparse
import torch
import numpy as np
from robot_nav.SIM_ENV.sim import SIM
from utils import get_buffer


def evaluate(model, epoch, eval_sim, eval_episodes=10, max_eval_steps=500):
    print("..............................................")
    print(f"Epoch {epoch}. Evaluating scenarios")
    avg_reward = 0.0
    col = 0
    goals = 0
    for _ in range(eval_episodes):
        count = 0
        latest_scan, distance, cos, sin, collision, goal, a, reward = eval_sim.reset()
        done = False
        while not done and count < max_eval_steps:
            state, terminal = model.prepare_state(
                latest_scan, distance, cos, sin, collision, goal, a)
            action = model.get_action(np.array(state), False)
            a_in = [(action[0]+1)/4, action[1]]
            latest_scan, distance, cos, sin, collision, goal, a, reward = eval_sim.step(
                lin_velocity=a_in[0], ang_velocity=a_in[1])
            avg_reward += reward
            count += 1
            if collision: col += 1
            if goal: goals += 1
            done = collision or goal
    avg_reward /= eval_episodes
    avg_col = col / eval_episodes
    avg_goal = goals / eval_episodes
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average Collision rate: {avg_col:.2f}")
    print(f"Average Goal rate: {avg_goal:.2f}")
    print("..............................................")
    try:
        model.writer.add_scalar("eval/avg_reward", avg_reward, epoch)
        model.writer.add_scalar("eval/avg_col", avg_col, epoch)
        model.writer.add_scalar("eval/avg_goal", avg_goal, epoch)
    except Exception:
        pass
    return avg_goal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-epochs", type=int, default=120)
    parser.add_argument("--episodes-per-epoch", type=int, default=70)
    parser.add_argument("--train-every-n", type=int, default=2)
    parser.add_argument("--training-iterations", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--nr-eval-episodes", type=int, default=10)
    parser.add_argument("--save-every", type=int, default=5)
    parser.add_argument("--model-name", type=str, default="CNNTD3_v4_improved")
    args = parser.parse_args()

    state_dim  = 185
    action_dim = 2
    max_action = 1
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CNNTD3(
        state_dim=state_dim, action_dim=action_dim, max_action=max_action,
        device=device, save_every=args.save_every, load_model=False,
        model_name=args.model_name,
    )

    sim      = SIM(world_file="worlds/robot_world.yaml", disable_plotting=True)
    eval_sim = SIM(world_file="worlds/robot_world.yaml", disable_plotting=True)

    replay_buffer = get_buffer(
        model, sim, False, False, 10, args.training_iterations, args.batch_size)

    latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(0.0, 0.0)

    epoch, episode, steps = 0, 0, 0
    best_sr = 0.0

    print(f"{args.model_name} training start | device={device}")

    while epoch < args.max_epochs:
        state, terminal = model.prepare_state(
            latest_scan, distance, cos, sin, collision, goal, a)
        action = model.get_action(np.array(state), True)
        a_in = [(action[0]+1)/4, action[1]]

        latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(
            lin_velocity=a_in[0], ang_velocity=a_in[1])

        next_state, terminal = model.prepare_state(
            latest_scan, distance, cos, sin, collision, goal, a)
        replay_buffer.add(state, action, reward, terminal, next_state)

        if terminal or steps == args.max_steps:
            last_collision = collision
            last_goal = goal
            latest_scan, distance, cos, sin, collision, goal, a, reward = sim.reset()
            outcome = "GOAL" if last_goal else ("COL" if last_collision else "timeout")
            print(f"Epoch {epoch+1}/{args.max_epochs} | Ep {episode+1}/{args.episodes_per_epoch} | {outcome}", flush=True)
            episode += 1
            steps = 0
            if episode % args.train_every_n == 0:
                model.train(replay_buffer=replay_buffer,
                           iterations=args.training_iterations,
                           batch_size=args.batch_size)
        else:
            steps += 1

        if episode >= args.episodes_per_epoch:
            episode = 0
            epoch += 1
            sr = evaluate(model, epoch, eval_sim, args.nr_eval_episodes)

            if epoch % args.save_every == 0:
                try:
                    model.save(f"{args.model_name}_epoch_{epoch}",
                               "models/CNNTD3/checkpoint")
                except Exception:
                    pass

            if sr > best_sr:
                best_sr = sr
                try:
                    model.save(f"{args.model_name}_best",
                               "models/CNNTD3/checkpoint")
                    print(f"★ Best model saved SR={sr:.0%}")
                except Exception:
                    pass

    print("Training finished")


if __name__ == "__main__":
    main()
