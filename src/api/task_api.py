from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from src.service.task_service import TaskService
from src.util.log_manager import LoggerManager

logger = LoggerManager(__name__)
task_service = TaskService()
task_router = APIRouter()

@task_router.post("/start_test_task")
async def start_test_task(
    env_id: str,
    module_ids: List[str],
    task_params: Optional[Dict[str, Any]] = None
):
    """
    启动一个测试任务，可包含多个具有DAG依赖关系的模块。
    参数:
        env_id (str): 环境的唯一标识符。
        module_ids (List[str]): 要包含在测试任务中的模块ID列表。
        task_params (Dict[str, Any], 可选): 任务的额外参数。默认为None。
    返回:
        Dict[str, Any]: 包含任务状态和结果的字典。
    """
    try:
        logger.info(f"启动测试任务，env_id: {env_id}, 模块: {module_ids}")
        if task_params is None:
            task_params = {}
        
        result = await task_service.run_dag_task(
            env_id=env_id,
            module_ids=module_ids,
            task_params=task_params
        )
        
        logger.info(f"测试任务启动成功。结果: {result}")
        return {"status": "success", "message": "测试任务启动成功", "result": result}
    except Exception as e:
        logger.error(f"启动测试任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试任务启动失败: {str(e)}")

@task_router.delete("/cancel_test_task")
async def cancel_test_task(env_id: str):
    """
    取消指定的测试任务，清理相关资源。
    参数:
        env_id (str): 要取消的任务环境ID。
    返回:
        Dict[str, Any]: 包含取消操作状态的字典。
    """
    try:
        logger.info(f"尝试取消测试任务: {env_id}")
        
        result = await task_service.cancel_task(env_id=env_id)
        
        if result.get("status") == "success":
            return {"status": "success", "message": result.get("message")}
        elif result.get("status") == "warning":
            return {"status": "warning", "message": result.get("message")}
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))
    except Exception as e:
        logger.error(f"取消测试任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消测试任务失败: {str(e)}")