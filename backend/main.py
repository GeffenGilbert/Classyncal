# source .venv/bin/activate
# python -m pip install -r requirements.txt
# uvicorn main:app --reload

from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from openai import OpenAI

import base64
import io
from typing import Literal

from docx import Document
from pydantic import BaseModel

from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import Request

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # this is for local testing, delete before putting on the cloud

openai_api_key = os.getenv("OPENAI_API_KEY")
# CHANGE: Keep production extraction on one default model. These env vars are
# the only knobs needed to swap models or PDF rendering detail later.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT")
OPENAI_PDF_DETAIL = os.getenv("OPENAI_PDF_DETAIL", "auto")
MAX_DOCUMENT_CHARS = int(os.getenv("MAX_DOCUMENT_CHARS", "600000"))

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks"
]

app = FastAPI()

# Allows your React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[0-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from the backend!"}

@app.get("/test")
def test():
    return {
        "status": "success",
        "message": "React successfully connected to FastAPI"
    }

@app.get("/auth/google")
def google_auth():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback",
        autogenerate_code_verifier=False
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return RedirectResponse(authorization_url)

@app.get("/auth/google/callback")
def google_auth_callback(request: Request):
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback",
        autogenerate_code_verifier=False
    )

    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials

    with open("token.json", "w") as token_file:
        token_file.write(credentials.to_json())

        return HTMLResponse(
                content="""
                <!doctype html>
                <html>
                    <body>
                        <script>
                            if (window.opener) {
                                window.opener.postMessage({ type: 'google-auth-success' }, 'http://localhost:5173');
                                window.close();
                            } else {
                                document.body.textContent = 'Google account connected successfully. You can close this window.';
                            }
                        </script>
                    </body>
                </html>
                """
        )

@app.get("/test-calendar")
def test_calendar():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": "Syllabus Calendar Test Event",
        "description": "This is a test event created by my syllabus calendar app.",
        "start": {
            "dateTime": "2026-06-18T10:00:00",
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": "2026-06-18T10:30:00",
            "timeZone": "America/New_York",
        },
    }
    
    service.events().insert(calendarId="primary", body=event).execute()
    return {"message": "Event added"}

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    DOCX_CONTENT_TYPE,
}

Confidence = Literal["high", "medium", "low"]

# CHANGE: Structured Outputs schema replaces hand-parsed JSON text so the
# model response must match the shape the review UI expects.
class Course(BaseModel):
    course_name: str | None
    course_code: str | None
    instructor: str | None
    term: str | None

class ClassMeeting(BaseModel):
    title: str
    days_of_week: list[Literal[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]]
    start_time: str | None
    end_time: str | None
    location: str | None
    start_date: str | None
    end_date: str | None
    confidence: Confidence
    source_text: str

class ClassSchedule(BaseModel):
    found: bool
    notes: str
    meetings: list[ClassMeeting]

class ClassCancellation(BaseModel):
    title: str
    date: str | None
    reason: str | None
    description: str
    confidence: Confidence
    source_text: str

class CalendarEvent(BaseModel):
    title: str
    event_type: Literal[
        "exam",
        "quiz",
        "final_exam",
        "presentation",
        "review_session",
        "special_class",
        "other",
    ]
    date: str | None
    start_time: str | None
    end_time: str | None
    location: str | None
    description: str
    confidence: Confidence
    source_text: str

class Task(BaseModel):
    title: str
    task_type: Literal[
        "homework",
        "assignment",
        "paper",
        "project",
        "lab",
        "problem_set",
        "other",
    ]
    due_date: str | None
    due_time: str | None
    description: str
    confidence: Confidence
    source_text: str

class Reading(BaseModel):
    title: str
    reading_type: Literal["textbook", "article", "class_notes", "book", "other"]
    due_date: str | None
    due_time: str | None
    description: str
    confidence: Confidence
    source_text: str

