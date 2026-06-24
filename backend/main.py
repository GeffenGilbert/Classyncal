# source .venv/bin/activate
# python -m pip install -r requirements.txt
# uvicorn main:app --reload

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv

import base64
from openai import OpenAI

from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import Request

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # this is for local testing, delete before putting on the cloud

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks"
]

app = FastAPI()

# Allows your React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

    return {"message": "Google account connected successfully"}

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

@app.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return {"error": "Only PDF files are supported for now"}
    
    contents = await file.read()
    base64_pdf = base64.b64encode(contents).decode("utf-8")

    client = OpenAI(
        api_key=api_key
    )

    print("sending to chatgpt")
    response = client.responses.create(
        model="gpt-5-mini",
        instructions=
        """
            You are a syllabus extraction assistant for a college calendar app.

            Your job is to read a college syllabus PDF and extract structured scheduling information.

            You must separate:
            1. recurring class meeting schedules,
            2. one-time calendar events such as exams, quizzes, finals, presentations, and tests,
            3. task due dates such as homework, assignments, papers, readings, projects, and problem sets.

            Do not invent dates, times, titles, or locations.
            If information is missing or unclear, use null and explain it in missing_information or warnings.
            Use 24-hour time format for all times.
            Use ISO date format YYYY-MM-DD for all dates.
            Return only valid JSON.
        """,
        input=[ # review sessions are in calendar events
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": file.filename,
                        "file_data": f"data:application/pdf;base64,{base64_pdf}",
                    },
                    {
                        "type": "input_text",
                        "text": 
                        """
                            Read this syllabus PDF and extract information for a calendar/task app.

                            Return only valid JSON in exactly this structure:

                            {
                            "course": {
                                "course_name": string or null,
                                "course_code": string or null,
                                "instructor": string or null,
                                "term": string or null
                            },
                            "class_schedule": {
                                "found": boolean,
                                "notes": string,
                                "meetings": [
                                {
                                    "title": string,
                                    "days_of_week": array of strings,
                                    "start_time": string or null,
                                    "end_time": string or null,
                                    "location": string or null,
                                    "start_date": string or null,
                                    "end_date": string or null,
                                    "confidence": "high" or "medium" or "low",
                                    "source_text": string
                                }
                                ]
                            },
                            "class_cancellations": [
                                {
                                "title": string,
                                "date": string or null,
                                "reason": string or null,
                                "description": string,
                                "confidence": "high" or "medium" or "low",
                                "source_text": string
                                }
                            ],
                            "calendar_events": [
                                {
                                "title": string,
                                "event_type": "exam" or "quiz" or "final_exam" or "presentation" or "review_session" or "special_class" or "other",
                                "date": string or null,
                                "start_time": string or null,
                                "end_time": string or null,
                                "location": string or null,
                                "description": string,
                                "confidence": "high" or "medium" or "low",
                                "source_text": string
                                }
                            ],
                            "tasks": [
                                {
                                "title": string,
                                "task_type": "homework" or "assignment" or "paper" or "project" or "lab" or "problem_set" or "other",
                                "due_date": string or null,
                                "due_time": string or null,
                                "description": string,
                                "confidence": "high" or "medium" or "low",
                                "source_text": string
                                }
                            ],
                            "readings": [
                                {
                                "title": string,
                                "reading_type": "textbook" or "article" or "class_notes" or "book" or "other",
                                "due_date": string or null,
                                "due_time": string or null,
                                "description": string,
                                "confidence": "high" or "medium" or "low",
                                "source_text": string
                                }
                            ],
                            "missing_information": array of strings,
                            "warnings": array of strings
                            }

                            Extraction rules:
                            - Class meeting schedules are recurring events, such as "MW 2:00-3:15", "Tues/Thurs 10am", "TR 450pm-605pm", or "every Monday and Wednesday".
                            - Put recurring class schedules in class_schedule.meetings, not in calendar_events.
                            - Tests, exams, midterms, finals, quizzes, presentations, review sessions, and special class meetings go in calendar_events.
                            - Homework, assignments, papers, projects, labs, problem sets, and other graded or submitted work go in tasks.
                            - Readings should not go in tasks. Put textbook readings, articles, book chapters, class notes, and other reading assignments in readings.
                            - "No Class", holidays, breaks, spring break, fall break, canceled classes, and university closures should not go in calendar_events.
                            - Put "No Class", holidays, breaks, canceled classes, and university closures in class_cancellations.
                            - If a final exam has a date but no time, include the date and set start_time and end_time to null.
                            - If class meeting times are not found, set class_schedule.found to false, meetings to [], and add "Class meeting times not found" to missing_information.
                            - If a date is ambiguous, use null for the date and explain the ambiguity in warnings.
                            - Do not include events that do not have a date unless they are recurring class meeting schedules.
                            - Do not invent missing information.
                            - source_text should be a short phrase copied from the syllabus that supports the extracted item.
                            - If a reading is listed as TBD, do not include it in readings. Add it to warnings instead.
                            - If the syllabus has a dated schedule of class meetings, use the first dated regular class meeting as class_schedule.meetings[].start_date and the last dated regular class meeting as end_date. Mark confidence as medium if inferred.
                            - If an exam, review, quiz, or presentation appears on a regular class meeting day without an explicit time/location, leave start_time, end_time, and location as null
                            - If a task, lab, homework, assignment, reading, or project is listed next to a week range, use the final day of that week range as the due_date.
                            - Example: "Jan 26 - Feb 1" means due_date is "2026-02-01"
                            - Example: "Apr 27 - May 3" means due_date is "2026-05-03"
                            - In the description, mention that the due date was inferred from the end of the listed week range
                            - Set confidence to "medium" when the due date is inferred from a week range rather than explicitly stated
                        """
                    },
                ],
            }
        ],
    )

    # returning_message = {
    #     "course_code": response.course.course_code, 
    #     "class_schedule": response.class_schedule, 
    #     "calendar_events": response.calendar_events, 
    #     "tasks": response.tasks
    # }

    print("sending response")

    return response.output_text

@app.get("/test-openai")
def test_openai():
    client = OpenAI(
        api_key=api_key
    )

    response = client.responses.create(
        model="gpt-5.5",
        instructions="You are a coding assistant that talks like a pirate.",
        input="Say Hello in one sentence.",
    )

    return {
        "message": response.output_text
    }