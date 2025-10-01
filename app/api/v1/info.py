from fastapi import APIRouter
from app.models.response import APIResponse
from app.utils.wx_package_manager import is_wxautox, get_supported_features
from app.utils.config import settings

router = APIRouter()

@router.get(
    "/package", 
    operation_id="获取包信息", 
    response_model=APIResponse,
    summary="获取当前使用的包信息"
)
async def get_package_info():
    """获取当前使用的包信息"""
    package_info = {
        "package": settings.package,
        "is_wxautox": is_wxautox(),
        "version": "Plus版" if is_wxautox() else "开源版",
        "description": "wxauto Plus版，功能更丰富" if is_wxautox() else "wxauto开源版，基础功能"
    }
    
    return APIResponse(
        success=True,
        message="获取包信息成功",
        data=package_info
    )

@router.get(
    "/features", 
    operation_id="获取支持功能", 
    response_model=APIResponse,
    summary="获取当前版本支持的功能列表"
)
async def get_supported_features_info():
    """获取当前版本支持的功能列表"""
    features = get_supported_features()
    
    return APIResponse(
        success=True,
        message="获取功能列表成功",
        data={
            "package": settings.package,
            "features": features,
            "feature_count": len(features)
        }
    )

@router.get(
    "/status", 
    operation_id="获取服务状态", 
    response_model=APIResponse,
    summary="获取服务状态信息"
)
async def get_service_status():
    """获取服务状态信息"""
    status_info = {
        "package": settings.package,
        "is_wxautox": is_wxautox(),
        "server": {
            "host": settings.server.host,
            "port": settings.server.port,
            "reload": settings.server.reload
        },
        "database": {
            "type": settings.database.type
        },
        "features": get_supported_features()
    }
    
    return APIResponse(
        success=True,
        message="获取服务状态成功",
        data=status_info
    ) 