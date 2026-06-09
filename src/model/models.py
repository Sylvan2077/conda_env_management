from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CreateOverlayEnvRequest(BaseModel):
    """创建虚环境请求"""
    env_id: str
    module_ids: List[str]

class MountOverlayEnvRequest(BaseModel):
    """挂载虚环境请求"""
    env_id: str
    module_ids: List[str]

class UnmountOverlayEnvRequest(BaseModel):
    """卸载虚环境请求"""
    env_id: str
    module_ids: List[str]

class Module(BaseModel):
    """模块定义"""
    id: str
    name: str
    conda_packages: List[str]          # 本模块需要安装的包
    test_command: str                  # 测试命令（在 merge_dir 下执行）

class Workflow(BaseModel):
    """工作流定义"""
    task_id: str
    base_conda_env: str = "/opt/base_env"  # 全局只读 base（可选）
    modules: List[Module]
    dependencies: dict                   # key: module_id, value: 它依赖的下游模块id列表

class OverlayEnvResponse(BaseModel):
    """虚环境响应"""
    env_id: str
    message: str
    result: dict

class TaskModule(BaseModel):
    """任务模块定义（用于DAG编排）"""
    module_id: str                          # 当前模块ID
    next_module_ids: Optional[List[str]] = None  # 下游模块ID列表（依赖当前模块的模块）

class TaskParams(BaseModel):
    """任务参数"""
    base_conda_env: Optional[str] = "base_env"  # 基础conda环境名称

class StartTestTaskRequest(BaseModel):
    """启动测试任务请求"""
    modules: List[TaskModule]               # 模块列表，包含DAG依赖信息
    task_params: Optional[TaskParams] = None