"""
ATD3: Attention-based TD3 for LiDAR Navigation
改进：用 Multi-head Self-Attention 替代 1D CNN 处理激光雷达
state_dim = 105 (100点雷达 + distance + cos + sin + 2action)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from torch.utils.tensorboard import SummaryWriter


class LiDARAttention(nn.Module):
    """Multi-head Self-Attention 处理激光雷达点云"""
    def __init__(self, n_points=100, d_model=32, n_heads=4):
        super().__init__()
        self.n_points = n_points
        self.d_model = d_model
        # 每个激光点嵌入到 d_model 维
        self.point_embed = nn.Linear(1, d_model)
        # 位置编码（角度信息）
        angles = torch.linspace(-np.pi/2, np.pi/2, n_points)
        pos_enc = torch.stack([torch.sin(angles), torch.cos(angles)], dim=-1)
        self.register_buffer('pos_enc', pos_enc)
        self.pos_embed = nn.Linear(2, d_model)
        # Multi-head attention
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        # 输出压缩
        self.output = nn.Linear(d_model * n_points, 64)

    def forward(self, laser):
        # laser: (batch, n_points)
        x = laser.unsqueeze(-1)                          # (B, N, 1)
        x = F.relu(self.point_embed(x))                  # (B, N, d_model)
        pos = F.relu(self.pos_embed(
            self.pos_enc.unsqueeze(0).expand(x.size(0), -1, -1)))
        x = x + pos                                      # 加位置编码
        x, _ = self.attn(x, x, x)                       # Self-attention
        x = self.norm(x)                                 # LayerNorm
        x = x.flatten(start_dim=1)                      # (B, N*d_model)
        x = F.relu(self.output(x))                      # (B, 64)
        return x


class Actor(nn.Module):
    def __init__(self, action_dim, n_points=100):
        super().__init__()
        self.n_points = n_points
        self.lidar_attn = LiDARAttention(n_points=n_points)
        self.goal_embed   = nn.Linear(3, 16)
        self.action_embed = nn.Linear(2, 16)
        # 64 + 16 + 16 = 96
        self.fc1 = nn.Linear(96, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, action_dim)
        self.tanh = nn.Tanh()

    def forward(self, s):
        if len(s.shape) == 1:
            s = s.unsqueeze(0)
        laser = s[:, :self.n_points]          # 前100维
        goal  = s[:, self.n_points:self.n_points+3]   # distance, cos, sin
        act   = s[:, self.n_points+3:]        # prev_action

        l = self.lidar_attn(laser)
        g = F.relu(self.goal_embed(goal))
        a = F.relu(self.action_embed(act))

        x = torch.cat([l, g, a], dim=-1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.tanh(self.fc3(x))


class Critic(nn.Module):
    def __init__(self, action_dim, n_points=100):
        super().__init__()
        self.n_points = n_points
        # Q1
        self.lidar_attn1 = LiDARAttention(n_points=n_points)
        self.goal_embed1   = nn.Linear(3, 16)
        self.action_embed1 = nn.Linear(2, 16)
        self.act_embed1    = nn.Linear(action_dim, 16)
        self.q1_fc1 = nn.Linear(112, 256)
        self.q1_fc2 = nn.Linear(256, 128)
        self.q1_fc3 = nn.Linear(128, 1)
        # Q2
        self.lidar_attn2 = LiDARAttention(n_points=n_points)
        self.goal_embed2   = nn.Linear(3, 16)
        self.action_embed2 = nn.Linear(2, 16)
        self.act_embed2    = nn.Linear(action_dim, 16)
        self.q2_fc1 = nn.Linear(112, 256)
        self.q2_fc2 = nn.Linear(256, 128)
        self.q2_fc3 = nn.Linear(128, 1)

    def _forward_q(self, laser, goal, prev_act, action,
                   attn, ge, ae, acte, fc1, fc2, fc3):
        l = attn(laser)
        g = F.relu(ge(goal))
        a = F.relu(ae(prev_act))
        ac = F.relu(acte(action))
        x = torch.cat([l, g, a, ac], dim=-1)
        x = F.relu(fc1(x))
        x = F.relu(fc2(x))
        return fc3(x)

    def forward(self, s, action):
        if len(s.shape) == 1:
            s = s.unsqueeze(0)
        laser    = s[:, :self.n_points]
        goal     = s[:, self.n_points:self.n_points+3]
        prev_act = s[:, self.n_points+3:]
        q1 = self._forward_q(laser, goal, prev_act, action,
            self.lidar_attn1, self.goal_embed1, self.action_embed1,
            self.act_embed1, self.q1_fc1, self.q1_fc2, self.q1_fc3)
        q2 = self._forward_q(laser, goal, prev_act, action,
            self.lidar_attn2, self.goal_embed2, self.action_embed2,
            self.act_embed2, self.q2_fc1, self.q2_fc2, self.q2_fc3)
        return q1, q2

    def Q1(self, s, action):
        if len(s.shape) == 1:
            s = s.unsqueeze(0)
        laser    = s[:, :self.n_points]
        goal     = s[:, self.n_points:self.n_points+3]
        prev_act = s[:, self.n_points+3:]
        return self._forward_q(laser, goal, prev_act, action,
            self.lidar_attn1, self.goal_embed1, self.action_embed1,
            self.act_embed1, self.q1_fc1, self.q1_fc2, self.q1_fc3)


class ATD3:
    """Attention-TD3 主类，接口与 CNNTD3 完全一致"""
    def __init__(self, state_dim=105, action_dim=2, max_action=1,
                 device='cpu', save_every=5, load_model=False,
                 model_name='ATD3',
                 save_directory=Path('robot_nav/models/ATD3/checkpoint'),
                 load_directory=Path('robot_nav/models/ATD3/checkpoint')):

        self.n_points   = state_dim - 5   # 100
        self.action_dim = action_dim
        self.max_action = max_action
        self.device     = device
        self.save_every = save_every
        self.model_name = model_name
        self.save_directory = Path(save_directory)
        self.load_directory = Path(load_directory)

        self.actor         = Actor(action_dim, self.n_points).to(device)
        self.actor_target  = Actor(action_dim, self.n_points).to(device)
        self.actor_target.load_state_dict(self.actor.state_dict())
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=3e-4)

        self.critic        = Critic(action_dim, self.n_points).to(device)
        self.critic_target = Critic(action_dim, self.n_points).to(device)
        self.critic_target.load_state_dict(self.critic.state_dict())
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=3e-4)

        self.writer = SummaryWriter(comment=model_name)
        self.training_step = 0

        if load_model:
            self.load(model_name, load_directory)

    def get_action(self, state, add_noise=False):
        state = torch.FloatTensor(state).to(self.device)
        action = self.actor(state).cpu().detach().numpy().flatten()
        if add_noise:
            noise = np.random.normal(0, 0.1, size=action.shape)
            action = np.clip(action + noise, -1, 1)
        return action

    def prepare_state(self, laser_scan, distance, cos, sin,
                      collision, goal, action):
        # state: [laser(100), distance, cos, sin, prev_lin, prev_ang]
        state = np.concatenate([
            np.array(laser_scan[:self.n_points], dtype=np.float32),
            [distance, cos, sin],
            action
        ])
        terminal = collision or goal
        return state, terminal

    def train(self, replay_buffer, iterations=80, batch_size=64,
              discount=0.99, tau=0.005, policy_noise=0.2,
              noise_clip=0.5, policy_freq=2):

        avg_q, max_q, total_loss = 0, 0, 0
        for it in range(iterations):
            s, a, r, t, s2 = replay_buffer.sample_batch(batch_size)
            state      = torch.FloatTensor(s).to(self.device)
            action     = torch.FloatTensor(a).to(self.device)
            reward     = torch.FloatTensor(r).reshape(-1, 1).to(self.device)
            done       = torch.FloatTensor(t).reshape(-1, 1).to(self.device)
            next_state = torch.FloatTensor(s2).to(self.device)

            with torch.no_grad():
                noise = (torch.randn_like(action) * policy_noise
                         ).clamp(-noise_clip, noise_clip)
                next_action = (self.actor_target(next_state) + noise
                               ).clamp(-self.max_action, self.max_action)
                tq1, tq2 = self.critic_target(next_state, next_action)
                target_q = reward + (1-done) * discount * torch.min(tq1, tq2)

            q1, q2 = self.critic(state, action)
            critic_loss = F.mse_loss(q1, target_q) + F.mse_loss(q2, target_q)

            self.critic_optimizer.zero_grad()
            critic_loss.backward()
            self.critic_optimizer.step()

            avg_q += q1.mean().item()
            max_q  = max(max_q, q1.max().item())
            total_loss += critic_loss.item()

            if it % policy_freq == 0:
                actor_loss = -self.critic.Q1(state, self.actor(state)).mean()
                self.actor_optimizer.zero_grad()
                actor_loss.backward()
                self.actor_optimizer.step()
                for p, tp in zip(self.actor.parameters(),
                                 self.actor_target.parameters()):
                    tp.data.copy_(tau*p.data + (1-tau)*tp.data)
                for p, tp in zip(self.critic.parameters(),
                                 self.critic_target.parameters()):
                    tp.data.copy_(tau*p.data + (1-tau)*tp.data)

        self.training_step += 1
        avg_q /= iterations
        total_loss /= iterations
        self.writer.add_scalar('train/avg_Q', avg_q, self.training_step)
        self.writer.add_scalar('train/max_Q', max_q, self.training_step)
        self.writer.add_scalar('train/loss',  total_loss, self.training_step)

    def save(self, filename, directory):
        Path(directory).mkdir(parents=True, exist_ok=True)
        torch.save(self.actor.state_dict(),
                   f'{directory}/{filename}_actor.pth')
        torch.save(self.critic.state_dict(),
                   f'{directory}/{filename}_critic.pth')

    def load(self, filename, directory):
        self.actor.load_state_dict(
            torch.load(f'{directory}/{filename}_actor.pth',
                       map_location=self.device, weights_only=False))
        self.critic.load_state_dict(
            torch.load(f'{directory}/{filename}_critic.pth',
                       map_location=self.device, weights_only=False))
        print(f'Loaded weights from: {directory}')
