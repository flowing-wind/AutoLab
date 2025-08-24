import time
import matplotlib.pyplot as plt
import numpy as np

#======================================================================
#== 1. CONFIGURATION
#======================================================================
# --- 物理系统参数 ---
INITIAL_TEMP = 300.0            # 系统初始温度 (K)
AMBIENT_TEMP = 300.0            # 环境温度 (K)
PARASITIC_HEAT_LOAD = 0.1       # 寄生热负载 (K/s)
HEAT_LOSS_COEFF = 0.0001        # 自然热交换系数
COOLING_EFFECT_FACTOR = 2.0     # 制冷功率转换系数 (100%功率下的最大降温速率 K/s)

# --- 控制目标 ---
# (时间点, 目标温度)
# SETPOINT_SCHEDULE = [
#     (0, 300.0), (200, 240.0), (1500, 150.0), (3000, 80.0), (4500, 30.0), (6000, 3.0)
# ]

SETPOINT_SCHEDULE = [
    (0, 300.0), (10,298)
]
SIMULATION_DURATION = 80      # 总仿真时长 (s)

# --- PID 参数调校 (软着陆优化配置) ---
KP = -130.0  # 比例项: 主导响应速度，确保快速降温
KI = -1.5    # 积分项: 消除稳态误差，确保精准到达目标温度
KD = -600.0  # 微分项: 抑制过冲，实现平滑的“软着陆”

# --- 噪声与滤波器 ---
NOISE_LEVEL = 0.1   # 模拟传感器读数的噪声标准差
FILTER_ALPHA = 0.2  # 低通滤波器平滑系数 (0-1)，越小越平滑

#======================================================================
#== 2. 系统模型与仿真
#======================================================================
class CryoSystem:
    """模拟一个可被主动降温并受环境影响的低温物理系统"""
    def __init__(self):
        self.temperature = INITIAL_TEMP
        self.cooling_power = 0

    def update(self, dt=1.0):
        radiative_heat_transfer = HEAT_LOSS_COEFF * (AMBIENT_TEMP - self.temperature)
        active_cooling = -COOLING_EFFECT_FACTOR * self.cooling_power / 100.0
        self.temperature += (radiative_heat_transfer + PARASITIC_HEAT_LOAD + active_cooling) * dt
        self.temperature = max(0, self.temperature)
        return self.temperature

# --- 主循环 ---
system = CryoSystem()
times, true_temps, setpoints, outputs = [], [], [], []
current_time, schedule_index = 0, 0
target_setpoint = INITIAL_TEMP
integral_sum = 0.0
last_filtered_temp = INITIAL_TEMP
filtered_temp = INITIAL_TEMP
dt = 1.0

print("开始低温PID控制仿真 (最终优化版)...")
while current_time < SIMULATION_DURATION:
    # 从时间表中获取当前的目标温度
    if schedule_index < len(SETPOINT_SCHEDULE) - 1 and current_time >= SETPOINT_SCHEDULE[schedule_index + 1][0]:
        schedule_index += 1
    target_setpoint = SETPOINT_SCHEDULE[schedule_index][1]
    
    # 模拟带噪声的传感器读数
    true_temp = system.temperature
    noise = np.random.normal(0, NOISE_LEVEL)
    current_temp = true_temp + noise
    
    # 对带噪声的读数进行低通滤波，获得平滑的温度值用于PID计算
    filtered_temp = (FILTER_ALPHA * current_temp) + (1 - FILTER_ALPHA) * filtered_temp

    # 基于平滑后的温度计算PID三项
    error = target_setpoint - filtered_temp
    
    # 带抗饱和功能的积分项累积
    if len(outputs) > 0 and 0 < outputs[-1] < 100:
        integral_sum += error * dt
    
    # 微分项计算
    derivative = (filtered_temp - last_filtered_temp) / dt
    
    # 计算总输出并限制在0-100之间
    output = (KP * error) + (KI * integral_sum) - (KD * derivative)
    control_output = max(0, min(100, output))
    
    # 将控制输出应用到物理系统
    system.cooling_power = control_output
    system.update(dt=dt)

    # 更新状态变量用于下一次循环
    last_filtered_temp = filtered_temp
    
    # 记录数据
    times.append(current_time)
    true_temps.append(true_temp)
    outputs.append(control_output)
    
    current_time += dt
print("仿真结束。")

#======================================================================
#== 3. 绘图
#======================================================================
plt.figure(figsize=(15, 8))

# --- 上方温度图 ---
plt.subplot(2, 1, 1)
plt.plot(times, true_temps, label='System Temperature (K)', linewidth=2.0)
plt.title('Optimized PID Control Simulation')
plt.ylabel('Temperature (K)')
plt.grid(True)
plt.legend()

# --- 下方功率图 ---
plt.subplot(2, 1, 2)
plt.plot(times, outputs, 'g-', label='PID Output (Cooling Power %)')
plt.ylabel('Cooling Power (%)')
plt.xlabel('Time (s)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()