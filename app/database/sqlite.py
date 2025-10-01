import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Tuple, Union
from app.models.base import BaseDBModel, BaseDatabase, QueryParams, QueryResult
from app.utils.config import settings

T = TypeVar('T', bound=BaseDBModel)

class SQLiteDatabase(BaseDatabase):
    """SQLite数据库实现"""
    
    def __init__(self) -> None:
        """初始化SQLite数据库连接"""
        # 获取数据库文件的绝对路径
        self.db_path = os.path.abspath(settings.database.sqlite.path)
        # 确保数据库目录存在
        self.db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        # 更新配置中的路径为绝对路径
        settings.database.sqlite.path = self.db_path
        # 调用父类初始化
        super().__init__(settings.database.sqlite)
        # 使用线程本地存储来管理连接
        self._local = threading.local()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, 'conn'):
            try:
                # 确保数据库文件存在
                if not os.path.exists(self.db_path):
                    # 确保目录存在
                    if not os.path.exists(self.db_dir):
                        os.makedirs(self.db_dir)
                    # 创建一个空的数据库文件
                    with open(self.db_path, 'w') as f:
                        pass
                self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._local.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                raise Exception(f"无法连接到数据库: {str(e)}")
            except Exception as e:
                raise Exception(f"创建数据库文件失败: {str(e)}")
        return self._local.conn
    
    def connect(self) -> None:
        """建立数据库连接（兼容性方法）"""
        # 不再使用全局连接，改为使用线程本地连接
        pass
    
    def disconnect(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
    
    def create_table(self, table_name: str, fields: Dict[str, str]) -> None:
        """创建表
        
        Args:
            table_name: 表名
            fields: 字段定义，格式为 {字段名: 字段类型}
        """
        try:
            conn = self._get_connection()
            fields_str = ', '.join([f"{k} {v}" for k, v in fields.items()])
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({fields_str})"
            conn.execute(sql)
            conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"创建表失败: {str(e)}")
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """插入数据
        
        Args:
            table_name: 表名
            data: 要插入的数据
            
        Returns:
            str: 插入记录的ID
        """
        try:
            conn = self._get_connection()
            fields = list(data.keys())
            placeholders = ','.join(['?' for _ in fields])
            sql = f"INSERT INTO {table_name} ({','.join(fields)}) VALUES ({placeholders})"
            cursor = conn.execute(sql, [data[field] for field in fields])
            conn.commit()
            return str(cursor.lastrowid)
        except sqlite3.Error as e:
            raise Exception(f"插入数据失败: {str(e)}")
    
    def update(self, table_name: str, id: str, data: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            table_name: 表名
            id: 记录ID
            data: 要更新的数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            conn = self._get_connection()
            fields = list(data.keys())
            set_clause = ','.join([f"{field}=?" for field in fields])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE id=?"
            cursor = conn.execute(sql, [data[field] for field in fields] + [id])
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise Exception(f"更新数据失败: {str(e)}")
    
    def delete(self, table_name: str, id: str) -> bool:
        """删除数据
        
        Args:
            table_name: 表名
            id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            conn = self._get_connection()
            sql = f"DELETE FROM {table_name} WHERE id=?"
            cursor = conn.execute(sql, [id])
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise Exception(f"删除数据失败: {str(e)}")
    
    def get_by_id(self, table_name: str, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取数据
        
        Args:
            table_name: 表名
            id: 记录ID
            
        Returns:
            Optional[Dict[str, Any]]: 记录数据，不存在则返回None
        """
        try:
            conn = self._get_connection()
            sql = f"SELECT * FROM {table_name} WHERE id=?"
            cursor = conn.execute(sql, [id])
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise Exception(f"获取数据失败: {str(e)}")
    
    def query(self, table_name: str, params: QueryParams) -> QueryResult:
        """查询数据，并返回符合 Pydantic 模型的结构化数据

        Args:
            table_name: 表名
            params: 查询参数
            model: 单条数据对应的Pydantic模型类

        Returns:
            QueryResult[T]: 查询结果
        """
        try:
            conn = self._get_connection()
            conditions = []
            values = []

            if params.filters:
                for field, value in params.filters.items():
                    conditions.append(f"{field}=?")
                    values.append(value)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
            order_clause = f" ORDER BY {params.sort_by} {params.sort_order}" if params.sort_by else ""
            limit_clause = f" LIMIT {params.limit} OFFSET {params.skip}"

            # 获取总数
            count_sql = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
            total = conn.execute(count_sql, values).fetchone()[0]

            # 获取数据
            sql = f"SELECT * FROM {table_name}{where_clause}{order_clause}{limit_clause}"
            cursor = conn.execute(sql, values)
            rows = cursor.fetchall()

            # 将 sqlite3.Row 转换为 Pydantic 模型实例
            items = [dict(row) for row in rows]

            page = params.skip // params.limit + 1 if params.limit else 1
            has_more = params.skip + params.limit < total

            return QueryResult(
                total=total,
                items=items,
                page=page,
                size=len(items),
                has_more=has_more
            )

        except sqlite3.Error as e:
            raise Exception(f"查询数据失败: {str(e)}")