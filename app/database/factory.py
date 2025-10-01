from typing import Optional
from app.database.sqlite import SQLiteDatabase
from app.utils.config import settings

class DatabaseFactory:
    """数据库工厂类"""
    
    _instance: Optional[SQLiteDatabase] = None
    
    @classmethod
    def get_database(cls):
        """获取数据库实例
        
        Returns:
            BaseDatabase: 数据库实例
        """
        if cls._instance is None:
            if settings.database.type == "sqlite":
                cls._instance = SQLiteDatabase()
            # elif settings.database.type == "mysql":
            #     cls._instance = MySQLDatabase()
            # elif settings.database.type == "mongodb":
            #     cls._instance = MongoDBDatabase()
            else:
                raise ValueError(f"Unsupported database type: {settings.database.type}")
        return cls._instance 