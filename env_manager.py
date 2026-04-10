import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from config import config


class OverlayTool:
    """overlayfs + conda 核心管理器"""
    
    def __init__(self, task_id: str):
        """初始化overlay管理器
        
        Args:
            task_id: 任务唯一标识符
        """
        self.task_id = task_id
        self.root_dir = config.workdir / task_id
        self.root_dir.mkdir(parents=True, exist_ok=True)
    
    def init_directory_structure(self):
        """初始化虚环境目录结构
        
        创建:
        - base/ (全局基础 conda 环境)
        - modules/ (所有模块的 overlay 目录)
        """
        # 创建base目录
        base_dir = self.root_dir / "base"
        base_dir.mkdir(exist_ok=True)
        
        # 创建modules目录
        modules_dir = self.root_dir / "modules"
        modules_dir.mkdir(exist_ok=True)
        
        return str(self.root_dir)
    
    def create_overlay_dirs(self, module_id: str, conda_env_name: str) -> Dict[str, str]:
        """创建模块的overlay目录结构
        
        Args:
            module_id: 模块唯一ID
            conda_env_name: conda环境名称
            
        Returns:
            包含各个目录路径的字典
        """
        module_dir = self.root_dir / "modules" / module_id
        
        # 创建overlay子目录
        upper_dir = module_dir / "upper"
        work_dir = module_dir / "work"
        merge_dir = module_dir / "merge"
        
        for dir_path in [upper_dir, work_dir, merge_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 设置权限
        os.chmod(module_dir, 0o777)
        
        # 在base目录下创建conda环境（实际项目中需要调用外部服务）
        base_conda_path = self.root_dir / "base" / conda_env_name
        if not base_conda_path.exists():
            base_conda_path.mkdir(parents=True, exist_ok=True)
            # 这里应该调用functiontest_service创建conda环境
            # self._create_conda_env(conda_env_name)
        
        # 挂载overlayfs
        self._mount_overlayfs(upper_dir, work_dir, merge_dir, base_conda_path)
        
        return {
            "upper_dir": str(upper_dir),
            "work_dir": str(work_dir),
            "merge_dir": str(merge_dir),
            "base_conda_path": str(base_conda_path)
        }
    
    def unmount_overlay_dirs(self, module_id: str) -> bool:
        """卸载模块的overlay目录
        
        Args:
            module_id: 模块唯一ID
            
        Returns:
            卸载是否成功
        """
        module_dir = self.root_dir / "modules" / module_id
        
        if not module_dir.exists():
            return False
        
        merge_dir = module_dir / "merge"
        
        try:
            # 卸载overlayfs
            self._unmount_overlayfs(merge_dir)
            
            # 删除模块目录
            import shutil
            shutil.rmtree(module_dir, ignore_errors=True)
            
            return True
        except Exception:
            return False
    
    def cleanup_task(self):
        """清理整个任务目录"""
        try:
            import shutil
            shutil.rmtree(self.root_dir, ignore_errors=True)
            return True
        except Exception:
            return False
    
    def _mount_overlayfs(self, upper_dir: Path, work_dir: Path, merge_dir: Path, base_dir: Path):
        """使用mount overlayfs挂载目录
        
        Args:
            upper_dir: 可写层
            work_dir: 工作层（必须为空）
            merge_dir: 挂载点（视图层）
            base_dir: 基础目录（只读层）
        """
        # 构造lowerdir（只有base作为基础层）
        lower_str = str(base_dir)
        
        # 使用mount命令而不是fuse-overlayfs（更标准）
        cmd = [
            "mount",
            "-t", "overlay",
            "-o", f"lowerdir={lower_str}",
            "-o", f"upperdir={upper_dir}",
            "-o", f"workdir={work_dir}",
            "overlay",
            str(merge_dir)
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"overlayfs挂载失败: {result.stderr.decode()}")
    
    def _unmount_overlayfs(self, merge_dir: Path):
        """卸载overlayfs
        
        Args:
            merge_dir: 挂载点
        """
        # 使用unmount -l强制卸载
        result = subprocess.run(["umount", "-l", str(merge_dir)], check=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"overlayfs卸载失败: {result.stderr.decode()}")
    
    def _create_conda_env(self, env_name: str):
        """创建conda环境（实际项目中需要调用外部服务）"""
        # 这里只是模拟，实际应该调用functiontest_service
        conda_cmd = [
            "conda", "create", "--prefix", str(self.root_dir / "base" / env_name),
            "-y", "--quiet", "python=3.8"
        ]
        subprocess.run(conda_cmd, check=True, capture_output=True)