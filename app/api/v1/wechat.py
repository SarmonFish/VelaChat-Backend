from fastapi import APIRouter, Request, Depends
from app.services.wechat_service import WeChatService
from app.models.request.wechat import *
from app.models.response import APIResponse
from app.utils.route_condition import (
    require_wxautox, 
    require_feature, 
    conditional_route, 
    has_url_card_feature, 
    has_listen_chat_feature, 
    has_new_message_feature, 
    has_quote_message_feature, 
    has_friend_management_feature, 
    has_page_switch_feature
)
from typing import Dict, Any
import asyncio

router = APIRouter()

@router.post(
    "/send", 
    operation_id="[wx]发送消息", 
    response_model=APIResponse,
    summary="发送文字消息"
)
async def send_message(
    request: SendMessageRequest, 
    service: WeChatService = Depends()
):
    """微信主窗口发送消息"""
    return service.send_message(
        msg=request.msg,
        who=request.who,
        clear=request.clear,
        at=request.at,
        exact=request.exact,
        wxname=request.wxname
    )

@router.post(
    "/sendfile", 
    operation_id="[wx]发送文件", 
    response_model=APIResponse,
    summary="发送文件、图片、视频等（请先调用上传文件接口）"
)
async def send_file(
    request: SendFileRequest,
    service: WeChatService = Depends()
):
    """微信主窗口发送文件"""
    return service.send_file(
        file_id=request.file_id,
        who=request.who,
        exact=request.exact,
        wxname=request.wxname
    )

@router.post(
    "/chatwith", 
    operation_id="[wx]切换聊天窗口", 
    response_model=APIResponse,
    summary="切换聊天窗口"
)
async def chat_with(
    request: ChatWithRequest,
    service: WeChatService = Depends()
):
    """微信主窗口切换聊天窗口"""
    result = service.chat_with(
        who=request.who,
        exact=request.exact,
        wxname=request.wxname
    )
    return result

@router.post(
    "/getallsubwindow", 
    operation_id="[wx]获取所有子窗口", 
    response_model=APIResponse,
    summary="获取所有子窗口信息"
)
async def get_all_sub_window(
    request: GetAllSubWindowRequest,
    service: WeChatService = Depends()
):
    """获取微信所有子窗口信息"""
    return service.get_all_sub_window(wxname=request.wxname)

@router.post(
    "/getallmessage", 
    operation_id="[wx]获取当前窗口加载的消息", 
    response_model=APIResponse,
    summary='获取当前窗口加载的消息'
)
async def get_all_message(
    request: GetAllMessageRequest,
    service: WeChatService = Depends()
):
    """获取当前窗口加载的消息"""
    print('xxxxxxxxxxxxxxxxxxxx')
    return service.get_all_message(who=request.who, wxname=request.wxname)

@router.post(
    "/sendurlcard", 
    operation_id="[wx]发送url卡片", 
    response_model=APIResponse, 
    summary='✨发送url卡片'
)
@conditional_route(has_url_card_feature)
async def send_url_card(
    request: SendUrlCardRequest,
    service: WeChatService = Depends()
):
    """微信发送url卡片（wxautox特有）"""
    return service.send_url_card(
        url=request.url,
        friends=request.friends,
        timeout=request.timeout,
        wxname=request.wxname
    )

@router.post(
    "/addlistenchat", 
    operation_id="[wx]添加监听", 
    response_model=APIResponse,
    summary="添加监听（需和配合/chat/getnewmessage来获取新消息）"
)
async def add_listen_chat(
    request: AddListenChatRequest,
    service: WeChatService = Depends()
):
    """添加微信子窗口监听"""
    return service.add_listen_chat(
        who=request.who,
        wxname=request.wxname
    )

@router.post(
    "/getnextnewmessage", 
    operation_id="[wx]获取下一个新消息", 
    response_model=APIResponse,
    summary="获取一个未读消息窗口的新消息"
)
async def get_next_new_message(
    request: GetNextNewMessageRequest,
    service: WeChatService = Depends()
):
    """获取微信下一个新消息"""
    return service.get_next_new_message(
        filter_mute=request.filter_mute, 
        wxname=request.wxname
    )

