from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.models.card import Card
from backend.services.card_service import get_cards, get_card, create_card, update_card, delete_card
from backend.models.db import get_db
from typing import List, Optional
from fastapi.responses import StreamingResponse
import csv
import io
import openpyxl
from fastapi import Query
import logging
import os
import shutil
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 創建圖片存儲目錄
UPLOAD_DIR = "output/card_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[Card])
def list_cards(db: Session = Depends(get_db)):
    return get_cards(db)

@router.get("/{card_id}", response_model=Card)
def read_card(card_id: int, db: Session = Depends(get_db)):
    card = get_card(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="名片不存在")
    return card

@router.post("/", response_model=Card)
async def add_card(
    # 基本資訊（中英文）
    name: str = Form(...),
    name_en: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    company_name_en: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    position_en: Optional[str] = Form(None),
    
    # 部門組織架構（中英文，三層）
    department1: Optional[str] = Form(None),
    department1_en: Optional[str] = Form(None),
    department2: Optional[str] = Form(None),
    department2_en: Optional[str] = Form(None),
    department3: Optional[str] = Form(None),
    department3_en: Optional[str] = Form(None),
    
    # 聯絡資訊
    mobile_phone: Optional[str] = Form(None),
    company_phone1: Optional[str] = Form(None),
    company_phone2: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    line_id: Optional[str] = Form(None),
    
    # 地址資訊（中英文）
    company_address1: Optional[str] = Form(None),
    company_address1_en: Optional[str] = Form(None),
    company_address2: Optional[str] = Form(None),
    company_address2_en: Optional[str] = Form(None),
    
    # 備註資訊
    note1: Optional[str] = Form(None),
    note2: Optional[str] = Form(None),
    
    # 圖片文件和OCR數據
    front_image: Optional[UploadFile] = File(None),
    back_image: Optional[UploadFile] = File(None),
    front_ocr_text: Optional[str] = Form(None),
    back_ocr_text: Optional[str] = Form(None),
    
    db: Session = Depends(get_db)
):
    """
    創建新名片，支持圖片上傳和OCR數據
    """
    try:
        # 保存圖片文件
        front_image_path = None
        back_image_path = None
        
        if front_image and front_image.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            front_filename = f"front_{timestamp}_{front_image.filename}"
            front_image_path = os.path.join(UPLOAD_DIR, front_filename)
            
            with open(front_image_path, "wb") as buffer:
                shutil.copyfileobj(front_image.file, buffer)
        
        if back_image and back_image.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            back_filename = f"back_{timestamp}_{back_image.filename}"
            back_image_path = os.path.join(UPLOAD_DIR, back_filename)
            
            with open(back_image_path, "wb") as buffer:
                shutil.copyfileobj(back_image.file, buffer)
        
        # 創建名片數據對象
        card_data = Card(
            name=name,
            name_en=name_en,
            company_name=company_name,
            company_name_en=company_name_en,
            position=position,
            position_en=position_en,
            department1=department1,
            department1_en=department1_en,
            department2=department2,
            department2_en=department2_en,
            department3=department3,
            department3_en=department3_en,
            mobile_phone=mobile_phone,
            company_phone1=company_phone1,
            company_phone2=company_phone2,
            email=email,
            line_id=line_id,
            company_address1=company_address1,
            company_address1_en=company_address1_en,
            company_address2=company_address2,
            company_address2_en=company_address2_en,
            note1=note1,
            note2=note2,
            front_image_path=front_image_path,
            back_image_path=back_image_path,
            front_ocr_text=front_ocr_text,
            back_ocr_text=back_ocr_text
        )
        
        created_card = create_card(db, card_data)
        return created_card
        
    except Exception as e:
        logger.error(f"創建名片失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"創建名片失敗: {str(e)}")

@router.put("/{card_id}", response_model=Card)
async def edit_card(
    card_id: int,
    # 基本資訊（中英文）
    name: str = Form(...),
    name_en: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    company_name_en: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    position_en: Optional[str] = Form(None),
    
    # 部門組織架構（中英文，三層）
    department1: Optional[str] = Form(None),
    department1_en: Optional[str] = Form(None),
    department2: Optional[str] = Form(None),
    department2_en: Optional[str] = Form(None),
    department3: Optional[str] = Form(None),
    department3_en: Optional[str] = Form(None),
    
    # 聯絡資訊
    mobile_phone: Optional[str] = Form(None),
    company_phone1: Optional[str] = Form(None),
    company_phone2: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    line_id: Optional[str] = Form(None),
    
    # 地址資訊（中英文）
    company_address1: Optional[str] = Form(None),
    company_address1_en: Optional[str] = Form(None),
    company_address2: Optional[str] = Form(None),
    company_address2_en: Optional[str] = Form(None),
    
    # 備註資訊
    note1: Optional[str] = Form(None),
    note2: Optional[str] = Form(None),
    
    # 可選的圖片文件和OCR數據
    front_image: Optional[UploadFile] = File(None),
    back_image: Optional[UploadFile] = File(None),
    front_ocr_text: Optional[str] = Form(None),
    back_ocr_text: Optional[str] = Form(None),
    
    db: Session = Depends(get_db)
):
    """
    更新名片資料，支持圖片上傳和OCR數據
    """
    try:
        # 檢查名片是否存在
        existing_card = get_card(db, card_id)
        if not existing_card:
            raise HTTPException(status_code=404, detail="名片不存在")
        
        # 處理圖片文件
        front_image_path = existing_card.front_image_path
        back_image_path = existing_card.back_image_path
        
        if front_image and front_image.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            front_filename = f"front_{timestamp}_{front_image.filename}"
            front_image_path = os.path.join(UPLOAD_DIR, front_filename)
            
            with open(front_image_path, "wb") as buffer:
                shutil.copyfileobj(front_image.file, buffer)
        
        if back_image and back_image.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            back_filename = f"back_{timestamp}_{back_image.filename}"
            back_image_path = os.path.join(UPLOAD_DIR, back_filename)
            
            with open(back_image_path, "wb") as buffer:
                shutil.copyfileobj(back_image.file, buffer)
        
        # 創建名片更新數據對象
        card_data = Card(
            id=card_id,
            name=name,
            name_en=name_en,
            company_name=company_name,
            company_name_en=company_name_en,
            position=position,
            position_en=position_en,
            department1=department1,
            department1_en=department1_en,
            department2=department2,
            department2_en=department2_en,
            department3=department3,
            department3_en=department3_en,
            mobile_phone=mobile_phone,
            company_phone1=company_phone1,
            company_phone2=company_phone2,
            email=email,
            line_id=line_id,
            company_address1=company_address1,
            company_address1_en=company_address1_en,
            company_address2=company_address2,
            company_address2_en=company_address2_en,
            note1=note1,
            note2=note2,
            front_image_path=front_image_path,
            back_image_path=back_image_path,
            front_ocr_text=front_ocr_text or existing_card.front_ocr_text,
            back_ocr_text=back_ocr_text or existing_card.back_ocr_text,
            created_at=existing_card.created_at  # 保持原創建時間
        )
        
        updated = update_card(db, card_id, card_data)
        if not updated:
            raise HTTPException(status_code=404, detail="更新名片失敗")
        return updated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新名片失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新名片失敗: {str(e)}")

@router.delete("/{card_id}")
def remove_card(card_id: int, db: Session = Depends(get_db)):
    if not delete_card(db, card_id):
        raise HTTPException(status_code=404, detail="名片不存在")
    return {"success": True}

@router.get("/export/download")
def export_cards(format: str = Query("csv", enum=["csv", "excel", "vcard"]), db: Session = Depends(get_db)):
    """匯出名片數據"""
    try:
        logger.info(f"開始匯出，格式: {format}")
        cards = get_cards(db)
        logger.info(f"找到 {len(cards)} 張名片")
        
        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            # 更新為新的標準化欄位
            writer.writerow([
                "姓名", "公司名稱", "職位", "手機", "公司電話", 
                "Email", "Line ID", "備註", "公司地址一", "公司地址二"
            ])
            for card in cards:
                writer.writerow([
                    card.name or "",
                    card.company_name or "",
                    card.position or "",
                    card.mobile_phone or "",
                    card.office_phone or "",
                    card.email or "",
                    card.line_id or "",
                    card.notes or "",
                    card.company_address_1 or "",
                    card.company_address_2 or ""
                ])
            output.seek(0)
            content = output.getvalue().encode('utf-8-sig')  # 添加BOM以支持中文
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=cards.csv",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )
            
        elif format == "excel":
            try:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "名片資料"
                
                # 設置標題行 - 更新為新的標準化欄位
                headers = [
                    "姓名", "公司名稱", "職位", "手機", "公司電話", 
                    "Email", "Line ID", "備註", "公司地址一", "公司地址二"
                ]
                ws.append(headers)
                
                # 添加數據
                for card in cards:
                    ws.append([
                        card.name or "",
                        card.company_name or "",
                        card.position or "",
                        card.mobile_phone or "",
                        card.office_phone or "",
                        card.email or "",
                        card.line_id or "",
                        card.notes or "",
                        card.company_address_1 or "",
                        card.company_address_2 or ""
                    ])
                
                # 自動調整列寬
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
                
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                
                logger.info("EXCEL文件生成成功")
                
                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={
                        "Content-Disposition": "attachment; filename=cards.xlsx",
                        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    }
                )
                
            except Exception as e:
                logger.error(f"生成EXCEL文件時發生錯誤: {str(e)}")
                raise HTTPException(status_code=500, detail=f"EXCEL生成失敗: {str(e)}")
                
        elif format == "vcard":
            output = io.StringIO()
            for card in cards:
                output.write(f"BEGIN:VCARD\nVERSION:3.0\n")
                if card.name:
                    output.write(f"FN:{card.name}\n")
                if card.company_name:
                    output.write(f"ORG:{card.company_name}\n")
                if card.position:
                    output.write(f"TITLE:{card.position}\n")
                if card.office_phone:
                    output.write(f"TEL;TYPE=WORK,VOICE:{card.office_phone}\n")
                if card.mobile_phone:
                    output.write(f"TEL;TYPE=CELL:{card.mobile_phone}\n")
                if card.email:
                    output.write(f"EMAIL;TYPE=INTERNET:{card.email}\n")
                if card.company_address_1:
                    address = card.company_address_1
                    if card.company_address_2:
                        address += f" {card.company_address_2}"
                    output.write(f"ADR;TYPE=WORK:;;{address};;;;\n")
                output.write("END:VCARD\n")
            output.seek(0)
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="text/vcard",
                headers={
                    "Content-Disposition": "attachment; filename=cards.vcf",
                    "Content-Type": "text/vcard; charset=utf-8"
                }
            )
        else:
            raise HTTPException(status_code=400, detail="不支援的匯出格式")
            
    except Exception as e:
        logger.error(f"匯出過程中發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}") 