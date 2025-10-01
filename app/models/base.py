from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from uuid import uuid4

T = TypeVar('T')

class BaseDBModel(BaseModel):
    """基础数据库模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

class QueryParams(BaseModel):
    """查询参数模型"""
    skip: int = 0
    limit: int = 100
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    filters: Optional[Dict[str, Any]] = None

class QueryResult(BaseModel):
    """查询结果模型"""
    total: int
    items: List[Any]
    page: int
    size: int
    has_more: bool

class BaseDatabase:
    """数据库基类"""
    
    def __init__(self, config: Any):
        """初始化数据库连接
        
        Args:
            config: 数据库配置
        """
        self.config = config
        self.connect()
    
    def connect(self) -> None:
        """建立数据库连接"""
        raise NotImplementedError
    
    def disconnect(self) -> None:
        """断开数据库连接"""
        raise NotImplementedError
    
    def create_table(self, model: type[BaseDBModel]) -> None:
        """创建数据表
        
        Args:
            model: 数据模型类
        """
        raise NotImplementedError
    
    def insert(self, model: BaseDBModel) -> str:
        """插入数据
        
        Args:
            model: 数据模型实例
            
        Returns:
            str: 插入数据的ID
        """
        raise NotImplementedError
    
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            data: 要更新的数据
            
        Returns:
            bool: 是否更新成功
        """
        raise NotImplementedError
    
    def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            bool: 是否删除成功
        """
        raise NotImplementedError
    
    def get(self, id: str) -> Optional[BaseDBModel]:
        """获取单条数据
        
        Args:
            id: 数据ID
            
        Returns:
            Optional[BaseDBModel]: 数据模型实例
        """
        raise NotImplementedError
    
    def query(self, params: QueryParams) -> QueryResult:
        """查询数据
        
        Args:
            params: 查询参数
            
        Returns:
            QueryResult[BaseDBModel]: 查询结果
        """
        raise NotImplementedError 