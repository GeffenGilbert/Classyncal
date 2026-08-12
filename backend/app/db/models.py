import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import ForeignKey, Integer, String, Text, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    google_sub: Mapped[str] = mapped_column(String, unique=True, index=True) # The stable identity from Google's ID token - never a self-generated id.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    token_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), unique=True) # One row per user - updated in place on refresh, never accumulated.
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Session(Base):
    __tablename__ = "sessions"

    # The session token itself (the value stored in the browser's cookie) is
    # the primary key - looked up by exact match on every request.
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    # Nullable: a session exists before login too, to carry the OAuth state
    # below across the redirect to Google and back.
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.user_id"))
    oauth_state: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.session_id"))
    status: Mapped[Literal["pending", "processing", "done", "failed"]] = mapped_column(String, default="pending")
    result_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )