from fastapi import APIRouter, Depends
from app.services.app_service import AppService
from app.models.request.apps import *
from app.models.response import APIResponse

router = APIRouter()

@router.post(
    "/accept_new_friend", 
    operation_id="[apps]接受新好友", 
    response_model=APIResponse,
    summary="✨根据关键词接受好友申请，并自动修改备注、加标签"
)
async def api_accept_new_friend(
    request: AcceptNewFriendRequest,
    service: AppService = Depends()
):
    """接受新好友"""
    return service.accept_new_friend(
        wxname=request.wxname,
        keywords=request.keywords,
        remark=request.remark,
        tags=request.tags
    )