"""Settings API (US-14, FR-19, FR-20)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import DEFAULT_SETTINGS, Settings
from ..repositories import SettingsRepository

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsPayload(BaseModel):
    model: str | None = None
    embedding_model: str | None = None
    top_k: int | None = None
    rerank_enabled: bool | None = None
    max_iterations: int | None = None
    token_budget: int | None = None
    web_enabled_default: bool | None = None
    price_per_1k_input: float | None = None
    price_per_1k_output: float | None = None


@router.get("")
def get_settings():
    return SettingsRepository().get().to_dict()


@router.put("")
def update_settings(payload: SettingsPayload):
    repo = SettingsRepository()
    current = repo.get().to_dict()
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    current.update(updates)
    saved = repo.save(Settings(**{k: current[k] for k in DEFAULT_SETTINGS.to_dict()}))
    return saved.to_dict()
