"""
快速抓取示例数据
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config, RSSConfig, RSSFeedConfig
from src.storage.db import Database, Article
from src.services.rss import RSSFetcher
from datetime import datetime


def main():
    """抓取一些真实的 RSS 源"""
    # 真实的 RSS 源
    sample_feeds = [
        RSSFeedConfig(
            name="36氪",
            url="https://36kr.com/feed",
        ),
        RSSFeedConfig(
            name="InfoQ",
            url="https://www.infoq.cn/rss",
        ),
        RSSFeedConfig(
            name="量子位",
            url="https://www.qbitai.com/feed",
        ),
    ]

    # 创建临时配置
    rss_config = RSSConfig(
        feeds=sample_feeds,
        fetch_interval=3600,
        timeout=30,
    )

    # 创建数据库
    db = Database("data/sqlite/rss.db")

    # 创建抓取器并抓取
    fetcher = RSSFetcher(rss_config, db)

    print("=" * 50)
    print("开始抓取 RSS 数据")
    print("=" * 50)

    count = fetcher.fetch_all()

    print(f"\n共抓取 {count} 篇文章")

    # 显示数据示例
    articles = db.get_articles(limit=5)
    print("\n" + "=" * 50)
    print("数据示例")
    print("=" * 50)

    for a in articles:
        print(f"\n标题: {a.title}")
        print(f"来源: {a.feed_name}")
        print(f"摘要: {a.summary[:100]}..." if a.summary else "摘要: 无")


if __name__ == "__main__":
    main()
