"""
收集完整RL指标：SR, 碰撞率, 回合奖励, 路径长度, 路径效率
对 baseline 和 STPS 在标准环境跑100 episodes
"""
from matplotlib.patches import Rectangle
import sys, os, numpy as np, torch, json
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, 'robot_nav')
os.chdir(os.path.expanduser('~/DRL-robot-navigation-IR-SIM'))
os.environ.pop("DISPLAY", None)

from robot_nav.SIM_ENV.sim import SIM
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3

device = torch.device('cpu')
ckpt = 'models/CNNTD3/checkpoint'
ckpt_r = 'robot_nav/models/CNNTD3/checkpoint'

m_base = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="m1")
try: m_base.load("CNNTD3",ckpt)
except: m_base.load("CNNTD3",ckpt_r)
m_base.actor.eval()

m_v7 = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="m2")
m_v7.load("CNNTD3_v7_finetune_best",ckpt); m_v7.actor.eval()

m_imp = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="m3")
try: m_imp.load("CNNTD3_improved",ckpt)
except: m_imp.load("CNNTD3_improved",ckpt_r)
m_imp.actor.eval()
print("Models loaded")

SW=20;SD=0.15;ES=120;PD=0.5;OW=12;OT=5

def osc(ph):
    if len(ph)<OW: return False
    r=list(ph)[-OW:]; rv=0; px,py=None,None
    for i in range(1,len(r)):
        dx=r[i][0]-r[i-1][0]; dy=r[i][1]-r[i-1][1]
        if px is not None and dx*px+dy*py<0: rv+=1
        px,py=dx,dy
    return rv>=OT

def run_metrics(model, world, max_steps, mode='single', random_obs=True):
    """Run one episode, return full metrics"""
    sim = SIM(world_file=world, disable_plotting=True)
    scan,d,c,s,col,g,a,r = sim.reset(random_obstacles=random_obs)
    prev = [0.0, 0.0]
    total_reward = 0.0
    positions = []
    
    ph = deque(maxlen=max(SW,OW+2))
    sm='main'; ec=0; est=None; sw=0; stm=0; es=ES
    
    start_state = sim.env.get_robot_state()
    start_pos = np.array([start_state[0].item(), start_state[1].item()])
    goal_pos = np.array([sim.env.robot.goal[0].item(), sim.env.robot.goal[1].item()])
    optimal_dist = np.linalg.norm(goal_pos - start_pos)
    
    for step in range(max_steps):
        rs = sim.env.get_robot_state()
        cp = np.array([rs[0].item(), rs[1].item()])
        positions.append(cp.copy())
        
        if mode == 'stps':
            ph.append(cp)
            if sm == 'main':
                stm += 1; tr = False
                if len(ph)>=SW and np.linalg.norm(ph[-1]-ph[-SW])<SD: tr=True
                if not tr and stm>8 and osc(ph): tr=True
                if tr: sm='escape';ec=0;est=cp.copy();sw+=1;stm=0;ph.clear()
                if sw>1: es=min(ES*2,240)
            else:
                ec+=1; dd=np.linalg.norm(cp-est)
                if ec>=es and dd>PD: sm='main';stm=0;ph.clear()
                elif ec>=es*3: sm='main';stm=0;ph.clear()
            am = m_v7 if sm=='main' else m_imp
        else:
            am = model
        
        state,_ = am.prepare_state(scan,d,c,s,col,g,prev)
        action = am.get_action(np.array(state), False)
        prev = list(action)
        lin = float(np.clip((action[0]+1)/4, 0, 0.5))
        ang = float(np.clip(action[1], -1, 1))
        scan,d,c,s,col,g,a,r = sim.step(lin, ang)
        total_reward += r
        
        if g:
            positions.append(np.array([sim.env.get_robot_state()[0].item(),
                                        sim.env.get_robot_state()[1].item()]))
            sim.env.end()
            path_len = sum(np.linalg.norm(positions[i+1]-positions[i]) for i in range(len(positions)-1))
            efficiency = optimal_dist / max(path_len, 0.01)
            return {'outcome': 'goal', 'reward': total_reward, 'steps': step+1,
                    'path_length': path_len, 'efficiency': min(efficiency, 1.0),
                    'collision': False}
        if col:
            sim.env.end()
            path_len = sum(np.linalg.norm(positions[i+1]-positions[i]) for i in range(len(positions)-1))
            return {'outcome': 'collision', 'reward': total_reward, 'steps': step+1,
                    'path_length': path_len, 'efficiency': 0.0,
                    'collision': True}
    
    sim.env.end()
    path_len = sum(np.linalg.norm(positions[i+1]-positions[i]) for i in range(len(positions)-1))
    return {'outcome': 'timeout', 'reward': total_reward, 'steps': max_steps,
            'path_length': path_len, 'efficiency': 0.0,
            'collision': False}


# ===== Run 100 episodes each =====
N = 100
world = 'robot_nav/worlds/robot_world.yaml'

results = {}
for name, model, mode in [('CNNTD3_baseline', m_base, 'single'),
                            ('STPS_v2', None, 'stps')]:
    print(f"\n===== {name} =====")
    metrics = []
    for i in range(N):
        m = run_metrics(model, world, 300, mode=mode)
        metrics.append(m)
        if (i+1) % 25 == 0:
            sr = sum(1 for x in metrics if x['outcome']=='goal') / len(metrics)
            print(f"  {i+1}/{N}: SR={sr:.0%}")
    
    sr = sum(1 for x in metrics if x['outcome']=='goal') / N
    col_rate = sum(1 for x in metrics if x['collision']) / N
    avg_reward = np.mean([x['reward'] for x in metrics])
    avg_path = np.mean([x['path_length'] for x in metrics])
    successes = [x for x in metrics if x['outcome']=='goal']
    avg_path_succ = np.mean([x['path_length'] for x in successes]) if successes else 0
    avg_eff = np.mean([x['efficiency'] for x in successes]) if successes else 0
    avg_steps = np.mean([x['steps'] for x in metrics])
    
    results[name] = {
        'SR': f"{sr:.0%}",
        'Collision_rate': f"{col_rate:.0%}",
        'Avg_reward': f"{avg_reward:.1f}",
        'Avg_path_length': f"{avg_path_succ:.2f}m",
        'Path_efficiency': f"{avg_eff:.2f}",
        'Avg_steps': f"{avg_steps:.0f}",
    }
    
    print(f"  SR: {sr:.0%}")
    print(f"  Collision rate: {col_rate:.0%}")
    print(f"  Avg reward: {avg_reward:.1f}")
    print(f"  Avg path length (success): {avg_path_succ:.2f}m")
    print(f"  Path efficiency (success): {avg_eff:.2f}")
    print(f"  Avg steps: {avg_steps:.0f}")

# Summary table
print(f"\n{'='*70}")
print(f"{'Metric':<22} {'CNNTD3 baseline':>18} {'STPS v2':>18}")
print(f"{'-'*70}")
for metric in ['SR','Collision_rate','Avg_reward','Avg_path_length','Path_efficiency','Avg_steps']:
    print(f"{metric:<22} {results['CNNTD3_baseline'][metric]:>18} {results['STPS_v2'][metric]:>18}")
print(f"{'='*70}")

with open('full_rl_metrics.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\n💾 full_rl_metrics.json")
