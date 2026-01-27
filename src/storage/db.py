"""
SQLite 数据库操作模块 - 使用 SQLModel ORM
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlmodel.sql.expression import desc


# ============ 模型定义 ============

class Article(SQLModel, table=True):
    """RSS 文章模型（原文，只读）"""
    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    feed_name: str
    title: str
    url: str = Field(unique=True)
    summary: str = ""
    content: str = ""
    published_at: datetime
    fetched_at: datetime
    tags: str = ""  # 逗号分隔


class ArticleAnalysis(SQLModel, table=True):
    """文章解析结果（可重跑）"""
    __tablename__ = "article_analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(unique=True, foreign_key="articles.id")
    summary_llm: str = ""
    keywords: str = ""  # 逗号分隔
    category: str = ""
    sentiment: str = "neutral"
    parsed_at: str = ""


class FeedConfig(SQLModel, table=True):
    """RSS 源配置"""
    __tablename__ = "feed_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True)
    name: str
    last_fetched: Optional[str] = None


class Report(SQLModel, table=True):
    """报告"""
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    report_type: str
    date_range: str
    content: str
    created_at: str


# ============ 数据库管理 ============

class Database:
    """SQLite 数据库管理"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # 使用 WAL 模式 + 超时，支持并发读写
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"timeout": 30, "check_same_thread": False},
        )
        self._init_db()
        self._enable_wal()

    def _init_db(self):
        """初始化数据库表"""
        SQLModel.metadata.create_all(self.engine)

    def _enable_wal(self):
        """启用 WAL 模式，提升并发性能"""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA busy_timeout=30000"))

    def _session(self) -> Session:
        """获取数据库 session"""
        return Session(self.engine)

    # ============ Article 操作 ============

    def upsert_article(self, article: Article) -> int | None:
        """插入或更新文章"""
        with self._session() as session:
            # 检查是否存在
            existing = session.exec(
                select(Article).where(Article.url == article.url)
            ).first()

            if existing:
                # 更新
                existing.feed_name = article.feed_name
                existing.title = article.title
                existing.summary = article.summary
                existing.content = article.content
                existing.published_at = article.published_at
                existing.fetched_at = article.fetched_at
                existing.tags = article.tags
                session.add(existing)
                session.commit()
                return existing.id
            else:
                # 插入
                session.add(article)
                session.commit()
                session.refresh(article)
                return article.id

    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        """根据 ID 获取文章"""
        with self._session() as session:
            return session.get(Article, article_id)

    def get_articles(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Article]:
        """获取指定日期范围的文章"""
        with self._session() as session:
            query = select(Article)

            if start_date:
                query = query.where(Article.published_at >= start_date)
            if end_date:
                query = query.where(Article.published_at <= end_date)

            query = query.order_by(desc(Article.published_at)).limit(limit)
            return list(session.exec(query).all())

    def get_articles_by_date(self, start: str, end: str | None = None) -> List[Article]:
        """获取指定日期范围的文章（字符串格式 YYYY-MM-DD）"""
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d") if end else start_date
        return self.get_articles(start_date=start_date, end_date=end_date, limit=100)

    def get_unparsed_articles(self, limit: int = 100) -> List[Article]:
        """获取未解析的文章（不在 article_analysis 表中）"""
        with self._session() as session:
            # 子查询：已解析的 article_id
            parsed_ids = select(ArticleAnalysis.article_id)

            query = (
                select(Article)
                .where(Article.id.not_in(parsed_ids))
                .order_by(desc(Article.published_at))
                .limit(limit)
            )
            return list(session.exec(query).all())

    # ============ ArticleAnalysis 操作 ============

    def save_analysis(self, analysis: ArticleAnalysis) -> int:
        """保存或更新解析结果"""
        with self._session() as session:
            existing = session.exec(
                select(ArticleAnalysis).where(
                    ArticleAnalysis.article_id == analysis.article_id
                )
            ).first()

            if existing:
                existing.summary_llm = analysis.summary_llm
                existing.keywords = analysis.keywords
                existing.category = analysis.category
                existing.sentiment = analysis.sentiment
                existing.parsed_at = analysis.parsed_at
                session.add(existing)
                session.commit()
                return existing.id
            else:
                session.add(analysis)
                session.commit()
                session.refresh(analysis)
                return analysis.id

    def get_analysis_by_article_id(self, article_id: int) -> Optional[ArticleAnalysis]:
        """根据文章 ID 获取解析结果"""
        with self._session() as session:
            return session.exec(
                select(ArticleAnalysis).where(
                    ArticleAnalysis.article_id == article_id
                )
            ).first()

    def get_parsed_articles(
        self, limit: int = 100
    ) -> List[tuple[Article, ArticleAnalysis]]:
        """获取已解析的文章（返回文章和解析结果）"""
        with self._session() as session:
            query = (
                select(Article, ArticleAnalysis)
                .join(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)
                .order_by(desc(Article.published_at))
                .limit(limit)
            )
            results = session.exec(query).all()
            return [(article, analysis) for article, analysis in results]

    def clear_all_analysis(self) -> int:
        """清空所有解析结果（重跑用）"""
        with self._session() as session:
            count = session.exec(select(ArticleAnalysis)).all()
            for analysis in count:
                session.delete(analysis)
            session.commit()
            return len(count)

    # ============ Report 操作 ============

    def save_report(self, report_type: str, date_range: str, content: str) -> int:
        """保存报告"""
        with self._session() as session:
            report = Report(
                report_type=report_type,
                date_range=date_range,
                content=content,
                created_at=datetime.now().isoformat(),
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report.id

    def get_reports(
        self, report_type: Optional[str] = None, limit: int = 10
    ) -> List[Report]:
        """获取报告列表"""
        with self._session() as session:
            query = select(Report)
            if report_type:
                query = query.where(Report.report_type == report_type)
            query = query.order_by(desc(Report.created_at)).limit(limit)
            return list(session.exec(query).all())
