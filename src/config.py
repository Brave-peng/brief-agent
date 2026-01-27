"""
配置文件加载模块
"""
from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import BaseModel

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()


class LLMConfig(BaseModel):
    provider: str
    api_key: str
    base_url: str
    model: str


class LLMProvidersConfig(BaseModel):
    minimax: Optional[LLMConfig] = None
    modelscope: Optional[LLMConfig] = None
    deepseek: Optional[LLMConfig] = None


class LLMConfigWrapper(BaseModel):
    default: str
    providers: LLMProvidersConfig


class RSSFeedConfig(BaseModel):
    url: str
    name: str


class RSSConfig(BaseModel):
    feeds: list[RSSFeedConfig]
    fetch_interval: int
    timeout: int


class DatabaseConfig(BaseModel):
    path: str


class VectorDBConfig(BaseModel):
    path: str
    collection: str


class LoggingConfig(BaseModel):
    level: str
    file: str
    rotation: str
    retention: str


class SchedulerConfig(BaseModel):
    timezone: str
    report_daily_hour: int
    report_weekly_hour: int


class Config(BaseModel):
    llm: LLMConfigWrapper
    rss: RSSConfig
    database: DatabaseConfig
    vector_db: VectorDBConfig
    logging: LoggingConfig
    scheduler: SchedulerConfig


def load_config(config_path: str | None = None) -> Config:
    """加载配置文件"""
    path: Path
    if config_path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    else:
        path = Path(config_path)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # 替换环境变量
    raw = _replace_env_vars(raw)

    return Config(**raw)


def _replace_env_vars(obj: Any) -> Any:
    """递归替换环境变量引用 ${VAR}"""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            env_key = obj[2:-1]
            return _get_env_or_default(env_key)
        return obj
    elif isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    return obj


def _get_env_or_default(key: str) -> str:
    """获取环境变量，不存在则返回空字符串"""
    import os
    return os.getenv(key, "")
