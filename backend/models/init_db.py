from backend.models.db import Base, engine
from backend.models.card import CardORM
from sqlalchemy import text

def init_db():
    """初始化數據庫並進行欄位遷移"""
    
    # 創建所有表格
    Base.metadata.create_all(bind=engine)
    
    # 檢查是否需要遷移現有數據
    with engine.connect() as connection:
        try:
            # 檢查新欄位是否存在
            result = connection.execute(text("PRAGMA table_info(cards)"))
            columns = [row[1] for row in result.fetchall()]
            
            # 基本欄位（保持原有邏輯）
            basic_columns = {
                'company_name': 'VARCHAR(200)',
                'position': 'VARCHAR(100)', 
                'mobile_phone': 'VARCHAR(50)',
                'line_id': 'VARCHAR(100)',
                'front_image_path': 'VARCHAR(500)',
                'back_image_path': 'VARCHAR(500)',
                'front_ocr_text': 'TEXT',
                'back_ocr_text': 'TEXT'
            }
            
            # 新增的22個欄位系統
            extended_columns = {
                # 基本資訊（英文）
                'name_en': 'VARCHAR(100)',
                'company_name_en': 'VARCHAR(200)',
                'position_en': 'VARCHAR(100)',
                
                # 部門組織架構（中英文，三層）
                'department1': 'VARCHAR(100)',
                'department1_en': 'VARCHAR(100)',
                'department2': 'VARCHAR(100)',
                'department2_en': 'VARCHAR(100)',
                'department3': 'VARCHAR(100)',
                'department3_en': 'VARCHAR(100)',
                
                # 聯絡資訊擴充
                'company_phone1': 'VARCHAR(50)',
                'company_phone2': 'VARCHAR(50)',
                
                # 地址資訊（新格式+英文）
                'company_address1': 'VARCHAR(300)',
                'company_address1_en': 'VARCHAR(300)',
                'company_address2': 'VARCHAR(300)',
                'company_address2_en': 'VARCHAR(300)',
                
                # 備註資訊
                'note1': 'TEXT',
                'note2': 'TEXT'
            }
            
            # 合併所有需要添加的欄位
            all_new_columns = {**basic_columns, **extended_columns}
            
            # 添加缺失的欄位
            for column_name, column_type in all_new_columns.items():
                if column_name not in columns:
                    try:
                        connection.execute(text(f"ALTER TABLE cards ADD COLUMN {column_name} {column_type}"))
                        print(f"已添加欄位: {column_name}")
                    except Exception as e:
                        print(f"添加欄位 {column_name} 時發生錯誤: {e}")
            
            # 數據遷移：將舊欄位映射到新欄位
            basic_migration_mapping = {
                'company': 'company_name',
                'title': 'position', 
                'mobile': 'mobile_phone',
                'phone': 'company_phone1',
                'address': 'company_address1',
                'image_path': 'front_image_path',
                'image_back_path': 'back_image_path',
                'raw_text': 'front_ocr_text'
            }
            
            # 進行基本遷移
            for old_column, new_column in basic_migration_mapping.items():
                if old_column in columns and new_column in columns:
                    try:
                        # 只遷移非空數據且新欄位為空的記錄
                        connection.execute(text(f"""
                            UPDATE cards 
                            SET {new_column} = {old_column} 
                            WHERE {old_column} IS NOT NULL 
                            AND {old_column} != '' 
                            AND ({new_column} IS NULL OR {new_column} = '')
                        """))
                        print(f"已遷移數據: {old_column} -> {new_column}")
                    except Exception as e:
                        print(f"遷移數據 {old_column} -> {new_column} 時發生錯誤: {e}")
            
            # 兼容欄位已被刪除，無需進行兼容性遷移
            
            connection.commit()
            print("數據庫初始化和遷移完成！支援22個完整欄位系統")
            
        except Exception as e:
            print(f"數據庫遷移過程中發生錯誤: {e}")
            connection.rollback()

if __name__ == "__main__":
    init_db() 