from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]

# Field descriptions are sent to the model as part of the Structured Outputs
# schema, so per-field mechanics live here rather than in the prompt. The
# prompt is left to explain only which bucket an item belongs in.
DATE = "ISO YYYY-MM-DD, or null if the syllabus does not state one."
TIME = "24-hour HH:MM, or null if the syllabus does not state one."
SOURCE_TEXT = "A short phrase copied verbatim from the syllabus supporting this item."
CONFIDENCE_NOTE = "Use medium or low when any part of this item was inferred."
# description is written into the Google Calendar event body / Google Task notes, so
# it is read by the student long after the upload. It is the one field that must carry
# no trace of the extraction process — source_text already holds the quote, confidence
# and missing_information already carry uncertainty.
DESCRIPTION = (
    "One short sentence saying plainly what this is, shown to the user in their "
    "calendar. Never quote the syllabus, never mention what was or was not specified, "
    "and never describe what you could or could not determine while reading. Leave it "
    "empty if the syllabus adds nothing beyond the title."
)

# CHANGE: Structured Outputs schema replaces hand-parsed JSON text so the
# model response must match the shape the review UI expects.
class Course(BaseModel):
    course_name: str | None
    course_code: str | None
    instructor: str | None
    term: str | None

class ClassMeeting(BaseModel):
    title: str = Field(
        description="The meeting type only, such as 'Lecture', 'Lab', or 'Recitation'. "
        "Do not include the course code; it is added automatically."
    )
    days_of_week: list[Literal[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]] = Field(
        description="Every day this meeting recurs, as full day names. A class meeting "
        "MW 10:00-11:15 is one meeting with both Monday and Wednesday here, not a "
        "separate meeting per day. Never list the set of days a section might fall on: "
        "if the syllabus says labs run Tuesday, Wednesday or Thursday depending on which "
        "section a student registered for, no single section's days are known, so record "
        "no meeting at all rather than one spanning all three. This list is never empty."
    )
    start_time: str | None = Field(description=TIME)
    end_time: str | None = Field(description=TIME)
    location: str | None
    start_date: str | None = Field(description=f"{DATE} The first date this meeting occurs.")
    end_date: str | None = Field(description=f"{DATE} The last date this meeting occurs.")
    confidence: Confidence = Field(description=CONFIDENCE_NOTE)
    source_text: str = Field(description=SOURCE_TEXT)

class ClassSchedule(BaseModel):
    found: bool
    notes: str
    meetings: list[ClassMeeting]

class ClassCancellation(BaseModel):
    title: str = Field(
        description="A short label for the cancelled session, normally 'No Class'. "
        "Not a sentence — the explanation belongs in reason and description."
    )
    date: str | None = Field(description=DATE)
    reason: str | None = Field(
        description="The cause, as a short noun phrase such as 'Spring Break'."
    )
    description: str = Field(description=DESCRIPTION)
    confidence: Confidence = Field(description=CONFIDENCE_NOTE)
    source_text: str = Field(description=SOURCE_TEXT)

# One-off things that occupy a block of time on a calendar. event_type carries
# the detail that used to be split across separate top-level arrays.
class Event(BaseModel):
    title: str = Field(
        description="The event name only, such as 'Midterm 1'. Do not include the "
        "course code; it is added automatically."
    )
    event_type: Literal[
        "exam",
        "quiz",
        "final_exam",
        "presentation",
        "review_session",
        "special_class",
        "other",
    ] = Field(
        description="What kind of event this is. Use 'other' only when the event belongs "
        "to this course and none of the named types fit."
    )
    date: str | None = Field(description=DATE)
    start_time: str | None = Field(
        description=f"{TIME} Leave null if the event falls on a regular class day "
        "with no separately stated time."
    )
    end_time: str | None = Field(description=TIME)
    location: str | None
    description: str = Field(description=DESCRIPTION)
    confidence: Confidence = Field(description=CONFIDENCE_NOTE)
    source_text: str = Field(description=SOURCE_TEXT)

# Things with a deadline rather than a duration. task_type carries the detail.
class Task(BaseModel):
    title: str = Field(
        description="The task name only, such as 'Project 1'. Do not include the "
        "course code; it is added automatically."
    )
    task_type: Literal[
        "homework",
        "assignment",
        "paper",
        "project",
        "lab",
        "problem_set",
        "other",
    ] = Field(
        description="What kind of work this is. Use 'project' only when the syllabus "
        "itself calls it a project. Use 'other' if none fit."
    )
    due_date: str | None = Field(
        description=f"{DATE} If the item is listed against a week range rather than a "
        "single day, use the last day of that range and set confidence to medium."
    )
    due_time: str | None = Field(description=TIME)
    description: str = Field(description=DESCRIPTION)
    confidence: Confidence = Field(description=CONFIDENCE_NOTE)
    source_text: str = Field(description=SOURCE_TEXT)

class Reading(BaseModel):
    """Material the student is told to read. A schedule row naming what the class will
    cover that day is a topic, not a reading - including when a chapter number is written
    into the topic label, as in "Descriptive statistics (CH 2)". Record a reading only
    where the syllabus presents something to read: a reading column, or wording directing
    the student to read it. A course stating it has no required text usually has none."""

    title: str = Field(
        description="The reading name only. Do not include the course code; it is "
        "added automatically. Never a lecture topic."
    )
    reading_type: Literal["textbook", "article", "class_notes", "book", "other"]
    due_date: str | None = Field(
        description=f"{DATE} If the reading is listed against a week range rather than "
        "a single day, use the last day of that range and set confidence to medium."
    )
    due_time: str | None = Field(description=TIME)
    description: str = Field(
        description=DESCRIPTION + " For a reading, name the topic it covers rather than "
        "the date it is assigned, which is already in due_date."
    )
    confidence: Confidence = Field(description=CONFIDENCE_NOTE)
    source_text: str = Field(description=SOURCE_TEXT)

class SyllabusExtraction(BaseModel):
    course: Course
    class_schedule: ClassSchedule
    class_cancellations: list[ClassCancellation]
    events: list[Event]
    tasks: list[Task]
    readings: list[Reading]
    missing_information: list[str]
    warnings: list[str]
