import re

# Every item reaching Calendar or Tasks is prefixed with the course code so it is
# identifiable out of context - a reading titled "1.3-1.5" means nothing in a
# calendar on its own. Done here rather than in the prompt so it is applied
# uniformly and cannot drift with the model's phrasing.

# Course codes arrive in whatever shape the syllabus wrote them - "CSC214",
# "csc 214", "CSC-214" - and the same document can report one shape in
# course_code while writing another inside a title. Canonicalise to
# "<DEPT> <NUMBER>" so the prefix reads the same on every item.
_CODE_SHAPE = re.compile(r"^([A-Za-z]{2,})[\s\-_]*(\d[\w\-]*)$")

def normalize_code(course_code):
    code = " ".join((course_code or "").split())
    match = _CODE_SHAPE.match(code)
    if match:
        return f"{match.group(1).upper()} {match.group(2).upper()}"
    return code

# Comparison key: letters and digits only, so "CSC 214", "CSC214" and "csc-214"
# all collapse to the same thing. The old guard compared with startswith() on the
# raw strings, so a model-supplied "CSC 214: ..." against a course_code of
# "CSC214" did not match and the code was prefixed a second time.
def _key(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())

def _strip_code_prefix(name, code):
    head, separator, tail = name.partition(":")
    if separator and _key(head) == _key(code) and tail.strip():
        return tail.strip()
    return name

def titled(payload, name, fallback):
    name = (name or "").strip() or fallback
    code = normalize_code((payload.get("course") or {}).get("course_code"))
    if not code:
        return name

    # Drop a code the model already wrote into the title, whatever shape it used,
    # then apply the canonical one - so the prefix is present exactly once and
    # spelled the same way everywhere.
    name = _strip_code_prefix(name, code) or fallback
    if _key(name).startswith(_key(code)):
        return name
    return f"{code}: {name}"

# The one place the course code is applied, run on the extraction before it reaches
# the review screen - so the titles the user reviews and edits are exactly the titles
# that get created. google_sync deliberately does not prefix again: a second pass has
# to guess whether a title already carries the code, and guessing wrong is what
# produced "CSC214: CSC 214: Reading 1". The cost is that an item the user adds by
# hand while reviewing keeps the title they typed, unprefixed.
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