@router.post(
    "/msg/quote", 
    operation_id="[wx]发送引用消息", 
    response_model=APIResponse,
    summary="根据消息id发送引用消息"
)
# @conditional_route(has_quote_message_feature)
async def send_quote_by_id(
    request: SendQuoteByIdRequest,
    service: WeChatService = Depends()
):
    """根据id发送引用消息"""
    return service.send_quote_by_id(
        msg_id=request.msg_id,
        content=request.content,
        wxname=request.wxname
    )

@router.post(
    "/getnewfriends", 
    operation_id="[wx]获取好友申请", 
    response_model=APIResponse,
    summary='✨获取好友申请列表'
)
@conditional_route(has_friend_management_feature)
async def get_new_friends(
    request: GetNewFriendsRequest,
    service: WeChatService = Depends()
):
    """获取微信新朋友（wxautox特有）"""
    return service.get_new_friends(
        acceptable=request.acceptable,
        wxname=request.wxname
    )

@router.post(
    "/newfriend/accept", 
    operation_id="[wx]接受好友申请", 
    response_model=APIResponse,
    summary='✨接受好友申请'
)
@conditional_route(has_friend_management_feature)
async def accept_new_friend(
    request: AcceptNewFriendRequest,
    service: WeChatService = Depends()
):
    """接受微信新朋友（wxautox特有）"""
    if isinstance(request.tags, str):
        tags = [request.tags]
    else:
        tags = request.tags
    return service.accept_new_friend(
        new_friend_id=request.new_friend_id, 
        remark=request.remark, 
        tags=tags, 
        wxname=request.wxname
    )

@router.post(
    "/switch/chat", 
    operation_id="[wx]切换到聊天页面", 
    response_model=APIResponse,
    summary="主窗口切换到聊天页面"
)
async def switch_to_chat_page(
    request: SwitchToChatPageRequest,
    service: WeChatService = Depends()
):
    """切换到聊天页面（wxautox特有）"""
    return service.switch_to_chat_page(wxname=request.wxname)

@router.post(
    "/isonline", 
    operation_id="[wx]是否在线（掉线）", 
    response_model=APIResponse,
    summary="✨微信是否在线（掉线）"
)
async def is_online(
    request: IsOnlineRequest,
    service: WeChatService = Depends()
):
    """微信是否在线（wxautox特有）"""
    return service.is_online(wxname=request.wxname)

# @router.post("/switch/contact", operation_id="[wx]切换到联系人页面", response_model=APIResponse)
# @conditional_route(has_page_switch_feature)
# async def switch_to_contact_page(
#     request: SwitchToContactPageRequest,
#     service: WeChatService = Depends()
# ):
#     """切换到联系人页面（wxautox特有）"""
#     return service.switch_to_contact_page(wxname=request.wxname)

@router.post(
    "/getsessions", 
    operation_id="[wx]获取当前会话列表", 
    response_model=APIResponse,
    summary="获取当前会话列表"
)
async def get_sessions(
    request: GetSessionsRequest,
    service: WeChatService = Depends()
):
    """获取微信当前会话列表"""
    return service.get_sessions(wxname=request.wxname)

# ===== pywechat 功能路由 =====

