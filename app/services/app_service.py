from .applications import *
from app.models.response import APIResponse
from app.services.wechat_service import get_wechat

class AppService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppService, cls).__new__(cls)
        return cls._instance
    
    def accept_new_friend(
        self,
        wxname: str,
        keywords: str,
        remark: str = '',
        tags: str = ''
    ) -> APIResponse:
        wx = get_wechat(wxname)
        return accept_new_friend(
            wx=wx,
            keywords=keywords,
            remark=remark,
            tags=tags
        )