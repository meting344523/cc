import os
import sys
from loguru import logger

def setup_logger():
    """配置系统日志"""
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True
    )
    
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 添加文件处理器 - 所有日志
    logger.add(
        os.path.join(log_dir, "app.log"),
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    # 添加文件处理器 - 错误日志
    logger.add(
        os.path.join(log_dir, "error.log"),
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # 添加文件处理器 - 数据获取日志
    logger.add(
        os.path.join(log_dir, "data_fetch.log"),
        format=file_format,
        level="INFO",
        rotation="5 MB",
        retention="3 days",
        filter=lambda record: "data_fetch" in record["extra"]
    )
    
    logger.info("日志系统初始化完成")

def get_data_logger():
    """获取数据获取专用日志器"""
    return logger.bind(data_fetch=True)

# 初始化日志系统
setup_logger()

