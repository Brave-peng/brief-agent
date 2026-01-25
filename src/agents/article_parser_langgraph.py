"""
文章解析 Agent - LangGraph 版本

工作流（优化后，单次 LLM 调用）：
    START → [load] → [parse] → [save] → END
"""
import json
import logging
import sys
import re
from pathlib import Path
from typing import TypedDict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END, START

from src.storage.db import Database

log = logging.getLogger(__name__)


# ============ 1. State 定义 ============

class ArticleState(TypedDict):
    """单篇文章解析状态"""
    article_id: int
    title: str
    original_summary: str
    original_content: str

    # LLM 结果
    summary: str
    keywords: List[str]
    category: str
    sentiment: str

    # 状态
    status: str
    error: str


# ============ 2. 工厂函数 ============

_llm_service = None
_db = None


def get_llm():
    """获取 LLM 实例（单例）"""
    from src.services import get_llm as _get_llm

    return _get_llm()


def get_db() -> Database:
    """获取数据库实例（单例）"""
    from src.storage import get_db as _get_db

    return _get_db()


# ============ 3. 节点函数 ============

def load_article(state: ArticleState) -> ArticleState:
    """加载文章"""
    db = get_db()
    article = db.get_article_by_id(state["article_id"])
    if article is None:
        return {"status": "failed", "error": f"Article {state['article_id']} not found"}

    return {
        "title": article.title,
        "original_summary": article.summary,
        "original_content": article.content,
        "status": "loaded",
    }


def parse_article(state: ArticleState) -> ArticleState:
    """单次 LLM 调用完成所有解析"""
    if state.get("status") == "failed":
        return state

    llm = get_llm()

    content_preview = state["original_content"][:2000] if state["original_content"] else state["original_summary"]

    prompt = f"""请分析以下文章，返回 JSON 格式结果。

文章标题：{state['title']}
文章内容：{content_preview}

请返回以下 JSON（不要添加其他文字）：
{{
    "summary": "100字以内的摘要",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "category": "从以下选一个：科技、财经、汽车、房产、教育、游戏、娱乐、体育、军事、国际、社会、其他",
    "sentiment": "positive/negative/neutral"
}}"""

    try:
        response = llm.generate(prompt)

        # 清理 <think> 标签
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

        # 清理可能的 markdown 代码块
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()

        result = json.loads(response)

        return {
            "summary": result.get("summary", ""),
            "keywords": result.get("keywords", []),
            "category": result.get("category", "其他"),
            "sentiment": result.get("sentiment", "neutral"),
            "status": "parsed",
        }
    except json.JSONDecodeError as e:
        log.warning(f"JSON 解析失败: {e}, response: {response[:200]}")
        return {"status": "failed", "error": f"JSON parse error: {e}"}
    except Exception as e:
        log.error(f"解析异常: {e}")
        return {"status": "failed", "error": str(e)}


def save_result(state: ArticleState) -> ArticleState:
    """保存解析结果到 article_analysis 表"""
    if state.get("status") == "failed":
        return state

    from src.storage.db import ArticleAnalysis

    db = get_db()
    analysis = ArticleAnalysis(
        article_id=state["article_id"],
        summary_llm=state["summary"],
        keywords=",".join(state["keywords"]),
        category=state["category"],
        sentiment=state["sentiment"],
        parsed_at=datetime.now().isoformat(),
    )
    db.save_analysis(analysis)
    return {"status": "completed"}


# ============ 4. 构建工作流 ============

def create_workflow() -> StateGraph:
    """创建解析工作流（优化版：3 节点）"""
    workflow = StateGraph(ArticleState)

    workflow.add_node("load", load_article)
    workflow.add_node("parse", parse_article)
    workflow.add_node("save", save_result)

    workflow.add_edge(START, "load")
    workflow.add_edge("load", "parse")
    workflow.add_edge("parse", "save")
    workflow.add_edge("save", END)

    return workflow


_compiled_workflow = None


def get_workflow():
    """获取编译后的工作流（单例）"""
    global _compiled_workflow
    if _compiled_workflow is None:
        _compiled_workflow = create_workflow().compile()
    return _compiled_workflow


# ============ 5. 主函数 ============

def parse_single(article_id: int) -> dict:
    """解析单篇文章"""
    app = get_workflow()

    initial_state: ArticleState = {
        "article_id": article_id,
        "title": "",
        "original_summary": "",
        "original_content": "",
        "summary": "",
        "keywords": [],
        "category": "",
        "sentiment": "neutral",
        "status": "pending",
        "error": "",
    }

    return app.invoke(initial_state)


def parse_batch(article_ids: List[int]) -> List[dict]:
    """批量解析多篇文章（并发）"""
    app = get_workflow()

    initial_states = [
        {
            "article_id": aid,
            "title": "",
            "original_summary": "",
            "original_content": "",
            "summary": "",
            "keywords": [],
            "category": "",
            "sentiment": "neutral",
            "status": "pending",
            "error": "",
        }
        for aid in article_ids
    ]

    return app.batch(initial_states)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("测试单篇解析（优化版）...")
    result = parse_single(1)
    print(f"状态: {result['status']}")
    if result["status"] == "completed":
        print(f"摘要: {result['summary'][:100]}...")
        print(f"关键词: {result['keywords']}")
        print(f"分类: {result['category']}")
        print(f"情感: {result['sentiment']}")
    else:
        print(f"错误: {result.get('error')}")
