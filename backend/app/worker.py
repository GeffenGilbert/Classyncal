from arq import cron
from arq.connections import RedisSettings

from app.config import REDIS_URL
from app.db.base import SessionLocal
from app.db.models import Job
from app.services.cleanup import cleanup_expired_sessions, cleanup_old_jobs
from app.services.dedupe import deduplicate
from app.services.openai_extraction import extract_syllabus
from app.services.titling import apply_course_code

async def extract_syllabus_job(ctx, job_id, input_content):
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        job.status = "processing"
        db.commit()

        parsed = await extract_syllabus(input_content)
        result = apply_course_code(deduplicate(parsed.model_dump(mode="json")))
        
        job.status = "done"
        job.result_json = result
        db.commit()
    except Exception:
        job.status = "failed"
        db.commit()
    finally:
        db.close()

class WorkerSettings:
    functions = [extract_syllabus_job]
    cron_jobs = [
        cron(cleanup_expired_sessions, hour=set(range(24)), minute=0),
        cron(cleanup_old_jobs, hour=set(range(24)), minute=0),
    ]
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
