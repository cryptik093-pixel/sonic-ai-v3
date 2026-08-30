from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load apps/api/.env
load_dotenv(Path(__file__).parent / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("SONIC_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("SONIC_OPENAI_MODEL", "gpt-4o"),
            openai_base_url=os.getenv("SONIC_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )


settings = Settings.from_env()
