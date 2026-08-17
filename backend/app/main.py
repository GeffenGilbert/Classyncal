from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import REDIS_URL
from app.routers import auth, events, health, syllabus
from app.services.session import SessionCookieMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(RedisSettings.from_dsn(REDIS_URL))
    yield
    await app.state.redis.aclose()

app = FastAPI(lifespan=lifespan)

# Allows the React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[0-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionCookieMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(events.router)
