# 1. 項目目標
本系統旨在數位化管理實體名片，結合 OCR（光學文字辨識）技術，讓使用者能夠：
上傳名片圖片，自動辨識並提取名片資訊
編輯、查詢、管理名片資料
匯出名片資料（CSV、Excel、vCard）
支援多欄位（姓名、公司、職位、電話、Email、地址、備註等）與圖片存檔

# 2. 技術架構
前端（frontend）
技術棧：React + Ant Design Mobile + axios
主要功能：
表單輸入與圖片上傳
調用後端 API 進行 OCR 與名片資料管理
名片列表、詳細頁、編輯、新增、刪除、匯出
使用 Toast、Modal 等元件提升用戶體驗
API 請求：統一走 /api/v1 路徑，支援環境變數配置
後端（backend）
技術棧：FastAPI + SQLAlchemy + Uvicorn
主要功能：
提供 RESTful API（CRUD、OCR、匯出）
圖片上傳與儲存
OCR 文字解析與欄位自動填充
資料庫管理名片資料
完善的錯誤處理與日誌記錄
API 路徑：/api/v1/cards/（名片管理）、/api/v1/ocr/image（OCR）、/api/v1/ocr/parse-fields（智能欄位解析）

# 3. 主要流程
上傳名片圖片 → 前端呼叫 /api/v1/ocr/image → 後端 OCR 辨識 → 回傳文字
智能欄位解析 → 前端呼叫 /api/v1/ocr/parse-fields → 後端自動對應欄位
保存名片 → 前端呼叫 /api/v1/cards/（POST） → 後端存入資料庫與圖片
名片管理 → 前端查詢、編輯、刪除、匯出 → 後端對應 API 處理

# 4. 適用場景
企業或個人需要大量管理實體名片
需要自動化 OCR 辨識與資料結構化
需支援多設備（手機、電腦）瀏覽與操作
