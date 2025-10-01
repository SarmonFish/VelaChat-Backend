from app.utils.wx_package_manager import get_wx_class, has_feature, is_wxautox
from pythoncom import CoInitialize
from typing import Optional, List
from app.models.response import APIResponse
import time

# 初始化COM
CoInitialize()

def accept_single_friend(new, keywords, remark, tags):

    if isinstance(keywords, str):
        keywords = [keywords]
    if isinstance(tags, str):
        tags = [tags]

    newmsg = new.msg.lower()
    newname = new.name
    result = {
        'new_message': newmsg,
        'new_nickname': newname,
        'new_account': '',
        'accept': False 
    }
    if any(keyword in newmsg for keyword in keywords):
        new_remark = f"{remark}_{int(time.strftime('%y%m%d%H%M%S'))}" 
        new.accept(remark=new_remark, tags=tags)
        account = new.get_account()
        result['accept'] = True
        result['new_account'] = account
    return result


def accept_new_friend(
        wx,
        keywords,
        remark: str = '',
        tags: List[str] = []
    ) -> APIResponse:
    """接受新朋友"""
    if not has_feature("accept_new_friend"):
        return APIResponse(success=False, message="此功能需要wxautox版本支持")
    try:
        result = []
        new_friends = wx.GetNewFriends()
        for new in new_friends:
            result.append(accept_single_friend(new, keywords, remark, tags))
        return APIResponse(success=bool(result), message='操作完成', data=result)
    except Exception as e:
        return APIResponse(success=False, message=str(e))
    finally:
        try:
            wx.SwitchToChat()
        except:
            import traceback
            traceback.print_exc()
            pass