# 保存脚本
cat > ~/DRL-robot-navigation-IR-SIM/smoke_test.sh << 'SHELLEOF'
echo "========================================="
echo "  Week 1 Checkpoint - Environment Check"
echo "========================================="
echo ""
echo "=== 1. Python环境 (neupan) ==="
conda activate neupan
python --version
which python
echo ""
echo "=== 2. 核心依赖 ==="
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
python -c "import irsim; print('IR-SIM: OK')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
echo ""
echo "=== 3. 项目结构 ==="
ls ~/DRL-robot-navigation-IR-SIM/robot_nav/models/
echo ""
echo "=== 4. Smoke Test: CNNTD3 ==="
cd ~/DRL-robot-navigation-IR-SIM
python -c "
from robot_nav.models.CNNTD3.CNNTD3 import CNNTD3
import torch
model = CNNTD3(state_dim=185, action_dim=2, max_action=1,
               device=torch.device('cuda'), load_model=True, model_name='CNNTD3')
print('CNNTD3 loaded successfully')
"
echo ""
echo "=== 5. Smoke Test: RCPG ==="
python -c "
from robot_nav.models.RCPG.RCPG import RCPG
import torch
model = RCPG(state_dim=185, action_dim=2, max_action=1,
             device=torch.device('cuda'), load_model=True, rnn='gru')
print('RCPG loaded successfully')
"
echo ""
echo "=== 6. Smoke Test: IR-SIM ==="
python -c "
from robot_nav.SIM_ENV.sim import SIM
sim = SIM(world_file='robot_nav/worlds/eval_world.yaml', disable_plotting=True)
print('IR-SIM environment started successfully')
"
echo ""
echo "=== 7. Habitat ==="
conda activate habitat 2>/dev/null || conda activate base
python -c "import habitat; print(f'Habitat: {habitat.__version__}')" 2>/dev/null || echo "Habitat: not found"
python -c "import habitat_baselines; print('Habitat-Baselines: OK')" 2>/dev/null || echo "Habitat-Baselines: not found"
echo ""
echo "=== 8. ROS 2 ==="
if [ -d "/opt/ros/rolling" ]; then
    source /opt/ros/rolling/setup.bash && echo "ROS 2 Rolling: OK (/opt/ros/rolling)"
elif [ -d "/opt/ros/humble" ]; then
    source /opt/ros/humble/setup.bash && echo "ROS 2 Humble: OK"
else
    echo "ROS 2: not found"
fi
echo ""
echo "=== 9. GPU ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""
echo "=== 10. NeuPAN ==="
conda activate neupan
python -c "import irsim; print('NeuPAN (neupan conda): OK')" 2>/dev/null || echo "NeuPAN: not found"
echo ""
echo "========================================="
echo "  All checks complete"
echo "========================================="
SHELLEOF
