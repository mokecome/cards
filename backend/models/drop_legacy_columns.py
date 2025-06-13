import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.db import engine
from sqlalchemy import text
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_legacy_columns():
    """刪除兼容舊資料的物理欄位"""
    
    # 要刪除的兼容欄位
    legacy_columns = [
        'office_phone',      # 公司電話(舊版) -> 已遷移到 company_phone1
        'notes',             # 備註(舊版) -> 已遷移到 note1
        'company_address_1', # 公司地址一(舊版) -> 已遷移到 company_address1
        'company_address_2'  # 公司地址二(舊版) -> 已遷移到 company_address2
    ]
    
    with engine.connect() as connection:
        try:
            # 檢查表格結構
            result = connection.execute(text("PRAGMA table_info(cards)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            logger.info(f"當前表格欄位: {existing_columns}")
            
            # 檢查要刪除的欄位是否存在
            columns_to_drop = [col for col in legacy_columns if col in existing_columns]
            
            if not columns_to_drop:
                logger.info("沒有需要刪除的兼容欄位")
                return
            
            logger.info(f"準備刪除的兼容欄位: {columns_to_drop}")
            
            # SQLite 不支持直接 DROP COLUMN，需要重建表格
            # 1. 獲取當前表格結構（排除要刪除的欄位）
            keep_columns = [col for col in existing_columns if col not in legacy_columns]
            
            logger.info(f"保留的欄位: {keep_columns}")
            
            # 2. 創建新表格結構
            create_new_table_sql = f"""
            CREATE TABLE cards_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                name_en VARCHAR(100),
                company_name VARCHAR(200),
                company_name_en VARCHAR(200),
                position VARCHAR(100),
                position_en VARCHAR(100),
                department1 VARCHAR(100),
                department1_en VARCHAR(100),
                department2 VARCHAR(100),
                department2_en VARCHAR(100),
                department3 VARCHAR(100),
                department3_en VARCHAR(100),
                mobile_phone VARCHAR(50),
                company_phone1 VARCHAR(50),
                company_phone2 VARCHAR(50),
                email VARCHAR(200),
                line_id VARCHAR(100),
                company_address1 VARCHAR(300),
                company_address1_en VARCHAR(300),
                company_address2 VARCHAR(300),
                company_address2_en VARCHAR(300),
                note1 TEXT,
                note2 TEXT,
                front_image_path VARCHAR(500),
                back_image_path VARCHAR(500),
                front_ocr_text TEXT,
                back_ocr_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # 3. 執行遷移
            logger.info("開始創建新表格...")
            connection.execute(text(create_new_table_sql))
            
            # 4. 複製數據（只複製保留的欄位）
            keep_columns_str = ', '.join(keep_columns)
            copy_data_sql = f"""
            INSERT INTO cards_new ({keep_columns_str})
            SELECT {keep_columns_str} FROM cards
            """
            
            logger.info("開始複製數據...")
            connection.execute(text(copy_data_sql))
            
            # 5. 刪除舊表格
            logger.info("刪除舊表格...")
            connection.execute(text("DROP TABLE cards"))
            
            # 6. 重命名新表格
            logger.info("重命名新表格...")
            connection.execute(text("ALTER TABLE cards_new RENAME TO cards"))
            
            # 7. 提交事務
            connection.commit()
            
            logger.info("✅ 成功刪除兼容舊資料欄位:")
            for col in columns_to_drop:
                logger.info(f"   - {col}")
            
            logger.info("🎉 資料庫結構已完全清理，僅保留22個標準欄位")
            
        except Exception as e:
            logger.error(f"❌ 刪除兼容欄位時發生錯誤: {e}")
            connection.rollback()
            raise

def verify_migration():
    """驗證遷移結果"""
    with engine.connect() as connection:
        try:
            result = connection.execute(text("PRAGMA table_info(cards)"))
            current_columns = [row[1] for row in result.fetchall()]
            
            logger.info("🔍 遷移後的表格結構:")
            for col in sorted(current_columns):
                logger.info(f"   ✓ {col}")
            
            # 檢查是否還有兼容欄位
            legacy_columns = ['office_phone', 'notes', 'company_address_1', 'company_address_2']
            remaining_legacy = [col for col in legacy_columns if col in current_columns]
            
            if remaining_legacy:
                logger.warning(f"⚠️  仍存在兼容欄位: {remaining_legacy}")
                return False
            else:
                logger.info("✅ 所有兼容欄位已成功刪除")
                return True
                
        except Exception as e:
            logger.error(f"❌ 驗證遷移時發生錯誤: {e}")
            return False

if __name__ == "__main__":
    print("🚀 開始刪除兼容舊資料欄位...")
    print("⚠️  注意：此操作將永久刪除資料庫中的兼容欄位，請確保已備份重要數據")
    
    # 詢問用戶確認
    confirm = input("是否繼續？(y/N): ").lower().strip()
    if confirm != 'y':
        print("❌ 操作已取消")
        exit(0)
    
    try:
        drop_legacy_columns()
        if verify_migration():
            print("🎉 遷移完成！資料庫已完全清理兼容欄位")
        else:
            print("⚠️  遷移可能未完全成功，請檢查日誌")
    except Exception as e:
        print(f"❌ 遷移失敗: {e}")
        exit(1) 