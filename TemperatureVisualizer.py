import sys
import time

from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QGroupBox,
                             QTextEdit)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import datetime
import csv


import TemperatureController









# ==================== PyQt主窗口 ====================
class TemperatureMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("温度实时监控仪表板 - 带稳定控制")
        self.setGeometry(100, 100, 1200, 800)
        
        # 数据存储
        self.MAX_DATA_POINTS = 200
        self.times = deque(maxlen=self.MAX_DATA_POINTS)
        self.temperatures = deque(maxlen=self.MAX_DATA_POINTS)
        self.setpoint = deque(maxlen=self.MAX_DATA_POINTS)
        
        # 初始化数据
        self.times.append(time.time())
        self.temperatures.append(controller.get_temperature())
        self.setpoint.append(controller.get_setpoint())
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 图表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 创建信息栏
        info_layout = QHBoxLayout()
        self.mode_label = QLabel(f"模式: {'仿真' if controller.DEBUG_MODE else '实际仪器'}")
        self.mode_label.setStyleSheet("color: green; font-weight: bold;" if not controller.DEBUG_MODE else "color: blue; font-weight: bold;")
        
        self.temp_label = QLabel(f"当前温度: {self.temperatures[-1]:.4f} K")
        self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # 添加目标温度显示
        self.target_label = QLabel(f"目标温度: {self.setpoint[-1]:.4f}  K")
        self.target_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 添加稳定标志显示
        self.stable_flag_label = QLabel("稳定标志: 0")
        self.stable_flag_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
        
        info_layout.addWidget(self.mode_label)
        info_layout.addStretch()
        info_layout.addWidget(self.target_label)
        info_layout.addStretch()
        info_layout.addWidget(self.stable_flag_label)
        info_layout.addStretch()
        info_layout.addWidget(self.temp_label)
        
        left_layout.addLayout(info_layout)
        
        # 创建图表
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', '温度', 'K')
        self.plot_widget.setLabel('bottom', '时间 (秒)')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        
        # 设置Y轴范围 - 调整为适合300K到298K的范围
        self.plot_widget.setYRange(297.5, 300.5)
        
        # 创建温度曲线
        self.curve = self.plot_widget.plot(
            [], 
            [], 
            pen=pg.mkPen(color='b', width=2),
            symbol='o',
            symbolSize=5,
            symbolBrush='b',
            name="实时温度"
        )
        
        # 创建设定点曲线
        self.setpoint_curve = self.plot_widget.plot(
            [], 
            [], 
            pen=pg.mkPen(color='r', width=2, style=Qt.DashLine),
            name="目标温度"
        )
        
        left_layout.addWidget(self.plot_widget)
        
        # 创建控制按钮
        control_layout = QHBoxLayout()
        
        self.pause_button = QPushButton("暂停")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        
        self.clear_button = QPushButton("清除数据")
        self.clear_button.clicked.connect(self.clear_data)
        
        # 添加重置按钮
        self.reset_button = QPushButton("重置仿真")
        self.reset_button.clicked.connect(self.reset_simulation)
        
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addStretch()
        
        left_layout.addLayout(control_layout)
        
        # 右侧面板 - 控制信息
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 稳定控制组
        stable_group = QGroupBox("稳定控制")
        stable_layout = QVBoxLayout(stable_group)
        
        self.update_button = QPushButton("发送更新指令 (UPDATE_FLAG = 1)")
        self.update_button.clicked.connect(self.send_update_command)
        self.update_button.setEnabled(False)
        
        self.stable_status_label = QLabel("状态: 未达到稳定")
        self.stable_status_label.setStyleSheet("color: gray; font-weight: bold;")
        
        self.current_stabletime_label = QLabel("当前稳定时间要求: 0秒")
        
        stable_layout.addWidget(self.stable_status_label)
        stable_layout.addWidget(self.current_stabletime_label)
        stable_layout.addWidget(self.update_button)
        
        right_layout.addWidget(stable_group)
        
        # 系统信息组
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)
        
        self.schedule_label = QLabel("设定点计划: 加载中...")
        # self.stabletimes_label = QLabel("稳定时间要求: 加载中...")
        self.current_index_label = QLabel("当前设定点索引: 0")
        
        info_layout.addWidget(self.schedule_label)
        # info_layout.addWidget(self.stabletimes_label)
        info_layout.addWidget(self.current_index_label)
        
        right_layout.addWidget(info_group)
        
        # 日志组
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        log_layout.addWidget(self.log_text)
        
        right_layout.addWidget(log_group)
        right_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(left_widget, 3)
        main_layout.addWidget(right_widget, 1)
        
        # 设置定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)
        
        self.paused = False
        
        # 初始更新图表和信息
        self.update_plot()
        self.update_system_info()
        
        # 记录启动日志
        self.log_message("系统启动完成")
        self.log_message(f"工作模式: {'仿真' if TemperatureController.DEBUG_MODE else '实际仪器'}")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def send_update_command(self):
        """发送更新指令"""
        controller.set_update_flag(1)
        self.update_button.setEnabled(False)
        self.stable_status_label.setText("状态: 更新指令已发送")
        self.stable_status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.log_message("发送更新指令: UPDATE_FLAG = 1")
        
    
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
            self.pause_button.setText("继续")
            self.log_message("监控暂停")
        else:
            self.timer.start(1000)
            self.pause_button.setText("暂停")
            self.log_message("监控继续")
    
    def clear_data(self):
        self.times.clear()
        self.temperatures.clear()
        self.setpoint.clear()
        self.times.append(time.time())
        self.temperatures.append(controller.get_temperature())
        self.setpoint.append(controller.get_setpoint())
        self.update_plot()
        self.log_message("数据已清除")
    
    def reset_simulation(self):
        """重置仿真系统"""
        global controller
        controller = TemperatureController('config.csv')
        self.clear_data()
        self.update_system_info()
        self.update_button.setEnabled(False)
        self.stable_status_label.setText("状态: 未达到稳定")
        self.stable_status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.log_message("仿真系统已重置")
    
    def update_system_info(self):
        """更新系统信息显示"""
        if TemperatureController.DEBUG_MODE:
            self.schedule_label.setText(f"设定点计划: {controller.config_file}")
            # self.stabletimes_label.setText(f"稳定时间要求: {controller.setpoint_stabletimes}秒")
            self.current_index_label.setText(f"当前设定点索引: {controller.schedule_index}/{len(controller.setpoint_stabletimes)-1}")
            self.current_stabletime_label.setText(f"当前稳定时间要求: {controller.current_stabletime}秒")
    
    def update_data(self):
        if not self.paused:
            current_time = time.time()
            new_temp = controller.get_temperature()
            
            self.times.append(current_time)
            self.temperatures.append(new_temp)

            new_setpoint = controller.get_setpoint()
            self.setpoint.append(new_setpoint)
            
            # 更新稳定标志
            stable_flag = controller.get_stable_flag()
            self.stable_flag_label.setText(f"稳定标志: {stable_flag}")
            
            # 根据稳定标志更新UI
            if stable_flag == 1:
                self.stable_flag_label.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
                self.stable_status_label.setText("状态: 已达到稳定，等待更新指令")
                self.stable_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.update_button.setEnabled(True)
            else:
                self.stable_flag_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
                self.update_button.setEnabled(False)
            
            self.temp_label.setText(f"当前温度: {new_temp:.4f} K")
            self.target_label.setText(f"目标温度: {new_setpoint:.4f}  K")
            
            # 更新系统信息
            self.update_system_info()
            
            self.update_plot()
    
    def update_plot(self):
        if len(self.times) > 0:
            # 转换时间为相对时间（秒）
            relative_times = [t - self.times[0] for t in self.times]
            
            # 更新曲线数据
            self.curve.setData(relative_times, list(self.temperatures))
            self.setpoint_curve.setData(relative_times, list(self.setpoint))
            
            # 动态调整Y轴范围，但保持在297-301K范围内
            if len(self.temperatures) > 0:
                min_temp = min(self.temperatures)
                max_temp = max(self.temperatures)
                margin = 0.2
                
                # 确保Y轴范围包含目标温度298K
                y_min = min(297.0, min_temp - margin)
                y_max = max(301.0, max_temp + margin)
                self.plot_widget.setYRange(y_min, y_max)

# ==================== 主程序 ====================
if __name__ == '__main__':
    # 创建配置文件示例
    # with open('config.csv', 'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['SETPOINT_SCHEDULE', '300', '295', '290', '285'])
    #     writer.writerow(['SETPOINT_STABLETIME', '5', '14', '13', '12'])
    
    # 创建控制器



    
    ConfigFilename = 'F:\Lab\Lab-Protocol\config.csv'
    controller = TemperatureController.TemperatureController(ConfigFilename)
    
    app = QApplication(sys.argv)
    window = TemperatureMonitor()
    window.show()
    sys.exit(app.exec_())