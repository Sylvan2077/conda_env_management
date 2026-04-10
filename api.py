from fastapi import APIRouter, HTTPException
from typing import List, Optional
from models import InitOverlayEnvRequest, CreateOverlayEnvRequest, UnmountOverlayEnvRequest
from service import overlay_service

router = APIRouter()

@router.post("/init_overlay_env")
async def init_overlay_env():
    """初始化虚环境目录结构"""
    try:
        env_id = await overlay_service.init_overlay_env()
        return {"env_id": env_id, "message": "虚环境目录初始化成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@router.post("/create_overlay_env")
async def create_overlay_env(request: CreateOverlayEnvRequest):
    """创建虚环境目录（upper、work、merge）"""
    try:
        result = await overlay_service.create_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids,
            conda_env_name=request.conda_env_name
        )
        return {"status": "success", "message": "虚环境创建成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.delete("/unmount_overlay_env")
async def unmount_overlay_env(request: UnmountOverlayEnvRequest):
    """卸载虚环境目录"""
    try:
        result = await overlay_service.unmount_overlay_env(
            env_id=request.env_id,
            module_ids=request.module_ids
        )
        return {"status": "success", "message": "虚环境卸载成功", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卸载失败: {str(e)}")