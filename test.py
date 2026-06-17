from openai import OpenAI

client = OpenAI(
    api_key="5f7581e7842a485eb5dbef89d8ef807e.waiqxzpLJptwdt7I",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

# 用列表存对话历史
history = [
    
    {"role": "system", "content": """
    你是一个网络安全漏洞分析专家。
    
    回答规则：
    - 只分析安全相关代码问题
    - 必须按【漏洞名称】【危险等级】【修复方案】格式输出
    - 分析时要一步步推理，不要跳步
    """}

#   {"role": "user", "content": """
# 分析以下代码是否存在安全漏洞，请一步步思考：

# ```python
# query = "SELECT * FROM users WHERE id=" + user_input
# db.execute(query)
# ```

# 请按步骤分析：
# 第一步：识别代码功能
# 第二步：找出潜在风险点  
# 第三步：给出修复建议
# """}


# 改变system里的内容，AI的行为完全不同
# 变成只回答安全问题的专家
# {"role": "system", "content": """
# 你是一个网络安全专家。
# 规则：
# 1. 只回答网络安全相关问题
# 2. 其他问题一律回复：'这不在我的专业范围内'
# 3. 回答要简洁专业
# """}
]

print("开始对话！输入 quit 退出\n")

while True:
    user_input = input("你：")
    if user_input == "quit":
        break
    
    # 把你说的话加入历史
    history.append({"role": "user", "content": user_input})
    
    # 把完整历史发给AI
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=history
    )
    
    ai_reply = response.choices[0].message.content
    
    # 把AI回复也存入历史
    history.append({"role": "assistant", "content": ai_reply})
    
    print(f"AI：{ai_reply}\n")