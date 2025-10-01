from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.config import settings

security = HTTPBearer()

async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证token是否有效
    
    Args:
        credentials: HTTP认证凭证
        
    Returns:
        str: 验证通过的token
        
    Raises:
        HTTPException: 当token无效时抛出401错误
    """
    if credentials.credentials != settings.auth.token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials 