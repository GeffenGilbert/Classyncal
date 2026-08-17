import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# Staging is deployed the same way production is (real domain, real HTTPS) -
# "development" is the only environment that should ever get the insecure/
# local-only defaults below, so this checks for that specifically rather
# than matching "production" exactly (which staging would silently fail).
IS_PRODUCTION = ENVIRONMENT != "development"

if not IS_PRODUCTION:
    # Lets the Google OAuth library accept plain-HTTP redirect URIs for local
    # testing. Never set this outside development - it would accept insecure
    # OAuth redirects even though the app is actually served over HTTPS.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# The app's own public URLs - used to build the OAuth redirect_uri and the
# postMessage origin checks between the OAuth popup and its opener. Defaults
# match local dev; overridden via .env wherever the app is actually deployed.
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")

# In dev, Vite may move ports (5170-5179) when 5173 is taken, so the default
# allows the whole range. Everywhere else there's exactly one real frontend
# origin, so the default narrows to an exact match on it - overridable
# directly via CORS_ORIGIN_REGEX if something more exotic is ever needed.
CORS_ORIGIN_REGEX = os.getenv(
    "CORS_ORIGIN_REGEX",
    re.escape(FRONTEND_BASE_URL) if IS_PRODUCTION else r"http://(localhost|127\.0\.0\.1):517[0-9]",
)

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

# Matches the local `syllabus-redis` Docker container. Overridden via .env
# in any environment where Redis lives somewhere else (e.g. the VPS).
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks"
]
