from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.models.file import FileInfo, FileUploadResponse
from app.services.file_service import FileService
from app.utils.auth import get_current_token
from app.models.base import QueryParams

router = APIRouter()
file_service = FileService()

@router.post(
    "/upload", 
    response_model=FileUploadResponse,
    summary="上传文件"
)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    uploader: Optional[str] = Form(None),
    token: str = Depends(get_current_token)
) -> FileUploadResponse:
    """上传文件
    
    Args:
        file: 上传的文件
        description: 文件描述
        uploader: 上传者
        token: 认证令牌
        
    Returns:
        FileUploadResponse: 文件上传响应
    """
    return await file_service.upload_file(file, description, uploader)

@router.get(
    "/{file_id}", 
    response_model=FileInfo,
    summary="获取文件信息"
)
async def get_file(
    file_id: str,
    token: str = Depends(get_current_token)
) -> FileInfo:
    """获取文件信息
    
    Args:
        file_id: 文件ID
        token: 认证令牌
        
    Returns:
        FileInfo: 文件信息
    """
    file_info = file_service.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    return file_info

@router.delete(
    "/{file_id}",
    summary="删除文件"
)
async def delete_file(
    file_id: str,
    token: str = Depends(get_current_token)
) -> dict:
    """删除文件
    
    Args:
        file_id: 文件ID
        token: 认证令牌
        
    Returns:
        dict: 删除结果
    """
    if file_service.delete_file(file_id):
        return {"message": "文件删除成功"}
    raise HTTPException(status_code=404, detail="文件不存在")

@router.get(
    "/", 
    response_model=List[FileInfo],
    summary="获取文件列表"
)
async def list_files(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(get_current_token)
) -> List[FileInfo]:
    """列出文件
    
    Args:
        skip: 跳过数量
        limit: 限制数量
        token: 认证令牌
        
    Returns:
        List[FileInfo]: 文件列表
    """
    total, files = file_service.list_files(skip, limit)
    return files 