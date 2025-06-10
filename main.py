from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import card, ocr
from backend.core.config import settings

app = FastAPI(title="名片OCR API", description="名片掃描與管理後端", version="1.0.0")

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由註冊
app.include_router(card.router, prefix="/api/v1/cards", tags=["名片管理"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])

# 啟動事件
@app.on_event("startup")
def startup_event():
    from backend.models.db import Base, engine
    # 確保資料庫表存在
    Base.metadata.create_all(bind=engine)
    print("🚀 名片OCR後端啟動完成！") 