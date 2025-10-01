"""
pywechat 包管理器
提供pywechat功能的统一接口，解决与wxauto/wxautox的冲突
"""

import importlib
from typing import Any, Optional, Dict, List
from app.utils.logger import setup_logger

logger = setup_logger()

class PyWeChatManager:
    """pywechat 包管理器"""
    
    def __init__(self):
        """初始化pywechat包管理器"""
        self._package = None
        self._is_loaded = False
        self._load_pywechat()
    
    def _load_pywechat(self) -> None:
        """加载pywechat包"""
        try:
            # 尝试加载pywechat
            self._package = importlib.import_module("pywechat")
            self._is_loaded = True
            logger.info("✅ 已加载 pywechat 包")
            
            # 检查WechatAuto模块
            if hasattr(self._package, 'WechatAuto'):
                logger.info("✅ 已加载 WechatAuto 模块")
            else:
                logger.warning("⚠️ WechatAuto 模块加载失败")
                
        except ImportError as e:
            logger.warning(f"⚠️ 无法导入 pywechat 包: {e}")
            self._package = None
            self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """pywechat是否已加载"""
        return self._is_loaded
    
    @property
    def package(self) -> Any:
        """获取pywechat包对象"""
        return self._package
    
    def get_class(self, class_name: str) -> Any:
        """获取pywechat中的类
        
        Args:
            class_name: 类名
            
        Returns:
            类对象
        """
        if not self._is_loaded:
            raise ImportError("pywechat包未加载")
            
        # 先检查WechatAuto模块
        if hasattr(self._package.WechatAuto, class_name):
            return getattr(self._package.WechatAuto, class_name)
        
        # 检查主模块
        if hasattr(self._package, class_name):
            return getattr(self._package, class_name)
            
        raise AttributeError(f"pywechat包中没有 {class_name} 类")
    
    def get_function(self, function_name: str) -> Any:
        """获取pywechat中的函数
        
        Args:
            function_name: 函数名
            
        Returns:
            函数对象
        """
        if not self._is_loaded:
            raise ImportError("pywechat包未加载")
            
        # 先检查WechatAuto模块
        if hasattr(self._package.WechatAuto, function_name):
            return getattr(self._package.WechatAuto, function_name)
        
        # 检查主模块
        if hasattr(self._package, function_name):
            return getattr(self._package, function_name)
            
        raise AttributeError(f"pywechat包中没有 {function_name} 函数")
    
    def has_function(self, function_name: str) -> bool:
        """检查是否支持某个函数
        
        Args:
            function_name: 函数名
            
        Returns:
            是否支持该函数
        """
        if not self._is_loaded:
            return False
            
        try:
            self.get_function(function_name)
            return True
        except (AttributeError, ImportError):
            return False

# 全局pywechat管理器实例
pywechat_manager = PyWeChatManager()

# 便捷函数
def get_pywechat_class(class_name: str) -> Any:
    """获取pywechat类"""
    return pywechat_manager.get_class(class_name)

def get_pywechat_function(function_name: str) -> Any:
    """获取pywechat函数"""
    return pywechat_manager.get_function(function_name)

def has_pywechat_function(function_name: str) -> bool:
    """检查pywechat是否支持某个函数"""
    return pywechat_manager.has_function(function_name)

def is_pywechat_loaded() -> bool:
    """pywechat是否已加载"""
    return pywechat_manager.is_loaded