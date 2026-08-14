import secrets
from datetime import datetime, timezone, timedelta

from fastapi import Request, Response, Depends
from sqlalchemy.orm import Session as DBSession

from app.db.base import get_db
from app.db.models import Session as BrowserSession

SESSION_COOKIE_NAME = "session_id"
SESSION_LIFETIME = timedelta(days=30)

def get_session(request: Request, response: Response, db: DBSession = Depends(get_db)) -> BrowserSession:
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
        
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=new_id,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=int(SESSION_LIFETIME.total_seconds()),
        )
    
    return session