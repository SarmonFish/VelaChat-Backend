from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.base import BaseDBModel

class FileInfo(BaseDBModel):
    """文件信息模型"""
    filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    file_hash: str = Field(..., description="文件哈希值")
    file_path: str = Field(..., description="文件存储路径")
    upload_time: datetime = Field(default_factory=datetime.utcnow, description="上传时间")
    description: Optional[str] = Field(None, description="文件描述")
    uploader: Optional[str] = Field(None, description="上传者")
    download_count: int = Field(default=0, description="下载次数")
    is_deleted: bool = Field(default=False, description="是否已删除")

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小")
    file_hash: str = Field(..., description="文件哈希值")
    file_path: str = Field(..., description="文件路径")
    upload_time: datetime = Field(..., description="上传时间")
    is_new: bool = Field(..., description="是否为新上传的文件") 