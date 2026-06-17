# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate

# llm = ChatOpenAI(
#     model="glm-4-flash",
#     api_key="5f7581e7842a485eb5dbef89d8ef807e.waiqxzpLJptwdt7I",
#     base_url="https://open.bigmodel.cn/api/paas/v4/"
# )

# prompt = ChatPromptTemplate.from_messages([
#     ("system", "你是一个网络安全专家"),
#     ("user", "请解释什么是{topic}攻击")
# ])

# chain = prompt | llm

# response = chain.invoke({"topic": "CSRF"})
# print(response.content)


from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(
    model="glm-4-flash",
    api_key="5f7581e7842a485eb5dbef89d8ef807e.waiqxzpLJptwdt7I",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 创建记忆存储
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 创建带记忆的链
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个网络安全专家"),
    ("human", "{input}"),
])

chain = RunnableWithMessageHistory(
    prompt | llm,
    get_session_history,
    input_messages_key="input",
)

# 连续对话，session_id相同就共享记忆
config = {"configurable": {"session_id": "test"}}

r1 = chain.invoke({"input": "我叫小兰，我在学网络安全"}, config=config)
print("AI：", r1.content)

r2 = chain.invoke({"input": "我叫什么名字？"}, config=config)
print("AI：", r2.content)

r3 = chain.invoke({"input": "我在学什么？"}, config=config)
print("AI：", r3.content)