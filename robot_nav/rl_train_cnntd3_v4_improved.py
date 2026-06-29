"""
Improved CNNTD3 training script.
- Combines features from original and v4 variants:
  - longer default training (max_epochs=120)
  - optional loading of saved replay buffer + optional pretraining
  - separate eval SIM instance
  - saves best checkpoint by eval SR and periodic saves
  - fixes outcome logging bug (uses last step's collision/goal rather than reset return)

Usage examples:
  python robot_nav/rl_train_cnntd3_v4_improved.py
  python robot_nav/rl_train_cnntd3_v4_improved.py --max-epochs 120 --load-buffer --pretrain
"""

from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3

import argparse
import torch
import numpy as np
from robot_nav.SIM_ENV.sim import SIM
from utils import get_buffer


def evaluate(model, epoch, eval_sim, eval_episodes=10, max_eval_steps=500):
    """Run deterministic evaluation using a separate sim instance."""
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
                latest_scan, distance, cos, sin, collision, goal, a
            )
            action = model.get_action(np.array(state), False)
            a_in = [(action[0] + 1) / 4, action[1]]
            latest_scan, distance, cos, sin, collision, goal, a, reward = eval_sim.step(
                lin_velocity=a_in[0], ang_velocity=a_in[1]
            )
            avg_reward += reward
            count += 1
            if collision:
                col += 1
            if goal:
                goals += 1
            done = collision or goal
    avg_reward /= eval_episodes
    avg_col = col / eval_episodes
    avg_goal = goals / eval_episodes
    print(f"Average Reward: {avg_reward}")
    print(f"Average Collision rate: {avg_col}")
    print(f"Average Goal rate: {avg_goal}")
    print("..............................................")
    # write scalars if writer exists
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
    parser.add_argument("--load-buffer", action="store_true", help="Load saved replay buffer from disk if available")
    parser.add_argument("--pretrain", action="store_true", help="Run a short pretraining phase using the loaded buffer (requires --load-buffer)")
    parser.add_argument("--pretraining-iterations", type=int, default=10)
    parser.add_argument("--save-every", type=int, default=5, help="Periodically save checkpoint every N epochs")
    parser.add_argument("--model-name", type=str, default="CNNTD3_v4_improved")
    args = parser.parse_args()

    action_dim = 2
    max_action = 1
    state_dim = 185
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # training hyperparams
    nr_eval_episodes = args.nr_eval_episodes
    max_epochs = args.max_epochs
    episodes_per_epoch = args.episodes_per_epoch
    train_every_n = args.train_every_n
    training_iterations = args.training_iterations
    batch_size = args.batch_size
    max_steps = args.max_steps
    save_every = args.save_every

    model = CNNTD3(
        state_dim=state_dim,
        action_dim=action_dim,
        max_action=max_action,
        device=device,
        save_every=save_every,
        load_model=False,
        model_name=args.model_name,
    )

    sim = SIM(world_file="worlds/robot_world.yaml", disable_plotting=True)

    # build or load replay buffer
    replay_buffer = get_buffer(
        model,
        sim,
        args.load_buffer,
        args.pretrain,
        args.pretraining_iterations,
        training_iterations,
        batch_size,
    )

    # optional pretraining using loaded buffer
    if args.load_buffer and args.pretrain:
        print("Running pretraining using loaded replay buffer...")
        model.train(replay_buffer=replay_buffer, iterations=args.pretraining_iterations, batch_size=batch_size)
        print("Pretraining finished")

    # get an initial state from environment
    latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(lin_velocity=0.0, ang_velocity=0.0)

    epoch = 0
    episode = 0
    steps = 0
    best_sr = 0.0

    print(f"{args.model_name} training start | device={device}")

    # separate evaluation simulator to avoid interfering with training sim
    eval_sim = SIM(world_file="worlds/robot_world.yaml", disable_plotting=True)

    while epoch < max_epochs:
        state, terminal = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
        action = model.get_action(np.array(state), True)
        a_in = [(action[0] + 1) / 4, action[1]]

        latest_scan, distance, cos, sin, collision, goal, a, reward = sim.step(
            lin_velocity=a_in[0], ang_velocity=a_in[1]
        )

        next_state, terminal = model.prepare_state(latest_scan, distance, cos, sin, collision, goal, a)
        replay_buffer.add(state, action, reward, terminal, next_state)

        if terminal or steps == max_steps:
            # save the last step outcome before reset (fix logging bug)
            last_collision = collision
            last_goal = goal
            latest_scan, distance, cos, sin, collision, goal, a, reward = sim.reset()
            outcome = "GOAL" if last_goal else ("COL" if last_collision else "timeout")
            print(f"Epoch {epoch+1}/{max_epochs} | Ep {episode+1}/{episodes_per_epoch} | {outcome}", flush=True)

            episode += 1

            if episode % train_every_n == 0:
                model.train(replay_buffer=replay_buffer, iterations=training_iterations, batch_size=batch_size)

            steps = 0
        else:
            steps += 1

        if episode >= episodes_per_epoch:
            # end of epoch
            episode = 0
            epoch += 1

            # evaluate on separate sim
            sr = evaluate(model, epoch, eval_sim, eval_episodes=nr_eval_episodes)

            # save periodic checkpoint
            if epoch % save_every == 0:
                try:
                    model.save(f"{args.model_name}_epoch_{epoch}", "models/CNNTD3/checkpoint")
                except Exception:
                    pass

            # save best checkpoint by success rate
            if sr > best_sr:
                best_sr = sr
                try:
                    model.save(f"{args.model_name}_best", "models/CNNTD3/checkpoint")
                    print(f"★ Best model saved SR={sr:.0%}")
                except Exception:
                    pass

    print("Training finished")


if __name__ == "__main__":
    main()
