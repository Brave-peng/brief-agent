"""
日报生成工作流（LangGraph）

工作流设计：
    START → [collect] → [organize] → [generate] → [save] → END

学习要点：
1. 从数据库读取已解析文章
2. 按分类组织文章
3. LLM 生成结构化日报
4. 保存到 reports 表
"""
import logging
import re
from datetime import datetime
from typing import List, Optional, TypedDict
from langgraph.graph import StateGraph, END, START

from src.storage.db import Database
from src.services import get_llm

log = logging.getLogger(__name__)


# ============ 1. State 定义 ============

class DailyReportState(TypedDict):
    """日报生成工作流状态"""
    date_range: str              # 日期范围，如 "2024-01-18"
    articles: List[dict]         # 收集的文章列表
    organized: dict              # 按 category 组织的文章
    report_content: str          # 生成的日报内容
    report_id: Optional[int]     # 保存后的报告 ID
    status: str                  # pending / collecting / organizing / generating / completed / failed
    error: str                   # 错误信息


# ============ 2. Node 函数 ============

def get_db() -> Database:
    """获取数据库单例"""
    from src.storage import get_db as _get_db
    return _get_db()


def collect_articles(state: DailyReportState) -> DailyReportState:
    """从数据库收集指定日期已解析的文章"""
    log.info(f"[collect] 开始收集 {state['date_range']} 的文章")

    try:
        db = get_db()
        articles = db.get_articles_by_date(state["date_range"])

        # 只保留有解析结果的文章
        parsed_articles = [a for a in articles if a.summary_llm]

        log.info(f"[collect] 找到 {len(parsed_articles)} 篇已解析的文章")
        return {"articles": parsed_articles, "status": "collecting"}
    except Exception as e:
        log.error(f"[collect] 收集文章失败: {e}")
        return {"status": "failed", "error": str(e)}


def organize_articles(state: DailyReportState) -> DailyReportState:
    """按 category 分类组织文章"""
    log.info("[organize] 开始分类组织文章")

    if state.get("status") == "failed":
        return state

    articles = state["articles"]
    organized = {}

    for article in articles:
        category = article.get("category", "其他")
        if category not in organized:
            organized[category] = []
        organized[category].append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "summary_llm": article.summary_llm,
            "keywords": article.keywords.split(",") if article.keywords else [],
            "sentiment": article.sentiment,
        })

    # 按每类文章数量排序
    organized = dict(sorted(organized.items(), key=lambda x: -len(x[1])))

    log.info(f"[organize] 分类完成，共 {len(organized)} 个分类")

    return {"organized": organized, "status": "organizing"}


def generate_report(state: DailyReportState) -> DailyReportState:
    """使用 LLM 生成日报"""
    log.info("[generate] 开始生成日报")

    if state.get("status") == "failed":
        return state

    llm = get_llm()

    date_range = state["date_range"]
    organized = state["organized"]

    # 构建带链接的文章摘要
    articles_summary = []
    for category, articles in organized.items():
        articles_summary.append(f"\n## {category} ({len(articles)} 篇)")
        for i, article in enumerate(articles, 1):
            articles_summary.append(f"[{i}] {article['title']}")
            articles_summary.append(f"链接: {article['url']}")
            articles_summary.append(f"核心: {article['summary_llm'][:200]}..." if len(article['summary_llm']) > 200 else f"核心: {article['summary_llm']}")
            articles_summary.append("")

    articles_text = "\n".join(articles_summary)

    prompt = f"""{articles_text}

请根据以上信息生成一份专业的AI日报。

## 输出格式

```
AI三大媒体日报 - {date_range}
📊 今日概览
一句话总结当日AI领域的核心动向（2-3句话，100字以内）。

📰 重点资讯

"""

    for category, articles in organized.items():
        prompt += f"### {category}\n"
        for i, article in enumerate(articles, 1):
            prompt += f"[{i}] {article['title']}\n"
            prompt += f"链接: {article['url']}\n"
            prompt += f"核心内容：{article['summary_llm'][:200]}...\n\n"

    prompt += """```

## 要求
1. 今日概览：2-3句话概括当日AI核心主题
2. 重点资讯：按媒体分类，每家列3-5条最重要新闻
3. 链接标记：使用 [编号] 格式
4. 核心内容：3-5句话概括要点
5. 总字数：800-1500字
6. 使用中文标点符号
"""

    report_content = llm.generate(prompt)

    # 清理 <think> 标签
    report_content = re.sub(r"<think>.*?</think>", "", report_content, flags=re.DOTALL)
    report_content = report_content.strip()

    log.info(f"[generate] 日报生成完成 ({len(report_content)} 字)")

    return {"report_content": report_content, "status": "generating"}


def save_report(state: DailyReportState) -> DailyReportState:
    """保存日报到数据库"""
    log.info("[save] 开始保存日报")

    if state.get("status") == "failed":
        return state

    try:
        db = get_db()
        report_id = db.save_report(
            report_type="daily",
            date_range=state["date_range"],
            content=state["report_content"],
        )
        log.info(f"[save] 日报已保存，ID: {report_id}")
        return {"report_id": report_id, "status": "completed"}
    except Exception as e:
        log.error(f"[save] 保存日报失败: {e}")
        return {"status": "failed", "error": str(e)}


# ============ 3. 构建工作流 ============

def create_daily_report_workflow() -> StateGraph:
    """创建日报生成工作流"""
    workflow = StateGraph(DailyReportState)

    workflow.add_node("collect", collect_articles)
    workflow.add_node("organize", organize_articles)
    workflow.add_node("generate", generate_report)
    workflow.add_node("save", save_report)

    workflow.add_edge(START, "collect")
    workflow.add_edge("collect", "organize")
    workflow.add_edge("organize", "generate")
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", END)

    return workflow


_compiled_workflow = None


def get_workflow():
    """获取编译后的工作流（单例）"""
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = create_daily_report_workflow().compile()
    return _compiled_workflow


# ============ 4. 主函数 ============

def generate_daily_report(date_range: str) -> dict:
    """生成指定日期的日报"""
    app = get_workflow()

    initial_state: DailyReportState = {
        "date_range": date_range,
        "articles": [],
        "organized": {},
        "report_content": "",
        "report_id": None,
        "status": "pending",
        "error": "",
    }

    result = app.invoke(initial_state)

    log.info(f"日报生成完成: status={result['status']}")
    if result.get("status") == "completed":
        log.info(f"报告ID: {result['report_id']}")

    return result


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    # 从命令行参数获取日期，默认为今天
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"日报生成工作流 - {date_str}")
    print("=" * 60)

    result = generate_daily_report(date_str)

    print("\n" + "=" * 60)
    if result["status"] == "completed":
        print("日报内容")
        print("=" * 60)
        print(result["report_content"])
        print(f"\n报告ID: {result['report_id']}")
    else:
        print(f"生成失败: {result.get('error')}")

    print(f"\n最终状态: {result['status']}")
