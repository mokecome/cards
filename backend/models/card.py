from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.models.db import Base
import datetime

class CardORM(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本資訊欄位（中英文）
    name = Column(String(100))                    # 姓名
    name_en = Column(String(100))                 # 英文姓名
    company_name = Column(String(200))            # 公司名稱
    company_name_en = Column(String(200))         # 英文公司名稱
    position = Column(String(100))                # 職位
    position_en = Column(String(100))             # 英文職位
    
    # 部門組織架構（中英文，三層）
    department1 = Column(String(100))             # 部門1(中文)
    department1_en = Column(String(100))          # 部門1(英文)
    department2 = Column(String(100))             # 部門2(中文)
    department2_en = Column(String(100))          # 部門2(英文)
    department3 = Column(String(100))             # 部門3(中文) 
    department3_en = Column(String(100))          # 部門3(英文)
    
    # 聯絡資訊
    mobile_phone = Column(String(50))             # 手機
    company_phone1 = Column(String(50))           # 公司電話1
    company_phone2 = Column(String(50))           # 公司電話2
    email = Column(String(200))                   # Email
    line_id = Column(String(100))                 # Line ID
    
    # 地址資訊（中英文）
    company_address1 = Column(String(300))        # 公司地址一(中文)
    company_address1_en = Column(String(300))     # 公司地址一(英文)
    company_address2 = Column(String(300))        # 公司地址二(中文)
    company_address2_en = Column(String(300))     # 公司地址二(英文)
    
    # 備註資訊
    note1 = Column(Text)                          # 備註1
    note2 = Column(Text)                          # 備註2
    
    # 系統管理欄位
    front_image_path = Column(String(500))        # 正面圖片路径
    back_image_path = Column(String(500))         # 反面圖片路径
    front_ocr_text = Column(Text)                 # 正面OCR原始文字
    back_ocr_text = Column(Text)                  # 反面OCR原始文字
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Card(BaseModel):
    id: Optional[int] = None
    
    # 基本資訊欄位（中英文）
    name: Optional[str] = None                    # 姓名
    name_en: Optional[str] = None                 # 英文姓名
    company_name: Optional[str] = None            # 公司名稱
    company_name_en: Optional[str] = None         # 英文公司名稱
    position: Optional[str] = None                # 職位
    position_en: Optional[str] = None             # 英文職位
    
    # 部門組織架構（中英文，三層）
    department1: Optional[str] = None             # 部門1(中文)
    department1_en: Optional[str] = None          # 部門1(英文)
    department2: Optional[str] = None             # 部門2(中文)
    department2_en: Optional[str] = None          # 部門2(英文)
    department3: Optional[str] = None             # 部門3(中文)
    department3_en: Optional[str] = None          # 部門3(英文)
    
    # 聯絡資訊
    mobile_phone: Optional[str] = None            # 手機
    company_phone1: Optional[str] = None          # 公司電話1
    company_phone2: Optional[str] = None          # 公司電話2
    email: Optional[str] = None                   # Email
    line_id: Optional[str] = None                 # Line ID
    
    # 地址資訊（中英文）
    company_address1: Optional[str] = None        # 公司地址一(中文)
    company_address1_en: Optional[str] = None     # 公司地址一(英文)
    company_address2: Optional[str] = None        # 公司地址二(中文)
    company_address2_en: Optional[str] = None     # 公司地址二(英文)
    
    # 備註資訊
    note1: Optional[str] = None                   # 備註1
    note2: Optional[str] = None                   # 備註2
    
    # 系統管理欄位
    front_image_path: Optional[str] = None        # 正面圖片路径
    back_image_path: Optional[str] = None         # 反面圖片路径
    front_ocr_text: Optional[str] = None          # 正面OCR原始文字
    back_ocr_text: Optional[str] = None           # 反面OCR原始文字
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True} 