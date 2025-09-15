import serial
import time
import sys
from datetime import datetime
from tqdm import tqdm

def send_trim_commands(start_num=0, end_num=65535):
    # 配置串口参数
    port = 'COM11'
    baudrate = 115200  # 使用115200波特率
    
    # 验证输入范围
    if start_num < 0:
        print("警告: 起始值不能小于0，已自动调整为0")
        start_num = 0
    if end_num > 65535:
        print("警告: 终止值不能大于65535，已自动调整为65535")
        end_num = 65535
    if start_num > end_num:
        print("错误: 起始值不能大于终止值")
        return
    
    total_numbers = end_num - start_num + 1
    
    try:
        # 初始化串口连接
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1  # 读取超时时间
        )
        
        # 等待串口就绪
        time.sleep(2)
        
        print(f"开始向 {port} 发送数据...")
        print(f"波特率: {baudrate}")
        print(f"数字范围: {start_num} 到 {end_num}")
        print(f"总计: {total_numbers} 条命令")
        print("按 Ctrl+C 停止发送")
        print("-" * 50)
        
        # 创建进度条
        progress_bar = tqdm(total=total_numbers, unit="cmd", desc="发送进度")
        
        # 发送指定范围的数字
        for num in range(start_num, end_num + 1):
            # 构建要发送的字符串
            command = f"Trim:{num}\r\n"
            
            # 发送数据
            ser.write(command.encode('utf-8'))
            
            # 更新进度条
            progress_bar.update(1)
            progress_bar.set_postfix_str(f"当前: {command.strip()}")
            
            # 添加短暂延迟，避免发送过快
            time.sleep(0.01)
            
        # 完成进度条
        progress_bar.close()
        print("所有数据发送完成！")
            
    except serial.SerialException as e:
        print(f"\n串口错误: {e}")
        print("请检查:")
        print("1. 串口名称是否正确")
        print("2. 是否有权限访问串口")
        print("3. 串口是否被其他程序占用")
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 确保关闭串口
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")

def get_user_input():
    """获取用户输入的起始值和终止值"""
    print("STM32 串口通信程序 - 带进度条版本")
    print("波特率: 115200")
    print("默认范围: 0 到 65535")
    print("-" * 50)
    
    try:
        start_input = input("请输入起始值 (直接回车使用默认值 0): ")
        end_input = input("请输入终止值 (直接回车使用默认值 65535): ")
        
        # 处理起始值
        if start_input.strip() == "":
            start_num = 0
        else:
            start_num = int(start_input)
        
        # 处理终止值
        if end_input.strip() == "":
            end_num = 65535
        else:
            end_num = int(end_input)
            
        return start_num, end_num
        
    except ValueError:
        print("错误: 请输入有效的数字")
        return get_user_input()  # 递归调用直到输入有效值
    except KeyboardInterrupt:
        print("\n用户取消输入")
        sys.exit(0)

if __name__ == "__main__":


    send_trim_commands()