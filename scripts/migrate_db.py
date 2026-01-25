"""
数据库迁移脚本 - 使用 SQLModel 创建新表结构

功能：
1. 创建 article_analysis 表（如不存在）
2. 迁移旧 articles 表中的解析字段到 article_analysis
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3


def migrate():
    db_path = "data/sqlite/rss.db"

    print("=" * 50)
    print("数据库迁移：SQLModel 表结构")
    print("=" * 50)

    # 先用 SQLModel 创建新表
    print("\n[1/3] 使用 SQLModel 初始化表结构...")
    from src.storage.db import Database
    db = Database(db_path)
    print("  ✓ 表结构已创建")

    # 检查是否需要迁移旧数据
    print("\n[2/3] 检查并迁移旧解析数据...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("PRAGMA table_info(articles)")
    columns = {row['name'] for row in cursor.fetchall()}

    if 'parsed_at' in columns:
        rows = conn.execute("""
            SELECT id, summary_llm, keywords, category, sentiment, parsed_at
            FROM articles
            WHERE parsed_at IS NOT NULL AND parsed_at != ''
        """).fetchall()

        if rows:
            print(f"  发现 {len(rows)} 条旧解析记录")
            migrated = 0
            for row in rows:
                existing = conn.execute(
                    "SELECT id FROM article_analysis WHERE article_id = ?",
                    (row['id'],)
                ).fetchone()

                if not existing:
                    conn.execute("""
                        INSERT INTO article_analysis
                        (article_id, summary_llm, keywords, category, sentiment, parsed_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],
                        row['summary_llm'] or '',
                        row['keywords'] or '',
                        row['category'] or '',
                        row['sentiment'] or 'neutral',
                        row['parsed_at'],
                    ))
                    migrated += 1

            conn.commit()
            print(f"  ✓ 迁移 {migrated} 条记录")
        else:
            print("  没有旧解析数据需要迁移")
    else:
        print("  articles 表无旧解析字段，跳过")

    # 统计
    print("\n[3/3] 验证结果...")
    article_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    analysis_count = conn.execute("SELECT COUNT(*) FROM article_analysis").fetchone()[0]

    print(f"  - articles: {article_count} 条")
    print(f"  - article_analysis: {analysis_count} 条")

    conn.close()

    print("\n" + "=" * 50)
    print("迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    migrate()
