from fastapi import APIRouter, Depends
from app.services.chat_service import ChatService
from app.models.request.chat import *
from app.models.response import APIResponse

router = APIRouter()

@router.post(
    "/send", 
    operation_id="[chat]发送消息",
    summary="子窗口发送消息"
)
async def send_message(
    request: SendMessageRequest, 
    service: ChatService = Depends()
):
    """微信子窗口发送消息"""
    return service.send_message(
        msg=request.msg,
        who=request.who,
        clear=request.clear,
        at=request.at
    )

@router.post(
    "/getallmessage", 
    operation_id="[chat]获取所有消息",
    summary="获取微信子窗口所有消息"
)
async def get_all_message(
    request: GetAllMessageRequest,
    service: ChatService = Depends()
):
    """获取微信子窗口所有消息"""
    return service.get_all_message(who=request.who, auto_save_image=request.auto_save_image)

@router.post(
    "/getnewmessage", 
    operation_id="[chat]获取新消息",
    summary="获取微信子窗口新消息"
)
async def get_new_message(
    request: GetNewMessageRequest,
    service: ChatService = Depends()
):
    """获取微信子窗口新消息"""
    return service.get_new_message(who=request.who, auto_save_image=request.auto_save_image)

@router.post(
    "/msg/quote", 
    operation_id="[chat]发送引用消息",
    summary="子窗口根据id发送引用消息"
)
async def send_quote_by_id(
    request: SendQuoteByIdRequest,
    service: ChatService = Depends()
):
    """根据id发送引用消息"""
    return service.send_quote_by_id(
        msg_id=request.msg_id,
        content=request.content,
        who=request.who,
        wxname=request.wxname
    )

@router.post(
    "/msg/download_image", 
    operation_id="[chat]下载消息图片",
    summary="下载指定ID的消息图片到static目录"
)
async def download_message_image(
    request: DownloadMessageImageRequest,
    service: ChatService = Depends()
):
    """下载指定ID的消息图片到static目录"""
    return service.download_message_image(
        msg_id=request.msg_id,
        who=request.who,
        wxname=request.wxname
    )

@router.post(
    "/close", 
    operation_id="[chat]关闭子窗口",
    summary="关闭子窗口"
)
async def close_sub_window(
    request: CloseSubWindowsRequest,
    service: ChatService = Depends()
):
    """关闭子窗口"""
    return service.close_sub_window(who=request.who, wxname=request.wxname)