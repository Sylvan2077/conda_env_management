import os
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import HTTPException
import shutil
from config import config

class OverlayService:
    def __init__(self):
        self.base_path = config.workdir
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def create_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """创建虚环境目录（upper、work、merge、base、modules/{module_id}）"""
        env_path = self.base_path / env_id
        
        # 创建环境目录
        env_path.mkdir(parents=True, exist_ok=True)
        
        # 创建base目录（全局基础conda环境）
        base_dir = env_path / "base"
        base_dir.mkdir(exist_ok=True)
        
        # 创建modules目录
        modules_dir = env_path / "modules"
        modules_dir.mkdir(exist_ok=True)
        
        results = {}
        
        for module_id in module_ids:
            module_path = modules_dir / module_id
            
            # 创建模块目录
            upper_dir = module_path / "upper"
            work_dir = module_path / "work"
            merge_dir = module_path / "merge"
            
            for dir_path in [upper_dir, work_dir, merge_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # 设置权限
            os.chmod(module_path, 0o777)
            results[module_id] = {
                "upper_dir": str(upper_dir),
                "work_dir": str(work_dir),
                "merge_dir": str(merge_dir),
                "status": "created"
            }
        
        return results
    
    async def mount_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """挂载虚环境目录（upper、work、merge）"""
        env_path = self.base_path / env_id
        
        if not env_path.exists():
            raise HTTPException(status_code=404, detail=f"环境 {env_id} 不存在")
        
        modules_dir = env_path / "modules"
        base_dir = env_path / "base"
        
        results = {}
        
        for module_id in module_ids:
            module_path = modules_dir / module_id
            
            if not module_path.exists():
                raise HTTPException(status_code=404, detail=f"模块 {module_id} 不存在")
            
            upper_dir = module_path / "upper"
            work_dir = module_path / "work"
            merge_dir = module_path / "merge"
            
            # 使用mount overlayfs挂载
            try:
                self._mount_overlay(upper_dir, work_dir, merge_dir, base_dir)
                results[module_id] = {
                    "upper_dir": str(upper_dir),
                    "work_dir": str(work_dir),
                    "merge_dir": str(merge_dir),
                    "status": "mounted"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"模块 {module_id} 挂载失败: {str(e)}")
        
        return results
    
    async def unmount_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """卸载虚环境目录"""
        env_path = self.base_path / env_id
        
        if not env_path.exists():
            raise HTTPException(status_code=404, detail=f"环境 {env_id} 不存在")
        
        modules_dir = env_path / "modules"
        base_dir = env_path / "base"
        
        results = {}
        
        for module_id in module_ids:
            module_path = modules_dir / module_id
            
            if not module_path.exists():
                continue
            
            merge_dir = module_path / "merge"
            
            # 卸载merge目录
            try:
                self._unmount_overlay(merge_dir)
            except Exception as e:
                # 即使卸载失败也继续清理目录
                pass
            
            # 删除模块目录
            try:
                shutil.rmtree(module_path, ignore_errors=True)
                results[module_id] = {"status": "unmounted"}
            except Exception as e:
                results[module_id] = {"status": "error", "message": str(e)}
        
        # 如果所有模块都已卸载，删除整个环境
        if all(not (modules_dir / module_id).exists() for module_id in module_ids):
            try:
                shutil.rmtree(env_path, ignore_errors=True)
                results["env_cleanup"] = {"status": "completed"}
            except Exception as e:
                results["env_cleanup"] = {"status": "error", "message": str(e)}
        
        return results
    
    def _mount_overlay(self, upper_dir: Path, work_dir: Path, merge_dir: Path, base_dir: Path):
        """使用mount overlayfs挂载目录"""
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
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _unmount_overlay(self, merge_dir: Path):
        """卸载overlayfs"""
        # 使用unmount -l强制卸载
        subprocess.run(["umount", "-l", str(merge_dir)], check=True)
    
    async def _create_conda_env(self, base_dir: Path, env_name: str):
        """创建conda环境（实际项目中需要调用外部服务）"""
        # 这里只是模拟，实际应该调用functiontest_service
        conda_cmd = [
            "conda", "create", "--prefix", str(base_dir / env_name),
            "-y", "--quiet", "python=3.8"
        ]
        subprocess.run(conda_cmd, check=True, capture_output=True)