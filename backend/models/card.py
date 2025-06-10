from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.models.db import Base
import datetime

class CardORM(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    # 標準化的9個欄位
    name = Column(String(100))                    # 姓名
    company_name = Column(String(200))            # 公司名稱
    position = Column(String(100))                # 職位
    mobile_phone = Column(String(50))             # 手機
    office_phone = Column(String(50))             # 公司電話
    email = Column(String(200))                   # Email
    line_id = Column(String(100))                 # Line ID
    notes = Column(Text)                          # 備註
    company_address_1 = Column(String(300))       # 公司地址一
    company_address_2 = Column(String(300))       # 公司地址二
    
    # 系統管理欄位
    front_image_path = Column(String(500))        # 正面圖片路径
    back_image_path = Column(String(500))         # 反面圖片路径
    front_ocr_text = Column(Text)                 # 正面OCR原始文字
    back_ocr_text = Column(Text)                  # 反面OCR原始文字
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Card(BaseModel):
    id: Optional[int] = None
    # 標準化的9個欄位
    name: Optional[str] = None                    # 姓名
    company_name: Optional[str] = None            # 公司名稱
    position: Optional[str] = None                # 職位
    mobile_phone: Optional[str] = None            # 手機
    office_phone: Optional[str] = None            # 公司電話
    email: Optional[str] = None                   # Email
    line_id: Optional[str] = None                 # Line ID
    notes: Optional[str] = None                   # 備註
    company_address_1: Optional[str] = None       # 公司地址一
    company_address_2: Optional[str] = None       # 公司地址二
    
    # 系統管理欄位
    front_image_path: Optional[str] = None        # 正面圖片路径
    back_image_path: Optional[str] = None         # 反面圖片路径
    front_ocr_text: Optional[str] = None          # 正面OCR原始文字
    back_ocr_text: Optional[str] = None           # 反面OCR原始文字
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True} 