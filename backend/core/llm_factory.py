from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
import httpx                                          # HTTP 客户端库（用来自定义网络行为）
from backend.core.logger import get_logger            # 结构化日志
from langchain_core.runnables import Runnable
from typing import Type, Any
from pydantic import BaseModel

from backend.config import get_settings
settings = get_settings()
logger = get_logger(__name__)         # 本模块的日志器，name 用当前模块名

# ── Agent 类型 → 模型标识符 的路由表 ────────────────────────────
# 想给某类业务换模型(对应模型厂商)，只改这里一行即可。
# 这里的_AGENT_MODEL_ROUTING键对应的是业务名称，值是每个业务选择的哪个模型厂商
_AGENT_MODEL_ROUTING: dict[str, str] = {
    "qa":               "deepseek-chat",   # 智能问答
    "exam_subjective":  "deepseek-chat",   # 试卷-简答题批改
    "exam_code":        "deepseek-chat",   # 试卷-代码题批改（coder 已并入 chat）
    "resume":           "deepseek-chat",   # 简历审查
    "interview":        "deepseek-chat",   # 模拟面试
    "intent":           "deepseek-chat",   # 意图识别
    "summarize":        "deepseek-chat",   # 对话摘要压缩
}
# ── 自定义 httpx 客户端：绕过系统代理 ───────────────────────────
# 背景：Windows 系统代理或 HTTPS_PROXY 环境变量会被 httpx 默认探测到，
#       导致 DeepSeek 请求经代理后 TLS 握手失败。DeepSeek 国内可直连，无需代理。
# trust_env=False 表示：完全忽略系统代理和相关环境变量。
_HTTP_ASYNC_CLIENT = httpx.AsyncClient(               # 异步客户端（给 ainvoke/astream 用）
    trust_env=False,
    timeout=httpx.Timeout(120.0, connect=15.0),       # 总超时 120 秒，建立连接超时 15 秒
)
_HTTP_SYNC_CLIENT = httpx.Client(                     # 同步客户端（给 invoke 用）
    trust_env=False,
    timeout=httpx.Timeout(120.0, connect=15.0),
)

# 模型标识符（实际模型） → DeepSeek API 实际接受的 model 名称
_MODEL_ID_MAP: dict[str, str] = {
    "deepseek-chat": "deepseek-v4-pro", # 这里面值：可以改成：deepseek_v4-pro
}
# 这里的_MODEL_ID_MAP键对应模型的厂商，值是真实的模型

class LLMFactory:

    _instance:dict[str, BaseChatModel] = {}


    @classmethod
    def _build_model_kwargs(cls, model_key: str) -> dict[str, Any]:
        model_id = _MODEL_ID_MAP[model_key]  # 把模型标识符转成 API 实际的 model 名
        return {
            "model":model_id,
            "model_provider": 'openai', # 强制走 langchain-openai（DeepSeek 兼容 OpenAI 接口）
            "temperature": 0,
            "api_key": settings.deepseek_api_key,
            "base_url": settings.deepseek_base_url,
            "max_retries": 0, # 模型层不重试；重试统一由 retry.py（3.5）管
            "http_async_client": _HTTP_ASYNC_CLIENT,  # 用上面绕过代理的异步客户端
            "http_client": _HTTP_SYNC_CLIENT,  # 同步客户端
        }

    @classmethod
    def get_llm(cls,
                agent_type:str,
                temperature: float = 0,
                streaming:bool = False) -> BaseChatModel:
        """
        按 Agent 类型获取模型实例(带缓存)
        相同 (模型, 温度, 是否流式) 的组合只会创建一次，之后复用。
        :param agent_type:
        :param temperature:
        :param streaming:
        :return:
        """

        if (agent_type not in _AGENT_MODEL_ROUTING):
            raise ValueError(
                f"agent_type {agent_type} "
                f"可用类型 {list(_AGENT_MODEL_ROUTING.keys())}")
        model_key = _AGENT_MODEL_ROUTING[agent_type]
        # 用「模型_温度_是否流式」拼一个缓存键：不同组合各缓存一份
        cache_key = f"{model_key}_{temperature}-{streaming}"

        if cache_key not in cls._instance:

            kwargs = cls._build_model_kwargs(model_key)
            kwargs['temperature'] = temperature
            kwargs['streaming'] = streaming
            kwargs["extra_body"] = {"thinking":{"type":"disabled"}}# 如果你想用deepseek-v4-pro/deepseek-v4-flash,可以强制关闭思考模式
            llm = init_chat_model( **kwargs )
            cls._instance[cache_key] = llm

            logger.info(  # 记一条结构化日志，便于观察
                "llm_factory.model_initialized",
                agent_type=agent_type, model_key=model_key, temperature=temperature, streaming=streaming,
            )

        return cls._instance[cache_key]

    @classmethod
    def get_structured_llm(cls, agent_type:str, output_schema: Type[BaseModel], temperature:float = 0 ) -> Runnable:
        llm = cls.get_llm(agent_type, temperature)
        return llm.with_structured_output(output_schema, method='function_calling')

    def clear_cache(cls) -> None:
        cls._instance.clear()
        logger.info("llm_factory.cache_cleared")


# ── 模块级便捷函数（Agent 代码里的推荐写法）────────────────────────
# 比写 LLMFactory.get_llm(...) 更简洁，直接 from llm_factory import get_llm 即可。
def get_llm(agent_type: str, temperature: float = 0, streaming: bool = False) -> BaseChatModel:
    """LLMFactory.get_llm 的便捷入口。"""
    return LLMFactory.get_llm(agent_type, temperature=temperature, streaming=streaming)


def get_structured_llm(agent_type: str, output_schema: Type[BaseModel]) -> Runnable:
    """LLMFactory.get_structured_llm 的便捷入口。"""
    return LLMFactory.get_structured_llm(agent_type, output_schema)

if __name__ == "__main__":
    # llm = LLMFactory.get_llm('qa')
    # resp = llm.invoke(
    #     [HumanMessage(content="红楼梦的作者名字叫什么")]
    # )
    # print(resp)

    import asyncio
    from langchain_core.messages import HumanMessage, SystemMessage
    from pydantic import Field


    async def main ():
        class PersonInfo(BaseModel):
            name: str = Field(description='姓名')
            age: int = Field(description='年龄(整数)')

        llm_struct = get_structured_llm('qa', PersonInfo)
        messages = [SystemMessage(content="你负责从文本中抽取任务信息"),
                    HumanMessage(content="我叫小明，今年25岁")]

        result = await llm_struct.ainvoke(messages)
        print(f"{result}")
        print(f"{result.name}")
        print(f"{result.model_dump()}")


    asyncio.run(main())

