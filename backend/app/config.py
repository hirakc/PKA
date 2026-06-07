"""Runtime configuration and tunable settings.

Settings are persisted in the DB (see ``repositories.SettingsRepository``); this module
holds the *defaults* and process-level paths/keys read from the environment.

AI-concept note: keeping every knob (model, top_k, max_iterations, token budget,
web default) in one editable place is what lets you experiment and *see* how each
choice changes the agent's behavior (PRD FR-19).
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

# --- Paths -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("PKA_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = Path(os.environ.get("PKA_DB_PATH", DATA_DIR / "pka.db"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --- Provider selection (env) ------------------------------------------------
# Default to fully-local/offline providers so the app runs with zero API keys.
# Swap to "openai" / "tavily" by setting these env vars + the matching key.
EMBEDDING_PROVIDER = os.environ.get("PKA_EMBEDDING_PROVIDER", "local")
LLM_PROVIDER = os.environ.get("PKA_LLM_PROVIDER", "mock")
WEB_SEARCH_PROVIDER = os.environ.get("PKA_WEB_PROVIDER", "mock")
RERANKER = os.environ.get("PKA_RERANKER", "lexical")

# --- API keys (stored locally / read from env) -------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


@dataclass
class Settings:
    """User-tunable settings (persisted; editable from the Settings screen)."""

    # Models
    model: str = os.environ.get("PKA_MODEL", "gpt-4o-mini")
    embedding_model: str = os.environ.get("PKA_EMBEDDING_MODEL", "local-hash-256")

    # Retrieval
    top_k: int = 5
    rerank_enabled: bool = True

    # Agent guardrails (LLD section 10)
    max_iterations: int = 6
    token_budget: int = 12000

    # Web fallback
    web_enabled_default: bool = True

    # Pricing (USD per 1K tokens) used for cost estimates (NFR-5)
    price_per_1k_input: float = 0.00015
    price_per_1k_output: float = 0.0006

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_SETTINGS = Settings()
