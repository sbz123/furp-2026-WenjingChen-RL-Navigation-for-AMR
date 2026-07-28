from matplotlib.patches import Rectangle
import sys, os, numpy as np, torch
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

m_base = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="s1")
try: m_base.load("CNNTD3",ckpt)
except: m_base.load("CNNTD3",ckpt_r)
m_base.actor.eval()

m_v7 = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="s2")
m_v7.load("CNNTD3_v7_finetune_best",ckpt); m_v7.actor.eval()

m_imp = CNNTD3(state_dim=185,action_dim=2,max_action=1,device=device,load_model=False,model_name="s3")
try: m_imp.load("CNNTD3_improved",ckpt)
except: m_imp.load("CNNTD3_improved",ckpt_r)
m_imp.actor.eval()
print("Models loaded")

SW=20; SD=0.15; ES=120; PD=0.5; OW=12; OT=5

def osc(ph):
    if len(ph)<OW: return False
    r=list(ph)[-OW:]; rv=0; px,py=None,None
    for i in range(1,len(r)):
        dx=r[i][0]-r[i-1][0]; dy=r[i][1]-r[i-1][1]
        if px is not None and dx*px+dy*py<0: rv+=1
        px,py=dx,dy
    return rv>=OT

def run(model, world, rs, rg, ms, mode='single'):
    sim=SIM(world_file=world,disable_plotting=True)
    sc,d,c,s,co,g,a,r=sim.reset(robot_state=rs,robot_goal=rg,random_obstacles=False)
    prev=[0.0,0.0]; traj=[]; swp=[]
    ph=deque(maxlen=max(SW,OW+2)); sm='main'; ec=0; est=None; sw=0; stm=0; es=ES
    for step in range(ms):
        rst=sim.env.get_robot_state(); cp=np.array([rst[0].item(),rst[1].item()]); traj.append(cp.copy())
        if mode=='stps':
            ph.append(cp)
            if sm=='main':
                stm+=1; tr=False
                if len(ph)>=SW and np.linalg.norm(ph[-1]-ph[-SW])<SD: tr=True
                if not tr and stm>8 and osc(ph): tr=True
                if tr: sm='escape';ec=0;est=cp.copy();sw+=1;stm=0;ph.clear();swp.append((step,cp.copy(),'esc'))
                if sw>1: es=min(ES*2,240)
            else:
                ec+=1; dd=np.linalg.norm(cp-est)
                if ec>=es and dd>PD: sm='main';stm=0;ph.clear();swp.append((step,cp.copy(),'main'))
                elif ec>=es*3: sm='main';stm=0;ph.clear();swp.append((step,cp.copy(),'main'))
            am=m_v7 if sm=='main' else m_imp
        else: am=model
        st,_=am.prepare_state(sc,d,c,s,co,g,prev)
        act=am.get_action(np.array(st),False); prev=list(act)
        sc,d,c,s,co,g,a,r=sim.step(float(np.clip((act[0]+1)/4,0,0.5)),float(np.clip(act[1],-1,1)))
        if g: traj.append(np.array([sim.env.get_robot_state()[0].item(),sim.env.get_robot_state()[1].item()])); sim.env.end(); return 'goal',np.array(traj),swp
        if co: sim.env.end(); return 'collision',np.array(traj),swp
    sim.env.end(); return 'timeout',np.array(traj),swp

def draw_obstacles(ax, wtype):
    if wtype=='u_trap':
        ax.add_patch(Rectangle((7.85,2.85),0.3,4.3,color='#2D3748',alpha=0.8))
        ax.add_patch(Rectangle((2.3,6.85),5.7,0.3,color='#2D3748',alpha=0.8))
        ax.add_patch(Rectangle((2.3,2.85),5.7,0.3,color='#2D3748',alpha=0.8))
    elif wtype=='narrow_door':
        ax.add_patch(Rectangle((4.8,0),0.4,4.5,color='#2D3748',alpha=0.8))
        ax.add_patch(Rectangle((4.8,5.5),0.4,4.5,color='#2D3748',alpha=0.8))

