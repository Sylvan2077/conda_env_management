from fastapi import FastAPI
from src.api.overlay_api import router
from src.api.doc_api import doc_router

app = FastAPI(
    title="conda-overlayfs 虚环境管理服务",
    description="基于 overlayfs 的 conda 虚环境管理服务",
    version="1.0.0",
    # 禁用默认文档页面，使用自定义文档路由
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# 包含API路由
app.include_router(router)
# 包含文档API路由
app.include_router(doc_router)