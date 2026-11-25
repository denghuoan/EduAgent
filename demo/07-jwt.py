from passlib.context import CryptContext
# 兼容性补丁：让 passlib 能读到 bcrypt 版本
import bcrypt as _b, types as _t
if not hasattr(_b, "__about__"):
    _b.__about__ = _t.SimpleNamespace(__version__=getattr(_b, "__version__", "4.x"))

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

pwd_hash = pwd_context.hash('123456')
res = pwd_context.verify(b'123456', pwd_hash) # true
print(res)