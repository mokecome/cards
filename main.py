from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.v1 import card, ocr
from backend.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.models.db import Base, engine
    Base.metadata.create_all(bind=engine)
    print("backend activate")
    yield

app = FastAPI(title="OCR API", description="Business Card Scanning and Management Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(card.router, prefix="/api/v1/cards", tags=["Business Card Management"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])

@app.on_event("startup")
def startup_event():
    from backend.models.db import Base, engine
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 