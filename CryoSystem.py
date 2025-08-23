import numpy as np


DEFAULT_KP = -130.0
DEFAULT_KI = -1.5
DEFAULT_KD = -600.0
# ==================== CryoSystem 类 ====================
class CryoSystem:
    """低温系统物理模型，只负责温度更新"""
    def __init__(self, initial_temp=300.0):
        self.temperature = initial_temp
        self.cooling_power = 0
        self.filtered_temp = initial_temp
        self.last_filtered_temp = initial_temp
        self.target_setpoint = initial_temp
        
    
        self.KP = DEFAULT_KP
        self.KI = DEFAULT_KI
        self.KD = DEFAULT_KD

        # 仿真参数
        self.AMBIENT_TEMP = 300.0
        self.PARASITIC_HEAT_LOAD = 0.1
        self.HEAT_LOSS_COEFF = 0.0001
        self.COOLING_EFFECT_FACTOR = 2.0
        self.NOISE_LEVEL = 0.1
        self.FILTER_ALPHA = 0.2
        self.integral_sum = 0.0
        
    def update_temperature(self,target_setpoint):
        """
        更新系统温度
        
        参数:
            cooling_power: 冷却功率 (0-100)
            
        返回:
            更新后的温度
        """

        
        self.target_setpoint = target_setpoint
        # 更新目标温度
        
        
        # 模拟带噪声的传感器读数
        noise = np.random.normal(0, self.NOISE_LEVEL)
        current_temp = self.temperature + noise
        
        # 对带噪声的读数进行低通滤波
        self.filtered_temp = (self.FILTER_ALPHA * current_temp) + (1 - self.FILTER_ALPHA) * self.filtered_temp

        # 基于平滑后的温度计算PID三项
        error = self.target_setpoint - self.filtered_temp
        
        # 带抗饱和功能的积分项累积
        if 0 < self.cooling_power < 100:
            self.integral_sum += error * 1.0
        
        # 微分项计算
        derivative = (self.filtered_temp - self.last_filtered_temp) / 1.0
        
        # 计算总输出并限制在0-100之间
        output = (self.KP * error) + (self.KI * self.integral_sum) - (self.KD * derivative)
        control_output = max(0, min(100, output))
        
        # 将控制输出应用到物理系统
        self.cooling_power = control_output
        
        # 更新系统温度
        radiative_heat_transfer = self.HEAT_LOSS_COEFF * (self.AMBIENT_TEMP - self.temperature)
        active_cooling = -self.COOLING_EFFECT_FACTOR * self.cooling_power / 100.0
        self.temperature += (radiative_heat_transfer + self.PARASITIC_HEAT_LOAD + active_cooling) * 1.0
        self.temperature = max(0, self.temperature)
        
        # 更新状态变量用于下一次循环
        self.last_filtered_temp = self.filtered_temp
        
        return self.temperature
    
    def get_temperature(self):
        """获取当前温度"""
        return self.temperature
    
    def get_filtered_temperature(self):
        """获取滤波后的温度"""
        return self.filtered_temp
