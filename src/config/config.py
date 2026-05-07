import os
from pathlib import Path
from typing import Optional
from src.util.log_manager import LoggerManager
logger = LoggerManager(__name__)


class Config:
    """配置文件读取器"""
    
    def __init__(self, config_file: str = "config/app.properties"):
        self.config_file = Path(config_file)
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            logger.error(f"Configuration file {self.config_file} does not exist")
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                logger.info(f"Loading line: {line}")
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._config[key.strip()] = value.strip()
                        logger.info(f"Loaded config: {key} = {value}")
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """获取配置值"""
        logger.info(f"Getting config: {key} = {self._config.get(key, default)}")
        return self._config.get(key, default)
    
    @property
    def workdir(self) -> Path:
        """获取工作目录"""
        workdir = self.get('workdir')
        if not workdir:
            logger.error("workdir not found in config file")
            raise ValueError("配置文件中未找到 workdir 配置")
        logger.info(f"Workdir from config: {workdir}")
        return Path(workdir)
    
    def __str__(self):
        logger.info(f"Config: {self._config}")
        return f"Config({self._config})"

# 全局配置实例
config = Config()