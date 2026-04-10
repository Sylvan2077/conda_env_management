import os
from pathlib import Path
from typing import Optional

class Config:
    """配置文件读取器"""
    
    def __init__(self, config_file: str = "config/app.properties"):
        self.config_file = Path(config_file)
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._config[key.strip()] = value.strip()
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """获取配置值"""
        return self._config.get(key, default)
    
    @property
    def workdir(self) -> Path:
        """获取工作目录"""
        workdir = self.get('workdir')
        if not workdir:
            raise ValueError("配置文件中未找到 workdir 配置")
        return Path(workdir)
    
    def __str__(self):
        return f"Config({self._config})"

# 全局配置实例
config = Config()