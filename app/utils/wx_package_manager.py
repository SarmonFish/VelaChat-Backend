"""
wxauto/wxautox 包管理器
提供统一的接口来使用wxauto或wxautox
"""

import importlib
from typing import Any, Optional, Dict, List
from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger()

class WxPackageManager:
    """wxauto/wxautox 包管理器"""
    
    def __init__(self):
        """初始化包管理器"""
        self.package_name = settings.package
        self._package = None
        self._is_wxautox = False
        self._load_package()
    
    def _load_package(self) -> None:
        """加载指定的包"""
        try:
            if self.package_name == "wxautox":
                self._package = importlib.import_module("wxautox")
                try:
                    self._package.utils.useful.authenticate(str())
                    self._is_wxautox = True
                    logger.info("已加载 wxautox 包")
                except:
                    logger.warning("wxautox鉴权失败，尝试加载wxauto包")
                    self._package = importlib.import_module("wxauto")
                    self._is_wxautox = False
                    logger.info("已加载 wxauto 包")
            else:
                self._package = importlib.import_module("wxauto")
                self._is_wxautox = False
                logger.info("已加载 wxauto 包")
        except ImportError as e:
            logger.error(f"无法导入 {self.package_name} 包: {e}")
            raise ImportError(f"请确保已安装 {self.package_name} 包")
    
    @property
    def is_wxautox(self) -> bool:
        """是否为wxautox版本"""
        return self._is_wxautox
    
    @property
    def package(self) -> Any:
        """获取包对象"""
        return self._package
    
    def get_class(self, class_name: str) -> Any:
        """获取包中的类
        
        Args:
            class_name: 类名
            
        Returns:
            类对象
        """
        if hasattr(self._package, class_name):
            return getattr(self._package, class_name)
        else:
            raise AttributeError(f"{self.package_name} 包中没有 {class_name} 类")
    
    def get_function(self, function_name: str) -> Any:
        """获取包中的函数
        
        Args:
            function_name: 函数名
            
        Returns:
            函数对象
        """
        if hasattr(self._package, function_name):
            return getattr(self._package, function_name)
        else:
            raise AttributeError(f"{self.package_name} 包中没有 {function_name} 函数")
    
    def has_feature(self, feature_name: str) -> bool:
        """检查是否支持某个功能
        
        Args:
            feature_name: 功能名称
            
        Returns:
            是否支持该功能
        """
        # wxautox特有功能列表
        wxautox_features = {
            "send_url_card",
            # "add_listen_chat", 
            # "get_next_new_message",
            # "send_quote_by_id",
            "get_new_friends",
            "accept_new_friend",
            "switch_to_chat_page",
            "switch_to_contact_page",
            "is_online",
            "WxParam",
            "WxResponse",
            "wxlog"
        }
        
        if self._is_wxautox:
            return feature_name in wxautox_features
        else:
            return feature_name not in wxautox_features
    
    def get_supported_features(self) -> List[str]:
        """获取当前包支持的功能列表
        
        Returns:
            支持的功能列表
        """
        if self._is_wxautox:
            return [
                "基础消息发送",
                "文件发送", 
                "聊天窗口切换",
                "获取子窗口",
                "获取消息",
                "URL卡片发送",
                "监听聊天",
                "获取新消息",
                "引用消息",
                "好友申请管理",
                "页面切换",
                "高级参数配置",
                "日志系统"
            ]
        else:
            return [
                "基础消息发送",
                "文件发送",
                "聊天窗口切换", 
                "获取子窗口",
                "获取消息"
            ]

# 全局包管理器实例
wx_manager = WxPackageManager()

# 便捷函数
def get_wx_class(class_name: str) -> Any:
    """获取wx类
    
    Args:
        class_name: 类名
        
    Returns:
        类对象
    """
    return wx_manager.get_class(class_name)

def get_wx_function(function_name: str) -> Any:
    """获取wx函数
    
    Args:
        function_name: 函数名
        
    Returns:
        函数对象
    """
    return wx_manager.get_function(function_name)

def is_wxautox() -> bool:
    """是否为wxautox版本"""
    return wx_manager.is_wxautox

def has_feature(feature_name: str) -> bool:
    """检查是否支持某个功能"""
    return wx_manager.has_feature(feature_name)

def get_supported_features() -> List[str]:
    """获取支持的功能列表"""
    return wx_manager.get_supported_features() 