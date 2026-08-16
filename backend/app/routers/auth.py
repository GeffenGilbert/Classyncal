from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session as DBSession

from app.config import SCOPES
from app.db.base import get_db
from app.db.models import GoogleToken, Session as BrowserSession, User
from app.services.session import get_session
from app.services.token_crypto import encrypt

router = APIRouter()

@router.get("/auth/google")
def google_auth(
    session: BrowserSession = Depends(get_session), 
    db: DBSession = Depends(get_db)
):
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback",
        autogenerate_code_verifier=False
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    session.oauth_state = state
    db.commit()

    return RedirectResponse(authorization_url)

@router.get("/auth/google/callback")
def google_auth_callback(
    request: Request, 
    session: BrowserSession = Depends(get_session), 
    db: DBSession = Depends(get_db)
):
    if request.query_params.get("error"):
        return HTMLResponse(
            content="""
            <!doctype html>
            <html>
                <body>
                    Google sign-in was declined. You can close this window.
                </body>
            </html>
            """
        )

    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/google/callback",
        autogenerate_code_verifier=False
    )
    
    state = request.query_params.get("state")
    if not state or state != session.oauth_state:
        raise HTTPException(
            status_code=403, 
            detail="Invalid OAuth State"
        )

    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    
    client_id = flow.client_config["client_id"]
    payload = id_token.verify_oauth2_token(
        credentials.id_token, 
        GoogleAuthRequest(), 
        client_id
    )
    google_sub = payload["sub"]
    
    # check user with this google sub, creating it if it doesn't exist
    user = db.query(User).filter_by(google_sub=google_sub).first()
    if user is None:
        user = User(google_sub=google_sub)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # get the users token row, creating that row if it does not exist
    token_row = db.query(GoogleToken).filter_by(user_id=user.user_id).first()
    if token_row is None:
        token_row = GoogleToken(user_id=user.user_id)
        db.add(token_row)
    
    # update the users token's
    token_row.access_token = encrypt(credentials.token)
    token_row.refresh_token = encrypt(credentials.refresh_token)
    token_row.expires_at = credentials.expiry.replace(tzinfo=timezone.utc)
    
    # update the session with the user_id
    session.user_id = user.user_id
    session.oauth_state = None
    
    db.commit()

    return HTMLResponse(
            content="""
            <!doctype html>
            <html>
                <body>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({ type: 'google-auth-success' }, 'http://localhost:5173');
                            window.close();
                        } else {
                            document.body.textContent = 'Google account connected successfully. You can close this window.';
                        }
                    </script>
                </body>
            </html>
            """
    )
