from fastapi.responses import JSONResponse


def error_response(status_code, error, message):
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message},
    )
