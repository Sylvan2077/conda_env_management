from fastapi import FastAPI
from api import router

app = FastAPI(
    title="conda-overlayfs 虚环境管理服务",
    description="基于 overlayfs 的 conda 虚环境管理服务",
    version="1.0.0"
)

# 包含API路由
app.include_router(router)
