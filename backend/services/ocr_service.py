from PIL import Image
import io
import numpy as np
import os
from datetime import datetime
import requests
import re
import json
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from backend.core.config import settings

@dataclass
class ParseResult:
    """解析結果封裝類"""
    fields: Dict[str, str]
    confidence: float = 0.0
    parse_method: str = ""
    
class FieldMapper:
    """負責欄位映射的獨立類"""
    
    def __init__(self):
        self.field_mapping = {
            # 姓名相關
            "姓名": "name", "名字": "name", "名稱": "name",
            # 公司相關
            "公司名稱": "company_name", "公司": "company_name", 
            "企業名稱": "company_name", "企業": "company_name",
            # 職位相關
            "職位": "position", "職稱": "position", "崗位": "position",
            # 手機相關
            "手機": "mobile_phone", "手機號": "mobile_phone", 
            "手機號碼": "mobile_phone", "行動電話": "mobile_phone", "行動": "mobile_phone",
            # 電話相關
            "公司電話": "office_phone", "電話": "office_phone", 
            "辦公電話": "office_phone", "固話": "office_phone", "市話": "office_phone",
            # 郵件相關
            "Email": "email", "email": "email", "E-mail": "email",
            "郵箱": "email", "電子郵件": "email", "信箱": "email",
            # Line相關
            "Line ID": "line_id", "LINE ID": "line_id", "line_id": "line_id",
            "Line": "line_id", "LINE": "line_id", "賴": "line_id",
            # 地址相關
            "公司地址一": "company_address_1", "公司地址": "company_address_1",
            "地址一": "company_address_1", "地址": "company_address_1", "住址": "company_address_1",
            "公司地址二": "company_address_2", "地址二": "company_address_2",
            # 備註相關
            "備註": "notes", "備注": "notes", "說明": "notes", "其他": "notes", "註": "notes"
        }
        
        # 預編譯模糊匹配規則
        self._fuzzy_patterns = self._build_fuzzy_patterns()
    
    def _build_fuzzy_patterns(self) -> List[Tuple[str, str]]:
        """構建模糊匹配模式"""
        patterns = []
        for chinese_key, english_key in self.field_mapping.items():
            # 為每個中文key建立模糊匹配模式
            pattern = f".*{re.escape(chinese_key)}.*"
            patterns.append((pattern, english_key))
        return patterns
    
    def map_field(self, key: str) -> Optional[str]:
        """精確映射欄位名"""
        cleaned_key = key.strip().strip('"\'')
        return self.field_mapping.get(cleaned_key)
    
    def fuzzy_map_field(self, key: str) -> Optional[str]:
        """模糊映射欄位名"""
        cleaned_key = key.strip().strip('"\'')
        
        # 先嘗試精確匹配
        exact_match = self.field_mapping.get(cleaned_key)
        if exact_match:
            return exact_match
        
        # 模糊匹配
        for pattern, english_key in self._fuzzy_patterns:
            if re.match(pattern, cleaned_key, re.IGNORECASE):
                return english_key
        
        return None

class TextParser:
    """文本解析器基類"""
    
    def __init__(self, field_mapper: FieldMapper, logger: logging.Logger):
        self.field_mapper = field_mapper
        self.logger = logger
    
    def parse(self, text: str) -> Optional[ParseResult]:
        """解析文本，子類需要實現此方法"""
        raise NotImplementedError

