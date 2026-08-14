import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # this is for local testing, delete before putting on the cloud

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# CHANGE: Keep production extraction on one default model. These env vars are
# the only knobs needed to swap models or PDF rendering detail later.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT")
OPENAI_PDF_DETAIL = os.getenv("OPENAI_PDF_DETAIL", "auto")
MAX_DOCUMENT_CHARS = int(os.getenv("MAX_DOCUMENT_CHARS", "600000"))

# Matches the local `syllabus-postgres` Docker container. Overridden via .env
# in any environment where the database lives somewhere else (e.g. the VPS).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://syllabus:syllabus@localhost:5432/syllabus"
)

# No hardcoded fallback on purpose - unlike DATABASE_URL, a convenient default here
# would mean every environment that forgets to set it shares the same well-known key.
TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks"
]
