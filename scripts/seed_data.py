# 灌入本地开发测试账号
import asyncpg # PostgreSQL 异步驱动（脚本直接用它，简单直接）
import uuid
import asyncio
from passlib.context import CryptContext
from backend.config import get_settings
# 兼容性补丁：同 auth.py，让 passlib 能读到 bcrypt 版本
import bcrypt as _b, types as _t
if not hasattr(_b, "__about__"):
    _b.__about__ = _t.SimpleNamespace(__version__=getattr(_b, "__version__", "4.x"))


s = get_settings()
# 用环境变量拼出 asyncpg 的连接串（注意 asyncpg 用的是 postgresql:// 而非 +asyncpg）
DB_DSN = (
    f"postgresql://{s.db_user}:{s.db_password}"
    f"@{s.db_host}:{s.db_port}"
    f"/{s.db_name}"
)
print(DB_DSN)
TENANT_ID = "tenant_default"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_users():
    conn = await asyncpg.connect(DB_DSN)
    print('连接成功')
    try:
        users = [
            {"username": "admin", "email": "admin@eduagent.local", "pwd": "Admin@123456", "role": "admin"},
            {"username": "teacher01", "email": "teacher01@eduagent.local", "pwd": "Teacher@123456", "role": "teacher"},
            {"username": "student01", "email": "student01@eduagent.local", "pwd": "Student@123456", "role": "student"},
            {"username": "student02", "email": "student02@eduagent.local", "pwd": "Student@123456", "role": "student"},
        ]
        for u in users:
            await conn.execute(
                """
                INSERT INTO users(id,tenant_id,username,email,password_hash,role)
                VALUES($1,$2,$3,$4,$5,$6)
                ON CONFLICT (tenant_id, email) DO NOTHING
                """,
                str(uuid.uuid4()),TENANT_ID, u["username"], u["email"],
                pwd_context.hash(u["pwd"]),
                u["role"]
            )
        print(f"✅ 测试账号灌入完成（{len(users)} 个，已存在则跳过）：")
        print("   admin@eduagent.local      / Admin@123456")
        print("   teacher01@eduagent.local  / Teacher@123456")
        print("   student01@eduagent.local  / Student@123456")
        print("   student02@eduagent.local  / Student@123456")

    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(seed_users())