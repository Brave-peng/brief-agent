"""
向量数据库模块 - 基于 ChromaDB 的 RAG 存储
"""
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.config import VectorDBConfig
from src.storage.db import Article


class VectorStore:
    """ChromaDB 向量存储"""

    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.path = Path(config.path)
        self.path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.path),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=config.collection,
            metadata={"description": "RSS Articles Vector Store"},
        )

        # 初始化嵌入模型
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def add_article(self, article: Article):
        """添加文章到向量库"""
        text = f"{article.title}\n\n{article.summary}"
        embedding = self.embedder.encode(text).tolist()

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[f"article_{article.id}"],
            metadatas=[
                {
                    "article_id": article.id,
                    "feed_name": article.feed_name,
                    "title": article.title,
                    "url": article.url,
                    "published_at": article.published_at.isoformat(),
                }
            ],
        )

    def add_articles(self, articles: List[Article]):
        """批量添加文章"""
        texts = [f"{a.title}\n\n{a.summary}" for a in articles]
        embeddings = self.embedder.encode(texts).tolist()

        ids = [f"article_{a.id}" for a in articles]
        metadatas = [
            {
                "article_id": a.id,
                "feed_name": a.feed_name,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at.isoformat(),
            }
            for a in articles
        ]

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

    def search(
        self, query: str, n_results: int = 5, feed_name: Optional[str] = None
    ) -> List[dict]:
        """语义搜索"""
        embedding = self.embedder.encode(query).tolist()

        where = {}
        if feed_name:
            where["feed_name"] = feed_name

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
        )

        return self._format_results(results)

    def search_by_date(
        self, query: str, start_date: str, end_date: str, n_results: int = 5
    ) -> List[dict]:
        """按日期范围搜索"""
        embedding = self.embedder.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={
                "$and": [
                    {"published_at": {"$gte": start_date}},
                    {"published_at": {"$lte": end_date}},
                ]
            },
        )

        return self._format_results(results)

    def delete_article(self, article_id: int):
        """删除文章"""
        self.collection.delete(ids=[f"article_{article_id}"])

    def count(self) -> int:
        """获取文章数量"""
        return self.collection.count()

    def _format_results(self, results) -> List[dict]:
        """格式化搜索结果"""
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return formatted

    def close(self):
        """关闭连接"""
        self.client.close()
