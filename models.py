from pydantic import BaseModel
from typing import List

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