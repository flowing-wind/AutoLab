# 文件:     PIDTuner_SimulatedAnnealing.py
# 日期:     2025-08-25
# 描述:     使用模拟退火 (Simulated Annealing) 算法为 CryoSystem 模型自动整定 PID 参数。
#           该算法旨在避免陷入局部最优解，寻找全局更优的参数。

import numpy as np
import math
import matplotlib.pyplot as plt
from CryoSystem import CryoSystem, DEFAULT_KP, DEFAULT_KI, DEFAULT_KD

# --- 仿真与整定配置 ---
TARGET_TEMP = 3.0        # 目标温度 (K)
INITIAL_TEMP = 300.0     # 初始温度 (K)
SIM_DURATION = 2000      # 每次仿真运行的持续时间（秒/时间步）

def run_simulation(kp, ki, kd):
    """
    使用一组给定的 PID 参数运行一次完整的仿真。
    """
    system = CryoSystem(initial_temp=INITIAL_TEMP)
    system.kp, system.ki, system.kd = kp, ki, kd
    
    temperatures = []
    for _ in range(SIM_DURATION):
        temp = system.update_temperature(TARGET_TEMP)
        temperatures.append(temp)
    return temperatures

def evaluate_performance(temperatures):
    """
    为一次仿真计算成本分数。分数越低越好。
    该函数确保在任何情况下都返回一个数值。
    """
    # 检查仿真结果是否为空
    if not temperatures:
        return float('inf')

    # --- 标准 1: 在 ±2K 区间内稳定下来 ---
    settling_band_upper = TARGET_TEMP + 2.0
    settling_band_lower = TARGET_TEMP - 2.0
    settling_time = -1

    for i in range(len(temperatures)):
        if settling_band_lower <= temperatures[i] <= settling_band_upper:
            # 检查温度是否“保持”在区间内
            if all(settling_band_lower <= t <= settling_band_upper for t in temperatures[i:]):
                settling_time = i
                break
    
    # 如果系统从未稳定下来，返回一个代表“失败”的极大值
    if settling_time == -1:
        return float('inf')

    # --- 标准 2: 稳态误差在 ±1K 以内 ---
    steady_state_band_upper = TARGET_TEMP + 1.0
    steady_state_band_lower = TARGET_TEMP - 1.0
    
    steady_state_start_index = int(SIM_DURATION * 0.8)
    steady_state_temps = temperatures[steady_state_start_index:]
    
    avg_steady_state_temp = np.mean(steady_state_temps)
    steady_state_error = abs(avg_steady_state_temp - TARGET_TEMP)
    
    steady_state_penalty = (steady_state_error - 1.0)**2 * 5000 if steady_state_error > 1.0 else 0
    
    # --- 计算总成本 ---
    cost = (settling_time * 0.1) + (steady_state_error * 100) + steady_state_penalty
    
    return cost

def plot_results(default_temps, tuned_temps, best_params):
    """生成对比默认和整定后 PID 性能的图表。"""
    time_axis = np.arange(SIM_DURATION)
    
    # 设置 matplotlib 支持中文显示
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei'] # Windows/Linux
        plt.rcParams['axes.unicode_minus'] = False
    except:
        try:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # Mac
            plt.rcParams['axes.unicode_minus'] = False
        except:
            print("警告：未能设置中文字体，图表标题可能显示不正常。")

    plt.figure(figsize=(14, 8))
    plt.plot(time_axis, default_temps, 'b--', label=f'默认PID (Kp={DEFAULT_KP:.2f}, Ki={DEFAULT_KI:.5f}, Kd={DEFAULT_KD:.2f})')
    plt.plot(time_axis, tuned_temps, 'r-', label=f'模拟退火调参后PID (Kp={best_params["kp"]:.2f}, Ki={best_params["ki"]:.5f}, Kd={best_params["kd"]:.2f})', linewidth=2)
    
    plt.axhline(y=TARGET_TEMP, color='k', linestyle=':', label=f'目标温度 ({TARGET_TEMP}K)')
    plt.axhspan(TARGET_TEMP - 2, TARGET_TEMP + 2, color='orange', alpha=0.2, label='稳定区间 (±2K)')
    plt.axhspan(TARGET_TEMP - 1, TARGET_TEMP + 1, color='green', alpha=0.2, label='稳态区间 (±1K)')
    
    plt.title('PID 自动整定性能对比 (模拟退火 vs. 默认)')
    plt.xlabel('时间 (秒)')
    plt.ylabel('温度 (K)')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.ylim(0, INITIAL_TEMP / 2) # 调整Y轴范围以便更好地观察降温过程
    plt.xlim(0, SIM_DURATION)
    plt.show()

