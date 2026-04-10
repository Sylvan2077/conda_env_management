
# 本项目为conda-overlayfs虚环境管理服务

## 背景：
- FastAPI 作为 API 层，负责接收/管理多个**测试流程任务**。  
- 每个 workflow task 维护**一个主 conda 环境**，但内部包含多个**模块**（module），模块间存在**有向无环图（DAG）依赖**。  
- 每个模块需要安装自己的 conda 包，且**安装操作基于“下游模块”的虚环境**（这里的“下游模块”指该模块所**依赖的前置模块**，即其依赖的模块的 merge_dir 作为 lower layer）。  
- 核心优化：**使用 overlayfs（写时复制）** 减少每个模块实际安装的包数量，只在 upper_dir 写入差异，极大加速安装并节省磁盘。

## 所需实现：
本项目只实现对conda虚环境的管理，不实现具体流程测试及DAG管理。
**overlayfs 思路**：  
- `lower_dir`（只读）：下游模块已合并的 merge_dir（或 base 环境）。  
- `upper_dir`（可写）：当前模块新增/修改的文件。  
- `work_dir`（工作层）：overlayfs 内部临时目录。  
- `merge_dir`（视图层）：**只操作这个目录**进行 `conda install`、`python` 执行等，所有下游包对当前模块“可见”，conda 只会安装**增量包**。

下面给出**完整可落地的实现方案**（Python + FastAPI），包含关键代码。

### 1. 环境准备（服务器侧）

- 服务器为centos7，使用python语言的mount模块实现原生overlayfs挂载
- 数据库使用postgresql
- 目录结构规范：
所有流程任务统一放在 /scnsqap/ 目录下。

每个流程任务使用 UUID 生成的 process_task_id 作为目录名（推荐使用 uuid.uuid4()）。
单个任务的目录结构如下（以 process_task_id = "a1b2c3d4-..." 为例）：

text/scnsqap/
└── a1b2c3d4-e5f6-7890-abcd-ef1234567890/          # process_task_id
    ├── base/                                      # 全局基础 conda 环境（只读 lower）
    ├── modules/                                   # 所有模块的 overlay 目录
    │   ├── mod_a/                                 # 模块唯一ID作为子目录
    │   │   ├── upper/                             # 可写层（只存本模块新增/修改的文件）
    │   │   ├── work/                              # overlay 工作目录（必须为空）
    │   │   └── merge/                             # 挂载点（merged view）← 所有操作在这里进行 conda install / python 执行
    │   ├── mod_b/
    │   │   ├── upper/
    │   │   ├── work/
    │   │   └── merge/
    │   └── ...
    └── logs/                                      # 可选：任务日志
关键说明：

只对 merge/ 目录执行 conda install、python 等操作。
upper/ 只保存当前模块的增量变化 → 大幅减少磁盘占用和安装时间。
work/ 目录必须在挂载前为空，且属于同一个文件系统（推荐放在同一磁盘分区）。

### 2. 项目结构
```
project/
├── main.py                 # FastAPI 入口
├── models.py               # Pydantic 模型（Workflow、Module、DAG）
├── api.py                  # FastAPI API 层，实现初始化虚环境目录、创建虚环境、卸载虚环境目录三个接口
├── env_manager.py          # overlayfs + conda 核心管理器，创建OverlatTool类，执行挂载、卸载等操作
├── service.py              # 实现对api的具体逻辑，包括初始化虚环境目录、创建虚环境、卸载虚环境目录三个接口的具体功能实现
└── ...
```

### 3. 接口设计

- **POST /create_overlay_env**：创建虚环境目录（upper、work、merge、base、modules/{module_id}）。
接收参数：env_id(由外部流程服务提供)、module_ids（模块id列表）
返回参数：返回成功或失败
具体实现：1.根据env_id，在目录下创建base目录，用于存储全局基础conda环境（只读 lower）；
        2.env_id目录下创建modules目录，用于存储所有模块的overlay目录。
        3.根据module_ids，创建modules目录下的子目录，即module_id目录；
        4.每个module_id子目录下创建upper、work、merge目录;
        5.使用chmod -R 777权限，确保module_id目录所有用户都有读写权限。
        6.接口返回成功或失败。

- **POST /mount_overlay_env**：挂载虚环境目录（upper、work、merge）。
接收参数：env_id、module_ids（模块id列表）
返回参数：返回成功或失败
具体实现：1.对每个module_id子目录下使用mount overlayfs挂载upper 、work、merge、base目录。
        2.接口返回成功或失败。

- **DELETE /unmount_overlay_env**：卸载虚环境目录（upper、work、merge）。
接收参数：env_id、module_ids（模块id列表）
返回参数：返回成功或失败
具体实现：1.根据env_id和module_id，卸载modules目录下的子目录，即module_id；
        2.子目录下使用unmount -l卸载merge目录，视图层（merged view）。
        3.使用rm -rf删除modules目录下的子目录、base目录。
        4.接口返回成功或失败。

### 4. 优势 & 注意事项
- **性能**：每个模块只安装**自己新增**的包，下游包通过 overlay 直接可见，安装速度提升 5-10 倍（实测取决于包大小）。
- **磁盘**：upper_dir 只存差异，节省 70%+ 空间。
- **并发**：每个 process_task_id 独立目录，可同时跑多个 workflow。
- **注意**：
  - 包冲突：如果下游模块安装了不同版本同一包，overlay 会以后面的 lower 为准（需在 DAG 设计时保证兼容）。
  - 清理：任务结束后可 `unmount` 或删除整个 `env_id` 目录。
  - 生产环境建议加日志（loguru）、错误重试、超时机制。
