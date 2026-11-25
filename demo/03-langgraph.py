from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class HelperState(TypedDict):
    question: str  # 用户的问题（输入）
    category: str  # 分类结果：concept / code / chat（中间结果）
    answer: str  # 最终回应（输出）


def classify_node(state: HelperState) -> dict:
    q = state['question']
    if "代码" in q or "报错" in q or "bug" in q:
        category = "code"
    elif "什么是" in q or "概念" in q or "原理" in q:
        category = "concept"
    else:
        category = "chat"
    return {"category": category}  # 只返回要更新的字段

def answer_concept_node(state: HelperState) -> dict:
    return {"answer": f"【概念解答】关于「{state['question']}」，它的核心思想是……"}

def answer_code_node(state: HelperState) -> dict:
    return {"answer": f"【代码助手】针对「{state['question']}」，我们一步步排查……"}

def answer_chat_node(state: HelperState) -> dict:
    return {"answer": "【闲聊】哈哈，没问题，我们继续聊～"}

def route_by_category(state: HelperState) -> str:
    return state['category']

builder = StateGraph(HelperState)
builder.add_node('classify', classify_node)
builder.add_node('concept', answer_concept_node)
builder.add_node('code', answer_code_node)
builder.add_node('chat', answer_chat_node)

builder.add_edge(START, 'classify')

# 条件边
builder.add_conditional_edges(
    'classify',
    route_by_category, # 路由函数
    {
        'concept': 'concept',
        'code': 'code',
        'chat': 'chat',
    }
)

builder.add_edge('concept', END)
builder.add_edge('code', END)
builder.add_edge('chat', END)

graph = builder.compile()


# 试三种不同的问题，观察走了不同分支
for q in ["什么是装饰器", "这段代码报错怎么办", "今天天气不错"]:
    result = graph.invoke({"question": q, "category": "", "answer": ""})
    print(f"问题：{q}\n  → 分类：{result['category']}　回应：{result['answer']}\n")