class SyllabusExtraction(BaseModel):
    course: Course
    class_schedule: ClassSchedule
    class_cancellations: list[ClassCancellation]
    calendar_events: list[CalendarEvent]
    tasks: list[Task]
    readings: list[Reading]
    missing_information: list[str]
    warnings: list[str]

def error_response(status_code, error, message):
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message},
    )

def _table_to_markdown(rows):
    rows = [row for row in rows if row]
    if not rows:
        return ""
    def format_row(row):
        cells = [str(cell).strip() if cell is not None else "" for cell in row]
        return "| " + " | ".join(cells) + " |"
    lines = [format_row(rows[0]), "| " + " | ".join(["---"] * len(rows[0])) + " |"]
    lines.extend(format_row(row) for row in rows[1:])
    return "\n".join(lines)

# docx is a structured XML format (not a rendering-only format like PDF), so
# extracting its text/tables locally is reliable and there's no accuracy
# tradeoff to weigh here the way there was for PDF.
def extract_docx_text(contents: bytes):
    doc = Document(io.BytesIO(contents))
    parts = [para.text for para in doc.paragraphs if para.text.strip()]
    for table in doc.tables:
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        markdown = _table_to_markdown(rows)
        if markdown:
            parts.append(f"[Table]\n{markdown}")
    return "\n\n".join(parts)

def truncate_document_text(text):
    if len(text) <= MAX_DOCUMENT_CHARS:
        return text

    return (
        text[:MAX_DOCUMENT_CHARS]
        + "\n\n[Document truncated because it exceeded the configured prompt size safety limit.]"
    )

def make_pdf_input_content(filename, contents):
    base64_pdf = base64.b64encode(contents).decode("utf-8")
    return [
        {
            "type": "input_file",
            "filename": filename or "syllabus.pdf",
            "file_data": f"data:application/pdf;base64,{base64_pdf}",
            "detail": OPENAI_PDF_DETAIL,
        },
        {
            "type": "input_text",
            "text": (
                "Read this syllabus PDF and extract structured calendar/task data. "
                "Use both the PDF text and page images. If the PDF includes scans, tables, "
                "or unusual formatting, inspect the visible page content rather than returning an error."
            ),
        },
    ]

def make_text_input_content(document_text):
    return truncate_document_text(document_text)

