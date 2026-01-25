"""
检查 HTML 结构
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.db import Database
from bs4 import BeautifulSoup
import httpx


def main():
    db = Database("data/sqlite/rss.db")

    # 获取一篇文章
    articles = db.get_articles(limit=1)
    if not articles:
        print("没有文章")
        return

    article = articles[0]
    print(f"标题: {article.title}")
    print(f"URL: {article.url}")
    print(f"现有 content 长度: {len(article.content)}")
    print("-" * 50)

    # 请求完整页面
    print("正在请求页面...")
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(article.url, follow_redirects=True)
            response.raise_for_status()

        html = response.text
        print(f"HTML 长度: {len(html)}")

        # 解析看看结构
        soup = BeautifulSoup(html, 'html.parser')

        print("\n" + "=" * 50)
        print("HTML 结构分析")
        print("=" * 50)

        # 找标题
        title_tag = (
            soup.find('h1') or
            soup.find(class_=lambda x: x and 'title' in x.lower()) or
            soup.find('meta', property='og:title')
        )
        print(f"\n标题元素: {title_tag}")
        if title_tag:
            print(f"标题文本: {title_tag.get_text(strip=True)[:100]}")

        # 找作者
        author_tag = (
            soup.find(rel='author') or
            soup.find(class_=lambda x: x and 'author' in x.lower()) or
            soup.find('meta', attrs={'name': 'author'}) or
            soup.find(class_=lambda x: x and 'writer' in x.lower())
        )
        print(f"\n作者元素: {author_tag}")
        if author_tag:
            print(f"作者文本: {author_tag.get_text(strip=True)}")

        # 找正文
        content_tag = (
            soup.find('article') or
            soup.find(class_=lambda x: x and 'content' in x.lower()) or
            soup.find(class_=lambda x: x and 'article' in x.lower()) or
            soup.find('main') or
            soup.find('div', id='content')
        )
        print(f"\n正文元素: {content_tag}")
        if content_tag:
            text = content_tag.get_text(strip=True)
            print(f"正文长度: {len(text)}")
            print(f"正文前200字: {text[:200]}")

        # 打印部分 HTML（供调试）
        print("\n" + "=" * 50)
        print("部分 HTML 源码（前 3000 字符）")
        print("=" * 50)
        print(html[:3000])

    except Exception as e:
        print(f"请求失败: {e}")


if __name__ == "__main__":
    main()
