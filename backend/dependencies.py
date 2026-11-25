from fastapi import status, Depends, HTTPException
from typing import AsyncGenerator

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker

from backend.config import get_settings

settings = get_settings()

# 创建异步引擎(连接池)
engine = create_async_engine(
    settings.database_url,
    pool_size=10, #连接池基础大小
    max_overflow=20, # 高峰时最多再额外开 20 个连接
    echo=False, # True 会打印所有 SQL，调试时可临时打开
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def  get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖: 获取异步数据库会话,自动提交/回滚/关闭"""
    async with AsyncSessionLocal() as session:
        try:
            yield session # 把会话交给接口使用
            await session.commit()
        except Exception:
            await session.rollback() # 出错自动回滚
            raise


# # JWT鉴权
bearer_scheme = HTTPBearer() # FastAPI安全方案:自动从请求头解析"Authorization: Bearer <token>"

async def get_current_user(
    # Depends(bearer_scheme):FastAPI自动取出Bearer Token,没带或格式错会直接401
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    # 预先准备好「401
    # 凭证无效」异常，多处复用
    # print(credentials) # scheme='Bearer' credentials='eyJhbG....'
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail='无效的认证凭证',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(
            credentials.credentials, # 实际的 token 字符串
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get('sub')
        role = payload.get('role', 'student')
        tenant_id = payload.get('tenant_id', settings.default_tenant_id)

        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {"user_id": user_id, "role": role, "tenant_id": tenant_id}