@router.post(
    "/pywechat/send_message_to_friend",
    operation_id="[pywechat]给单个好友发送单条消息",
    response_model=APIResponse,
    summary="pywechat: 给单个好友发送单条消息"
)
async def pywechat_send_message_to_friend(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 给单个好友发送单条消息"""
    return service.send_message_to_friend(
        friend=request.get("friend"),
        message=request.get("message"),
        tickle=request.get("tickle", False),
        search_pages=request.get("search_pages", 0)
    )

@router.post(
    "/pywechat/send_messages_to_friend",
    operation_id="[pywechat]给单个好友发送多条消息",
    response_model=APIResponse,
    summary="pywechat: 给单个好友发送多条消息"
)
async def pywechat_send_messages_to_friend(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 给单个好友发送多条消息"""
    return service.send_messages_to_friend(
        friend=request.get("friend"),
        messages=request.get("messages", []),
        tickle=request.get("tickle", False),
        search_pages=request.get("search_pages", 0)
    )

@router.post(
    "/pywechat/send_message_to_friends",
    operation_id="[pywechat]给多个好友分别发送单条消息",
    response_model=APIResponse,
    summary="pywechat: 给多个好友分别发送单条消息"
)
async def pywechat_send_message_to_friends(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 给多个好友分别发送单条消息"""
    return service.send_message_to_friends(
        friends=request.get("friends", []),
        message=request.get("message", []),
        tickle=request.get("tickle")
    )

@router.post(
    "/pywechat/send_messages_to_friends",
    operation_id="[pywechat]给多个好友分别发送多条消息",
    response_model=APIResponse,
    summary="pywechat: 给多个好友分别发送多条消息"
)
async def pywechat_send_messages_to_friends(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 给多个好友分别发送多条消息"""
    return service.send_messages_to_friends(
        friends=request.get("friends", []),
        messages=request.get("messages", [])
    )

@router.post(
    "/pywechat/forward_message",
    operation_id="[pywechat]转发消息",
    response_model=APIResponse,
    summary="pywechat: 转发消息"
)
async def pywechat_forward_message(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 转发消息"""
    return service.forward_message(
        friends=request.get("friends", []),
        message=request.get("message"),
        search_pages=request.get("search_pages", 0)
    )

@router.post(
    "/pywechat/check_new_message",
    operation_id="[pywechat]检查新消息",
    response_model=APIResponse,
    summary="pywechat: 检查（监听）新消息"
)
async def pywechat_check_new_message(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 检查（监听）新消息"""
    return service.check_new_message(
        duration=request.get("duration", "1min")
    )

@router.get(
    "/pywechat/friends/names",
    operation_id="[pywechat]获取好友名称",
    response_model=APIResponse,
    summary="pywechat: 获取所有好友的备注与名称"
)
async def pywechat_get_friends_names(
    service: WeChatService = Depends()
):
    """pywechat: 获取所有好友的备注与名称"""
    return service.get_friends_names()

@router.get(
    "/pywechat/friends/info",
    operation_id="[pywechat]获取好友信息",
    response_model=APIResponse,
    summary="pywechat: 获取所有好友昵称、备注与微信号"
)
async def pywechat_get_friends_info(
    service: WeChatService = Depends()
):
    """pywechat: 获取所有好友昵称、备注与微信号"""
    return service.get_friends_info()

@router.get(
    "/pywechat/friends/detail",
    operation_id="[pywechat]获取好友详情",
    response_model=APIResponse,
    summary="pywechat: 获取所有好友详细信息"
)
async def pywechat_get_friends_detail(
    service: WeChatService = Depends()
):
    """pywechat: 获取所有好友详细信息"""
    return service.get_friends_detail()

@router.get(
    "/pywechat/groups/info",
    operation_id="[pywechat]获取群聊信息",
    response_model=APIResponse,
    summary="pywechat: 获取所有群聊信息"
)
async def pywechat_get_groups_info(
    service: WeChatService = Depends()
):
    """pywechat: 获取所有群聊信息"""
    return service.get_groups_info()

@router.post(
    "/pywechat/friend/chat_history",
    operation_id="[pywechat]获取好友聊天记录",
    response_model=APIResponse,
    summary="pywechat: 获取好友聊天记录"
)
async def pywechat_get_friend_chat_history(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 获取好友聊天记录"""
    return service.get_friend_chat_history(
        friend=request.get("friend"),
        number=request.get("number", 100),
        capture_screen=request.get("capture_screen", True),
        folder_path=request.get("folder_path")
    )

@router.post(
    "/pywechat/friend/clear_chat_history",
    operation_id="[pywechat]清空好友聊天记录",
    response_model=APIResponse,
    summary="pywechat: 清空好友聊天记录"
)
async def pywechat_clear_friend_chat_history(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 清空好友聊天记录"""
    return service.clear_friend_chat_history(
        friend=request.get("friend")
    )

@router.post(
    "/pywechat/friend/tickle",
    operation_id="[pywechat]拍一拍好友",
    response_model=APIResponse,
    summary="pywechat: 拍一拍好友"
)
async def pywechat_tickle_friend(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 拍一拍好友"""
    return service.tickle_friend(
        friend=request.get("friend")
    )

@router.post(
    "/pywechat/group/chat_history",
    operation_id="[pywechat]获取群聊聊天记录",
    response_model=APIResponse,
    summary="pywechat: 获取群聊聊天记录"
)
async def pywechat_get_group_chat_history(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 获取群聊聊天记录"""
    return service.get_group_chat_history(
        friend=request.get("friend"),
        number=request.get("number", 100),
        capture_screen=request.get("capture_screen", True),
        folder_path=request.get("folder_path")
    )

@router.post(
    "/pywechat/group/clear_chat_history",
    operation_id="[pywechat]清空群聊聊天记录",
    response_model=APIResponse,
    summary="pywechat: 清空群聊聊天记录"
)
async def pywechat_clear_group_chat_history(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 清空群聊聊天记录"""
    return service.clear_group_chat_history(
        group_name=request.get("group_name")
    )

@router.post(
    "/pywechat/listen_on_chat",
    operation_id="[pywechat]监听聊天窗口",
    response_model=APIResponse,
    summary="pywechat: 监听某个聊天窗口（自动保存聊天图片与文件）"
)
async def pywechat_listen_on_chat(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 监听某个聊天窗口（自动保存聊天图片与文件）"""
    return service.listen_on_chat(
        friend=request.get("friend"),
        duration=request.get("duration", "5min"),
        photo_folder=request.get("photo_folder"),
        file_folder=request.get("file_folder")
    )

@router.post(
    "/pywechat/save_photos",
    operation_id="[pywechat]保存聊天图片",
    response_model=APIResponse,
    summary="pywechat: 保存与某个好友或群聊的聊天图片"
)
async def pywechat_save_photos(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 保存与某个好友或群聊的聊天图片"""
    return service.save_photos(
        friend=request.get("friend"),
        number=request.get("number", 10),
        save_method=request.get("save_method", 1),
        folder_path=request.get("folder_path")
    )

@router.get(
    "/pywechat/current_wxid",
    operation_id="[pywechat]获取当前wxid",
    response_model=APIResponse,
    summary="pywechat: 获取本机当前登录微信的wxid"
)
async def pywechat_find_current_wxid(
    service: WeChatService = Depends()
):
    """pywechat: 获取本机当前登录微信的wxid"""
    return service.find_current_wxid()

@router.post(
    "/pywechat/pull_messages",
    operation_id="[pywechat]获取聊天记录",
    response_model=APIResponse,
    summary="pywechat: 从聊天界面获取聊天记录"
)
async def pywechat_pull_messages(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 从聊天界面获取聊天记录"""
    return service.pull_messages(
        friend=request.get("friend"),
        number=request.get("number", 100)
    )

@router.post(
    "/pywechat/pull_latest_message",
    operation_id="[pywechat]获取最新一条聊天记录",
    response_model=APIResponse,
    summary="pywechat: 从聊天界面获取最新一条聊天记录"
)
async def pywechat_pull_latest_message(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 从聊天界面获取最新一条聊天记录"""
    return service.pull_latest_message(
        friend=request.get("friend")
    )

# ===== 1.9.7版本新增功能 (pywechat) =====

@router.get(
    "/pywechat/session_list",
    operation_id="[pywechat]获取会话列表",
    response_model=APIResponse,
    summary="pywechat: 获取会话列表内的所有聊天好友"
)
async def pywechat_dump_session_list(
    service: WeChatService = Depends()
):
    """pywechat: 获取会话列表内的所有聊天好友"""
    return service.dump_session_list()

@router.post(
    "/pywechat/recent_session_list",
    operation_id="[pywechat]获取最近会话",
    response_model=APIResponse,
    summary="pywechat: 获取会话列表中最近的聊天好友"
)
async def pywechat_dump_recent_session_list(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 获取会话列表中最近的聊天好友"""
    return service.dump_recent_session_list(
        recent=request.get("recent", "today")
    )

@router.post(
    "/pywechat/recent_chat_history",
    operation_id="[pywechat]获取最近聊天记录",
    response_model=APIResponse,
    summary="pywechat: 获取最近的聊天记录"
)
async def pywechat_get_recent_chat_history(
    request: dict,
    service: WeChatService = Depends()
):
    """pywechat: 获取最近的聊天记录"""
    return service.get_recent_chat_history(
        friend=request.get("friend"),
        recent=request.get("recent", "today")
    )

@router.get(
    "/pywechat/status",
    operation_id="[pywechat]获取状态",
    response_model=APIResponse,
    summary="pywechat: 获取pywechat加载状态"
)
async def pywechat_get_status(
    service: WeChatService = Depends()
):
    """pywechat: 获取pywechat加载状态"""
    return service.get_pywechat_status()

# ===== 朋友圈功能 (pywechat) =====

@router.get(
    "/pywechat/moments/dump_all",
    operation_id="[pywechat]获取朋友圈所有内容",
    response_model=APIResponse,
    summary="pywechat: 获取朋友圈所有内容"
)
async def pywechat_dump_moments(
    service: WeChatService = Depends()
):
    """pywechat: 获取朋友圈所有内容"""
    return service.dump_moments()

@router.post(
    "/pywechat/moments/dump_recent",
    operation_id="[pywechat]获取最近朋友圈内容",
    response_model=APIResponse,
    summary="pywechat: 获取最近朋友圈内容"
)
async def pywechat_dump_recent_moments(
    request: DumpRecentMomentsRequest,
    service: WeChatService = Depends()
):
    """pywechat: 获取最近朋友圈内容"""
    return service.dump_recent_moments(
        recent=request.recent
    )

@router.post(
    "/pywechat/moments/export_images",
    operation_id="[pywechat]导出最近朋友圈图片",
    response_model=APIResponse,
    summary="pywechat: 导出最近朋友圈图片"
)
async def pywechat_export_recent_moments_images(
    request: ExportRecentMomentsImagesRequest,
    service: WeChatService = Depends()
):
    """pywechat: 导出最近朋友圈图片"""
    return service.export_recent_moments_images(
        recent=request.recent,
        folder_path=request.folder_path
    )

@router.post(
    "/pywechat/moments/export_videos",
    operation_id="[pywechat]导出最近朋友圈视频",
    response_model=APIResponse,
    summary="pywechat: 导出最近朋友圈视频"
)
async def pywechat_export_recent_moments_videos(
    request: ExportRecentMomentsVideosRequest,
    service: WeChatService = Depends()
):
    """pywechat: 导出最近朋友圈视频"""
    return service.export_recent_moments_videos(
        recent=request.recent,
        folder_path=request.folder_path
    )

@router.post(
    "/pywechat/moments/export_cache",
    operation_id="[pywechat]导出朋友圈缓存",
    response_model=APIResponse,
    summary="pywechat: 导出指定年份月份的朋友圈图片与视频本地缓存"
)
async def pywechat_export_moments_cache(
    request: ExportMomentsCacheRequest,
    service: WeChatService = Depends()
):
    """pywechat: 导出指定年份月份的朋友圈图片与视频本地缓存"""
    return service.export_moments_cache(
        year=request.year,
        month=request.month,
        folder_path=request.folder_path
    )