def plot(traj, swp, wtype, title, outcome, fname, sxy, gxy):
    fig,ax=plt.subplots(figsize=(6,6))
    ax.set_xlim(0,10); ax.set_ylim(0,10); ax.set_aspect('equal')
    ax.set_xlabel('x (m)',fontsize=12); ax.set_ylabel('y (m)',fontsize=12)
    ax.set_title(title,fontsize=14,fontweight='bold',pad=10); ax.grid(True,alpha=0.2)
    draw_obstacles(ax,wtype)
    ax.plot([0,10,10,0,0],[0,0,10,10,0],'k-',linewidth=2)
    if len(swp)>0:
        segs=[]; ss=0; md='main'
        for st,pos,sw in swp:
            segs.append((ss,st,md)); md='escape' if sw=='esc' else 'main'; ss=st
        segs.append((ss,len(traj)-1,md))
        for a,b,m in segs:
            if b<=a: continue
            seg=traj[a:b+1]; cl='#2B6CB0' if m=='main' else '#E53E3E'
            ax.plot(seg[:,0],seg[:,1],'-',color=cl,linewidth=2,alpha=0.8)
        for st,pos,sw in swp:
            mk='v' if sw=='esc' else '^'; cl='#E53E3E' if sw=='esc' else '#38A169'
            ax.plot(pos[0],pos[1],mk,color=cl,markersize=10,zorder=5)
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([0],[0],color='#2B6CB0',lw=2,label='Precision'),Line2D([0],[0],color='#E53E3E',lw=2,label='Escape'),Line2D([0],[0],marker='v',color='#E53E3E',ls='None',ms=8,label='Switch')],loc='upper left',fontsize=9)
    else:
        cl='#38A169' if outcome=='goal' else '#E53E3E'
        ax.plot(traj[:,0],traj[:,1],'-',color=cl,linewidth=2,alpha=0.8)
    ax.plot(sxy[0],sxy[1],'o',color='#2B6CB0',markersize=12,zorder=10)
    ax.plot(gxy[0],gxy[1],'*',color='#D69E2E',markersize=15,zorder=10)
    rc='#38A169' if outcome=='goal' else '#E53E3E'
    rt={'goal':'SUCCESS','collision':'COLLISION','timeout':'TIMEOUT'}[outcome]
    ax.text(0.98,0.02,f'{rt} ({len(traj)} steps)',transform=ax.transAxes,ha='right',va='bottom',fontsize=11,fontweight='bold',color=rc,bbox=dict(boxstyle='round,pad=0.3',facecolor='white',alpha=0.9))
    plt.tight_layout(); plt.savefig(fname,dpi=150,bbox_inches='tight'); plt.close()
    print(f"  Saved: {fname}")

out=os.path.expanduser('~/poster_screenshots')
os.makedirs(out,exist_ok=True)

cases=[
    ('1_fail_baseline_utrap','Failure: Baseline in U-trap',m_base,'single','robot_nav/worlds/u_trap_world.yaml','u_trap',[[7.5],[5.0],[0.0]],[[9.0],[5.0],[0]],[7.5,5.0],[9.0,5.0]),
    ('2_fail_explore_narrow','Failure: Exploration in narrow door',m_imp,'single','robot_nav/worlds/narrow_door_world.yaml','narrow_door',[[2.0],[5.0],[0.0]],[[8.0],[5.0],[0]],[2.0,5.0],[8.0,5.0]),
    ('3_fail_annealed_utrap','Failure: Annealed in U-trap',m_v7,'single','robot_nav/worlds/u_trap_world.yaml','u_trap',[[7.5],[5.0],[3.14]],[[9.0],[5.0],[0]],[7.5,5.0],[9.0,5.0]),
    ('4_success_stps_utrap','Success: STPS escapes U-trap',None,'stps','robot_nav/worlds/u_trap_world.yaml','u_trap',[[7.5],[5.0],[1.57]],[[9.0],[5.0],[0]],[7.5,5.0],[9.0,5.0]),
    ('5_success_stps_narrow','Success: STPS passes narrow door',None,'stps','robot_nav/worlds/narrow_door_world.yaml','narrow_door',[[2.0],[5.0],[0.0]],[[8.0],[5.0],[0]],[2.0,5.0],[8.0,5.0]),
    ('6_success_stps_standard','Success: STPS in standard env',None,'stps','robot_nav/worlds/robot_world.yaml','standard',[[2.0],[2.0],[0.0]],[[9.0],[9.0],[0]],[2.0,2.0],[9.0,9.0]),
]

for name,title,model,mode,world,wtype,start,goal,sxy,gxy in cases:
    print(f"\n{name}...")
    out_path,traj,swp=run(model,world,start,goal,500,mode)
    print(f"  {out_path}, steps={len(traj)}, switches={len(swp)}")
    plot(traj,swp,wtype,title,out_path,os.path.join(out,f"{name}.png"),sxy,gxy)

print(f"\nDone! Files in {out}/")
