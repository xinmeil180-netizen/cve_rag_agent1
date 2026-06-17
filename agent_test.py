from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(
    model="glm-4-flash",
    api_key="5f7581e7842a485eb5dbef89d8ef807e.waiqxzpLJptwdt7I",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# ====== 定义工具 ======

@tool
def check_vulnerability(code: str) -> str:
    """分析代码片段是否包含SQL注入漏洞"""
    if "SELECT" in code and "+" in code:
        return "⚠️ 发现SQL注入风险：使用了字符串拼接构造SQL语句"
    return "✅ 未发现明显SQL注入风险"

@tool
def get_fix_suggestion(vuln_type: str) -> str:
    """根据漏洞类型返回修复建议"""
    fixes = {
        "SQL注入": "使用参数化查询，例如：cursor.execute('SELECT * FROM users WHERE id=?', (user_input,))",
        "XSS":    "对用户输入进行HTML转义，使用bleach库或html.escape()",
        "CSRF":   "添加CSRF Token验证，每次请求校验Token有效性"
    }
    return fixes.get(vuln_type, "请查阅OWASP Top 10文档")

# ====== 创建Agent ======
tools = [check_vulnerability, get_fix_suggestion]
agent = create_react_agent(llm, tools)

# ====== 运行Agent ======
print("=" * 50)
print("测试1：让Agent分析有漏洞的代码")
print("=" * 50)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": """帮我检查这段代码有没有安全问题，如果有请给出修复建议：
        
query = "SELECT * FROM users WHERE id=" + user_input
db.execute(query)
"""
    }]
})

# 打印最终回复
print(result["messages"][-1].content)

print("\n" + "=" * 50)
print("测试2：让Agent查询修复方案")
print("=" * 50)

result2 = agent.invoke({
    "messages": [{
        "role": "user", 
        "content": "XSS攻击应该怎么修复？"
    }]
})
print(result2["messages"][-1].content)