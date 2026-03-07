import asyncio
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def my_node(state: State):
    return {"messages": []}

workflow = StateGraph(State)
workflow.add_node("node", my_node)
workflow.add_edge(START, "node")
workflow.add_edge("node", END)
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

async def main():
    config = {"configurable": {"thread_id": "1"}}
    await app.ainvoke({"messages": [HumanMessage(content="Hi"), AIMessage(content="", tool_calls=[{"name": "foo", "id": "123", "args": {}}], id="msg-ai"), HumanMessage(content="Interrupted")]}, config)
    
    state = await app.aget_state(config)
    print("Before:")
    for m in state.values["messages"]:
        print(type(m).__name__, getattr(m, "id", None), getattr(m, "tool_calls", None))
        
    from langchain_core.messages import AIMessage
    new_msg = AIMessage(content="[Tool call interrupted]", id="msg-ai", tool_calls=[])
    await app.aupdate_state(config, {"messages": [new_msg]})
    
    state = await app.aget_state(config)
    print("\nAfter:")
    for m in state.values["messages"]:
        print(type(m).__name__, getattr(m, "id", None), getattr(m, "tool_calls", None), m.content)

asyncio.run(main())
