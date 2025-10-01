from fastapi import HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from app.utils.auth import get_current_token
from starlette.types import Scope
import os
from typing import Optional

class AuthStaticFiles(StaticFiles):
    """带认证的静态文件服务"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def __call__(self, scope: Scope, receive, send) -> None:
        """处理静态文件请求，添加认证检查"""
        # 获取请求路径
        path = scope.get("path", "")
        
        # 只对图片目录进行认证检查
        if path.startswith("/static/images/"):
            # 从headers中获取认证信息
            headers = scope.get("headers", [])
            auth_header = None
            for header_name, header_value in headers:
                if header_name == b"authorization":
                    auth_header = header_value.decode("utf-8")
                    break
            
            # 从URL查询参数中获取token
            token = None
            if not auth_header:
                # 获取查询字符串
                query_string = scope.get("query_string", b"").decode("utf-8")
                if query_string:
                    # 解析查询参数
                    from urllib.parse import parse_qs
                    query_params = parse_qs(query_string)
                    token_params = query_params.get("token", [])
                    if token_params:
                        token = token_params[0]
            else:
                # 从Authorization header中提取token
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            
            # 验证token
            if not token:
                response = Response("未提供认证凭据", status_code=401)
                await response(scope, receive, send)
                return
            
            from app.utils.config import settings
            
            if token != settings.auth.token:
                response = Response("无效的认证凭据", status_code=401)
                await response(scope, receive, send)
                return
        
        # 通过认证检查，继续处理静态文件
        await super().__call__(scope, receive, send)