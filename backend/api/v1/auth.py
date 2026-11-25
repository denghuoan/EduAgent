import asyncio
from datetime import datetime, timezone, timedelta
import uvicorn
from fastapi import APIRouter, Depends, HTTPException,status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dependencies import get_db, get_current_user
from sqlalchemy import text
from backend.config import get_settings
from backend.core.logger import get_logger


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)
class LoginRequest(BaseModel):
    """登录请求体。"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """登录成功的响应体。"""
    access_token: str                 # JWT 令牌
    token_type:   str = "bearer"      # 令牌类型，固定 bearer
    expires_in:   int                 # 有效期（秒）
    role:         str                 # 用户角色
    user_id:      str                 # 用户ID


def _create_access_token(data:dict,expires_minutes:int) -> str:
    payload = data.copy()  # 拷一份，避免改到原字典
    expires = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload['exp'] = expires # exp 是 JWT 标准的过期字段
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.get('/me')
async def get_me(
        current_user:dict = Depends(get_current_user) # 注入当前用户（顺带完成鉴权）
):
    return current_user

@router.post("/login", response_model=TokenResponse)
async def login(
        req: LoginRequest,
        db: AsyncSession = Depends(get_db)
):
    # 查用户
    result = await db.execute(
        text(
            "SELECT id, password_hash, is_active, role, tenant_id "
            "FROM users WHERE username = :val OR email = :val LIMIT 1"
        ),
        {"val": req.username}
    )
    row = result.fetchone()
    # 账号校验
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not row.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用，请联系管理员")

    # 密码校验:CPU 密集型（~100ms）-> 异步中的同步操作
    loop = asyncio.get_event_loop()
    password_ok = await loop.run_in_executor(
        None,pwd_context.verify, req.password, row.password_hash
    )
    if not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 校验通过,签发token
    token = _create_access_token(
        data={
            "sub": str(row.id),
            "role": row.role,
            'tenant_id': row.tenant_id,
        },
        expires_minutes=settings.jwt_access_token_expire_minutes
    )
    logger.info("auth.login_success", user_id=str(row.id), role=row.role)



    return TokenResponse(
        role=row.role,
        user_id=str(row.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,  # 分钟转秒
        access_token=token
    )




if __name__ == '__main__':
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix='/auth', tags=["auth"])
    uvicorn.run(app, host="127.0.0.1", port=8000)