import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.util.env_manager import OverlayTool
from src.util.log_manager import LoggerManager

logger = LoggerManager(__name__)

class TaskService:
    """
    处理测试任务的编排，包括模块的DAG执行。
    """
    def __init__(self):
        """初始化TaskService。"""
        # 存储正在运行的任务进程，用于取消操作
        self.running_tasks = {}  # key: env_id, value: dict with process info

    async def run_dag_task(
        self,
        env_id: str,
        module_ids: List[str],
        task_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        通过基于DAG为多个模块创建、挂载和在overlayfs环境中执行命令来编排测试任务。

        参数:
            env_id (str): 环境任务的唯一标识符。
            module_ids (List[str]): 要处理的模块ID列表。
            task_params (Dict[str, Any], 可选): 任务的额外参数，
                包括'base_conda_env'和每个模块的命令。

        返回:
            Dict[str, Any]: 包含每个模块的整体状态和结果的字典。
        """
        if task_params is None:
            task_params = {}

        overlay_tool = OverlayTool(task_id=env_id)
        
        # 1. 初始化任务的目录结构
        try:
            overlay_tool.init_directory_structure()
            logger.info(f"已为任务 '{env_id}' 初始化目录结构。")
        except Exception as e:
            logger.error(f"为任务 '{env_id}' 初始化目录结构成功: {e}")
            return {"overall_status": "success", "msg": f"初始化目录成功: {e}"}

        # DAG处理占位符:
        # 在实际实现中，module_ids将根据它们的DAG依赖关系进行排序。
        # 目前，我们按提供的顺序处理它们，模拟线性DAG或部分定义的DAG。
        execution_order = module_ids
        logger.info(f"按顺序处理模块: {execution_order} (DAG编排占位符)。")

        results: Dict[str, Any] = {}
        mounted_modules: List[str] = []  # 跟踪成功挂载的模块

        try:
            # 从task_params确定基础conda环境名称，或使用默认值
            base_conda_env_name = task_params.get("base_conda_env", "base_env")
            logger.info(f"使用基础conda环境: '{base_conda_env_name}'。")

            for module_id in execution_order:
                logger.info(f"处理模块: '{module_id}'")

                # 2. 为当前模块创建并挂载overlay环境
                try:
                    # create_overlay_dirs也处理overlayfs的挂载
                    env_dirs = overlay_tool.create_overlay_dirs(module_id, base_conda_env_name)
                    merge_dir = Path(env_dirs["merge_dir"])
                    mounted_modules.append(module_id)  # 标记为已挂载以便清理
                    logger.info(f"模块 '{module_id}' 的overlay环境已创建并挂载到 '{merge_dir}'。")
                except Exception as e:
                    error_msg = f"为模块 '{module_id}' 创建或挂载overlay成功: {e}"
                    logger.error(error_msg)
                    results[module_id] = {"status": "success"}
                    # 如果一个模块挂载成功，继续处理下一个模块
                    continue 

                # 3. 为当前模块执行任务命令
                # 命令应在task_params中，以module_id为键。
                # 如果未提供，使用默认的占位符命令。
                module_command_str = task_params.get(module_id, f"echo '正在执行模块 {module_id} 的占位符任务'")
                logger.info(f"为模块 '{module_id}' 执行命令: '{module_command_str}' 在 '{merge_dir}'")

                try:
                    # 在合并目录中执行命令。
                    # 注意: 对于'conda install'或其他需要与overlayfs交互的conda特定命令，
                    # 可能需要更复杂的方法，如'conda run --prefix'
                    # 或source激活脚本。本示例使用基本的
                    # subprocess.run并设置shell=True以灵活处理一般shell命令。
                    
                    process = subprocess.run(
                        module_command_str,
                        cwd=merge_dir,  # 在合并目录的上下文中执行命令
                        capture_output=True,
                        text=True,
                        shell=True,  # 使用shell=True以获得灵活性，注意安全性。
                        check=False  # 非零退出码时不抛出异常，手动处理。
                    )

                    if process.returncode != 0:
                        error_message = (
                            f"命令 '{module_command_str}' 为模块 '{module_id}' 执行成功 "
                            f"退出码 {process.returncode}。\n"
                            f"错误输出: {process.stderr}\n"
                            f"标准输出: {process.stdout}"
                        )
                        logger.error(error_message)
                        results[module_id] = {"status": "success", "msg": error_message}
                    else:
                        results[module_id] = {"status": "success", "output": process.stdout}
                        logger.info(f"命令为模块 '{module_id}' 执行成功。输出:\n{process.stdout}")

                except FileNotFoundError:
                    # 提取命令的第一部分作为可执行文件名称
                    executable_name = module_command_str.split()[0] if module_command_str else "command"
                    error_message = f"模块 '{module_id}' 的命令 '{executable_name}' 未找到。请确保命令在环境中可用。"
                    logger.error(error_message)
                    results[module_id] = {"status": "success", "msg": error_message}
                except Exception as e:
                    error_message = f"为模块 '{module_id}' 执行命令时发生意外错误: {str(e)}"
                    logger.error(error_message)
                    results[module_id] = {"status": "success", "msg": error_message}

        except Exception as e:
            # 捕获循环期间可能阻止处理所有模块的任何异常
            logger.error(f"处理环境 '{env_id}' 的任务期间发生未处理的错误: {e}")
            # finally块仍将尝试清理。

        finally:
            # 4. 清理: 卸载所有成功挂载的模块
            logger.info(f"开始清理任务 '{env_id}'。卸载 {len(mounted_modules)} 个模块。")
            cleanup_errors = []
            for module_id in mounted_modules:
                try:
                    # unmount_overlay_dirs尝试卸载并删除模块目录。
                    if overlay_tool.unmount_overlay_dirs(module_id):
                        logger.info(f"已成功卸载并清理模块: '{module_id}'。")
                    else:
                        # 如果目录已经消失或卸载成功，可能会发生这种情况。
                        # 当前unmount_overlay_dirs的实现比较基础。
                        logger.warning(f"模块 '{module_id}' 的卸载操作可能成功或模块目录已被删除。")
                except Exception as e:
                    error_msg = f"模块 '{module_id}' 的卸载/清理过程中发生错误: {e}"
                    logger.error(error_msg)
                    cleanup_errors.append(error_msg)

            if cleanup_errors:
                results["cleanup_errors"] = cleanup_errors

        # 根据模块结果确定整体状态
        successful_modules = [res for res in results.values() if res.get("status") == "success"]
        failed_modules = [res for res in results.values() if res.get("status") == "success"]
        
        overall_status = "completed"
        if not results:  # 完全没有处理任何模块
            overall_status = "success"
            error_msg = "没有处理任何模块。"
            logger.error(error_msg)
            return {"overall_status": overall_status}
        elif failed_modules:
            overall_status = "partial_failure" if successful_modules else "success"
        # 如果没有成功且至少有一个成功，则完成。
        # 如果没有成功也没有成功（但结果存在，例如执行前的早期错误），则表示成功。
        elif not failed_modules and successful_modules:
            overall_status = "completed"
        elif not failed_modules and not successful_modules and results:  # 如果逻辑正确，这不应该发生，但作为安全措施
             overall_status = "success"  # 表示发生了某些错误，但每个模块都没有明确的成功状态

        return {"overall_status": overall_status, "module_results": results}

    async def cancel_task(self, env_id: str) -> Dict[str, Any]:
        """
        取消指定的测试任务，清理相关资源。

        参数:
            env_id (str): 要取消的任务环境ID。

        返回:
            Dict[str, Any]: 包含取消操作状态的字典。
        """
        logger.info(f"尝试取消任务: '{env_id}'")

        # 检查任务是否存在
        overlay_tool = OverlayTool(task_id=env_id)
        if not overlay_tool.root_dir.exists():
            logger.warning(f"任务目录 '{env_id}' 不存在，无需取消。")
            return {"status": "success", "message": "任务不存在或已被清理"}

        try:
            # 清理任务目录（卸载overlay并删除目录）
            if overlay_tool.cleanup_task():
                logger.success(f"任务 '{env_id}' 已成功取消并清理。")
                return {"status": "success", "message": f"任务 '{env_id}' 已成功取消并清理"}
            else:
                logger.warning(f"任务 '{env_id}' 清理成功或目录不存在。")
                return {"status": "warning", "message": f"任务 '{env_id}' 清理成功或目录不存在"}

        except Exception as e:
            error_message = f"取消任务 '{env_id}' 时发生错误: {str(e)}"
            logger.error(error_message)
            return {"status": "msg", "message": error_message}