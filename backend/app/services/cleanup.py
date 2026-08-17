from datetime import datetime, timedelta, timezone

from app.db.base import SessionLocal
from app.db.models import Job, Session as BrowserSession

JOB_RETENTION = timedelta(hours=24)


# Sessions and jobs can't be cleaned up independently of each other: jobs.session_id
# is a FK with no ON DELETE behavior, so deleting a session that still has jobs
# pointing at it would fail. Delete each expired session's jobs first, in the same pass.
async def cleanup_expired_sessions(ctx):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_session_ids = db.query(BrowserSession.session_id).filter(
            BrowserSession.expires_at < now
        )
        db.query(Job).filter(
            Job.session_id.in_(expired_session_ids)
        ).delete(synchronize_session=False)
        db.query(BrowserSession).filter(
            BrowserSession.expires_at < now
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# No expires_at on jobs, so this uses an arbitrary retention window instead - and
# deliberately ignores status, since a job still "pending"/"processing" after 24
# hours isn't legitimately in flight, it's orphaned (e.g. from a crashed worker).
async def cleanup_old_jobs(ctx):
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - JOB_RETENTION
        db.query(Job).filter(Job.created_at < cutoff).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
