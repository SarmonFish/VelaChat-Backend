from app.utils.wx_package_manager import has_feature
from app.utils.pywechat_manager import (
    get_pywechat_class, get_pywechat_function, 
    has_pywechat_function, is_pywechat_loaded
)
from typing import Optional, Union, List
from pathlib import Path
from app.models.response import APIResponse
from app.services.file_service import FileService
from .init import WeChat, WxClient, Chat, HumanMessage
from app.utils.config import settings
import os

def get_wechat(wxname: str) -> WeChat:
    """获取微信实例
    
    Args:
        wxname: 微信客户端名称
        
    Returns:
        WeChat实例
    """
    if (not wxname) and WxClient:
        wx = list(WxClient.values())[0]
    elif wxname in WxClient:
        wx = WxClient[wxname]
    else:
        wx = WeChat(nickname=wxname)
    return wx

def get_wechat_subwin(wxname: str, who: str) -> Optional[Chat]:
    """获取微信子窗口
    
    Args:
        wxname: 微信客户端名称
        who: 聊天对象
        
    Returns:
        Chat实例或None
    """
    wx = get_wechat(wxname)
    subwins = wx.GetAllSubWindow()
    if targets := [i for i in subwins if i.who == who]:
        return targets[0]
    else:
        return None

class WeChatService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeChatService, cls).__new__(cls)
        return cls._instance
    
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
            who: Optional[str] = None, 
            clear: bool = True, 
            at: Optional[str | list] = None, 
            exact: bool = False,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """发送消息"""
        try:
            wx = get_wechat(wxname)
            result = wx.SendMsg(msg=msg, who=who, clear=clear, at=at, exact=exact)
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def send_file(
            self,
            file_id: str,
            who: Optional[str] = None,
            exact: bool = False,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """发送文件"""
        try:
            # 获取文件信息
            file_service = FileService()
            file_info = file_service.get_file(file_id)
            if not file_info:
                return APIResponse(success=False, message="文件不存在")
            
            # 检查文件是否存在
            if not file_info.file_path or not os.path.exists(file_info.file_path):
                return APIResponse(success=False, message="文件路径不存在")
            
            # 发送文件
            wx = get_wechat(wxname)
            result = wx.SendFiles(filepath=file_info.file_path, who=who, exact=exact)
            
            if result:
                return APIResponse(
                    success=True, 
                    message="文件发送成功", 
                    data={
                        "file_id": file_id,
                        "filename": file_info.filename,
                        "file_path": file_info.file_path,
                        "recipient": who
                    }
                )
            else:
                return APIResponse(success=False, message="文件发送失败")
                
        except Exception as e:
            return APIResponse(success=False, message=f"发送文件时发生错误: {str(e)}")

    def chat_with(
            self, 
            who: str,
            exact: bool = False,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """切换聊天窗口"""
        try:
            wx = get_wechat(wxname)
            result = wx.ChatWith(who=who, exact=exact)
            if result:
                return APIResponse(success=True, message='主窗口聊天切换成功', data={'chatname': result})
            else:
                return APIResponse(success=False, message='主窗口聊天切换失败')
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def get_all_sub_window(
            self,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取所有子窗口"""
        try:
            wx = get_wechat(wxname)
            result = wx.GetAllSubWindow()
            data = [{'name': i.who, 'type': i.chat_type} for i in result]
            return APIResponse(success=True, message='', data=data)
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def get_all_message(
            self,
            who: str,
            auto_save_image: bool = True,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取所有消息
        
        对于图片消息(type=image)，会根据auto_save_image参数决定是否自动保存到本地
        对于引用消息(type=quote)，会添加quote_content属性
        对于语音消息(type=voice)，会自动转换为文本，并在返回的消息中添加voice_text字段
        """
        try:
            wx = get_wechat(wxname)
            if who:
                if not wx.ChatWith(who):
                    return APIResponse(success=False, message='找不到聊天窗口')
            result = wx.ChatInfo()
            msgs = wx.GetAllMessage()
            # 确保消息包含sender字段，并处理图片消息、引用消息和语音消息
            result['msg'] = []
            for msg in msgs:
                msg_info = msg.info
                # 确保sender字段存在
                if 'sender' not in msg_info:
                    msg_info['sender'] = getattr(msg, 'sender', '未知')
                
                # 处理图片消息
                if hasattr(msg, 'type') and msg.type == 'image':
                    # 根据auto_save_image参数决定是否保存图片到本地
                    if auto_save_image:
                        image_path = self._save_image_message(msg, who)
                        if image_path:
                            msg_info['image_path'] = image_path
                    else:
                        # 如果不自动保存，只提供图片的基本信息
                        msg_info['image_saved'] = False
                
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
                            print(f"语音消息已转换为文本: {voice_text}")
                    except Exception as voice_error:
                        print(f"语音消息转换失败: {str(voice_error)}")
                        msg_info['voice_text'] = None
                
                result['msg'].append(msg_info)
            return APIResponse(success=True, message='', data=result)
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    # wxautox特有功能
    def send_url_card(
            self,
            url: str,
            friends: Union[str, List[str]],
            timeout: int = 10,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """发送URL卡片（wxautox特有）"""
        if not has_feature("send_url_card"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.SendUrlCard(url=url, friends=friends, timeout=timeout)
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        except Exception as e:
            return APIResponse(success=False, message=str(e))
        
    def add_listen_chat(
            self,
            who: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """添加监听聊天"""
        
        try:
            wx = get_wechat(wxname)
            if who in [i.who for i in wx.GetAllSubWindow()]:
                return APIResponse(success=False, message='该聊天已监听中')
            wxapi = wx._api if hasattr(wx, '_api') else wx.core
            subwin = wxapi.open_separate_window(who)
            if subwin is None:
                return APIResponse(success=False, message='找不到聊天窗口')
            return APIResponse(success=True, message=f'{who} 聊天窗口已添加监听')
        except Exception as e:
            return APIResponse(success=False, message=str(e))
        
    def get_next_new_message(
            self,
            filter_mute: bool = False,
            auto_save_image: bool = True,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取下一个新消息
        
        对于图片消息(type=image)，会根据auto_save_image参数决定是否自动保存到本地
        对于引用消息(type=quote)，会添加quote_content属性
        对于语音消息(type=voice)，会自动转换为文本，并在返回的消息中添加voice_text字段
        """
        
        try:
            wx = get_wechat(wxname)
            result = wx.GetNextNewMessage(filter_mute=filter_mute)
            if result:
                # 确保消息包含sender字段，并处理图片消息、引用消息和语音消息
                processed_msgs = []
                for msg in result['msg']:
                    msg_info = msg.info
                    if 'sender' not in msg_info:
                        msg_info['sender'] = getattr(msg, 'sender', '未知')
                    
                    # 处理图片消息
                    if hasattr(msg, 'type') and msg.type == 'image':
                        # 获取聊天对象名称
                        who = msg_info.get('name', 'unknown')
                        # 根据auto_save_image参数决定是否保存图片到本地
                        if auto_save_image:
                            image_path = self._save_image_message(msg, who)
                            if image_path:
                                msg_info['image_path'] = image_path
                        else:
                            # 如果不自动保存，只提供图片的基本信息
                            msg_info['image_saved'] = False
                    
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
                    
                    processed_msgs.append(msg_info)
                result['msg'] = processed_msgs
            return APIResponse(success=True, message='', data=result)
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def send_quote_by_id(
            self,
            content: str,
            msg_id: str,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """根据ID发送引用消息"""
        try:
            wx = get_wechat(wxname)
            if (msg := wx.GetMessageById(msg_id)) is not None:
                if isinstance(msg, HumanMessage):
                    result = msg.quote(text=content)
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

    def get_new_friends(
            self,
            acceptable: bool = True,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取新朋友（wxautox特有）"""
        if not has_feature("get_new_friends"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.GetNewFriends(acceptable=acceptable)
            return APIResponse(success=True, message='', data=result)
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def accept_new_friend(
            self,
            new_friend_id: str,
            remark: str = '',
            tags: List[str] = [],
            wxname: Optional[str] = None
        ) -> APIResponse:
        """接受新朋友（wxautox特有）"""
        if not has_feature("accept_new_friend"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.AcceptNewFriend(new_friend_id=new_friend_id, remark=remark, tags=tags)
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def switch_to_chat_page(
            self,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """切换到聊天页面（wxautox特有）"""
        if not has_feature("switch_to_chat_page"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.SwitchToChat()
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def switch_to_contact_page(
            self,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """切换到联系人页面（wxautox特有）"""
        if not has_feature("switch_to_contact_page"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.SwitchToContactPage()
            return APIResponse(success=bool(result), message=result['message'], data=result['data'])
        except Exception as e:
            return APIResponse(success=False, message=str(e))
        
    def is_online(
            self,
            wxname: Optional[str] = None
        ) -> APIResponse:
        if not has_feature("is_online"):
            return APIResponse(success=False, message="此功能需要wxautox版本支持")
        
        try:
            wx = get_wechat(wxname)
            result = wx.IsOnline()
            if result:
                return APIResponse(success=True, message='在线', data={'status': 'online', 'online': True})
            else:
                return APIResponse(success=True, message='离线', data={'status': 'offline', 'online': False})
        except Exception as e:
            return APIResponse(success=False, message=str(e))

    def get_sessions(
            self,
            wxname: Optional[str] = None
        ) -> APIResponse:
        """获取当前会话列表
        
        返回会话列表，包含会话名、时间、内容、是否免打扰、是否有新消息、新消息数量等信息
        """
        try:
            wx = get_wechat(wxname)
            sessions = wx.GetSession()
            
            # 将SessionElement转换为字典格式
            session_list = []
            for session in sessions:
                session_info = {
                    'name': session.name,
                    'time': session.time,
                    'content': session.content,
                    'ismute': session.ismute,
                    'isnew': session.isnew,
                    'new_count': session.new_count,
                    'info': session.info
                }
                session_list.append(session_info)
            
            return APIResponse(
                success=True, 
                message='获取会话列表成功', 
                data={
                    'sessions': session_list,
                    'total_count': len(session_list)
                }
            )
        except Exception as e:
            return APIResponse(success=False, message=f'获取会话列表失败: {str(e)}')

    # ===== pywechat 集成功能 =====
    
    def send_message_to_friend(self, friend: str, message: str, 
                             tickle: bool = False, search_pages: int = 0) -> APIResponse:
        """给单个好友发送单条消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Messages = get_pywechat_class('Messages')
            result = Messages.send_message_to_friend(
                friend=friend, message=message, 
                tickle=tickle, search_pages=search_pages,
                close_wechat=False, is_maximize=False
            )
            return APIResponse(success=True, message="消息发送成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"发送消息失败: {str(e)}")
    
    def send_messages_to_friend(self, friend: str, messages: List[str],
                              tickle: bool = False, search_pages: int = 0) -> APIResponse:
        """给单个好友发送多条消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Messages = get_pywechat_class('Messages')
            result = Messages.send_messages_to_friend(
                friend=friend, messages=messages,
                tickle=tickle, search_pages=search_pages,
                close_wechat=False, is_maximize=False
            )
            return APIResponse(success=True, message="多条消息发送成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"发送多条消息失败: {str(e)}")
    
    def send_message_to_friends(self, friends: List[str], message: List[str], 
                              tickle: List[bool] = None) -> APIResponse:
        """给多个好友分别发送单条消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Messages = get_pywechat_class('Messages')
            kwargs = {
                'friends': friends,
                'message': message,
                'close_wechat': False,
                'is_maximize': False
            }
            if tickle is not None:
                kwargs['tickle'] = tickle
            
            result = Messages.send_message_to_friends(**kwargs)
            return APIResponse(success=True, message="批量消息发送成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"批量消息发送失败: {str(e)}")
    
    def send_messages_to_friends(self, friends: List[str], messages: List[List[str]]) -> APIResponse:
        """给多个好友分别发送多条消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Messages = get_pywechat_class('Messages')
            result = Messages.send_messages_to_friends(
                friends=friends, messages=messages,
                close_wechat=False, is_maximize=False
            )
            return APIResponse(success=True, message="批量多条消息发送成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"批量多条消息发送失败: {str(e)}")
    
    def forward_message(self, friends: List[str], message: str, search_pages: int = 0) -> APIResponse:
        """转发消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Messages = get_pywechat_class('Messages')
            result = Messages.forward_message(
                friends=friends, message=message, search_pages=search_pages
            )
            return APIResponse(success=True, message="消息转发成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"消息转发失败: {str(e)}")
    
    def check_new_message(self, duration: str = '1min') -> APIResponse:
        """检查（监听）新消息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            check_new_message_func = get_pywechat_function('check_new_message')
            result = check_new_message_func(duration=duration)
            return APIResponse(success=True, message="检查新消息成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"检查新消息失败: {str(e)}")
    
    def get_friends_names(self) -> APIResponse:
        """获取所有好友的备注与名称 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Contacts = get_pywechat_class('Contacts')
            result = Contacts.get_friends_names(close_wechat=False)
            
            # 获取完成后打开文件传输助手的聊天界面
            try:
                Tools = get_pywechat_class('Tools')
                Tools.open_dialog_window(friend='文件传输助手')
            except Exception as open_error:
                print(f"打开聊天界面失败: {str(open_error)}")
            
            return APIResponse(success=True, message="获取好友名称成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取好友名称失败: {str(e)}")
    
    def get_friends_info(self) -> APIResponse:
        """获取所有好友昵称、备注与微信号 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Contacts = get_pywechat_class('Contacts')
            result = Contacts.get_friends_info()
            return APIResponse(success=True, message="获取好友信息成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取好友信息失败: {str(e)}")
    
    def get_friends_detail(self) -> APIResponse:
        """获取所有好友详细信息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Contacts = get_pywechat_class('Contacts')
            result = Contacts.get_friends_detail()
            return APIResponse(success=True, message="获取好友详情成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取好友详情失败: {str(e)}")
    
    def get_groups_info(self) -> APIResponse:
        """获取所有群聊信息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Contacts = get_pywechat_class('Contacts')
            result = Contacts.get_groups_info()
            return APIResponse(success=True, message="获取群聊信息成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取群聊信息失败: {str(e)}")
    
    def get_friend_chat_history(self, friend: str, number: int = 100, 
                              capture_screen: bool = True, folder_path: str = None) -> APIResponse:
        """获取好友聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            FriendSettings = get_pywechat_class('FriendSettings')
            kwargs = {
                'friend': friend,
                'number': number,
                'capture_screen': capture_screen
            }
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = FriendSettings.get_chat_history(**kwargs)
            return APIResponse(success=True, message="获取好友聊天记录成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取好友聊天记录失败: {str(e)}")
    
    def clear_friend_chat_history(self, friend: str) -> APIResponse:
        """清空好友聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            FriendSettings = get_pywechat_class('FriendSettings')
            result = FriendSettings.clear_friend_chat_history(friend=friend)
            return APIResponse(success=True, message="清空好友聊天记录成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"清空好友聊天记录失败: {str(e)}")
    
    def tickle_friend(self, friend: str) -> APIResponse:
        """拍一拍好友 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            FriendSettings = get_pywechat_class('FriendSettings')
            result = FriendSettings.tickle_friend(friend=friend)
            return APIResponse(success=True, message="拍一拍好友成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"拍一拍好友失败: {str(e)}")
    
    def get_group_chat_history(self, friend: str, number: int = 100, 
                             capture_screen: bool = True, folder_path: str = None) -> APIResponse:
        """获取群聊聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            GroupSettings = get_pywechat_class('GroupSettings')
            kwargs = {
                'friend': friend,
                'number': number,
                'capture_screen': capture_screen
            }
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = GroupSettings.get_chat_history(**kwargs)
            return APIResponse(success=True, message="获取群聊聊天记录成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取群聊聊天记录失败: {str(e)}")
    
    def clear_group_chat_history(self, group_name: str) -> APIResponse:
        """清空群聊聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            GroupSettings = get_pywechat_class('GroupSettings')
            result = GroupSettings.clear_group_chat_history(group_name=group_name)
            return APIResponse(success=True, message="清空群聊聊天记录成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"清空群聊聊天记录失败: {str(e)}")
    
    def listen_on_chat(self, friend: str, duration: str = '5min', 
                      photo_folder: str = None, file_folder: str = None) -> APIResponse:
        """监听某个聊天窗口（自动保存聊天图片与文件） (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            listen_on_chat_func = get_pywechat_function('listen_on_chat')
            kwargs = {'friend': friend, 'duration': duration}
            if photo_folder:
                kwargs['photo_folder'] = photo_folder
            if file_folder:
                kwargs['file_folder'] = file_folder
            
            result = listen_on_chat_func(**kwargs)
            return APIResponse(success=True, message="监听聊天窗口成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"监听聊天窗口失败: {str(e)}")
    
    def save_photos(self, friend: str, number: int = 10, save_method: int = 1, 
                   folder_path: str = None) -> APIResponse:
        """保存与某个好友或群聊的聊天图片 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            save_photos_func = get_pywechat_function('save_photos')
            kwargs = {
                'friend': friend,
                'number': number,
                'save_method': save_method
            }
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = save_photos_func(**kwargs)
            return APIResponse(success=True, message="保存聊天图片成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"保存聊天图片失败: {str(e)}")
    
    def find_current_wxid(self) -> APIResponse:
        """获取本机当前登录微信的wxid (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Tools = get_pywechat_class('Tools')
            result = Tools.find_current_wxid()
            return APIResponse(success=True, message="获取wxid成功", data={'wxid': result})
        except Exception as e:
            return APIResponse(success=False, message=f"获取wxid失败: {str(e)}")
    
    def pull_messages(self, friend: str, number: int = 100) -> APIResponse:
        """从聊天界面获取聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            Tools = get_pywechat_class('Tools')
            contents, senders, types = Tools.pull_messages(
                friend=friend, 
                number=number,
                chats_only=False,
                is_maximize=False,
                close_wechat=False
            )
            return APIResponse(
                success=True, 
                message="获取聊天记录成功", 
                data={
                    'contents': contents,
                    'senders': senders,
                    'types': types
                }
            )
        except Exception as e:
            return APIResponse(success=False, message=f"获取聊天记录失败: {str(e)}")
    
    def pull_latest_message(self, friend: str) -> APIResponse:
        """从聊天界面获取最新一条聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            from pywechat import Tools
            from pywechat.Uielements import Lists
            
            Lists = Lists(language=Tools.language_detector())
            edit_area, main_window = Tools.open_dialog_window(friend=friend)
            chatList = main_window.child_window(**Lists.FriendChatList)
            contents, senders = Tools.pull_latest_message(chatList)
            
            return APIResponse(
                success=True, 
                message="获取最新消息成功", 
                data={
                    'contents': contents,
                    'senders': senders
                }
            )
        except Exception as e:
            return APIResponse(success=False, message=f"获取最新消息失败: {str(e)}")
    
    # ===== 1.9.7版本新增功能 (pywechat)
    
    def dump_session_list(self) -> APIResponse:
        """获取会话列表内的所有聊天好友 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            dump_session_list_func = get_pywechat_function('dump_session_list')
            result = dump_session_list_func()
            return APIResponse(success=True, message="获取会话列表成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取会话列表失败: {str(e)}")
    
    def dump_recent_session_list(self, recent: str = 'today') -> APIResponse:
        """获取会话列表中最近的聊天好友 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            dump_recent_session_list_func = get_pywechat_function('dump_recent_session_list')
            result = dump_recent_session_list_func(recent=recent)
            return APIResponse(success=True, message="获取最近会话成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取最近会话失败: {str(e)}")
    
    def get_recent_chat_history(self, friend: str, recent: str = 'today') -> APIResponse:
        """获取最近的聊天记录 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            get_recent_chat_history_func = get_pywechat_function('get_recent_chat_history')
            result = get_recent_chat_history_func(recent=recent,friend=friend)
            return APIResponse(success=True, message="获取最近聊天记录成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取最近聊天记录失败: {str(e)}")
    
    def get_pywechat_status(self) -> APIResponse:
        """获取pywechat加载状态"""
        return APIResponse(
            success=is_pywechat_loaded(),
            message="pywechat已加载" if is_pywechat_loaded() else "pywechat未加载",
            data={
                'loaded': is_pywechat_loaded(),
                'available_functions': [
                    'send_message_to_friend', 'send_messages_to_friend',
                    'send_message_to_friends', 'send_messages_to_friends',
                    'forward_message', 'check_new_message',
                    'get_friends_names', 'get_friends_info', 'get_friends_detail',
                    'get_groups_info', 'get_friend_chat_history', 'clear_friend_chat_history',
                    'tickle_friend', 'get_group_chat_history', 'clear_group_chat_history',
                    'listen_on_chat', 'save_photos', 'find_current_wxid',
                    'pull_messages', 'pull_latest_message',
                    'dump_session_list', 'dump_recent_session_list', 'get_recent_chat_history',
                    'dump_moments', 'dump_recent_moments', 'export_recent_moments_images',
                    'export_recent_moments_videos', 'export_moments_cache'
                ]
            }
        )

    # ===== 朋友圈功能 (pywechat)

    def dump_moments(self) -> APIResponse:
        """获取朋友圈所有内容 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            dump_moments_func = get_pywechat_function('dump_moments')
            result = dump_moments_func()
            return APIResponse(success=True, message="获取朋友圈所有内容成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取朋友圈所有内容失败: {str(e)}")

    def dump_recent_moments(self, recent: str = 'today') -> APIResponse:
        """获取最近朋友圈内容 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            dump_recent_moments_func = get_pywechat_function('dump_recent_moments')
            result = dump_recent_moments_func(recent=recent)
            return APIResponse(success=True, message="获取最近朋友圈内容成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"获取最近朋友圈内容失败: {str(e)}")

    def export_recent_moments_images(self, recent: str = 'today', folder_path: str = None) -> APIResponse:
        """导出最近朋友圈图片 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            export_recent_moments_images_func = get_pywechat_function('export_recent_moments_images')
            kwargs = {'recent': recent}
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = export_recent_moments_images_func(**kwargs)
            return APIResponse(success=True, message="导出最近朋友圈图片成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"导出最近朋友圈图片失败: {str(e)}")

    def export_recent_moments_videos(self, recent: str = 'today', folder_path: str = None) -> APIResponse:
        """导出最近朋友圈视频 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            export_recent_moments_videos_func = get_pywechat_function('export_recent_moments_videos')
            kwargs = {'recent': recent}
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = export_recent_moments_videos_func(**kwargs)
            return APIResponse(success=True, message="导出最近朋友圈视频成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"导出最近朋友圈视频失败: {str(e)}")

    def export_moments_cache(self, year: int, month: int, folder_path: str = None) -> APIResponse:
        """导出指定年份月份的朋友圈图片与视频本地缓存 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            export_moments_cache_func = get_pywechat_function('export_moments_cache')
            kwargs = {'year': year, 'month': month}
            if folder_path:
                kwargs['folder_path'] = folder_path
            
            result = export_moments_cache_func(**kwargs)
            return APIResponse(success=True, message="导出朋友圈缓存成功", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"导出朋友圈缓存失败: {str(e)}")

    def check_my_info(self) -> APIResponse:
        """获取微信个人信息 (pywechat)"""
        if not is_pywechat_loaded():
            return APIResponse(success=False, message="pywechat包未加载")
        
        try:
            from pywechat import open_wechat
            from pywechat import Tools
            from pywechat.Uielements import Buttons
            
            # 检测语言并创建Buttons对象
            Buttons = Buttons(language=Tools.language_detector())
            
            # 打开微信主窗口
            main_window = open_wechat()
            
            # 获取我的昵称
            myname = main_window.child_window(**Buttons.MySelfButton).window_text()
            
            # 获取wxid
            wxid = Tools.find_current_wxid()
            
            # 不关闭微信窗口，保持窗口打开状态
            # main_window.close()  # 注释掉关闭窗口的操作
            
            # 返回昵称和wxid
            return APIResponse(
                success=True, 
                message="获取微信个人信息成功", 
                data={
                    'nickname': myname,
                    'wxid': wxid
                }
            )
        except Exception as e:
            return APIResponse(success=False, message=f"获取微信个人信息失败: {str(e)}")