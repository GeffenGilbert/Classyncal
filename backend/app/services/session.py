import secrets
from datetime import datetime, timezone, timedelta

from fastapi import Request, Depends
from sqlalchemy.orm import Session as DBSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import IS_PRODUCTION
from app.db.base import get_db
from app.db.models import Session as BrowserSession

SESSION_COOKIE_NAME = "session_id"
SESSION_LIFETIME = timedelta(days=30)

def get_session(
    request: Request,
    db: DBSession = Depends(get_db)
) -> BrowserSession:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = None

    if session_id:
        session = db.get(BrowserSession, session_id)

        if session is not None and session.expires_at < datetime.now(timezone.utc):
            session = None

    if session is None:
        new_id = secrets.token_urlsafe(32)
        session = BrowserSession(session_id=new_id, expires_at=datetime.now(timezone.utc) + SESSION_LIFETIME)
        db.add(session)
        db.commit()
        db.refresh(session)

        # The route may return a Response object directly (RedirectResponse,
        # HTMLResponse, ...), which bypasses FastAPI's automatic header-merging
        # for dependency-injected Response params. Flagging the new session id
        # on request.state instead lets SessionCookieMiddleware set the cookie
        # on the actual final response, regardless of what the route returns.
        request.state.new_session_id = new_id

    return session


class SessionCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        new_session_id = getattr(request.state, "new_session_id", None)
        if new_session_id:
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=new_session_id,
                httponly=True,
                samesite="lax",
                secure=IS_PRODUCTION,
                max_age=int(SESSION_LIFETIME.total_seconds()),
            )

        return response