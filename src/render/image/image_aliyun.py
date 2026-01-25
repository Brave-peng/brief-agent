import os
import json
import time
import requests
from http import HTTPStatus
import dashscope
from dashscope import ImageSynthesis
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# 加载 .env 文件
load_dotenv()

# --- 配置 ---
# 检查 API Key
if not os.getenv('DASHSCOPE_API_KEY'):
    print("❌ 错误: 未找到 DASHSCOPE_API_KEY，请在 .env 文件中配置。")
    exit(1)

JSON_PATH = 'scripts/被折叠的增长：为什么勤劳致富越来越难.json'
OUTPUT_DIR = 'assets/images'
MAX_WORKERS = 2  # 降低并发数，避免限流

# 统一风格提示词
STYLE_PREFIX = "Simple hand-drawn sketch, black and white line art, clean white background, minimalist style, doodle style, abstract concept, large negative space, "
STYLE_SUFFIX = ", high quality, clean lines, no text, no words, no typography, no watermark, no signature"

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_single_task(seg):
    """单个生成任务函数"""
    image_path = seg.get('image_path')
    visual_desc = seg.get('visual')
    seg_id = seg['id']

    # 检查逻辑
    if not image_path:
        return f"Segment {seg_id}: 跳过 (无路径)"
        
    normalized_path = image_path.replace('\\', '/')
    
    # 只处理 assets/images/ 下的文件
    if 'assets/images/' not in normalized_path:
        return f"Segment {seg_id}: 跳过 (手动指定图表)"

    # 检查文件是否已存在
    if os.path.exists(image_path):
        return f"Segment {seg_id}: 跳过 (已存在)"

    print(f"🚀 [Seg {seg_id}] 开始生成: {visual_desc[:20]}...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 构建完整提示词
            full_prompt = STYLE_PREFIX + visual_desc + STYLE_SUFFIX
            
            resp = ImageSynthesis.call(
                model="wanx2.1-t2i-plus",
                prompt=full_prompt,
                n=1,
                size='1024*1024'
            )

            if resp.status_code == HTTPStatus.OK:
                img_url = resp.output.results[0].url
                img_data = requests.get(img_url).content
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                return f"✅ [Seg {seg_id}] 完成: {image_path}"
            
            # 检查是否是限流错误
            elif resp.code == 'Throttling.RateQuota':
                wait_time = (attempt + 1) * 2
                print(f"⚠️ [Seg {seg_id}] 限流重试 ({attempt+1}/{max_retries}), 等待 {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                return f"❌ [Seg {seg_id}] 失败: {resp.code}, {resp.message}"

        except Exception as e:
            # 网络异常等也稍微等待重试
            print(f"⚠️ [Seg {seg_id}] 异常重试: {e}")
            time.sleep(2)
            if attempt == max_retries - 1:
                return f"❌ [Seg {seg_id}] 最终异常: {e}"
    
    return f"❌ [Seg {seg_id}] 重试次数耗尽"

def main():
    print(f"开始并发生成任务 (并发数: {MAX_WORKERS})...")
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get('segments', [])
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_seg = {}
        for seg in segments:
            image_path = seg.get('image_path')
            # 提前检查：如果存在且大于0字节，直接打印跳过，不进线程池
            if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                print(f"Segment {seg['id']}: 跳过 (已存在)")
                continue
            
            future = executor.submit(generate_single_task, seg)
            future_to_seg[future] = seg
        
        # 获取结果
        if not future_to_seg:
            print("🎉 所有图片已生成完毕，无需执行。")
            return

        for future in as_completed(future_to_seg):
            try:
                result = future.result()
                print(result)
            except Exception as exc:
                print(f"任务执行异常: {exc}")

if __name__ == '__main__':
    main()
