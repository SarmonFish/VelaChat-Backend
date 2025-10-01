from pydantic import BaseModel
from typing import Optional, List, Union

# 基础请求
class BaseRequest(BaseModel):
    wxname: Union[None, str] = ''
    who: str

# 发送消息请求
class SendMessageRequest(BaseRequest):
    msg: str
    clear: bool = True
    at: List[str] = None

# 获取所有消息请求
class GetAllMessageRequest(BaseRequest):
    pass

# 获取新消息请求
class GetNewMessageRequest(BaseRequest):
    pass


# 根据id发送引用消息请求
class SendQuoteByIdRequest(BaseRequest):
    msg_id: str
    content: str

class CloseSubWindowsRequest(BaseRequest):
    ...
