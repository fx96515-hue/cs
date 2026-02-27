from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any


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


@router.post("/seed")
def enqueue_seed(payload: SeedRequest, _=Depends(require_role("admin", "analyst"))):
    """Enqueue a discovery seed job.

    Requires PERPLEXITY_API_KEY configured.
    """
    task = celery.send_task(
        "app.workers.tasks.seed_discovery",
        kwargs=payload.model_dump(),
    )
    return {"task_id": task.id, "state": "PENDING"}


@router.get("/seed/{task_id}")
def get_seed_status(
    task_id: str, _=Depends(require_role("admin", "analyst", "viewer"))
):
    res = celery.AsyncResult(task_id)
    body: dict[str, Any] = {"task_id": task_id, "state": res.state}
    if res.successful():
        body["result"] = res.result
    elif res.failed():
        body["error"] = str(res.result)
    else:
        # can include progress info if provided via update_state
        if res.info and res.info != "PENDING":
            body["info"] = res.info
    return body
