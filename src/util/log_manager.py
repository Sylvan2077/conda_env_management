import logging
import sys

class LoggerManager:
    """
    日志管理器类，提供自定义方法如success和warning。
    """
    def __init__(self, name: str = __name__, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 防止重新初始化时添加多个handler
        if not self.logger.handlers:
            # 控制台handler
            c_handler = logging.StreamHandler(sys.stdout)
            c_handler.setLevel(level)

            # 格式化器
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            c_handler.setFormatter(formatter)

            # 添加handler
            self.logger.addHandler(c_handler)

    def info(self, message: str, *args, **kwargs):
        """记录信息消息。"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """记录警告消息。"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """记录错误消息。"""
        self.logger.error(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs):
        """记录成功消息。"""
        # 自定义成功处理，如果需要可以使用不同样式
        # 目前，使用INFO级别并添加"SUCCESS:"前缀
        self.logger.info(f"SUCCESS: {message}", *args, **kwargs)