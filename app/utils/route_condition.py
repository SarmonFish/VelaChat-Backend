"""
条件路由装饰器
根据wx包版本决定是否显示某些API接口
"""

from functools import wraps
from fastapi import HTTPException
from app.utils.wx_package_manager import has_feature, is_wxautox

def require_wxautox(func):
    """要求wxautox版本的装饰器
    
    如果用户使用的是wxauto版本，该接口将返回错误
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not is_wxautox():
            raise HTTPException(
                status_code=501, 
                detail="此功能需要wxautox版本支持，当前使用的是wxauto版本"
            )
        return await func(*args, **kwargs)
    return wrapper

def require_feature(feature_name: str):
    """要求特定功能的装饰器
    
    Args:
        feature_name: 功能名称
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not has_feature(feature_name):
                raise HTTPException(
                    status_code=501,
                    detail=f"此功能需要 {feature_name} 支持，当前版本不支持此功能"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def conditional_route(condition_func):
    """条件路由装饰器
    
    Args:
        condition_func: 条件函数，返回True表示显示路由，False表示隐藏
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not condition_func():
                raise HTTPException(
                    status_code=404,
                    detail="接口不存在"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 预定义的条件函数
def is_wxautox_available():
    """检查wxautox是否可用"""
    return is_wxautox()

def has_url_card_feature():
    """检查是否有URL卡片功能"""
    return has_feature("send_url_card")

def has_listen_chat_feature():
    """检查是否有监听聊天功能"""
    return has_feature("add_listen_chat")

def has_new_message_feature():
    """检查是否有新消息功能"""
    return has_feature("get_next_new_message")

def has_quote_message_feature():
    """检查是否有引用消息功能"""
    return has_feature("send_quote_by_id")

def has_friend_management_feature():
    """检查是否有好友管理功能"""
    return has_feature("get_new_friends")

def has_page_switch_feature():
    """检查是否有页面切换功能"""
    return has_feature("switch_to_chat_page") 