class JSONParser(TextParser):
    """JSON格式解析器"""
    
    def parse(self, text: str) -> Optional[ParseResult]:
        """解析JSON格式文本"""
        try:
            normalized_text = self._normalize_json_text(text)
            
            if not (normalized_text.strip().startswith('{') and normalized_text.strip().endswith('}')):
                return None
            
            raw_data = json.loads(normalized_text)
            mapped_fields = self._map_fields(raw_data)
            
            if mapped_fields:
                return ParseResult(
                    fields=mapped_fields,
                    confidence=0.9,
                    parse_method="JSON"
                )
                
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.debug(f"JSON解析失敗: {e}")
        except Exception as e:
            self.logger.error(f"JSON解析異常: {e}")
        
        return None
    
    def _normalize_json_text(self, text: str) -> str:
        """標準化JSON文本格式"""
        try:
            text = text.strip()
            
            # 優化正則表達式，使用編譯後的模式提升性能
            replacements = [
                (r"'([^']*)':", r'"\1":'),  # 'key': -> "key":
                (r":\s*'([^']*)'", r': "\1"'),  # : 'value' -> : "value"
                (r'([{,]\s*)([^"{\s][^:]*?)(\s*:)', r'\1"\2"\3'),  # key: -> "key":
                (r',\s*}', '}'),  # 移除多餘逗號
                (r',\s*]', ']')
            ]
            
            for pattern, replacement in replacements:
                text = re.sub(pattern, replacement, text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"JSON文本標準化失敗: {e}")
            return text
    
    def _map_fields(self, raw_data: Dict) -> Dict[str, str]:
        """映射欄位"""
        mapped_fields = {}
        
        for key, value in raw_data.items():
            if not value or not str(value).strip():
                continue
            
            cleaned_value = str(value).strip()
            mapped_key = self.field_mapper.map_field(key)
            
            if mapped_key:
                mapped_fields[mapped_key] = cleaned_value
            else:
                # 嘗試模糊匹配
                fuzzy_key = self.field_mapper.fuzzy_map_field(key)
                if fuzzy_key:
                    mapped_fields[fuzzy_key] = cleaned_value
        
        return mapped_fields

class KeyValueParser(TextParser):
    """鍵值對格式解析器"""
    
    def __init__(self, field_mapper: FieldMapper, logger: logging.Logger):
        super().__init__(field_mapper, logger)
        # 預編譯正則表達式提升性能
        self.patterns = [
            re.compile(r'"([^"]+)"\s*:\s*"([^"]*)"'),  # "key": "value"
            re.compile(r"'([^']+)'\s*:\s*'([^']*)'"),  # 'key': 'value'
            re.compile(r'"([^"]+)"\s*:\s*([^",}]+)'),  # "key": value
            re.compile(r'([^":]+?)\s*:\s*"([^"]*)"'),  # key: "value"
            re.compile(r'([^":]+?)\s*:\s*([^",}\n]+)', re.MULTILINE)  # key: value
        ]
    
    def parse(self, text: str) -> Optional[ParseResult]:
        """解析鍵值對格式文本"""
        try:
            result = {}
            matches_found = False
            
            for pattern in self.patterns:
                matches = pattern.findall(text)
                for key, value in matches:
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    
                    if key and value:
                        mapped_key = self.field_mapper.map_field(key)
                        if mapped_key:
                            result[mapped_key] = value
                            matches_found = True
                        else:
                            # 嘗試模糊匹配
                            fuzzy_key = self.field_mapper.fuzzy_map_field(key)
                            if fuzzy_key:
                                result[fuzzy_key] = value
                                matches_found = True
            
            if matches_found:
                return ParseResult(
                    fields=result,
                    confidence=0.7,
                    parse_method="KeyValue"
                )
                
        except Exception as e:
            self.logger.error(f"鍵值對解析失敗: {e}")
        
        return None

