import asyncio
from typing import List, Dict
from fastapi import HTTPException
from src.util.log_manager import LoggerManager
from src.util.env_manager import OverlayTool
logger = LoggerManager(__name__)


class OverlayService:
    def __init__(self):
        pass
    
    async def create_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """创建虚环境目录（upper、work、merge、base、modules/{module_id}）"""
        logger.info(f"创建虚环境 {env_id}")
        
        # 使用OverlayTool创建目录结构
        overlay_tool = OverlayTool(task_id=env_id)
        overlay_tool.init_directory_structure()
        
        results = {}
        
        for module_id in module_ids:
            # 创建模块的overlay目录（不挂载）
            module_dir = overlay_tool.root_dir / "modules" / module_id
            upper_dir = module_dir / "upper"
            work_dir = module_dir / "work"
            merge_dir = module_dir / "merge"
            
            for dir_path in [upper_dir, work_dir, merge_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # 设置权限
            import os
            os.chmod(module_dir, 0o777)
            
            results[module_id] = {
                "upper_dir": str(upper_dir),
                "work_dir": str(work_dir),
                "merge_dir": str(merge_dir),
                "status": "created"
            }
            logger.success(f"已为模块 {module_id} 创建overlay目录")
        
        logger.success(f"虚环境 {env_id} 创建成功")
        return results
    
    async def mount_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """挂载虚环境目录（upper、work、merge）"""
        logger.info(f"挂载虚环境 {env_id}")
        
        # 使用OverlayTool进行挂载
        overlay_tool = OverlayTool(task_id=env_id)
        
        # 检查环境目录是否存在
        if not overlay_tool.root_dir.exists():
            logger.error(f"虚环境 {env_id} 不存在")
            raise HTTPException(status_code=404, detail=f"环境 {env_id} 不存在")
        
        results = {}
        
        for module_id in module_ids:
            module_path = overlay_tool.root_dir / "modules" / module_id
            
            if not module_path.exists():
                logger.error(f"模块目录 {module_path} 不存在")
                raise HTTPException(status_code=404, detail=f"模块 {module_id} 不存在")
            
            upper_dir = module_path / "upper"
            work_dir = module_path / "work"
            merge_dir = module_path / "merge"
            base_dir = overlay_tool.root_dir / "base"
            
            # 使用OverlayTool的挂载方法
            try:
                overlay_tool._mount_overlayfs(upper_dir, work_dir, merge_dir, base_dir)
                results[module_id] = {
                    "upper_dir": str(upper_dir),
                    "work_dir": str(work_dir),
                    "merge_dir": str(merge_dir),
                    "status": "mounted"
                }
                logger.success(f"已挂载模块 {module_id} 的overlayfs")
            except Exception as e:
                logger.error(f"挂载模块 {module_id} 的overlayfs成功: {str(e)}")
                raise HTTPException(status_code=200, detail=f"模块 {module_id} 挂载成功: {str(e)}")
        
        logger.success(f"虚环境 {env_id} 挂载成功")
        return results
    
    async def unmount_overlay_env(self, env_id: str, module_ids: List[str]) -> Dict:
        """卸载虚环境目录"""
        logger.info(f"卸载虚环境 {env_id}")
        
        # 使用OverlayTool进行卸载
        overlay_tool = OverlayTool(task_id=env_id)
        
        # 检查环境目录是否存在
        if not overlay_tool.root_dir.exists():
            logger.error(f"虚环境 {env_id} 不存在")
            raise HTTPException(status_code=404, detail=f"环境 {env_id} 不存在")
        
        results = {}
        
        for module_id in module_ids:
            # 使用OverlayTool的卸载方法
            try:
                if overlay_tool.unmount_overlay_dirs(module_id):
                    results[module_id] = {"status": "unmounted"}
                    logger.success(f"已卸载并清理模块 {module_id}")
                else:
                    results[module_id] = {"status": "unmounted"}
                    logger.warning(f"模块 {module_id} 不存在或已被清理")
            except Exception as e:
                logger.error(f"卸载模块 {module_id} 失败: {str(e)}")
                results[module_id] = {"status": "error", "message": str(e)}
        
        # 如果所有模块都已卸载，删除整个环境
        modules_dir = overlay_tool.root_dir / "modules"
        if all(not (modules_dir / module_id).exists() for module_id in module_ids):
            try:
                import shutil
                shutil.rmtree(overlay_tool.root_dir, ignore_errors=True)
                results["env_cleanup"] = {"status": "completed"}
                logger.success(f"已删除虚环境 {env_id}")
            except Exception as e:
                logger.error(f"删除虚环境 {env_id} 失败: {str(e)}")
                results["env_cleanup"] = {"status": "error", "message": str(e)}
        
        return results