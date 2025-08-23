import CryoSystem
import csv
import time
import numpy as np
import datetime
import logging
import sys

# ==================== 配置区域 ====================
DEBUG_MODE = True  # 设置为False使用实际仪器，True使用仿真模式

# ==================== 日志配置 ====================
# 创建logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建控制台handler并设置级别
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# 创建文件handler并设置级别
file_handler = logging.FileHandler(f"./log/print_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加formatter到handler
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加handler到logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==================== 全局变量 ====================
sim_system = None
controller = None


# ==================== 默认参数和CSV读取 ====================

DEFAULT_SETPOINT_SCHEDULE = [300, 298, 295]
DEFAULT_SETPOINT_STABLETIMES = [10, 10, 10]
def ReadCSV(filename):
    """从CSV文件中读取设定点计划和对应的稳定时间"""
    setpoint_schedule = DEFAULT_SETPOINT_SCHEDULE.copy()
    setpoint_stabletimes = DEFAULT_SETPOINT_STABLETIMES.copy()
    
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2 and row[0].lower() == 'setpoint_schedule':
                    try:
                        setpoint_schedule = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        logger.warning(f"无法解析设定点计划: {row[1:]}, 使用默认值")
                
                elif len(row) >= 2 and row[0].lower() == 'setpoint_stabletime':
                    try:
                        setpoint_stabletimes = [float(x.strip()) for x in row[1:] if x.strip()]
                    except ValueError:
                        logger.warning(f"无法解析稳定时间: {row[1:]}, 使用默认值")
    
    except FileNotFoundError:
        logger.warning(f"文件 {filename} 未找到，使用默认参数")
    except Exception as e:
        logger.warning(f"读取CSV文件时出错: {e}, 使用默认参数")
    
    if len(setpoint_stabletimes) != len(setpoint_schedule):
        setpoint_stabletimes = [DEFAULT_SETPOINT_STABLETIMES[0]] * len(setpoint_schedule)
    
    return setpoint_schedule, setpoint_stabletimes


# ==================== 温度控制器 ====================
class TemperatureController:
    """温度控制器，负责PID控制和设定点管理"""
    def __init__(self, config_file=None):
        # 从CSV文件读取配置或使用默认值
        if config_file:
            self.config_file = config_file
            self.setpoint_schedule, self.setpoint_stabletimes = ReadCSV(config_file)
        else:
            self.setpoint_schedule = DEFAULT_SETPOINT_SCHEDULE.copy()
            self.setpoint_stabletimes = DEFAULT_SETPOINT_STABLETIMES.copy()
        
        self.cryo_system = CryoSystem.CryoSystem()
        self.integral_sum = 0.0
        self.schedule_index = 0
        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
        self.current_stabletime = self.setpoint_stabletimes[self.schedule_index]
        self.stable_start_time = None
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        logger.info(f"当前温度点为：{self.target_setpoint}K")
        logger.info(f"稳定时间为：{self.current_stabletime}秒")
        # 标志位
        self.STABLE_FLAG = 0
        self.UPDATE_FLAG = 0
        self.DEBUG_MODE = True  # 默认使用仿真模式

        

    def set_debug_mode(self, debug_mode):
        """设置调试模式"""
        self.DEBUG_MODE = debug_mode

    def get_temperature(self):
        """获取当前温度"""
        if self.DEBUG_MODE:
            # 仿真模式
            return self.update()
        else:
            # 实际仪器读取
            try:
                # 这里添加实际仪器读取代码
                return 0.0
            except Exception as e:
                logger.error(f"读取温度错误: {e}")
                return 0.0

    def get_setpoint(self):
        """获取当前设定点"""
        if self.DEBUG_MODE:
            # 仿真模式
            return self.target_setpoint
        else:
            # 实际仪器读取
            return 0

    def get_stable_flag(self):
        """获取稳定标志"""
        if self.DEBUG_MODE:
            # 仿真模式
            return self.STABLE_FLAG
        else:
            # 实际仪器相关功能
            return 0

    def set_update_flag(self, flag_value):
        """设置更新标志"""
        if self.DEBUG_MODE:
            # 仿真模式
            self.UPDATE_FLAG = flag_value
            if flag_value == 1:
                logger.info("收到更新指令，准备切换到下一个设定点")
        else:
            # 实际仪器相关功能
            pass

    def update_target(self, current_time, stability_threshold=0.5):
        """更新目标温度，如果需要切换到下一个设定点"""
        if self.schedule_index < len(self.setpoint_schedule) - 1:
            current_target = self.setpoint_schedule[self.schedule_index]
            
            # 检查是否已经稳定
            if self.is_temperature_stable(current_target, stability_threshold):
                if self.stable_start_time is None:
                    self.stable_start_time = current_time
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    logger.info(f"当前开始稳定计时")
                elif current_time - self.stable_start_time >= self.current_stabletime:
                    if self.STABLE_FLAG == 0:
                        self.STABLE_FLAG = 1
                        logger.info(f"当前稳定")
                        self.stable_function()
                    
                    if self.UPDATE_FLAG == 1:
                        self.schedule_index += 1
                        self.target_setpoint = self.setpoint_schedule[self.schedule_index]
                        self.current_stabletime = self.setpoint_stabletimes[self.schedule_index]
                        logger.info(f"更新当前温度点为：{self.target_setpoint}K")
                        logger.info(f"更新稳定时间为：{self.current_stabletime}秒")

                        self.stable_start_time = None
                        self.integral_sum = 0.0
                        self.STABLE_FLAG = 0
                        self.UPDATE_FLAG = 0
            else:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                logger.info(f"当前不稳定，{self.temperature}K")
                self.stable_start_time = None
                self.STABLE_FLAG = 0
        elif self.schedule_index == len(self.setpoint_schedule) - 1:
            if self.stable_start_time is None:
                self.stable_start_time = current_time
                logger.info(f"当前开始稳定计时")
            elif current_time - self.stable_start_time >= self.current_stabletime:
                if self.STABLE_FLAG == 0:
                    self.STABLE_FLAG = 1
                    logger.info(f"当前稳定")
                    self.stable_function()
                
                if self.UPDATE_FLAG == 1:
                    self.schedule_index += 1
                    logger.info(f"当前已完成所有")
                    self.stable_start_time = None
                    self.integral_sum = 0.0
                    self.STABLE_FLAG = 0
                    self.UPDATE_FLAG = 0
            
        
        return self.target_setpoint
    
    def stable_function(self):
        # 稳定了以后做的测量操作
        logger.info("执行稳定后的测量操作")
        pass

    def is_temperature_stable(self, target_temp, threshold=0.5):
        """检查当前温度是否在目标温度附近阈值范围内"""
        if abs(self.temperature - target_temp) <= threshold:
            return True
        else:
            return False

    def update(self):
        """执行一次完整的控制循环"""
        current_time = time.time()

        # 更新系统温度
        self.temperature = self.cryo_system.update_temperature(self.target_setpoint)
        self.update_target(current_time)
        
        return self.temperature