class TextAnalyzer:
    """文本分析器 - 使用正則表達式和關鍵字匹配"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # 預編譯所有正則表達式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """預編譯正則表達式模式"""
        # 台灣手機號碼
        self.mobile_patterns = [
            re.compile(r'09\d{8}'),
            re.compile(r'09\d{2}-\d{3}-\d{3}'),
            re.compile(r'09\d{2}\s\d{3}\s\d{3}'),
            re.compile(r'\+886\s?9\d{8}')
        ]
        
        # 台灣市話
        self.office_patterns = [
            re.compile(r'0[2-8]-?\d{7,8}'),
            re.compile(r'\(0[2-8]\)\s?\d{7,8}'),
            re.compile(r'02-?\d{8}'),
            re.compile(r'0[3-8]-?\d{7,8}')
        ]
        
        # Email
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Line ID
        self.line_patterns = [
            re.compile(r'Line\s*ID\s*[:\s]\s*([A-Za-z0-9._-]+)', re.IGNORECASE),
            re.compile(r'LINE\s*[:\s]\s*([A-Za-z0-9._-]+)', re.IGNORECASE),
            re.compile(r'賴\s*[:\s]\s*([A-Za-z0-9._-]+)', re.IGNORECASE)
        ]
    
    def extract_phone_numbers(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取手機和辦公電話"""
        mobile_phone = None
        office_phone = None
        
        # 提取手機號碼
        for pattern in self.mobile_patterns:
            match = pattern.search(text)
            if match:
                mobile_phone = re.sub(r'[^\d+]', '', match.group())
                break
        
        # 提取辦公電話（如果沒有找到手機號碼）
        if not mobile_phone:
            for pattern in self.office_patterns:
                match = pattern.search(text)
                if match:
                    office_phone = match.group()
                    break
        
        return mobile_phone, office_phone
    
    def extract_email(self, text: str) -> Optional[str]:
        """提取郵件地址"""
        match = self.email_pattern.search(text)
        return match.group() if match else None
    
    def extract_line_id(self, text: str) -> Optional[str]:
        """提取Line ID"""
        for pattern in self.line_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None
    
    def extract_address(self, lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """提取地址信息"""
        address_keywords = ['市', '區', '鄉', '鎮', '路', '街', '巷', '弄', '號', '樓', '縣']
        address_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in address_keywords) and len(line) > 5:
                address_lines.append(line)
        
        address_1 = address_lines[0] if len(address_lines) > 0 else None
        address_2 = address_lines[1] if len(address_lines) > 1 else None
        
        return address_1, address_2
    
    def extract_name_and_position(self, lines: List[str], side: str) -> Tuple[Optional[str], Optional[str]]:
        """提取姓名和職位"""
        name = None
        position = None
        
        if side == 'front' and lines:
            # 姓名通常在前面幾行
            for line in lines[:3]:
                if not re.search(r'[\d@./-]', line) and 2 <= len(line) <= 8:
                    name = line
                    break
        
        # 職位關鍵字
        position_keywords = ['經理', '總監', '主任', '課長', '部長', '總經理', '執行長', '董事', '協理', '專員', '組長', '副理']
        for line in lines:
            if any(keyword in line for keyword in position_keywords):
                position = line
                break
        
        return name, position
    
    def extract_company(self, lines: List[str]) -> Optional[str]:
        """提取公司名稱"""
        company_keywords = ['公司', '企業', '集團', '股份', '有限', 'Co.', 'Ltd', 'Inc', 'Corp']
        for line in lines:
            if any(keyword in line for keyword in company_keywords):
                return line
        return None

