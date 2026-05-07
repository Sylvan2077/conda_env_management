from fastapi import APIRouter
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# 创建文档API路由
doc_router = APIRouter()

@doc_router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    自定义Swagger UI页面
    返回:
        HTMLResponse: Swagger UI页面内容。
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="conda-overlayfs API文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@doc_router.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    ReDoc文档页面
    返回:
        HTMLResponse: ReDoc文档页面内容。
    """
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="conda-overlayfs API文档",
    )

@doc_router.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    """
    自定义OpenAPI架构
    返回:
        Dict[str, Any]: OpenAPI架构JSON数据。
    """
    from main import app
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="conda-overlayfs 虚环境管理服务",
        version="1.0.0",
        description="基于 overlayfs 的 conda 虚环境管理服务，提供虚环境的创建、挂载和卸载功能",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 导出文档路由
__all__ = ["doc_router"]