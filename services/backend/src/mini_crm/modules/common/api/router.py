from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.common.context import RequestContext

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/context")
async def get_context(context: RequestContext = Depends(get_request_context)) -> dict[str, int | str]:
    return {
        "user_id": context.user.id,
        "role": context.organization.role.value,
        "organization_id": context.organization.organization_id,
    }
