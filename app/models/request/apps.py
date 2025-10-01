from pydantic import BaseModel
from typing import Optional, List, Union

# 基础请求
class BaseRequest(BaseModel):
    wxname: Union[None, str] = ''

class AcceptNewFriendRequest(BaseRequest):
    keywords: str
    remark: str = ''
    tags: str = ''