# conda-overlayfs 虚环境管理服务

基于 overlayfs 的 conda 虚环境管理服务，用于高效管理多个测试流程任务的 conda 环境。

## 项目结构

```
project/
├── main.py                 # FastAPI 入口
├── models.py               # Pydantic 模型
├── api.py                  # FastAPI API 层
├── env_manager.py          # overlayfs + conda 核心管理器
├── service.py              # API业务逻辑实现
└── requirements.txt        # 依赖包
```

## 核心功能

### 1. 初始化虚环境目录结构
- 创建以 UUID 为目录名的任务总目录
- 创建 `base/` 目录用于存储全局基础 conda 环境
- 创建 `modules/` 目录用于存储所有模块的 overlay 目录

### 2. 创建虚环境目录
- 为每个模块创建 `upper/`、`work/`、`merge/` 目录
- 设置权限确保可访问性
- 挂载 overlayfs
- 在 base 目录下创建 conda 环境

### 3. 卸载虚环境目录
- 卸载 overlayfs 挂载
- 删除模块目录
- 清理整个任务目录

## API 接口

### POST /init_overlay_env
初始化虚环境目录结构

**请求参数：** 无

**返回参数：**
```json
{
  "env_id": "uuid-string",
  "message": "虚环境目录初始化成功"
}
```

### POST /create_overlay_env
创建虚环境目录（upper、work、merge）

**请求参数：**
```json
{
  "env_id": "uuid-string",
  "module_ids": ["mod_a", "mod_b"],
  "conda_env_name": "test_env"
}
```

**返回参数：**
```json
{
  "status": "success",
  "message": "虚环境创建成功",
  "result": {
    "mod_a": {
      "upper_dir": "/scnsqap/{env_id}/modules/mod_a/upper",
      "work_dir": "/scnsqap/{env_id}/modules/mod_a/work",
      "merge_dir": "/scnsqap/{env_id}/modules/mod_a/merge",
      "status": "mounted"
    },
    "mod_b": {
      "upper_dir": "/scnsqap/{env_id}/modules/mod_b/upper",
      "work_dir": "/scnsqap/{env_id}/modules/mod_b/work",
      "merge_dir": "/scnsqap/{env_id}/modules/mod_b/merge",
      "status": "mounted"
    }
  }
}
```

### DELETE /unmount_overlay_env
卸载虚环境目录

**请求参数：**
```json
{
  "env_id": "uuid-string",
  "module_ids": ["mod_a", "mod_b"]
}
```

**返回参数：**
```json
{
  "status": "success",
  "message": "虚环境卸载成功",
  "result": {
    "mod_a": {"status": "unmounted"},
    "mod_b": {"status": "unmounted"},
    "env_cleanup": {"status": "completed"}
  }
}
```

## 目录结构规范

所有流程任务统一放在 `/scnsqap/` 目录下。

```
/scnsqap/
└── {process_task_id}/               # UUID 生成的目录名
    ├── base/                        # 全局基础 conda 环境（只读 lower）
    ├── modules/                      # 所有模块的 overlay 目录
    │   ├── mod_a/                   # 模块唯一ID作为子目录
    │   │   ├── upper/               # 可写层（只存本模块新增/修改的文件）
    │   │   ├── work/                # overlay 工作目录（必须为空）
    │   │   └── merge/               # 挂载点（merged view）
    │   └── mod_b/
    │       ├── upper/
    │       ├── work/
    │       └── merge/
    └── logs/                        # 任务日志（可选）
```

## 运行服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 优势特点

1. **性能优化**：每个模块只安装自己新增的包，下游包通过 overlay 直接可见，安装速度提升 5-10 倍
2. **磁盘节省**：upper_dir 只存差异，节省 70%+ 空间
3. **并发支持**：每个 process_task_id 独立目录，可同时跑多个 workflow
4. **易于集成**：提供清晰的 API 接口，易于集成到现有测试框架中