# --- 主模拟退火逻辑 ---
if __name__ == "__main__":
    print("--- 开始使用模拟退火进行PID自动整定 ---")

    # 模拟退火参数
    INITIAL_SA_TEMP = 1000.0  # 模拟退火的初始温度
    COOLING_RATE = 0.99       # 降温速率
    MIN_SA_TEMP = 0.1         # 模拟退火的最小温度
    
    # 初始解 (从默认值开始)
    current_params = {'kp': DEFAULT_KP, 'ki': DEFAULT_KI, 'kd': DEFAULT_KD}
    current_temps = run_simulation(**current_params)
    current_score = evaluate_performance(current_temps)

    # 记录历史最优解
    best_params = current_params
    best_score = current_score
    print(f"初始分数 (使用默认参数): {best_score:.2f}")
    
    temperature = INITIAL_SA_TEMP
    iteration = 0
    while temperature > MIN_SA_TEMP:
        iteration += 1
        
        # 1. 生成一个邻近解 (随机扰动当前解)
        new_params = current_params.copy()
        param_to_change = np.random.choice(['kp', 'ki', 'kd'])
        
        # 扰动幅度与温度相关，温度高时扰动大，探索范围广
        perturbation_scale = 0.5 * (temperature / INITIAL_SA_TEMP) + 0.05
        perturbation = np.random.normal(0, perturbation_scale)
        new_params[param_to_change] *= (1 + perturbation)
        
        # 确保 ki 保持非常小且为负
        if new_params['ki'] > 0: new_params['ki'] = -1e-6

        # 2. 评估新解
        new_temps = run_simulation(**new_params)
        new_score = evaluate_performance(new_temps)
        
        # 3. 决定是否接受新解
        delta_score = new_score - current_score
        
        if delta_score < 0: # 如果新解更好，总是接受
            current_params = new_params
            current_score = new_score
            if new_score < best_score: # 如果比历史最优还好，就更新历史最优
                best_params = new_params
                best_score = new_score
                print(f"  * 新最优! 迭代: {iteration}, 分数: {best_score:.2f}, Kp: {best_params['kp']:.2f}, Ki: {best_params['ki']:.6f}, Kd: {best_params['kd']:.2f}")
        else: # 如果新解更差，按一定概率接受 (Metropolis准则)
            acceptance_probability = math.exp(-delta_score / temperature)
            if np.random.rand() < acceptance_probability:
                current_params = new_params
                current_score = new_score
        
        # 4. 降温
        temperature *= COOLING_RATE
        
        if iteration % 50 == 0:
            print(f"迭代: {iteration}, 温度: {temperature:.2f}, 当前分数: {current_score:.2f}, 最佳分数: {best_score:.2f}")

    print("\n--- 整定完成 ---")
    print(f"找到的最佳参数 (最终分数: {best_score:.2f}):")
    print(f"  Kp = {best_params['kp']:.4f}")
    print(f"  Ki = {best_params['ki']:.6f}")
    print(f"  Kd = {best_params['kd']:.4f}")

    # --- 最终对比 ---
    print("\n正在运行最终对比仿真并绘图...")
    default_temps = run_simulation(DEFAULT_KP, DEFAULT_KI, DEFAULT_KD)
    tuned_temps = run_simulation(**best_params)
    
    plot_results(default_temps, tuned_temps, best_params)