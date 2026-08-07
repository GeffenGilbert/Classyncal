# Every item reaching Calendar or Tasks is prefixed with the course code so it is
# identifiable out of context. Done here rather than in the prompt so it is applied
# uniformly and cannot drift with the model's phrasing.
def titled(payload, name, fallback):
    name = (name or "").strip() or fallback
    course_code = (payload.get("course") or {}).get("course_code")
    if not course_code:
        return name
    course_code = course_code.strip()
    if not course_code or name.startswith(course_code):
        return name
    return f"{course_code}: {name}"

# Applied to the extraction before it reaches the review screen, so the titles the
# user edits are the titles that get created. titled() still runs at sync time and is
# idempotent, which covers anything the user adds by hand while reviewing.
def apply_course_code(payload):
    defaults = {
        "events": "Event",
        "tasks": "Task",
        "readings": "Reading",
        "class_cancellations": "No Class",
    }
    for key, fallback in defaults.items():
        for item in payload.get(key, []):
            item["title"] = titled(payload, item.get("title"), fallback)

    meetings = payload.get("class_schedule", {}).get("meetings", [])
    for meeting in meetings:
        meeting["title"] = titled(payload, meeting.get("title"), "Class Meeting")

    return payload
