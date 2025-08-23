import logging
import sys
from datetime import datetime

def setup_logging(log_file=None):
    """设置日志配置"""
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的handler
    logger.handlers.clear()
    
    # 创建formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 文件handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 重写print函数
def custom_print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    logging.info(message)
    # 如果需要保留原print功能，可以取消下面的注释
    # original_print(*args, **kwargs)

# 使用示例
if __name__ == "__main__":
    # 设置日志文件
    log_file = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置日志
    setup_logging(log_file)
    
    # 替换print函数
    original_print = print
    print = custom_print
    
    try:
        # 你的代码
        print("这是一条记录到日志的消息")
        print("多个参数:", "test", 123, [1, 2, 3])
        print(f"带格式的消息: {datetime.now()}")
        
        # 模拟一些操作
        for i in range(3):
            print(f"进度: {i + 1}/3")
            
    except Exception as e:
        logging.error(f"发生错误: {e}")
    finally:
        # 恢复原print函数
        print = original_print
        print("程序执行完成，请查看日志文件")