class OCRService:
    def __init__(self, OCR_URL=None):
        self.OCR_URL = OCR_URL or settings.OCR_URL
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        
        # 初始化組件
        self.field_mapper = FieldMapper()
        self.text_analyzer = TextAnalyzer(self.logger)
        
        # 初始化解析器
        self.parsers = [
            JSONParser(self.field_mapper, self.logger),
            KeyValueParser(self.field_mapper, self.logger)
        ]
        
    async def ocr_image(self, image_bytes: bytes):
        """OCR圖片識別"""
        files = []
        try:
            # 準備圖片
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            files.append(('file', ('image.jpg', buffer, 'image/jpeg')))
            
            # 設置請求headers和超時
            headers = {
                'User-Agent': 'OCR-Service/1.0',
            }
            
            self.logger.info(f"正在調用OCR API: {self.OCR_URL}")
            
            # 嘗試不同的請求方式
            # 直接使用正確的API格式
            response = requests.post(
                self.OCR_URL, 
                files=files, 
                headers=headers,
                verify=settings.OCR_VERIFY_SSL,
                timeout=settings.OCR_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"OCR API響應成功: {result}")
            return result.get("result")
        
        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL證書錯誤: {e}")
            self.logger.info("建議：檢查OCR API的SSL配置或聯繫API提供方")
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP錯誤: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"響應內容: {e.response.text}")
                self.logger.error(f"響應headers: {dict(e.response.headers)}")
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"連接錯誤: {e}")
            self.logger.info("建議：檢查網絡連接或API服務狀態")
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"請求超時: {e}")
            self.logger.info("建議：檢查網絡速度或增加超時時間")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OCR請求失敗: {e}")
            
        except ValueError as e:
            self.logger.error(f"OCR回傳格式錯誤: {e}")
            
        except Exception as e:
            self.logger.error(f"OCR處理異常: {e}")
            
        # 降級策略：返回空結果但不影響後續處理
        self.logger.warning("OCR API調用失敗，返回空結果。可使用手動輸入或檢查API配置")
        return None

    def parse_ocr_to_fields(self, ocr_text: str, side: str = 'front') -> Dict[str, Optional[str]]:
        """
        智能解析OCR文字到標準化欄位
        
        優化後的解析策略：
        1. 結構化數據解析 (JSON, 鍵值對)
        2. 文本分析解析 (正則表達式 + 關鍵字)
        3. 結果合併和驗證

        Args:
            ocr_text: OCR識別的原始文字
            side: 'front' 或 'back' 表示名片正面或反面
            
        Returns:
            Dict: 包含解析後的欄位資料
        """
        if not ocr_text or not ocr_text.strip():
            return {}
        
        self.logger.info(f"開始解析OCR文本 ({side}): {ocr_text[:100]}...")
        
        # 階段1: 嘗試結構化解析
        best_result = None
        for parser in self.parsers:
            result = parser.parse(ocr_text)
            if result and (not best_result or result.confidence > best_result.confidence):
                best_result = result
        
        if best_result and best_result.fields:
            self.logger.info(f"{best_result.parse_method}解析成功，置信度: {best_result.confidence}")
            return best_result.fields
        
        # 階段2: 文本分析解析
        self.logger.info("使用文本分析模式")
        return self._analyze_text_content(ocr_text, side)
    
    def _analyze_text_content(self, ocr_text: str, side: str) -> Dict[str, Optional[str]]:
        """分析文本內容並提取字段"""
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        full_text = ' '.join(lines)
        parsed_fields = {}
        
        # 提取各種信息
        mobile_phone, office_phone = self.text_analyzer.extract_phone_numbers(full_text)
        if mobile_phone:
            parsed_fields['mobile_phone'] = mobile_phone
        if office_phone:
            parsed_fields['office_phone'] = office_phone
        
        email = self.text_analyzer.extract_email(full_text)
        if email:
            parsed_fields['email'] = email
        
        line_id = self.text_analyzer.extract_line_id(full_text)
        if line_id:
            parsed_fields['line_id'] = line_id
        
        address_1, address_2 = self.text_analyzer.extract_address(lines)
        if address_1:
            parsed_fields['company_address_1'] = address_1
        if address_2:
            parsed_fields['company_address_2'] = address_2
        
        name, position = self.text_analyzer.extract_name_and_position(lines, side)
        if name:
            parsed_fields['name'] = name
        if position:
            parsed_fields['position'] = position
        
        company = self.text_analyzer.extract_company(lines)
        if company:
            parsed_fields['company_name'] = company
        
        # 處理備註 (反面專用)
        if side == 'back':
            remaining_text = []
            for line in lines:
                if not any(field_value == line for field_value in parsed_fields.values()):
                    remaining_text.append(line)
            
            if remaining_text:
                parsed_fields['notes'] = '\n'.join(remaining_text)
        
        return parsed_fields
    
    def merge_front_back_data(self, front_data: Dict, back_data: Dict) -> Dict:
        """
        合併正面和反面的解析數據
        
        Args:
            front_data: 正面OCR解析結果
            back_data: 反面OCR解析結果
            
        Returns:
            Dict: 合併後的完整名片資料
        """
        merged_data = {}
        
        # 優先使用正面的關鍵資訊
        front_priority_fields = ['name', 'company_name', 'position', 'mobile_phone', 'office_phone', 'email']
        
        for field in front_priority_fields:
            if front_data.get(field):
                merged_data[field] = front_data[field]
            elif back_data.get(field):
                merged_data[field] = back_data[field]
        
        # 其他欄位取非空值或合併
        other_fields = ['line_id', 'company_address_1', 'company_address_2', 'notes']
        for field in other_fields:
            front_value = front_data.get(field, "")
            back_value = back_data.get(field, "")
            
            if front_value and back_value:
                if field == 'notes':
                    merged_data[field] = f"{front_value}\n{back_value}"
                else:
                    # 選擇較長的值，通常包含更多信息
                    merged_data[field] = front_value if len(front_value) > len(back_value) else back_value
            elif front_value:
                merged_data[field] = front_value
            elif back_value:
                merged_data[field] = back_value
        
        return merged_data
