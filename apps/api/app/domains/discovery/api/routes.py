from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Literal, Optional, Any


from app.api.deps import require_role
from app.workers.celery_app import celery


router = APIRouter()


EntityType = Literal["cooperative", "roaster", "both"]


class SeedRequest(BaseModel):
    entity_type: EntityType = Field(..., description="cooperative|roaster|both")
    max_entities: int = Field(100, ge=1, le=2000)
    dry_run: bool = False
    country_filter: Optional[str] = Field(
        None, description="Override country filter (PE|DE)"
    )

    @field_validator("country_filter")
    @classmethod
    def validate_country_filter(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("country_filter must be a 2-letter ISO code (e.g. PE)")
        return normalized


@router.post("/seed")
def enqueue_seed(
    payload: SeedRequest,
    _: Annotated[None, Depends(require_role("admin", "analyst"))],
):
    """Enqueue a discovery seed job.

    Requires PERPLEXITY_API_KEY or TAVILY_API_KEY configured.
    """
    task = celery.send_task(
        "app.workers.tasks.seed_discovery",
        kwargs=payload.model_dump(),
    )
    return {"task_id": task.id, "status": "queued", "state": "PENDING"}


@router.get("/seed/{task_id}")
@router.get("/tasks/{task_id}")
def get_seed_status(
    task_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=128,
            pattern=r"^[A-Za-z0-9._:-]+$",
            description="Celery task id for discovery jobs",
        ),
    ],
    _: Annotated[None, Depends(require_role("admin", "analyst", "viewer"))],
):
    res = celery.AsyncResult(task_id)
    body: dict[str, Any] = {"task_id": task_id, "state": res.state}
    if res.successful():
        body["result"] = res.result
    elif res.failed():
        body["error"] = "Discovery task failed"
    else:
        # can include progress info if provided via update_state
        if res.info and res.info != "PENDING":
            body["info"] = res.info
    return body
