from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage,HumanMessage
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

def reply_node(state: ChatState) -> dict:
    last_user_msg = state["messages"][-1].content
    reply = f'我收到了[{last_user_msg}]当前历史共{len(state["messages"])}条消息'
    return { 'messages': [AIMessage(content=reply)] }

builder = StateGraph(ChatState)
builder.add_node('reply',reply_node)
builder.add_edge(START,'reply')
builder.add_edge('reply',END)

graph = builder.compile(checkpointer=MemorySaver())

config = { "configurable": { "thread_id" : 'user-1'} }

graph.invoke(
    {'messages': [HumanMessage(content='你好')]},
    config
)
result = graph.invoke(
    {'messages': [HumanMessage(content='还记得我说啥了吗')]},
    config
)
for m in result["messages"]:
    # print(m) # content='' additional_kwargs={} response_metadata={} id=''
    print(f"{type(m).__name__}: {m.content}")

#