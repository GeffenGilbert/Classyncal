from fastapi import APIRouter, UploadFile, File

from app.config import OPENAI_API_KEY
from app.services.dedupe import deduplicate
from app.services.document_parsing import (
    ALLOWED_CONTENT_TYPES,
    DOCX_CONTENT_TYPE,
    extract_docx_text,
    make_pdf_input_content,
    make_text_input_content,
)
from app.services.openai_extraction import extract_syllabus
from app.services.titling import apply_course_code
from app.utils import error_response

router = APIRouter()

@router.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
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

    try:
        parsed = extract_syllabus(input_content)
    except Exception:
        return error_response(
            502,
            "openai_request_failed",
            "OpenAI could not process the extracted syllabus text. Please try again.",
        )

    if not parsed:
        return error_response(
            502,
            "invalid_model_response",
            "Model returned an unexpected response shape.",
        )

    # Deduplicate before prefixing, so the course code does not mask a generic title.
    return apply_course_code(deduplicate(parsed.model_dump(mode="json")))
