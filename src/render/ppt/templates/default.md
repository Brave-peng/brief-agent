/* Marp 默认模板 - 简洁商务风格 */
<style>
/* 布局类 */
.stack { display: flex; flex-direction: column; }

/* 左右分栏布局 */
.side-by-side { display: flex; gap: 40px; align-items: center; }
.side-by-side .content { flex: 1; }
.side-by-side .visual { flex: 1; }
.side-by-side.image-left .visual { order: -1; }
.side-by-side.image-right .visual { order: 2; }

/* 图片优先布局 */
.image-first { text-align: center; }
.image-first img { max-height: 55%; margin-bottom: 20px; }

/* 卡片多列布局 */
.cards { display: flex; flex-wrap: wrap; gap: 20px; }
.cards .card { flex: 1 1 45%; padding: 20px; border-radius: 8px; background: #f8f9fa; }

/* 封面样式 */
.cover {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.cover h1 { color: #fff !important; font-size: 2.5em; }
.cover p { color: rgba(255,255,255,0.9); }

/* 结束页样式 */
.ending {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}
.ending h1 { color: #fff !important; }

/* 暗色主题 */
.dark { background-color: #1a1a2e; color: #eee; }
.dark h1, .dark h2 { color: #fff; }
.dark ul li { color: #ddd; }

/* 基础样式 */
section { font-family: "Microsoft YaHei", sans-serif; }
h1 { color: #2c3e50; font-size: 1.8em; }
h2 { color: #34495e; font-size: 1.4em; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
ul li { margin: 8px 0; line-height: 1.6; }
img { border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
</style>
