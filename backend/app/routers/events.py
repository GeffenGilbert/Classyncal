import os

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import SCOPES
from app.services.google_sync import (
    add_class_schedule,
    add_events_to_calendar,
    add_readings,
    add_tasks,
)

router = APIRouter()

@router.post("/add-events")
def add_events(payload: dict = Body(...)):
    print("adding events")

    if not os.path.exists("token.json"):
        return JSONResponse(
            status_code=401,
            content={"error": "not_authenticated", "message": "Google account not connected"},
        )

    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    calendar_service = build("calendar", "v3", credentials=creds)
    tasks_service = build("tasks", "v1", credentials=creds)
    color_id = payload.get("color_id", 1)

    schedule_report = add_class_schedule(payload, calendar_service, color_id)
    add_events_to_calendar(payload, calendar_service, color_id)
    add_tasks(payload, tasks_service)
    add_readings(payload, tasks_service)
    print("added events successfully")

    # Report what happened to the class schedule so a meeting that could not be
    # scheduled is visible to the caller instead of disappearing.
    return {"message": "Events added successfully", "class_schedule": schedule_report}
