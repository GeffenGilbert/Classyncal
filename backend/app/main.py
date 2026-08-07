from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, events, health, syllabus

app = FastAPI()

# Allows your React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[0-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(syllabus.router)
app.include_router(events.router)
