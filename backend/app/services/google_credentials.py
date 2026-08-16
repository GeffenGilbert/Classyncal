import json
from datetime import datetime, timedelta, timezone

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session as DBSession

from app.config import SCOPES
from app.db.models import GoogleToken
from app.services.token_crypto import decrypt, encrypt

REFRESH_BUFFER = timedelta(minutes=5)

with open("credentials.json") as _f:
    _client_config = json.load(_f)["web"]

CLIENT_ID = _client_config["client_id"]
CLIENT_SECRET = _client_config["client_secret"]
TOKEN_URI = _client_config["token_uri"]


def get_credentials(user_id: int, db: DBSession) -> Credentials | None:
    token_row = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if token_row is None:
        return None

    creds = Credentials(
        token=decrypt(token_row.access_token),
        refresh_token=decrypt(token_row.refresh_token),
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )
    
    # google-auth stores expiry as a naive UTC datetime; our column is timezone-aware.
    creds.expiry = token_row.expires_at.replace(tzinfo=None)

    if token_row.expires_at <= datetime.now(timezone.utc) + REFRESH_BUFFER:
        try:
            creds.refresh(GoogleAuthRequest())
        except RefreshError:
            db.delete(token_row)
            db.commit()
            return None

        token_row.access_token = encrypt(creds.token)
        token_row.expires_at = creds.expiry.replace(tzinfo=timezone.utc)
        db.commit()

    return creds
