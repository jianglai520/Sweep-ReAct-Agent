"""
日志工具
"""
import logging
import os
from utils.path_tool import get_abs_path
from datetime import datetime

# 目录保存的根目录
LOG_ROOT = get_abs_path("logs")

# 确保日志的目录存在
os.makedirs(LOG_ROOT, exist_ok = True)

# 日志的格式配置
"""
%(asctime)s 日志事件发生的时间（字符串）
%(name)s 产生日志的logger名称
%(levelname)s 日志级别的文本名称 INFO / WARNING / ERROR
%(filename)s 产生日志的源文件名（不含路径）
%(lineno)d  产生日志的源代码行号（整数）
%(messages)s 日志的实际消息内容
"""
DEFAULT_LOG_FORMAT = logging.Formatter(
   '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

def get_logger(
        name: str = "Sweep-ReAct-Agent",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        log_file = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加Handler
    if logger.handlers:
        return logger

    # 控制台Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)


    logger.addHandler(console_handler)


    # 文件Handler
    if not log_file:  # 日志文件的存放路径
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_file, encoding = 'utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)

    logger.addHandler(file_handler)

    return logger

# 快捷获取日志器
logger = get_logger()


# 测试
if __name__ == '__main__':
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")