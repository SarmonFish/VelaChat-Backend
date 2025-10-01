from app.utils.wx_package_manager import (
    wx_manager,
    get_wx_class, 
    get_wx_function, 
    has_feature, 
    is_wxautox
)
from pythoncom import CoInitialize


# 动态导入wx包
WeChat = get_wx_class("WeChat")
Chat = get_wx_class("Chat")
HumanMessage = wx_manager.package.msgs.base.HumanMessage
try:
    get_wx_clients = get_wx_function("get_wx_clients")
except:
    def get_wx_clients():
        return [WeChat()]

# 初始化COM
CoInitialize()

# 如果是wxautox版本，导入额外模块
if is_wxautox():
    try:
        WxResponse = wx_manager.package.param.WxResponse
    except Exception as e:
        print(f"警告：无法导入WxResponse: {e}")

# 获取微信客户端
try:
    WxClient = {}
    for client in get_wx_clients():
        WxClient[client.nickname] = client
        client.StopListening()
except Exception as e:
    print(f"警告：无法获取微信客户端: {e}")
    WxClient = {}