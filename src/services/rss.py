"""
RSS 抓取服务模块
"""
import feedparser
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
import httpx

from src.config import RSSConfig, RSSFeedConfig
from src.storage.db import Database, Article
from src.storage.logger import logger


class RSSFetcher:
    """RSS 订阅源抓取器"""

    def __init__(self, config: RSSConfig, db: Database):
        self.config = config
        self.db = db

    def fetch_all(self) -> int:
        """抓取所有配置的 RSS 源"""
        total_fetched = 0
        for feed_config in self.config.feeds:
            try:
                fetched = self.fetch_feed(feed_config)
                total_fetched += fetched
                logger.info(f"抓取 {feed_config.name}: 获取 {fetched} 篇新文章")
            except Exception as e:
                logger.error(f"抓取 {feed_config.name} 失败: {e}")
        return total_fetched

    def fetch_feed(self, feed_config: RSSFeedConfig) -> int:
        """抓取单个 RSS 源"""
        try:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(feed_config.url, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"请求失败 {feed_config.url}: {e}")
            return False

        feed = feedparser.parse(response.content)

        if hasattr(feed, "bozo_exception"):
            logger.error(f"RSS 解析失败 {feed_config.url}: {feed.bozo_exception}")
            return False

        articles = []
        for entry in feed.entries:
            article = self._parse_entry(entry, feed_config.name)
            if article:
                articles.append(article)

        # 批量保存到数据库
        for article in articles:
            self.db.upsert_article(article)

        return len(articles)

    def _parse_entry(
        self, entry: feedparser.FeedParserDict, feed_name: str
    ) -> Optional[Article]:
        """解析单个 RSS 条目"""
        # 获取发布时间
        published = datetime.now()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])

        # 提取摘要和内容
        summary = ""
        content = ""
        if hasattr(entry, "summary"):
            summary = self._clean_html(entry.summary)
        if hasattr(entry, "content"):
            for c in entry.content:
                content += c.value
        elif hasattr(entry, "description"):
            content = self._clean_html(entry.description)

        # 提取标签
        tags = [tag.term for tag in entry.tags] if hasattr(entry, "tags") else []
        tags_str = ",".join(tags)  # 转为逗号分隔字符串

        # 构建 Article 对象
        article = Article(
            feed_name=feed_name,
            title=entry.get("title", "无标题"),
            url=entry.get("link", ""),
            summary=summary[:500] if summary else "",
            content=content[:5000] if content else "",
            published_at=published,
            fetched_at=datetime.now(),
            tags=tags_str,
        )

        return article

    def _clean_html(self, html: str) -> str:
        """清理 HTML 标签，提取纯文本"""
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(strip=True)


class RSSScheduler:
    """RSS 定时抓取调度器"""

    def __init__(self, fetcher: RSSFetcher, interval: int = 3600):
        self.fetcher = fetcher
        self.interval = interval

    def start(self):
        """启动定时任务"""
        import time
        while True:
            self.fetcher.fetch_all()
            time.sleep(self.interval)
