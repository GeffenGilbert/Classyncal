import uuid

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session as DBSession

from app.config import OPENAI_API_KEY
from app.db.base import get_db
from app.db.models import Job, Session as BrowserSession
from app.services.document_parsing import (
    ALLOWED_CONTENT_TYPES,
    DOCX_CONTENT_TYPE,
    extract_docx_text,
    make_pdf_input_content,
    make_text_input_content,
)
from app.services.rate_limit import check_upload_quota
from app.services.session import get_session
from app.utils import error_response

router = APIRouter()

@router.post("/upload-syllabus")
async def upload_syllabus(
    request: Request,
    file: UploadFile = File(...),
    session: BrowserSession = Depends(get_session),
    db: DBSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return error_response(
            415,
            "unsupported_file_type",
            "Unsupported file type. Please upload a PDF or DOCX file.",
        )

    if not OPENAI_API_KEY:
        return error_response(
            503,
            "missing_openai_api_key",
            "OPENAI_API_KEY is not configured on the backend.",
        )

    # Checked before the file is read into memory, and well before anything is
    # enqueued - this endpoint needs no login, so it is the one place a stranger
    # can spend our OpenAI budget.
    refusal = check_upload_quota(session.session_id)
    if refusal is not None:
        code, message = refusal
        return error_response(429 if code == "rate_limited" else 503, code, message)

    contents = await file.read()

    if file.content_type == "application/pdf":
        # CHANGE: Send PDFs directly to OpenAI so normal or scanned syllabi do
        # not get blocked by local text-extraction failures.
        input_content = make_pdf_input_content(file.filename, contents)
    elif file.content_type == DOCX_CONTENT_TYPE:
        try:
            extracted_text = extract_docx_text(contents)
        except Exception:
            return error_response(
                422,
                "docx_text_extraction_failed",
                "Could not read this DOCX file. Please check that it is not corrupted.",
            )

        if not extracted_text.strip():
            return error_response(
                422,
                "docx_has_no_extractable_text",
                "Could not find text in this DOCX file.",
            )

        document_text = f"Here is the text extracted from the syllabus document, including any tables converted to markdown:\n\n{extracted_text}"
        input_content = make_text_input_content(document_text)

    job = Job(session_id=session.session_id)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    await request.app.state.redis.enqueue_job(
        "extract_syllabus_job",
        job.job_id,
        input_content,
        _job_id=str(job.job_id),
    )

    return {"job_id": str(job.job_id)}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: uuid.UUID, db: DBSession = Depends(get_db)):
    job = db.get(Job, job_id)
    
    if job is None:
        return error_response(404, "job_not_found", "No job found with this id.")
    
    return {"status": job.status, "result": job.result_json}
