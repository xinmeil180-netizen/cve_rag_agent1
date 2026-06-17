"""
从NVD（国家漏洞数据库）官方API获取真实CVE漏洞数据
并清洗、格式化为RAG知识库可用的文本文档
"""
import requests
import time
import json

# ====== 配置 ======
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEYWORD = "SQL injection"   # 搜索关键词，可以换成 "XSS"、"buffer overflow" 等
RESULTS_LIMIT = 30          # 想获取多少条数据（建议先测试用小数字）


def fetch_cve_data(keyword: str, limit: int = 30):
    """调用NVD API，按关键词搜索CVE数据"""
    params = {
        "keywordSearch": keyword,
        "resultsPerPage": limit
    }

    print(f"正在请求NVD API，关键词：{keyword} ...")
    response = requests.get(NVD_API_URL, params=params, timeout=30)

    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        print(response.text)
        return []

    data = response.json()
    print(f"获取成功，本次返回 {len(data.get('vulnerabilities', []))} 条数据")
    return data.get("vulnerabilities", [])


def clean_and_extract(raw_items: list) -> list:
    """
    数据清洗核心逻辑：
    - 提取关键字段（CVE编号、描述、危险评分、发布日期）
    - 过滤掉没有英文描述或没有评分的脏数据
    - 统一格式
    """
    cleaned = []

    for item in raw_items:
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")

        # 提取英文描述（NVD返回多语言描述列表，取英文）
        descriptions = cve.get("descriptions", [])
        eng_desc = ""
        for d in descriptions:
            if d.get("lang") == "en":
                eng_desc = d.get("value", "")
                break

        # 过滤：没有描述的脏数据直接丢弃
        if not eng_desc or not cve_id:
            continue

        # 提取CVSS评分
        # 数据治理说明：NVD不同年代CVE使用不同CVSS版本评分。
        # 早期数据（约2015年前）通常只有v2评分，且v2的baseSeverity
        # 字段经常缺失，需要按官方阈值用baseScore自行换算等级
        # （v2标准：0-3.9低危，4.0-6.9中危，7.0-10高危）
        severity = "未知"
        score = "未知"
        cvss_version = "无评分数据"
        metrics = cve.get("metrics", {})

        if "cvssMetricV31" in metrics:
            cvss = metrics["cvssMetricV31"][0]["cvssData"]
            severity = cvss.get("baseSeverity", "未知")
            score = cvss.get("baseScore", "未知")
            cvss_version = "v3.1"
        elif "cvssMetricV30" in metrics:
            cvss = metrics["cvssMetricV30"][0]["cvssData"]
            severity = cvss.get("baseSeverity", "未知")
            score = cvss.get("baseScore", "未知")
            cvss_version = "v3.0"
        elif "cvssMetricV2" in metrics:
            v2_item = metrics["cvssMetricV2"][0]
            cvss = v2_item["cvssData"]
            score = cvss.get("baseScore", "未知")
            cvss_version = "v2.0"
            severity = v2_item.get("baseSeverity", "")
            if not severity and isinstance(score, (int, float)):
                if score >= 7.0:
                    severity = "HIGH"
                elif score >= 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

        published = cve.get("published", "未知")[:10]  # 只取日期部分

        cleaned.append({
            "cve_id": cve_id,
            "description": eng_desc.strip(),
            "severity": severity,
            "score": score,
            "cvss_version": cvss_version,
            "published": published
        })

    return cleaned


def save_as_knowledge_base(cleaned_data: list, output_file: str = "cve_data.txt"):
    """把清洗后的数据格式化成知识库可读的文本格式"""
    with open(output_file, "w", encoding="utf-8") as f:
        for item in cleaned_data:
            block = f"""【{item['cve_id']}】
危险等级：{item['severity']}（CVSS{item['cvss_version']}评分：{item['score']}）
发布日期：{item['published']}
漏洞描述：{item['description']}

"""
            f.write(block)

    print(f"已保存 {len(cleaned_data)} 条清洗后的数据到 {output_file}")


if __name__ == "__main__":
    raw = fetch_cve_data(KEYWORD, RESULTS_LIMIT)

    if raw:
        cleaned = clean_and_extract(raw)
        print(f"清洗完成，原始 {len(raw)} 条 -> 有效 {len(cleaned)} 条")
        save_as_knowledge_base(cleaned, "cve_data.txt")

        # 打印第一条看看效果
        if cleaned:
            print("\n示例数据：")
            print(json.dumps(cleaned[0], ensure_ascii=False, indent=2))
    else:
        print("未获取到数据，请检查网络或关键词")