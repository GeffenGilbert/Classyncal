"""Rate limiting for the paid extraction endpoint.

`/upload-syllabus` triggers an OpenAI call that costs real money and needs no
login, so without a limit anyone who finds the URL can run up the bill in a
loop. Redis is already a hard dependency (arq runs on it), so the counters live
there rather than adding a new one.

Two layers, because each catches what the other misses:

- **Per session** is the normal-use limit. It is the one a real student would
  ever notice, and it is generous enough that they should not.
- **Global daily** is the circuit breaker. It does not care who is calling; it
  is the ceiling on a day's OpenAI spend if something gets past the session
  limit (e.g. someone dropping their cookie between requests).

Both are fixed windows (INCR + EXPIRE), not sliding. A fixed window lets
through at most 2x the limit across a boundary, which does not matter at these
values and avoids keeping a timestamp set per caller.
"""

import os
from datetime import datetime, timezone

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Tunable without a rebuild - they are read per call, not captured at import.
def _limit(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))

HOUR = 3600
DAY = 86400

_client = redis.Redis.from_url(
    REDIS_URL, socket_connect_timeout=2, socket_timeout=2, decode_responses=True
)


def _over_limit(key: str, limit: int, window: int) -> bool:
    count = _client.incr(key)
    if count == 1:
        _client.expire(key, window)
    return count > limit


def check_upload_quota(session_id: str):
    """Returns None when allowed, or (error_code, message) when refused.

    Fails **open**: if Redis is unreachable the upload proceeds. A limiter that
    takes the site down when its own backing store blips is worse than the
    problem it solves - and an unreachable Redis means the job queue is down
    anyway, so the request will fail a moment later for a clearer reason.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    checks = (
        (f"rl:sess:{session_id}", _limit("RATE_LIMIT_PER_SESSION_HOURLY", 15), HOUR,
         "rate_limited",
         "You've uploaded a lot of syllabi in the last hour. Please try again later."),
        (f"rl:global:{today}", _limit("RATE_LIMIT_GLOBAL_DAILY", 5000), DAY,
         "capacity_reached",
         "The service has hit its daily processing limit. Please try again tomorrow."),
    )

    try:
        for key, limit, window, code, message in checks:
            if _over_limit(key, limit, window):
                return code, message
    except redis.RedisError:
        return None

    return None
