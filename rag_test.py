from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ====== 配置 ======
API_KEY = "5f7581e7842a485eb5dbef89d8ef807e.waiqxzpLJptwdt7I"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

# ====== 第1步：加载文档 ======
with open("cve_data.txt", "r", encoding="utf-8") as f:
    text = f.read()

print("文档加载成功，长度：", len(text))

# ====== 第2步：切片 ======
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". "]
)
chunks = splitter.split_text(text)

print(f"切片完成，共{len(chunks)}片")
for i, c in enumerate(chunks):
    print(f"--- 片段{i+1} ---")
    print(c)
    print()

# ====== 第3步：向量化 + 存入数据库 ======
embeddings = OpenAIEmbeddings(
    model="embedding-3",   # 智谱的向量模型
    api_key=API_KEY,
    base_url=BASE_URL
)

vectorstore = Chroma.from_texts(
    texts=chunks,
    embedding=embeddings,
    collection_name="vuln_kb"  # 知识库名字
)

print("向量数据库构建完成！")

# ====== 第4步：创建检索器 ======
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 2}  # 每次搜索返回最相关的2个片段
)

# ====== 第5步：测试检索效果（先不接AI，看搜索本身准不准）======
print("\n" + "="*50)
print("测试检索：搜索'文件上传'相关内容")
print("="*50)

results = retriever.invoke("文件上传有什么风险")
for i, doc in enumerate(results):
    print(f"\n检索结果{i+1}：")
    print(doc.page_content)

# ====== 第6步：创建大模型 ======
llm = ChatOpenAI(
    model="glm-4-flash",
    api_key=API_KEY,
    base_url=BASE_URL
)

# ====== 第7步：构建RAG Prompt ======
rag_prompt = ChatPromptTemplate.from_template("""
你是一个网络安全知识库助手，请仅根据下面提供的资料回答问题。
如果资料中没有相关信息，请直接说"知识库中没有相关信息"。

【资料】
{context}

【问题】
{question}

【回答】
""")

# ====== 第8步：把检索结果格式化成文本 ======
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ====== 第9步：组装RAG链 ======
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# ====== 第10步：测试问答 ======
print("\n" + "="*50)
print("RAG问答测试")
print("="*50)

# 测试不同问题
questions = [
    "What is a SQL injection vulnerability?",
    "哪些CVE漏洞的危险等级是HIGH？",
    "请列举几个SQL注入相关的CVE编号",
]

for q in questions:
    print(f"\n问题：{q}")
    print(f"回答：{rag_chain.invoke(q)}")
    print("-" * 50)

