from typing import Optional
from pathlib import Path
from app.models.response import APIResponse
from .wechat_service import get_wechat_subwin
from .init import WeChat, WxClient, HumanMessage
from .file_service import FileService
from app.utils.config import settings
import hashlib
import os
from datetime import datetime

def get_wechat(wxname: str) -> 'WeChat':
    """获取微信实例"""
    if (not wxname) and WxClient:
        wx = list(WxClient.values())[0]
    elif wxname in WxClient:
        wx = WxClient[wxname]
    else:
        wx = WeChat(nickname=wxname)
    return wx

class ChatService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatService, cls).__new__(cls)
        return cls._instance
    
    def __repr__(self):
        return f'<Chat Service object at {id(self)}>'
    
    def __init__(self):
        # 延迟初始化FileService，避免数据库连接问题
        self._file_service = None
    
    @property
    def file_service(self):
        """延迟获取FileService实例"""
        if self._file_service is None:
            self._file_service = FileService()
        return self._file_service
    
    def _save_image_message(self, image_msg, who: str) -> Optional[str]:
        """保存图片消息到本地
        
        Args:
            image_msg: ImageMessage对象
            who: 聊天对象名称
            
        Returns:
            Optional[str]: 保存的图片路径，失败返回None
        """
        try:
            # 创建图片保存目录到static/images目录下，使其可以通过URL访问
            base_dir = Path(__file__).parent.parent.parent / "static" / "images" / who
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载图片
            image_path = image_msg.download(dir_path=str(base_dir))
            
            if isinstance(image_path, Path):
                # 返回相对路径，用于URL访问
                relative_path = f"/static/images/{who}/{image_path.name}"
                return relative_path
            else:
                # 如果download返回的是响应对象，尝试获取路径
                if hasattr(image_path, 'path'):
                    path_obj = Path(image_path.path)
                    relative_path = f"/static/images/{who}/{path_obj.name}"
                    return relative_path
                return None
        except Exception as e:
            print(f"保存图片消息失败: {e}")
            return None

    def send_message(
        self,
        msg: str,
        who: str,
        clear: bool = True,
        at: Optional[str | list] = None,
        wxname: Optional[str] = None
    ) -> APIResponse:
        subwin = get_wechat_subwin(wxname, who)
        if subwin:
            result = subwin.SendMsg(msg=msg, clear=clear, at=at)
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        else:
            return APIResponse(success=False, message='找不到该聊天窗口')
        
    def get_all_message(
            self,
            who: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取微信子窗口所有消息
        
        对于图片消息(type=image)，会自动保存到本地，并在返回的消息中添加image_path字段
        对于引用消息(type=quote)，会添加quote_content属性
        对于语音消息(type=voice)，会自动转换为文本，并在返回的消息中添加voice_text字段
        """
        subwin = get_wechat_subwin(wxname, who)
        if subwin:
            result = subwin.ChatInfo()
            msgs = subwin.GetAllMessage()
            # 确保消息包含sender字段，并处理图片消息、引用消息和语音消息
            result['msg'] = []
            for msg in msgs:
                msg_info = msg.info
                if 'sender' not in msg_info:
                    msg_info['sender'] = getattr(msg, 'sender', '未知')
                
                # 处理图片消息
                if hasattr(msg, 'type') and msg.type == 'image':
                    # 保存图片到本地
                    image_path = self._save_image_message(msg, who)
                    if image_path:
                        msg_info['image_path'] = image_path
                
                # 处理引用消息，确保包含quote_content属性
                if hasattr(msg, 'type') and msg.type == 'quote' and 'quote_content' not in msg_info:
                    # 尝试获取引用内容
                    if hasattr(msg, 'quote_content'):
                        msg_info['quote_content'] = msg.quote_content
                    elif hasattr(msg, 'content'):
                        # 如果没有quote_content属性，则使用content作为引用内容
                        msg_info['quote_content'] = msg.content
                
                # 处理语音消息，转换为文本
                if hasattr(msg, 'type') and msg.type == 'voice':
                    try:
                        if hasattr(msg, 'to_text'):
                            voice_text = msg.to_text()
                            msg_info['voice_text'] = voice_text
                    except Exception as voice_error:
                        print(f"语音消息转换失败: {str(voice_error)}")
                        msg_info['voice_text'] = None
                
                result['msg'].append(msg_info)
            return APIResponse(success=True, message='', data=result)
        else:
            return APIResponse(success=False, message='找不到该聊天窗口')
        
    def get_new_message(
            self,
            who: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取微信子窗口新消息
        
        对于图片消息(type=image)，会自动保存到本地，并在返回的消息中添加image_path字段
        对于引用消息(type=quote)，会添加quote_content属性
        对于语音消息(type=voice)，会自动转换为文本，并在返回的消息中添加voice_text字段
        """
        subwin = get_wechat_subwin(wxname, who)
        if subwin:
            result = subwin.ChatInfo()
            msgs = subwin.GetNewMessage()
            # 确保消息包含sender字段
            result['msg'] = []
            for msg in msgs:
                msg_info = msg.info
                if 'sender' not in msg_info:
                    msg_info['sender'] = getattr(msg, 'sender', '未知')
                
                # 处理图片消息
                if hasattr(msg, 'type') and msg.type == 'image':
                    # 保存图片到本地
                    image_path = self._save_image_message(msg, who)
                    if image_path:
                        msg_info['image_path'] = image_path
                
                # 处理引用消息，确保包含quote_content属性
                if hasattr(msg, 'type') and msg.type == 'quote' and 'quote_content' not in msg_info:
                    # 尝试获取引用内容
                    if hasattr(msg, 'quote_content'):
                        msg_info['quote_content'] = msg.quote_content
                    elif hasattr(msg, 'content'):
                        # 如果没有quote_content属性，则使用content作为引用内容
                        msg_info['quote_content'] = msg.content
                
                # 处理语音消息，转换为文本
                if hasattr(msg, 'type') and msg.type == 'voice':
                    try:
                        if hasattr(msg, 'to_text'):
                            voice_text = msg.to_text()
                            msg_info['voice_text'] = voice_text
                    except Exception as voice_error:
                        print(f"语音消息转换失败: {str(voice_error)}")
                        msg_info['voice_text'] = None
                
                result['msg'].append(msg_info)
            return APIResponse(success=True, message='', data=result)
        else:
            return APIResponse(success=False, message='找不到该聊天窗口')
        
    def _get_msg_by_id(
            self,
            msg_id: str,
            who: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        subwin = get_wechat_subwin(wxname, who)
        if subwin:
            msg = subwin.GetMessageById(msg_id)
            return msg
        else:
            return None
        
    def send_quote_by_id(
            self,
            content: str,
            msg_id: str,
            who: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """根据ID发送引用消息"""
        try:
            msg = self._get_msg_by_id(msg_id, who, wxname)
            if msg is not None:
                if msg.attr in ('self', 'friend'):
                    result = msg.quote(content)
                    # 处理返回结果，确保包含quote_content属性
                    if result and result.get('data'):
                        # 确保返回的消息对象包含quote_content属性
                        if isinstance(result['data'], dict) and 'msg' in result['data']:
                            for msg_data in result['data']['msg']:
                                if msg_data.get('type') == 'quote' and 'quote_content' not in msg_data:
                                    # 添加quote_content属性，值为被引用消息的内容
                                    msg_data['quote_content'] = msg.content
                    return APIResponse(success=bool(result), message=result.get('message', ''), data=result.get('data', {}))
                else:
                    return APIResponse(success=False, message=f'当前消息不可引用(消息类型："{msg.type}"  内容："{msg.content}")')
            else:
                return APIResponse(success=False, message=f"消息不存在：{msg_id}")
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def get_chat_info(self, who: str, wxname: Optional[str] = None) -> APIResponse:
        """获取聊天信息"""
        try:
            subwin = get_wechat_subwin(wxname, who)
            result = subwin.ChatInfo()
            return APIResponse(success=True, message='', data=result)
        except Exception as e:
            return APIResponse(success=False, message=str(e))
        
    def close_sub_window(self, who: str, wxname: Optional[str] = None) -> APIResponse:
        try:
            subwin = get_wechat_subwin(wxname, who)
            if subwin is None:
                return APIResponse(success=False, message=f'窗口不存在：{who}')
            subwin.Close()
            return APIResponse(success=True, message='')

        except Exception as e:
            return APIResponse(success=False, message=str(e))
