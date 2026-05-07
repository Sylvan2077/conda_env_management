from fastapi import APIRouter, HTTPException
from typing import List, Optional
from src.model.models import CreateOverlayEnvRequest, MountOverlayEnvRequest, UnmountOverlayEnvRequest
from src.service.overlay_service import OverlayService
from src.util.log_manager import LoggerManager
logger = LoggerManager(__name__)
overlay_service = OverlayService()
overlay_router = APIRouter()

@overlay_router.post("/create_overlay_env")
async def create_overlay_env(request: CreateOverlayEnvRequest):
    """
    创建虚环境目录（upper、work、merge、base、modules/{module_id}）
    参数:
        request (CreateOverlayEnvRequest): 创建虚环境请求对象，包含 env_id 和 module_ids。
    返回:
        Dict[str, Any]: 包含创建状态和结果的字典。
    """
    try:
        result = await overlay_service.create_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"虚环境创建成功: {result}")
        return {"status": "success", "message": "虚环境创建成功", "result": result}
    except Exception as e:
        logger.error(f"创建虚环境失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@overlay_router.post("/mount_overlay_env")
async def mount_overlay_env(request: MountOverlayEnvRequest):
    """
    挂载虚环境目录（upper、work、merge）
    参数:
        request (MountOverlayEnvRequest): 挂载虚环境请求对象，包含 env_id 和 module_ids。
    返回:
        Dict[str, Any]: 包含挂载状态和结果的字典。
    """
    try:
        result = await overlay_service.mount_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"虚环境挂载成功: {result}")
        return {"status": "success", "message": "虚环境挂载成功", "result": result}
    except Exception as e:
        logger.error(f"挂载虚环境失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"挂载失败: {str(e)}")

@overlay_router.delete("/unmount_overlay_env")
async def unmount_overlay_env(request: UnmountOverlayEnvRequest):
    """
    卸载虚环境目录
    参数:
        request (UnmountOverlayEnvRequest): 卸载虚环境请求对象，包含 env_id 和 module_ids。
    返回:
        Dict[str, Any]: 包含卸载状态和结果的字典。
    """
    try:
        result = await overlay_service.unmount_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        logger.info(f"虚环境卸载成功: {result}")
        return {"status": "success", "message": "虚环境卸载成功", "result": result}
    except Exception as e:
        logger.error(f"卸载虚环境失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"卸载失败: {str(e)}")