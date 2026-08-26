"""Hand-checked answer keys, item by item rather than by count.

A category count alone can be right for the wrong reasons - 14 tasks with three
wrong dates still scores 14. So each expected item is listed with the date it
must land on and a keyword its title must contain, and scoring matches extracted
items against these one at a time.

Derived by reading the PDFs directly. Where the source is genuinely ambiguous the
entry carries a `soft` flag: it is still scored, but a config should not be judged
on it alone. Keep those honest - a soft item is one two careful readers would
disagree about, not one the model happens to get wrong.
"""

# --- Psyc 161 (Spring 2026) ----------------------------------------------
# Page 1 header: "Spring 2026, 3:25-4:40pm, Monday/Wednesday" - that is the only
# recurring pattern stated. The dated schedule on page 5 runs 1/21 (W) to 4/29 (W).
# The lone 1/23 (F) row is a Friday, which the MW pattern cannot cover, so it is a
# one-off session rather than evidence of a second weekly meeting.
PSYC = {
    "meetings": [
        {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:25",
            "end_time": "16:40",
            "start_date": "2026-01-21",
            "end_date": "2026-04-29",
        }
    ],
    # Exam 3 is "TBA" with no date, so the prompt's "no date, no item" rule drops it.
    "events": [
        {"date": "2026-02-23", "kw": "exam"},
        {"date": "2026-04-06", "kw": "exam"},
        # A Friday session inside an otherwise Monday/Wednesday course. Recording it
        # as a one-off is the reading we settled on, but calling it noise is defensible.
        {"date": "2026-01-23", "kw": "overview", "soft": True},
    ],
    # 3 essays + 7 rows on the Questionnaire Schedule + 4 extra-credit questionnaires.
    "tasks": [
        {"date": "2026-01-21", "kw": "information sheet"},
        {"date": "2026-01-21", "kw": "questionnaire 1"},
        {"date": "2026-01-24", "kw": "questionnaire 2"},
        {"date": "2026-01-28", "kw": "questionnaire 3"},
        {"date": "2026-01-31", "kw": "questionnaire 4"},
        {"date": "2026-03-17", "kw": "questionnaire 5"},
        {"date": "2026-04-27", "kw": "questionnaire 6"},
        {"date": "2026-01-26", "kw": "extra credit"},
        {"date": "2026-02-21", "kw": "extra credit"},
        {"date": "2026-03-19", "kw": "extra credit"},
        {"date": "2026-04-14", "kw": "extra credit"},
        {"date": "2026-02-16", "kw": "personal application"},
        {"date": "2026-03-30", "kw": "unplug"},
        {"date": "2026-04-27", "kw": "pop culture"},
    ],
    # The reading column of the page 5 schedule table. Nine cells, each naming the
    # material for the section that starts on that row.
    # Keywords name the chapter/topic rather than the "Packet 1"/"Packet 2" prefix:
    # nano keeps that prefix and mini drops it, so keying on it would score a
    # difference in title style as a difference in accuracy.
    "readings": [
        {"date": "2026-01-26", "kw": "types"},
        {"date": "2026-02-04", "kw": "motives"},
        {"date": "2026-02-11", "kw": "biological"},
        {"date": "2026-02-25", "kw": "2, 3"},
        # This cell sits on the "No class - spring break" row in the extracted text.
        # Column alignment in the source is loose enough that a reader could attach
        # it to 3/16 instead.
        {"date": "2026-03-09", "kw": "4, 7", "soft": True},
        {"date": "2026-03-25", "kw": "10, 12"},
        {"date": "2026-04-08", "kw": "9"},
        {"date": "2026-04-15", "kw": "11"},
        {"date": "2026-04-22", "kw": "6, 8"},
    ],
    "cancellations": [
        {"date": "2026-03-09", "kw": "spring break"},
        {"date": "2026-03-11", "kw": "spring break"},
    ],
}

# --- STAT190 (Spring 2026) ------------------------------------------------
# Yesterday's reproducible problem case, kept so a config that fixes Psyc can be
# checked for not regressing here. Counts come from the earlier hand-check.
STAT190 = {
    "meetings": [
        {
            "days": ["Tuesday", "Thursday"],
            "start_time": "14:00",
            "end_time": "15:15",
            # Dated schedule runs Jan 20 (first Tuesday) to Apr 30 (last Thursday);
            # May 9 is the final, held after lectures end.
            "start_date": "2026-01-20",
            "end_date": "2026-04-30",
        }
    ],
    "events": [
        {"date": "2026-03-05", "kw": "midterm"},
        {"date": "2026-05-09", "kw": "final"},
    ],
    "tasks": [],
    "readings": [],
    "cancellations": [
        {"date": "2026-03-10", "kw": "spring break"},
        {"date": "2026-03-12", "kw": "spring break"},
    ],
}

TRUTH = {
    "Psyc 161 Syllabus.pdf": PSYC,
    "STAT190_Spring2026.pdf": STAT190,
}

CATEGORIES = ["meetings", "events", "tasks", "readings", "cancellations"]

