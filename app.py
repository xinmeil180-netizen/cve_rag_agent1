"""
CVE安全漏洞知识库问答系统 - Streamlit网页版
基于真实NVD CVE数据的RAG（检索增强生成）问答应用
"""
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ====== 配置 ======
import os

API_KEY = os.environ["ZHIPU_API_KEY"]
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"


# ====== 页面基础设置 ======
st.set_page_config(page_title="CVE安全知识库问答", page_icon="🛡️", layout="wide")
st.title("🛡️ CVE安全漏洞知识库问答系统")
st.caption("基于NVD官方真实CVE数据构建的RAG检索增强问答应用")


# ====== 用缓存避免每次提问都重新构建知识库（重点：性能优化）======
@st.cache_resource(show_spinner="正在构建知识库，请稍候...")
def build_rag_chain():
    # 1. 加载文档
    with open("cve_data.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # 2. 切片
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". "]
    )
    chunks = splitter.split_text(text)

    # 3. 向量化 + 存储
    embeddings = OpenAIEmbeddings(
        model="embedding-3",
        api_key=API_KEY,
        base_url=BASE_URL
    )
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name="vuln_kb"
    )

    # 4. 检索器
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 5. 大模型
    llm = ChatOpenAI(
        model="glm-4-flash",
        api_key=API_KEY,
        base_url=BASE_URL
    )

    # 6. Prompt模板
    rag_prompt = ChatPromptTemplate.from_template("""
你是一个网络安全知识库助手，请仅根据下面提供的资料回答问题，并尽量用中文回答。
如果资料中没有相关信息，请直接说"知识库中没有相关信息"。

【资料】
{context}

【问题】
{question}

【回答】
""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 7. 组装链
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | llm
        | StrOutputParser()
    )

    return chain, len(chunks)


# ====== 构建（首次加载会慢一点，之后走缓存）======
rag_chain, chunk_count = build_rag_chain()

with st.sidebar:
    st.header("📊 知识库信息")
    st.metric("文档切片数量", chunk_count)
    st.markdown("---")
    st.markdown("**数据来源**：NVD国家漏洞数据库官方API")
    st.markdown("**技术栈**：LangChain + Chroma + GLM-4-Flash")
    st.markdown("---")
    st.markdown("**示例问题：**")
    st.code("What is a SQL injection vulnerability?")
    st.code("哪些CVE漏洞的危险等级是HIGH？")
    st.code("请列举几个SQL注入相关的CVE编号")


# ====== 聊天历史状态管理 ======
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ====== 输入框 ======
user_input = st.chat_input("请输入你的安全漏洞相关问题...")

if user_input:
    # 显示用户问题
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 生成并显示AI回答
    with st.chat_message("assistant"):
        with st.spinner("正在检索知识库并生成回答..."):
            answer = rag_chain.invoke(user_input)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})