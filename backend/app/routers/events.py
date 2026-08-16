from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build
from sqlalchemy.orm import Session as DBSession

from app.db.base import get_db
from app.db.models import Session as BrowserSession
from app.services.session import get_session
from app.services.google_credentials import get_credentials
from app.services.google_sync import (
    add_class_schedule,
    add_events_to_calendar,
    add_readings,
    add_tasks,
)

router = APIRouter()

NOT_AUTHENTICATED = JSONResponse(
    status_code=401,
    content={"error": "not_authenticated", "message": "Google account not connected"},
)

@router.post("/add-events")
def add_events(
    payload: dict = Body(...), 
    session: BrowserSession = Depends(get_session), 
    db: DBSession = Depends(get_db)
):
    if not session.user_id:
        return NOT_AUTHENTICATED
    
    creds = get_credentials(session.user_id, db)
    if not creds:
        return NOT_AUTHENTICATED
    
    calendar_service = build("calendar", "v3", credentials=creds)
    tasks_service = build("tasks", "v1", credentials=creds)
    color_id = payload.get("color_id", 1)

    schedule_report = add_class_schedule(payload, calendar_service, color_id)
    add_events_to_calendar(payload, calendar_service, color_id)
    add_tasks(payload, tasks_service)
    add_readings(payload, tasks_service)

    return {"message": "Events added successfully", "class_schedule": schedule_report}