@app.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return error_response(
            415,
            "unsupported_file_type",
            "Unsupported file type. Please upload a PDF or DOCX file.",
        )

    if not openai_api_key:
        return error_response(
            503,
            "missing_openai_api_key",
            "OPENAI_API_KEY is not configured on the backend.",
        )

    contents = await file.read()

    if file.content_type == "application/pdf":
        # CHANGE: Send PDFs directly to OpenAI so normal or scanned syllabi do
        # not get blocked by local text-extraction failures.
        input_content = make_pdf_input_content(file.filename, contents)
    elif file.content_type == DOCX_CONTENT_TYPE:
        try:
            extracted_text = extract_docx_text(contents)
        except Exception:
            return error_response(
                422,
                "docx_text_extraction_failed",
                "Could not read this DOCX file. Please check that it is not corrupted.",
            )

        if not extracted_text.strip():
            return error_response(
                422,
                "docx_has_no_extractable_text",
                "Could not find text in this DOCX file.",
            )

        document_text = f"Here is the text extracted from the syllabus document, including any tables converted to markdown:\n\n{extracted_text}"
        input_content = make_text_input_content(document_text)

    client = OpenAI(api_key=openai_api_key)

    instructions = """You are a syllabus extraction assistant for a college calendar app.

Read the full syllabus text and extract structured scheduling information.

You must separate:
1. recurring class meeting schedules,
2. one-time calendar events such as exams, quizzes, finals, presentations, and tests,
3. task due dates such as homework, assignments, papers, labs, projects, and problem sets,
4. readings,
5. cancellations such as holidays, breaks, and no-class days.

Rules:
- Do not invent dates, times, titles, or locations.
- If information is missing or unclear, use null and explain it in missing_information or warnings.
- Use 24-hour HH:MM time format for times.
- Use ISO YYYY-MM-DD format for dates.
- Class meeting schedules are recurring events, such as "MW 2:00-3:15", "Tues/Thurs 10am", "TR 450pm-605pm", or "every Monday and Wednesday".
- Put recurring class schedules in class_schedule.meetings, not in calendar_events.
- Tests, exams, midterms, finals, quizzes, presentations, review sessions, and special class meetings go in calendar_events.
- Homework, assignments, papers, projects, labs, problem sets, and other graded or submitted work go in tasks.
- Readings should not go in tasks. Put textbook readings, articles, book chapters, class notes, and other reading assignments in readings.
- Put "No Class", holidays, breaks, canceled classes, and university closures in class_cancellations, not calendar_events.
- If a final exam has a date but no time, include the date and set start_time and end_time to null.
- If class meeting times are not found, set class_schedule.found to false, meetings to [], and add "Class meeting times not found" to missing_information.
- Do not include events that do not have a date unless they are recurring class meeting schedules.
- source_text should be a short phrase copied from the syllabus that supports the extracted item.
- If a reading is listed as TBD, do not include it in readings. Add it to warnings instead.
- If the syllabus has a dated schedule of class meetings, use the first dated regular class meeting as start_date and the last dated regular class meeting as end_date. Mark confidence as medium if inferred.
- If an exam, review, quiz, or presentation appears on a regular class meeting day without an explicit time/location, leave start_time, end_time, and location as null.
- If a task, lab, homework, assignment, reading, or project is listed next to a week range, use the final day of that week range as the due_date. Mention the inference in description and set confidence to medium.
- For days_of_week, use a flat array of full day names only: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.
- For class meeting titles, use the course_code followed by the meeting type, such as "CSC 242 Lecture", "CSC 242 Lab", "CSC 242 Recitation", or "CSC 242 Class"."""

    request = {
        "model": OPENAI_MODEL,
        "instructions": instructions,
        "input": [
            {
                "role": "user",
                "content": input_content,
            }
        ],
        "text_format": SyllabusExtraction,
        "prompt_cache_key": "syllabus-extraction-v1",
    }
    if OPENAI_REASONING_EFFORT:
        request["reasoning"] = {"effort": OPENAI_REASONING_EFFORT}

    try:
        response = client.responses.parse(**request)
    except Exception:
        return error_response(
            502,
            "openai_request_failed",
            "OpenAI could not process the extracted syllabus text. Please try again.",
        )

    parsed = response.output_parsed
    if not parsed:
        return error_response(
            502,
            "invalid_model_response",
            "Model returned an unexpected response shape.",
        )

    return parsed.model_dump(mode="json")

def create_repeating_event(
    service,
    name,
    start,
    end,
    repeat_days,
    repeat_until,
    location="", 
    colorId=None,
    description="",
    timezone="America/New_York"
    ):
    day_map = {
        "Monday": "MO",
        "Tuesday": "TU",
        "Wednesday": "WE",
        "Thursday": "TH",
        "Friday": "FR",
        "Saturday": "SA",
        "Sunday": "SU",

        "Mon": "MO",
        "Tue": "TU",
        "Tues": "TU",
        "Wed": "WE",
        "Thu": "TH",
        "Thur": "TH",
        "Thurs": "TH",
        "Fri": "FR",
        "Sat": "SA",
        "Sun": "SU",

        "M": "MO",
        "T": "TU",
        "W": "WE",
        "R": "TH",
        "F": "FR",
    }

    byday = ",".join(day_map[day] for day in repeat_days)
    until = repeat_until.replace("-", "")

    body = {
        "summary": name,
        "description": description,
        "start": {
            "dateTime": start,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end,
            "timeZone": timezone,
        },
        "location": location,
        "recurrence": [
            f"RRULE:FREQ=WEEKLY;BYDAY={byday};UNTIL={until}"
        ]
    }
    if colorId:
        body["colorId"] = str(colorId)
    print(body)

    service.events().insert(calendarId="primary", body=body).execute()

