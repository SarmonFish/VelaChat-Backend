import logging
from app.utils.config import settings

def setup_logger():
    """设置日志记录器
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger("wxautox_api")
    logger.setLevel(getattr(logging, settings.logging.level))
    
    # 文件处理器
    file_handler = logging.FileHandler(settings.logging.file)
    file_handler.setFormatter(logging.Formatter(settings.logging.format))
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(settings.logging.format))
    logger.addHandler(console_handler)
    
    return logger