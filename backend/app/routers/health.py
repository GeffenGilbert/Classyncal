from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Hello from the backend!"}

@router.get("/test")
def test():
    return {
        "status": "success",
        "message": "React successfully connected to FastAPI"
    }
