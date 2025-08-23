import time
import numpy as np
import csv

# 仿真参数
INITIAL_TEMP = 300.0  # 初始温度设为300K
AMBIENT_TEMP = 300.0
PARASITIC_HEAT_LOAD = 0.1
HEAT_LOSS_COEFF = 0.0001
COOLING_EFFECT_FACTOR = 2.0
NOISE_LEVEL = 0.1     # 减小噪声水平以便更清晰地观察降温过程
FILTER_ALPHA = 0.2     # 调整滤波器参数

# 默认的PID参数和设定点计划
DEFAULT_KP = -130.0
DEFAULT_KI = -1.5
DEFAULT_KD = -600.0
DEFAULT_SETPOINT_SCHEDULE = [300, 298, 290]
DEFAULT_SETPOINT_STABLETIMES = [10, 10, 10]  # 每个设定点对应的稳定时间

def ReadCSV(filename):
    """
    从CSV文件中读取设定点计划和对应的稳定时间
    
    参数:
        filename: CSV文件名
        
    返回:
        setpoint_schedule: 设定点温度列表
        setpoint_stabletimes: 每个设定点对应的稳定时间列表
    """
    setpoint_schedule = DEFAULT_SETPOINT_SCHEDULE.copy()
    setpoint_stabletimes = DEFAULT_SETPOINT_STABLETIMES.copy()
    
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2 and row[0].lower() == 'setpoint_schedule':
                    # 读取设定点计划
                    try:
                        setpoint_schedule = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        print(f"警告: 无法解析设定点计划: {row[1:]}, 使用默认值")
                        setpoint_schedule = DEFAULT_SETPOINT_SCHEDULE.copy()
                
                elif len(row) >= 2 and row[0].lower() == 'setpoint_stabletime':
                    # 读取每个设定点的稳定时间
                    try:
                        setpoint_stabletimes = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        print(f"警告: 无法解析稳定时间: {row[1:]}, 使用默认值")
                        setpoint_stabletimes = DEFAULT_SETPOINT_STABLETIMES.copy()
    
    except FileNotFoundError:
        print(f"警告: 文件 {filename} 未找到，使用默认参数")
    except Exception as e:
        print(f"警告: 读取CSV文件时出错: {e}, 使用默认参数")
    
    # 确保稳定时间列表长度与设定点列表长度一致
    if len(setpoint_stabletimes) != len(setpoint_schedule):
        print(f"警告: 稳定时间数量({len(setpoint_stabletimes)})与设定点数量({len(setpoint_schedule)})不匹配，使用默认值")
        setpoint_stabletimes = [DEFAULT_SETPOINT_STABLETIMES[0]] * len(setpoint_schedule)
    
    return setpoint_schedule, setpoint_stabletimes


