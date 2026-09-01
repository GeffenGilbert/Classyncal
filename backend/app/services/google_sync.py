from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo



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

# Monday=0, matching date.weekday(). Abbreviations included because the schema asks
# for full day names but nothing enforces it on a hand-edited payload.
WEEKDAY_INDEX = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
    "Mon": 0, "Tue": 1, "Tues": 1, "Wed": 2, "Thu": 3, "Thur": 3, "Thurs": 3,
    "Fri": 4, "Sat": 5, "Sun": 6,
    "M": 0, "T": 1, "W": 2, "R": 3, "F": 4,
}

# In RFC 5545 - which Google Calendar implements - DTSTART is always an occurrence of
# the series, whether or not it matches BYDAY. So a Tue/Thu class whose start date
# lands on a Monday gets that Monday too, on top of the Tue/Thu pattern. That happens
# whenever the syllabus gave no start date and term_bounds fell back to today, which
# is why the stray meeting always appeared on the day of upload.
#
# Move the start forward to the first day that actually matches, so DTSTART is a real
# occurrence and adds nothing extra.
def first_matching_day(start_date, days_of_week):
    try:
        current = date.fromisoformat(start_date)
    except (TypeError, ValueError):
        return start_date
    wanted = {WEEKDAY_INDEX[day] for day in days_of_week if day in WEEKDAY_INDEX}
    if not wanted:
        return start_date
    for offset in range(7):
        candidate = current + timedelta(days=offset)
        if candidate.weekday() in wanted:
            return candidate.isoformat()
    return start_date

# A recurring meeting needs a start and end date to be scheduled at all, and the model
# supplies them unreliably. Rather than silently skipping the meeting, fall back to the
# span of everything else that is dated in the same syllabus - exams, due dates,
# cancellations - which brackets the term closely enough to be useful and is at worst a
# week or so long at the end. Returns (None, None) only if nothing anywhere has a date.
# If the term is still ongoing (its latest dated item is still in the future), start
# from today instead of the earliest dated item, so the recurring event doesn't fill
# the user's calendar with occurrences for weeks that have already passed.
def term_bounds(payload):
    dates = []
    for meeting in payload.get("class_schedule", {}).get("meetings", []):
        dates += [meeting.get("start_date"), meeting.get("end_date")]
    for key in ("events", "class_cancellations"):
        dates += [item.get("date") for item in payload.get(key, [])]
    for key in ("tasks", "readings"):
        dates += [item.get("due_date") for item in payload.get(key, [])]

    dates = sorted(d for d in dates if d)
    if not dates:
        return None, None

    today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    if dates[-1] > today:
        return today, dates[-1]
    return dates[0], dates[-1]

def add_class_schedule(payload, service, color_id):
    class_schedule = payload.get("class_schedule", {})
    meetings = class_schedule.get("meetings", [])

    if not meetings:
        return

    fallback_start, fallback_end = term_bounds(payload)
    report = {"added": 0, "dates_inferred": 0, "skipped": []}

    for meeting in meetings:
        title = (meeting.get("title") or "").strip() or "Class Meeting"
        days_of_week = meeting.get("days_of_week", [])
        start_time = meeting.get("start_time")
        end_time = meeting.get("end_time")
        start_date = meeting.get("start_date")
        end_date = meeting.get("end_date")
        location = meeting.get("location", "")

        inferred = not (start_date and end_date)
        start_date = start_date or fallback_start
        end_date = end_date or fallback_end

        if not (days_of_week and start_time and end_time and start_date and end_date):
            # Still unschedulable. Name it in the response rather than dropping it
            # silently, which previously made a whole schedule vanish with no error.
            report["skipped"].append(title)
            continue

        first_day = first_matching_day(start_date, days_of_week)
        if first_day > end_date:
            # The whole pattern falls past the end of the term - creating it would
            # put a single occurrence outside the term rather than a series in it.
            report["skipped"].append(title)
            continue

        start = f"{first_day}T{start_time}:00"
        end = f"{first_day}T{end_time}:00"

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
        report["added"] += 1
        report["dates_inferred"] += 1 if inferred else 0

    return report

def add_events_to_calendar(payload, service, color_id):
    for event in payload.get("events", []):
        date = event.get("date")
        start_time = event.get("start_time")
        end_time = event.get("end_time")
        if not date:
            continue

        title = (event.get("title") or "").strip() or "Event"

        if start_time and end_time:
            start = date + "T" + start_time + ":00"
            end = date + "T" + end_time + ":00"
            create_event(
                service,
                title,
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
            title,
            date,
            next_day,
            event.get("description", ""),
            event.get("location", ""),
            color_id,
            all_day=True,
        )

def add_due_items(payload, items, service, default_title):
    for item in items:
        due_date = item.get("due_date")
        if not due_date:
            continue

        create_task(
            service,
            (item.get("title") or "").strip() or default_title,
            due_date,
            item.get("due_time"),
            item.get("description", ""),
        )

def add_tasks(payload, service):
    add_due_items(payload, payload.get("tasks", []), service, "Task")

def add_readings(payload, service):
    add_due_items(payload, payload.get("readings", []), service, "Reading")
