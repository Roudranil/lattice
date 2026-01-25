from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

base_dir = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # model families
    # agent
    reasoning_model: str = "zai-org/GLM-4.5-Air"
    # reasoning_model: str = "deepseek-ai/DeepSeek-V3-0324-fast"
    # reasoning_model: str = "meta-llama/Llama-3.3-70B-Instruct-fast"
    tool_user_model: str = "Qwen/Qwen3-30B-A3B-Instruct-2507"
    writing_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-fast"
    # embeddings
    snowflake: str = "Snowflake/snowflake-arctic-embed-l-v2.0"
    specter: str = "allenai/specter2_base"
    _specter_adapter: str = "allenai/specter2"
    # reranker
    encoder_model: str = "m3rg-iitd/matscibert"
    reranker_model: str = "Qwen/Qwen3-Reranker-0.6B"

    # environment variables
    model_config = SettingsConfigDict(
        env_file=base_dir / ".env",
        env_file_encoding="UTF-8",
        extra="allow",
        case_sensitive=True,
    )

    # paths
    # resolve the following paths from __file__ at runtime
    # in comments = paths relative to __file__
    # data_dir = "../data"
    # logs_dir = "../logs"
    # agents_dir = "../agents/"
    # skills_dir = "../skills/"
    # tools_dir = "../tools/"

    base_dir: Path = base_dir

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / "logs"

    @property
    def agents_dir(self) -> Path:
        return self.base_dir / "agents"

    @property
    def skills_dir(self) -> Path:
        return self.base_dir / "skills"

    @property
    def tools_dir(self) -> Path:
        return self.base_dir / "tools"


@lru_cache
def get_settings():
    return Settings()
