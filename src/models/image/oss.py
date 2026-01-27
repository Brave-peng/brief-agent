"""
阿里云OSS图片上传模块
"""
import os
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime

import oss2


class OSSUploader:
    """阿里云OSS上传器"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
        base_path: str = "blog/images",
        custom_domain: str = None,
    ):
        """
        初始化OSS上传器

        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            endpoint: OSS endpoint, 如 'oss-cn-hangzhou.aliyuncs.com'
            bucket_name: Bucket名称
            base_path: 上传路径前缀
            custom_domain: 自定义域名（可选），如 'cdn.example.com'
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.base_path = base_path.strip("/")
        self.custom_domain = custom_domain.rstrip("/") if custom_domain else None

        auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(auth, endpoint, bucket_name)

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:12]

    def _get_content_type(self, file_path: str) -> str:
        """获取文件MIME类型"""
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"

    def upload_file(self, local_path: str, remote_name: str = None) -> str:
        """
        上传单个文件到OSS

        Args:
            local_path: 本地文件路径
            remote_name: 远程文件名（可选，默认使用原文件名+哈希）

        Returns:
            文件的公开访问URL
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"文件不存在: {local_path}")

        # 生成远程路径：base_path/年月/hash_filename
        file_hash = self._get_file_hash(str(local_path))
        date_prefix = datetime.now().strftime("%Y%m")

        if remote_name:
            object_key = f"{self.base_path}/{date_prefix}/{remote_name}"
        else:
            # 使用 hash_原文件名 格式，避免重复和冲突
            safe_name = local_path.name.replace(" ", "_")
            object_key = f"{self.base_path}/{date_prefix}/{file_hash}_{safe_name}"

        # 检查是否已存在（避免重复上传）
        if self.bucket.object_exists(object_key):
            print(f"  ⏭️  文件已存在，跳过上传: {object_key}")
        else:
            # 设置Content-Type
            headers = {"Content-Type": self._get_content_type(str(local_path))}

            # 上传文件
            with open(local_path, "rb") as f:
                self.bucket.put_object(object_key, f, headers=headers)
            print(f"  ✅ 上传成功: {local_path.name} -> {object_key}")

        # 返回访问URL
        return self._get_url(object_key)

    def _get_url(self, object_key: str) -> str:
        """获取文件的公开访问URL"""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{object_key}"
        else:
            # 使用bucket默认域名
            return f"https://{self.bucket_name}.{self.endpoint}/{object_key}"

    def upload_directory(self, local_dir: str, extensions: list = None) -> dict:
        """
        上传目录下的所有文件

        Args:
            local_dir: 本地目录路径
            extensions: 允许的文件扩展名列表，如 ['.png', '.jpg']

        Returns:
            {本地文件名: 远程URL} 的映射字典
        """
        local_dir = Path(local_dir)
        if not local_dir.is_dir():
            raise NotADirectoryError(f"目录不存在: {local_dir}")

        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]

        url_mapping = {}

        for file_path in local_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                url = self.upload_file(str(file_path))
                url_mapping[file_path.name] = url

        return url_mapping


def create_uploader_from_env() -> OSSUploader:
    """从环境变量创建OSS上传器"""
    from dotenv import load_dotenv

    load_dotenv()

    required_vars = [
        "OSS_ACCESS_KEY_ID",
        "OSS_ACCESS_KEY_SECRET",
        "OSS_ENDPOINT",
        "OSS_BUCKET_NAME",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"缺少必要的环境变量: {', '.join(missing)}")

    return OSSUploader(
        access_key_id=os.getenv("OSS_ACCESS_KEY_ID"),
        access_key_secret=os.getenv("OSS_ACCESS_KEY_SECRET"),
        endpoint=os.getenv("OSS_ENDPOINT"),
        bucket_name=os.getenv("OSS_BUCKET_NAME"),
        base_path=os.getenv("OSS_BASE_PATH", "blog/images"),
        custom_domain=os.getenv("OSS_CUSTOM_DOMAIN"),
    )