def create_event(
    service, 
    name, 
    start, 
    end, 
    description="", 
    location="", 
    colorId = None, 
    timezone="America/New_York",
    all_day=False
):
    if all_day:
        body = {
            "summary": name,
            "description": description,
            "start": {
                "date": start,
            },
            "end": {
                "date": end,
            },
            "location": location
        }
    else:
        body = {
            "summary": name,
            "description": description,
            "start": {
                "dateTime": start,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end,
                "timeZone": timezone,
            },
            "location": location
        }
    if colorId:
        body["colorId"] = str(colorId)
    
    service.events().insert(calendarId="primary", body=body).execute()

def create_task(
    service,
    name,
    due_date,
    due_time=None,
    description="",
    tasklist="@default"
):
    if due_time:
        due = f"{due_date}T{due_time}:00.000Z"
    else:
        due = f"{due_date}T00:00:00.000Z"

    body = {
        "title": name,
        "notes": description,
        "due": due,
    }

    service.tasks().insert(tasklist=tasklist, body=body).execute()

def add_class_schedule(payload, service, color_id):
    class_schedule = payload.get("class_schedule", {})
    meetings = class_schedule.get("meetings", [])

    if not meetings:
        return

    for meeting in meetings:
        title = meeting.get("title", "Class Meeting")
        days_of_week = meeting.get("days_of_week", [])
        start_time = meeting.get("start_time")
        end_time = meeting.get("end_time")
        start_date = meeting.get("start_date")
        end_date = meeting.get("end_date")
        location = meeting.get("location", "")

        if not (days_of_week and start_time and end_time and start_date and end_date):
            continue

        start = f"{start_date}T{start_time}:00"
        end = f"{start_date}T{end_time}:00"

        create_repeating_event(
            service,
            title,
            start,
            end,
            days_of_week,
            end_date, 
            location, 
            color_id
        )

def add_calendar_events(payload, service, color_id):
    calendar_events = payload.get("calendar_events", [])

    if not calendar_events:
        return

    for event in calendar_events:
        date = event.get("date")
        start_time = event.get("start_time")
        end_time = event.get("end_time")
        if not date:
            continue

        if start_time and end_time:
            start = date + "T" + start_time + ":00"
            end = date + "T" + end_time + ":00"
            create_event(
                service, 
                event.get("title", "Calendar Event"), 
                start, 
                end, 
                event.get("description", ""), # this is if we want descriptions included, if not then make this ""
                event.get("location", ""), 
                color_id
            )
            continue

        next_day = date
        create_event(
            service,
            event.get("title", "Calendar Event"),
            date,
            next_day,
            event.get("description", ""),
            event.get("location", ""),
            color_id,
            all_day=True,
        )

def add_tasks(payload, service):
    tasks = payload.get("tasks", [])

    if not tasks:
        return

    for task in tasks:
        due_date = task.get("due_date")
        if not due_date:
            continue

        create_task(
            service,
            task.get("title", "Task"),
            due_date,
            task.get("due_time"),
            task.get("description", ""),
        )

def add_readings(payload, service): 
    readings = payload.get("readings", [])

    if not readings:
        return

    for reading in readings:
        due_date = reading.get("due_date")
        if not due_date:
            continue

        create_task(
            service,
            reading.get("title", "Reading"),
            due_date,
            reading.get("due_time"),
            reading.get("description", ""),
        )

@app.post("/add-events")
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

    add_class_schedule(payload, calendar_service, color_id)
    add_calendar_events(payload, calendar_service, color_id)
    add_tasks(payload, tasks_service)
    add_readings(payload, tasks_service)
    print("added events successfully")

    return {"message": "Events added successfully"}