class CryoSystem:
    """模拟一个可被主动降温并受环境影响的低温物理系统"""
    def __init__(self, config_file=None):
        # 从CSV文件读取配置或使用默认值
        if config_file:
            self.setpoint_schedule, self.setpoint_stabletimes = ReadCSV(config_file)
        else:
            self.setpoint_schedule = DEFAULT_SETPOINT_SCHEDULE.copy()
            self.setpoint_stabletimes = DEFAULT_SETPOINT_STABLETIMES.copy()
        
        self.temperature = INITIAL_TEMP
        self.cooling_power = 0
        self.start_time = time.time()
        self.integral_sum = 0.0
        self.last_filtered_temp = INITIAL_TEMP
        self.filtered_temp = INITIAL_TEMP
        self.schedule_index = 0
        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
        self.current_stabletime = self.setpoint_stabletimes[self.schedule_index]
        self.stable_start_time = None  # 用于记录稳定开始时间
        
        # 标志位
        self.STABLE_FLAG = 0  # 稳定标志，达到稳定时间后置1
        self.UPDATE_FLAG = 0  # 更新标志，需要外部传入1才能更新
        
        # PID 参数
        self.KP = DEFAULT_KP
        self.KI = DEFAULT_KI
        self.KD = DEFAULT_KD

    def set_update_flag(self, flag_value):
        """设置更新标志"""
        self.UPDATE_FLAG = flag_value
        if flag_value == 1:
            print("收到更新指令，准备切换到下一个设定点")

    def update_target(self, current_time, stability_threshold=0.5):
        """更新目标温度
        如果连续稳定时间在目标温度附近stability_threshold K内，则切换到下一个目标温度
        """
        # 检查是否需要切换到下一个目标温度
        if self.schedule_index < len(self.setpoint_schedule) - 1:
            current_target = self.setpoint_schedule[self.schedule_index]
            current_stabletime = self.setpoint_stabletimes[self.schedule_index]
            
            # 检查是否已经稳定
            if self.is_temperature_stable(current_target, stability_threshold):
                # 检查是否已经稳定足够长时间
                if self.stable_start_time is None:
                    # 开始稳定计时
                    self.stable_start_time = current_time
                    print(f"温度进入稳定范围({current_target}±{stability_threshold}K)，需要稳定{current_stabletime}秒...")
                elif current_time - self.stable_start_time >= current_stabletime:
                    # 稳定时间达到要求，设置稳定标志
                    if self.STABLE_FLAG == 0:
                        self.STABLE_FLAG = 1
                        print(f"稳定{current_stabletime}秒完成，等待外部更新指令...")
                    
                    # 检查是否收到更新指令
                    if self.UPDATE_FLAG == 1:
                        # 切换到下一个目标
                        self.schedule_index += 1
                        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
                        self.current_stabletime = self.setpoint_stabletimes[self.schedule_index]
                        self.stable_start_time = None
                        self.integral_sum = 0.0  # 重置积分项
                        self.STABLE_FLAG = 0  # 重置稳定标志
                        self.UPDATE_FLAG = 0  # 重置更新标志
                        print(f"切换到目标温度: {self.target_setpoint}K，需要稳定{self.current_stabletime}秒")
            else:
                # 温度不在稳定范围内，重置计时器和标志
                self.stable_start_time = None
                self.STABLE_FLAG = 0
        
        return self.target_setpoint

    def is_temperature_stable(self, target_temp, threshold=0.5):
        """检查当前温度是否在目标温度附近阈值范围内"""
        return abs(self.filtered_temp - target_temp) <= threshold
    
    def get_setpoint(self):
        return self.target_setpoint
    
    def get_stable_flag(self):
        return self.STABLE_FLAG

    def update(self):
        """更新系统状态"""
        current_time = time.time()
        
        # 更新目标温度
        self.update_target(current_time)
        
        # 模拟带噪声的传感器读数
        noise = np.random.normal(0, NOISE_LEVEL)
        current_temp = self.temperature + noise
        
        # 对带噪声的读数进行低通滤波
        self.filtered_temp = (FILTER_ALPHA * current_temp) + (1 - FILTER_ALPHA) * self.filtered_temp

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
        radiative_heat_transfer = HEAT_LOSS_COEFF * (AMBIENT_TEMP - self.temperature)
        active_cooling = -COOLING_EFFECT_FACTOR * self.cooling_power / 100.0
        self.temperature += (radiative_heat_transfer + PARASITIC_HEAT_LOAD + active_cooling) * 1.0
        self.temperature = max(0, self.temperature)
        
        # 更新状态变量用于下一次循环
        self.last_filtered_temp = self.filtered_temp
        
        return self.temperature


# 使用示例
if __name__ == "__main__":
    # 创建配置文件示例
    with open('config.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['SETPOINT_SCHEDULE', '300', '295', '290', '285'])
        writer.writerow(['SETPOINT_STABLETIME', '5', '4', '3', '2'])  # 缩短时间用于演示
    
    # 使用配置文件初始化系统
    cryo_system = CryoSystem('config.csv')
    print(f"设定点计划: {cryo_system.setpoint_schedule}")
    print(f"稳定时间: {cryo_system.setpoint_stabletimes}秒")
    
    # 模拟运行
    for i in range(50):
        temp = cryo_system.update()
        
        # 检查是否需要外部更新
        if cryo_system.get_stable_flag() == 1:
            print(f"时间 {i}s: STABLE_FLAG = 1, 等待UPDATE_FLAG...")
            # 模拟外部决策，延迟几秒后发送更新指令
            if i > 30:  # 在第30秒后发送更新指令
                cryo_system.set_update_flag(1)
        else:
            print(f"时间 {i}s: 温度 = {temp:.2f}K, 目标 = {cryo_system.target_setpoint}K, 冷却功率 = {cryo_system.cooling_power:.1f}%")
        
        time.sleep(0.1)