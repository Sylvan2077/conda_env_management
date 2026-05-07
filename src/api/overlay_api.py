from fastapi import APIRouter, HTTPException
from typing import List, Optional
from src.model.models import CreateOverlayEnvRequest, MountOverlayEnvRequest, UnmountOverlayEnvRequest
from src.service.service import OverlayService
from src.util.log_manager import LoggerManager
logger = LoggerManager(__name__)
overlay_service = OverlayService()
router = APIRouter()

@router.post("/create_overlay_env")
async def create_overlay_env(request: CreateOverlayEnvRequest):
    """创建虚环境目录（upper、work、merge、base、modules/{module_id}）"""
    try:
        result = await overlay_service.create_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"Overlay environment created: {result}")
        return {"status": "success", "message": "虚环境创建成功", "result": result}
    except Exception as e:
        logger.error(f"Error creating overlay environment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.post("/mount_overlay_env")
async def mount_overlay_env(request: MountOverlayEnvRequest):
    """挂载虚环境目录（upper、work、merge）"""
    try:
        result = await overlay_service.mount_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"Overlay environment mounted: {result}")
        return {"status": "success", "message": "虚环境挂载成功", "result": result}
    except Exception as e:
        logger.error(f"Error mounting overlay environment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"挂载失败: {str(e)}")

@router.delete("/unmount_overlay_env")
async def unmount_overlay_env(request: UnmountOverlayEnvRequest):
    """卸载虚环境目录"""
    try:
        result = await overlay_service.unmount_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"Overlay environment unmounted: {result}")
        return {"status": "success", "message": "虚环境卸载成功", "result": result}
    except Exception as e:
        logger.error(f"Error unmounting overlay environment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"卸载失败: {str(e)}")