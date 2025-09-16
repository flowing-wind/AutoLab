import serial
import time

A = True
try:
    ser = serial.Serial(
        port="COM4",
        baudrate=115200,
        timeout=0.2  # 设置一个较短的超时，比如0.2秒，用于判断数据流是否结束
    )
    print(f"串口 {ser.name} 已打开。")

    while A:
        # 1. 发送指令，并加上换行符，这几乎是必须的
        command = "Trim:458\r\n"
        ser.write(command.encode('ascii'))
        print(f"[Tx] 发送指令: {command.strip()}")

        # 2. 等待设备开始响应
        # 从日志看，至少有10ms延迟，我们多等一会儿
        time.sleep(0.05) 

        # 3. 循环读取所有返回的行
        print("[Rx] 开始接收数据...")
        response_lines = []
        empty_read_count = 0
        max_empty_reads = 3

        while True:
            # 读取一行数据
            line = ser.readline()

            # 如果读到了数据55646+
            if line:
                # 将字节串解码为字符串，并去掉两端的空白（包括\r\n）
                decoded_line = line.decode('ascii', errors='ignore').strip()
                print(decoded_line)  # 实时打印接收到的每一行
                response_lines.append(decoded_line)

                # 检查是否是结束标志
                if "================================" in decoded_line:
                    print("[Rx] 接收到结束标志，数据接收完毕。")
                    break
            # 如果没读到数据（readline超时返回空字节串）
            else:
                empty_read_count += 1
                # print(f"[Rx] 读取超时，第 {empty_read_count} 次...")
                
                if empty_read_count >= max_empty_reads:
                    print(f"[Rx] 连续 {max_empty_reads} 次读取超时，认为数据已全部接收。")
                    break
                else:
                    continue
        
        # 打印完整的接收内容（可选）
        print("\n--- 完整响应内容 ---")
        for l in response_lines:
            print(l)
        print("---------------------\n")

        # 4. 等待一段时间再进行下一次循环，避免过于频繁地发送
        time.sleep(2)
        A = False

except serial.SerialException as e:
    print(f"打开串口时出错: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print(f"串口 {ser.name} 已关闭。")