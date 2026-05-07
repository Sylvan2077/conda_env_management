import logging
import sys

class LoggerManager:
    """
    A class to manage logging with custom methods like success and warning.
    """
    def __init__(self, name: str = __name__, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent adding multiple handlers if the logger is re-initialized
        if not self.logger.handlers:
            # Console handler
            c_handler = logging.StreamHandler(sys.stdout)
            c_handler.setLevel(level)

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            c_handler.setFormatter(formatter)

            # Add handler
            self.logger.addHandler(c_handler)

    def info(self, message: str, *args, **kwargs):
        """Logs an info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Logs a warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Logs an error message."""
        self.logger.error(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs):
        """Logs a success message."""
        # Custom handling for success, can be styled differently if needed
        # For now, using INFO level with a "SUCCESS:" prefix
        self.logger.info(f"SUCCESS: {message}", *args, **kwargs)
        
