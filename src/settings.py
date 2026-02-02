import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings

base_dir = Path(__file__).resolve().parent.parent


class EnvSettings:
    def __init__(self, env_file: Path | None = None):
        load_dotenv(env_file)

    def __getattr__(self, key: str) -> str:
        try:
            return os.environ[key]
        except KeyError:
            raise AttributeError(f"Environment variable '{key}' not set")


class PathSettings(BaseSettings):
    # paths
    # resolve the following paths from __file__ at runtime
    # in comments = paths relative to __file__
    # data_dir = "../data"
    # logs_dir = "../logs"
    # agents_dir = "../agents/"
    # skills_dir = "../skills/"
    # tools_dir = "../tools/"

    base_dir: Path = base_dir

    @computed_field
    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @computed_field
    @property
    def logs_dir(self) -> Path:
        return self.base_dir / "logs"

    @computed_field
    @property
    def agents_dir(self) -> Path:
        return self.base_dir / "agents"

    @computed_field
    @property
    def skills_dir(self) -> Path:
        return self.base_dir / "skills"

    @computed_field
    @property
    def tools_dir(self) -> Path:
        return self.base_dir / "tools"


class HfModelSettings(BaseSettings):
    chat: str = "EssentialAI/rnj-1-instruct:together"  # some weird model with both struc and tool
    embedding_snowflake: str = "Snowflake/snowflake-arctic-embed-l-v2.0"
    embedding_specter: str = "allenai/specter2_base"
    _embedding_specter_adapter: str = "allenai/specter2"
    encoder: str = "m3rg-iitd/matscibert"
    reranker: str = "Qwen/Qwen3-Reranker-0.6B"
    # for gpt-oss-20b, hyperbolic is the cheapest provider and also provides function calling
    router: str = "openai/gpt-oss-20b:together"


class NebiusModelSettings(BaseSettings):
    reasoning: str = "zai-org/GLM-4.5-Air"
    tool_user: str = "Qwen/Qwen3-30B-A3B-Instruct-2507"
    chat: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-fast"
    embedding_baai_bge: str = "BAAI/bge-multilingual-gemma2"
    router: str = "openai/gpt-oss-20b"


class ModelSettings(BaseSettings):
    hf: HfModelSettings = HfModelSettings()
    nebius: NebiusModelSettings = NebiusModelSettings()


class Settings(BaseSettings):
    models: ModelSettings = ModelSettings()
    paths: PathSettings = PathSettings()
    env: EnvSettings = Field(
        default_factory=lambda: EnvSettings(base_dir / ".env"),
        exclude=True,
    )


@lru_cache
def get_settings():
    return Settings()
