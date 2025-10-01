import os
import hashlib
from datetime import datetime
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException
from app.models.file import FileInfo, FileUploadResponse
from app.models.base import QueryParams
from app.database.factory import DatabaseFactory
from app.utils.config import settings

class FileService:
    """文件服务"""
    
    def __init__(self) -> None:
        """初始化文件服务"""
        self.db = DatabaseFactory.get_database()
        self.base_dir = settings.upload.base_dir
        self.max_size = settings.upload.max_size
        self.allowed_types = settings.upload.allowed_types
        self.chunk_size = settings.upload.chunk_size
        
        # 确保上传目录存在
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        # 创建文件表
        self.db.create_table("files", {
            "id": "TEXT PRIMARY KEY",
            "filename": "TEXT NOT NULL",
            "file_type": "TEXT NOT NULL",
            "file_size": "INTEGER NOT NULL",
            "file_hash": "TEXT NOT NULL",
            "file_path": "TEXT NOT NULL",
            "upload_time": "TIMESTAMP NOT NULL",
            "description": "TEXT",
            "uploader": "TEXT",
            "download_count": "INTEGER DEFAULT 0",
            "is_deleted": "INTEGER DEFAULT 0"
        })
        
    def _calculate_hash(self, file: UploadFile) -> str:
        """计算文件哈希值
        
        Args:
            file: 上传的文件
            
        Returns:
            str: 文件哈希值
        """
        sha256 = hashlib.sha256()
        while chunk := file.file.read(self.chunk_size):
            sha256.update(chunk)
        file.file.seek(0)  # 重置文件指针
        return sha256.hexdigest()
        
    def _get_file_path(self, file_hash: str, filename: str) -> str:
        """获取文件存储路径
        
        Args:
            file_hash: 文件哈希值
            filename: 原始文件名
            
        Returns:
            str: 文件存储路径
        """
        # 使用哈希值的前两位作为子目录
        sub_dir = os.path.join(self.base_dir, file_hash[:2])
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)
            
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        return os.path.join(sub_dir, f"{file_hash}{ext}")
        
    def _validate_file(self, file: UploadFile) -> None:
        """验证文件
        
        Args:
            file: 上传的文件
            
        Raises:
            HTTPException: 文件验证失败
        """
        # 检查文件大小
        file_size = 0
        while chunk := file.file.read(self.chunk_size):
            file_size += len(chunk)
            if file_size > self.max_size:
                raise HTTPException(status_code=400, detail="文件大小超过限制")
        file.file.seek(0)
        
        # 检查文件类型
        if self.allowed_types and file.content_type not in self.allowed_types:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
            
    async def upload_file(
        self,
        file: UploadFile,
        description: Optional[str] = None,
        uploader: Optional[str] = None
    ) -> FileUploadResponse:
        """上传文件
        
        Args:
            file: 上传的文件
            description: 文件描述
            uploader: 上传者
            
        Returns:
            FileUploadResponse: 文件上传响应
        """
        # 验证文件
        self._validate_file(file)
        
        # 计算文件哈希值
        file_hash = self._calculate_hash(file)
        
        # 获取文件存储路径
        file_path = self._get_file_path(file_hash, file.filename)
        
        # 检查文件是否已存在
        existing_file = self.db.get_by_id("files", file_hash)
        if existing_file:
            # 文件已存在，返回现有文件信息
            return FileUploadResponse(
                file_id=existing_file["id"],
                filename=existing_file["filename"],
                file_type=existing_file["file_type"],
                file_size=existing_file["file_size"],
                file_hash=existing_file["file_hash"],
                file_path=existing_file["file_path"],
                upload_time=existing_file["upload_time"],
                is_new=False
            )
            
        # 保存文件
        with open(file_path, "wb") as f:
            while chunk := file.file.read(self.chunk_size):
                f.write(chunk)
                
        # 记录文件信息
        file_info = {
            "id": file_hash,
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": os.path.getsize(file_path),
            "file_hash": file_hash,
            "file_path": file_path,
            "upload_time": datetime.now().isoformat(),
            "description": description,
            "uploader": uploader,
            "download_count": 0,
            "is_deleted": 0
        }
        
        self.db.insert("files", file_info)
        
        return FileUploadResponse(
            file_id=file_info["id"],
            filename=file_info["filename"],
            file_type=file_info["file_type"],
            file_size=file_info["file_size"],
            file_hash=file_info["file_hash"],
            file_path=file_info["file_path"],
            upload_time=file_info["upload_time"],
            is_new=True
        )
        
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[FileInfo]: 文件信息
        """
        file_info = self.db.get_by_id("files", file_id)
        if not file_info or file_info["is_deleted"]:
            return None
        return FileInfo(**file_info)
        
    def delete_file(self, file_id: str) -> bool:
        """删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.db.update("files", file_id, {"is_deleted": 1})
        
    def list_files(self, skip: int = 0, limit: int = 100) -> Tuple[int, List[FileInfo]]:
        """列出文件
        
        Args:
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            Tuple[int, List[FileInfo]]: 总数和文件列表
        """
        params = QueryParams(
            skip = skip,
            limit = limit,
            filters = {"is_deleted": 0},
            sort_by = "upload_time",
            sort_order = "DESC"
        )
        result = self.db.query("files", params)
        return result.total, [FileInfo(**item) for item in result.items] 