# --- CSC 242 (Spring 2026) ------------------------------------------------
# The structurally easiest of the four: a five-column table (Date | DoW | Topic |
# Reading | Assignments) where every row carries an explicit date, the reading
# column is labelled as such, and deadlines are written out ("Project 1 assigned;
# due Feb 9."). Nothing has to be inferred.
CSC242 = {
    "meetings": [
        {
            "days": ["Thursday", "Tuesday"],
            "start_time": "16:50",
            "end_time": "18:05",
            "start_date": "2026-01-20",
            "end_date": "2026-04-30",
        }
    ],
    "events": [
        {"date": "2026-03-05", "kw": "midterm"},
        {"date": "2026-04-16", "kw": "midterm"},
        {"date": "2026-05-06", "kw": "final"},
    ],
    "tasks": [
        {"date": "2026-02-09", "kw": "1"},
        {"date": "2026-02-23", "kw": "2"},
        {"date": "2026-03-02", "kw": "3"},
        {"date": "2026-04-06", "kw": "4"},
        {"date": "2026-04-27", "kw": "5"},
    ],
    # Apr 30's reading is "TBD", which the prompt sends to warnings rather than readings.
    "readings": [
        {"date": "2026-01-20", "kw": "1.3"},
        {"date": "2026-01-22", "kw": "2.1"},
        {"date": "2026-01-27", "kw": "3.5"},
        {"date": "2026-01-29", "kw": "4.1"},
        {"date": "2026-02-05", "kw": "5.1"},
        {"date": "2026-02-10", "kw": "5.3"},
        {"date": "2026-02-12", "kw": "6.1"},
        {"date": "2026-02-17", "kw": "7.1"},
        {"date": "2026-02-19", "kw": "notes"},
        {"date": "2026-02-24", "kw": "8.1"},
        {"date": "2026-02-26", "kw": "9.1"},
        {"date": "2026-03-17", "kw": "12.1"},
        {"date": "2026-03-19", "kw": "13.1"},
        {"date": "2026-03-24", "kw": "13.4"},
        {"date": "2026-03-26", "kw": "14.1"},
        {"date": "2026-03-31", "kw": "19.1"},
        {"date": "2026-04-02", "kw": "19.6"},
        {"date": "2026-04-07", "kw": "21.1"},
        {"date": "2026-04-09", "kw": "21.2"},
        {"date": "2026-04-21", "kw": "21.3"},
        {"date": "2026-04-23", "kw": "17.1"},
        {"date": "2026-04-28", "kw": "24.1"},
    ],
    "cancellations": [
        {"date": "2026-03-10", "kw": "spring break"},
        {"date": "2026-03-12", "kw": "spring break"},
    ],
}

# --- BIOL 110 (Fall 2025) -------------------------------------------------
# Exams and breaks are stated in clean prose with explicit dates, but two things
# are genuinely hard: a seven-row lab section table (day/time/room, no dates - the
# prompt's "table of sections" case), and breaks given as ranges that have to be
# intersected with the Tue/Thu lecture pattern to know which sessions are lost.
BIO110 = {
    "meetings": [
        # The header reads "2:00-3:15 AM", plainly a typo for PM; the prompt says to
        # record the time meant and note the correction in warnings.
        {"days": ["Thursday", "Tuesday"], "start_time": "14:00", "end_time": "15:15",
         "start_date": "2025-08-26", "end_date": "2025-12-04"},
        {"days": ["Wednesday"], "start_time": "11:50", "end_time": "13:50",
         "start_date": None, "end_date": None},
        {"days": ["Wednesday"], "start_time": "12:30", "end_time": "14:30",
         "start_date": None, "end_date": None},
        {"days": ["Wednesday"], "start_time": "16:50", "end_time": "18:50",
         "start_date": None, "end_date": None},
        {"days": ["Thursday"], "start_time": "16:50", "end_time": "18:50",
         "start_date": None, "end_date": None},
        {"days": ["Thursday"], "start_time": "16:50", "end_time": "18:50",
         "start_date": None, "end_date": None},
        {"days": ["Friday"], "start_time": "11:50", "end_time": "13:50",
         "start_date": None, "end_date": None},
        {"days": ["Friday"], "start_time": "14:00", "end_time": "16:00",
         "start_date": None, "end_date": None},
    ],
    "events": [
        {"date": "2025-09-18", "kw": "1"},
        {"date": "2025-10-16", "kw": "2"},
        {"date": "2025-11-13", "kw": "3"},
        {"date": "2025-12-13", "kw": "final"},
    ],
    # Problem sets and the take-home paper are mentioned but never dated.
    "tasks": [],
    # "Assigned chapters from Principles of Life" - never tied to a date.
    "readings": [],
    # Fall break is Mon-Tue 10/13-10/14 and Thanksgiving is Wed-Fri 11/26-11/28;
    # the Tue/Thu lecture only loses 10/14 and 11/27. Add/drop, last-day-to-W,
    # last-day-S/F and "classes start" are university-wide and belong in no list.
    "cancellations": [
        {"date": "2025-10-14", "kw": "fall break"},
        {"date": "2025-11-27", "kw": "thanksgiving"},
    ],
}

TRUTH["CSC 242 Artificial Intelligence (Spring 2026).pdf"] = CSC242
TRUTH["Bio110 2025 syllabus v2.pdf"] = BIO110
