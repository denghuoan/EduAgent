import os

from pydantic_settings import BaseSettings
from functools import lru_cache  # 标准库装饰器：缓存函数结果，让函数实际只执行一次

live_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_local_path = os.path.join(live_path, '.env.local')
# print(env_local_path)

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


    @property
    def database_url(self) -> str:
        """
            用@property装饰后可像访问属性一样 settings.database_url取值,不用加括号调用。
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19531

    # DEEPSEEK
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model_chat: str
    deepseek_model_coder: str



    # ── JWT 认证 ──
    jwt_secret_key: str                           # 必填：签发登录令牌用的密钥
    jwt_algorithm: str = "HS256"                  # 签名算法
    jwt_access_token_expire_minutes: int = 10080  # 令牌有效期（分钟）



    # 应用基础配置
    app_env:str = 'local'
    app_debug: bool = False
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    log_level: str = 'INFO'
    default_tenant_id: str = 'tenant_default'





    class Config:
        env_file = env_local_path
        env_file_encoding = 'utf-8'
        case_sensitive = False # 大小写不敏感：环境变量 DB_HOST 能对应字段 db_host
        extra = 'ignore'


@lru_cache()                             # 缓存：保证 get_settings() 只创建一次 Settings、只读一次文件
def get_settings() -> Settings:
    """获取全局唯一的配置对象。任何模块要用配置，都调用这个函数。"""
    return Settings()                    # 首次调用时创建实例；之后每次都返回同一个缓存对象




if __name__ == '__main__':
    settings = get_settings()
    print(settings.database_url)