from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from src.application.dtos.event_dto import (
    DuplicateEventResponse,
    EventCreateRequest,
    EventResponse,
)
from src.application.services.event_service import EventService
from src.config.dependencies import get_event_service
from src.infrastructure.security.auth import get_current_user
from src.infrastructure.security.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=201,
    responses={
        200: {"model": DuplicateEventResponse, "description": "Duplicate event"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("100/minute")
async def create_event(
    request: Request,
    payload: EventCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> EventResponse:
    event = await event_service.create_event(payload)

    background_tasks.add_task(event_service.dispatch_notification, event)

    return EventResponse(
        status="created",
        event_id=event.id,
        severity=event.severity.value,
        received_at=datetime.now(timezone.utc),
    )
