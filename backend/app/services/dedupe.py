import re

# --- Deduplication -----------------------------------------------------------------
#
# Syllabi name the same thing in more than one place. Psyc lists every essay twice:
# once in the weekly schedule ("Essay 2") and again in a separate essay schedule
# ("Unplug Day Essay"). The model dutifully records both, so the user sees six essays
# where there are three. Prompt rules catch this only sometimes; these three do it every
# time. Two items are the same thing when:
#
#   1. their titles match, or one is the start of the other
#      ("Principles of Life (Hillis et al.)" and "...(Hillis et al.) a")
#   2. they fall on the same date, are the same type, and one is a generic label
#      ("Essay 2" next to "Unplug Day Essay", both due 3/30)
#   3. the same title appears in both events and tasks - an exam belongs in events
#
# Rule 2 requires a generic label on one side deliberately: two differently-named
# assignments due the same day are two assignments, and must not be merged.

# A title that names a category and a number but nothing specific about the work.
GENERIC_TITLE = re.compile(
    r"^(essay|assignment|homework|hw|quiz|test|exam|midterm|final|project|paper"
    r"|problem set|pset|lab|reading|questionnaire)\s*\d*$"
)

def normalized_title(title):
    """Lowercased, punctuation stripped, so 'Essay 1.' and 'essay 1' compare equal."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).split())

def same_item(a, b, date_field, type_field):
    title_a = normalized_title(a.get("title"))
    title_b = normalized_title(b.get("title"))
    date = a.get(date_field)

    # Same day, or both undated. Two "No Class" cancellations a week apart are two
    # separate days off, however identical their titles.
    if date != b.get(date_field):
        return False

    # The shorter title must end on a word boundary in the longer one, or "Project 1"
    # would swallow "Project 10".
    if title_a and title_b:
        short, long = sorted((title_a, title_b), key=len)
        if long == short or long.startswith(short + " "):
            return True

    if not date:
        return False
    # A second, generic listing tends to come with a generic type: Psyc returns its
    # essays once as "Personal Application Essay" typed 'paper' and again as "Essay 1"
    # typed 'other'. So the catch-all type agrees with anything, while two specific
    # types still have to match - an exam and its review session share a name and
    # sometimes a date, and are not the same thing.
    if type_field:
        type_a, type_b = a.get(type_field), b.get(type_field)
        if type_a != type_b and "other" not in (type_a, type_b):
            return False

    # The generic label must name the same kind of work as the title it is merging
    # into - "Essay 1" into "Personal Application Essay". Without this, "Questionnaire 1"
    # merges with "Information Sheet and Written Release Form" purely for sharing a date,
    # which loses a real item.
    for generic, other in ((title_a, title_b), (title_b, title_a)):
        match = GENERIC_TITLE.match(generic)
        if match and match.group(1) in other:
            return True
    return False

def dedupe_list(items, date_field, type_field):
    """Keep one of each item, preferring the longer - and so more descriptive - title."""
    kept = []
    for item in items:
        match = next((k for k in kept if same_item(item, k, date_field, type_field)), None)
        if match is None:
            kept.append(item)
        elif len(item.get("title") or "") > len(match.get("title") or ""):
            kept[kept.index(match)] = item
    return kept

CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2}
WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]

def compatible(a, b):
    """Two values describe the same thing when they agree or one is simply absent."""
    return not a or not b or a == b

def same_meeting(a, b):
    """Whether two entries describe one class meeting. Matching on agreement rather
    than equality is what merges a schedule the model split in two - the syllabus
    states the lecture's days and times in one place and its date range in another, so
    neither copy is a duplicate of the other but together they are one meeting.

    One day set inside the other counts as agreement, because the other way a schedule
    splits is per day: a Monday/Wednesday lecture returned again as a bare Monday entry
    and a bare Wednesday entry. A genuinely separate session on one of those days -
    a Wednesday lab, an extra Friday hour - differs in title, room or time, and every
    one of those still has to agree below."""
    days_a = set(a.get("days_of_week") or [])
    days_b = set(b.get("days_of_week") or [])
    if not (days_a <= days_b or days_b <= days_a):
        return False
    if not compatible(a.get("start_time"), b.get("start_time")):
        return False
    if not compatible(a.get("end_time"), b.get("end_time")):
        return False

    # Location must agree: Bio runs two recitation sections at Thursday 16:50 in
    # different rooms, and they are different sections, not a duplicate.
    location_a = normalized_title(a.get("location"))
    location_b = normalized_title(b.get("location"))
    if not compatible(location_a, location_b):
        return False
    # Nothing else can be in the same room at the same time, so two known and equal
    # locations settle it - which catches the same class recorded once as "Lecture"
    # and again as "Class". Otherwise the titles have to agree too, since two
    # untimed, unplaced meetings may genuinely differ.
    if location_a and location_b:
        return True
    return compatible(normalized_title(a.get("title")), normalized_title(b.get("title")))

def merge_meetings(a, b):
    """One meeting carrying whatever either copy knew. Takes the widest date range:
    a truncated end date is the likelier mistake, and the same holds of a start date
    that begins mid-term."""
    merged = dict(a)
    for field in ("start_time", "end_time", "location", "source_text"):
        merged[field] = a.get(field) or b.get(field)
    # Keep every day either copy knew about, in the schedule's own order.
    days = list(a.get("days_of_week") or [])
    days += [d for d in (b.get("days_of_week") or []) if d not in days]
    merged["days_of_week"] = sorted(days, key=WEEKDAY_ORDER.index)
    # Prefer the more descriptive of two disagreeing titles, as dedupe_list does.
    merged["title"] = max((a.get("title") or "", b.get("title") or ""), key=len)
    merged["start_date"] = min(filter(None, (a.get("start_date"), b.get("start_date"))),
                               default=None)
    merged["end_date"] = max(filter(None, (a.get("end_date"), b.get("end_date"))),
                             default=None)
    # A merged meeting is partly assembled, so it is only as trustworthy as its
    # weaker half.
    merged["confidence"] = max(
        (a.get("confidence"), b.get("confidence")),
        key=lambda c: CONFIDENCE_RANK.get(c, 0),
    )
    return merged

def dedupe_meetings(meetings):
    """A class recurring on the same days at the same time is one meeting, however
    many times the syllabus mentions it. Psyc returns its Monday/Wednesday lecture
    twice, sometimes with different end dates."""
    kept = []
    for meeting in meetings:
        match = next((i for i, k in enumerate(kept) if same_meeting(meeting, k)), None)
        if match is None:
            kept.append(meeting)
        else:
            kept[match] = merge_meetings(kept[match], meeting)
    return kept

DEDUPE_FIELDS = {
    "events": ("date", "event_type"),
    "tasks": ("due_date", "task_type"),
    "readings": ("due_date", "reading_type"),
    "class_cancellations": ("date", None),
}

def deduplicate(payload):
    for key, (date_field, type_field) in DEDUPE_FIELDS.items():
        payload[key] = dedupe_list(payload.get(key, []), date_field, type_field)

    schedule = payload.setdefault("class_schedule", {})
    schedule["meetings"] = dedupe_meetings(schedule.get("meetings", []))

    # Rule 3. Anything recorded as both an event and a task stays an event.
    event_titles = {normalized_title(e.get("title")) for e in payload["events"]}
    payload["tasks"] = [
        t for t in payload["tasks"] if normalized_title(t.get("title")) not in event_titles
    ]
    return payload
