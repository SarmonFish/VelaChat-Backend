from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1 import wechat, chat, apps, files, info
from app.utils.auth import get_current_token
from app.utils.auth_static import AuthStaticFiles
from app.models.response import APIResponse
from app.utils.config import settings
from app.utils.wx_package_manager import is_wxautox, get_supported_features
from typing import Any, Dict
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="WXAuto API",
    description="微信自动化API服务，✨标识为plus版本特有接口",
    version="1.0.0",
    docs_url=None,  # 禁用默认文档，使用自定义
    redoc_url=None,  # 禁用默认ReDoc，使用自定义
    openapi_url=settings.api.openapi_url
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 挂载静态文件
# 使用带认证的静态文件服务，对图片目录进行访问控制
app.mount("/static", AuthStaticFiles(directory="static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一处理HTTP异常
    
    Args:
        request: 请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: 统一格式的响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            data=None
        ).model_dump()
    )

@app.get("/")
async def root():
    """根路径
    
    Returns:
        dict: 欢迎信息和包信息
    """
    package_info = {
        "message": "欢迎使用WXAuto API",
        "package": settings.package,
        "version": "Plus版" if is_wxautox() else "开源版",
        "description": "wxauto Plus版，功能更丰富" if is_wxautox() else "wxauto开源版，基础功能",
        "features_count": len(get_supported_features()),
        "docs_url": f"http://{settings.server.host}:{settings.server.port}{settings.api.docs_url}"
    }
    
    return package_info

# 注册路由，添加认证依赖
app.include_router(wechat.router, prefix=f"{settings.api.prefix}/wechat", tags=["WeChat"], dependencies=[Depends(get_current_token)])
app.include_router(chat.router, prefix=f"{settings.api.prefix}/chat", tags=["Chat"], dependencies=[Depends(get_current_token)])
app.include_router(apps.router, prefix=f"{settings.api.prefix}/apps", tags=["Apps"], dependencies=[Depends(get_current_token)])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(info.router, prefix=f"{settings.api.prefix}/info", tags=["Info"])

# 自定义Swagger UI路由
@app.get(settings.api.docs_url, include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义Swagger UI页面，使用本地静态资源"""
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
    <head>
        <title>WXAuto API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="/static/swagger-ui/swagger-ui.css" />
        <link rel="shortcut icon" type="image/png" href="/static/swagger-ui/favicon.png">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: '/openapi.json',
                    "dom_id": "#swagger-ui",
                    "layout": "BaseLayout",
                    "deepLinking": true,
                    "showExtensions": true,
                    "showCommonExtensions": true,
                    oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                }});
            }};
        </script>
    </body>

</html>
    """)

# 自定义ReDoc路由
@app.get(settings.api.redoc_url, include_in_schema=False)
async def custom_redoc_html():
    """自定义ReDoc页面，使用本地静态资源"""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WXAuto API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <div id="redoc-container"></div>
        <script src="/static/redoc/redoc.standalone.js"></script>
        <script>
            window.onload = function() {{
                Redoc.init("{settings.api.openapi_url}", {{}}, document.getElementById("redoc-container"));
            }};
        </script>
    </body>
    </html>
    """)




