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
            # 基本資訊（中英文）
            "姓名": "name", "名字": "name", "名稱": "name",
            "name_en": "name_en", "英文姓名": "name_en",
            "公司名稱": "company_name", "公司": "company_name", 
            "企業名稱": "company_name", "企業": "company_name",
            "company_name_en": "company_name_en", "Company": "company_name_en", 
            "英文公司名稱": "company_name_en", "英文公司": "company_name_en",
            "職位": "position", "職稱": "position", "崗位": "position",
            "position_en": "position_en", "Position": "position_en", 
            "英文職位": "position_en", "英文職稱": "position_en",
            
            # 部門組織架構（中英文，三層）
            "部門1": "department1", "部門1(單位1)": "department1", "單位1": "department1",
            "部門2": "department2", "部門2(單位2)": "department2", "單位2": "department2", 
            "部門3": "department3", "部門3(單位3)": "department3", "單位3": "department3",
            "Department1": "department1_en", "Department1_en": "department1_en",
            "Department2": "department2_en", "Department2_en": "department2_en",
            "Department3": "department3_en", "Department3_en": "department3_en",
            
            # 聯絡資訊
            "手機": "mobile_phone", "手機號": "mobile_phone", "手機(mobile)": "mobile_phone",
            "手機號碼": "mobile_phone", "行動電話": "mobile_phone", "行動": "mobile_phone",
            "公司電話1": "company_phone1", "電話1": "company_phone1", 
            "公司電話2": "company_phone2", "電話2": "company_phone2",
            "公司電話": "company_phone1", "電話": "company_phone1", 
            "辦公電話": "company_phone1", "固話": "company_phone1", "市話": "company_phone1",
            "Email": "email", "email": "email", "E-mail": "email",
            "郵箱": "email", "電子郵件": "email", "信箱": "email",
            "Line ID": "line_id", "LINE ID": "line_id", "line_id": "line_id",
            "Line": "line_id", "LINE": "line_id", "賴": "line_id",
            
            # 地址資訊（中英文）
            "公司地址一": "company_address1", "公司地址": "company_address1",
            "地址一": "company_address1", "地址": "company_address1", "住址": "company_address1",
            "公司地址二": "company_address2", "地址二": "company_address2",
            "company_address1_en": "company_address1_en", "company_address2_en": "company_address2_en",
            "英文地址一": "company_address1_en", "英文地址二": "company_address2_en",
            
            # 備註資訊
            "note1": "note1", "備註1": "note1", "備註一": "note1",
            "note2": "note2", "備註2": "note2", "備註二": "note2",
            "備註": "note1", "備注": "note1", "說明": "note1", "其他": "note1", "註": "note1"
        }
        
        # 預編譯模糊匹配規則
        self._fuzzy_patterns = self._build_fuzzy_patterns()
        
        # 智能提取的正則表達式
        self._compile_extraction_patterns()
    
    def _compile_extraction_patterns(self):
        """編譯智能提取用的正則表達式"""
        # 電話號碼提取模式（支援多種格式，包括換行符分隔）
        self.phone_patterns = [
            # 台灣手機號碼格式（09開頭）
            re.compile(r'\b09\d{8}\b'),  # 0912345678
            re.compile(r'\b09\d{2}[-\s]\d{3}[-\s]\d{3}\b'),  # 0912-345-678
            
            # 台灣市話格式（02-08開頭）
            re.compile(r'\b0[2-8][-\s]?\d{7,8}\b'),  # 02-12345678
            re.compile(r'\b\(0[2-8]\)\s?\d{7,8}\b'),  # (02) 12345678
            re.compile(r'\b0[2-8][-\s]?\d{4}[-\s]?\d{4}(?:[-\s]?\d{1,4})?\b'),  # 02-1234-5678-123
            
            # 純數字格式（10-11位）
            re.compile(r'\b\d{10,11}\b')
        ]
        
        # 部門名稱提取模式
        self.department_patterns = [
            re.compile(r'部門[：:]\s*([^,，\n]+?)(?:[,，]|$)', re.MULTILINE),
            re.compile(r'單位[：:]\s*([^,，\n]+?)(?:[,，]|$)', re.MULTILINE),
            re.compile(r'([^,，\n]*(?:部|處|司|課|組|中心|事業群)[^,，\n]*)'),
        ]
        
        # 地址提取模式
        self.address_patterns = [
            re.compile(r'地址[：:]\s*([^,，\n]+?)(?:[,，]|$)', re.MULTILINE),
            re.compile(r'(?:台北|新北|桃園|台中|台南|高雄|基隆|新竹|苗栗|彰化|南投|雲林|嘉義|屏東|宜蘭|花蓮|台東|澎湖|金門|連江)[^,，\n]*[路街巷弄號][^,，\n]*'),
        ]
    
    def extract_multiple_phones_from_text(self, text: str) -> List[str]:
        """從文字中提取多個電話號碼，支援換行符分隔和語義判別"""
        phones = []
        
        # 首先按換行符分割文字，處理換行符分隔的電話
        lines = text.split('\n')
        
        # 對每一行進行電話號碼提取
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 檢查整行是否就是電話號碼
            if self._is_phone_number(line):
                phones.append(line)
                continue
            
            # 使用正則表達式提取電話號碼
            for pattern in self.phone_patterns:
                matches = pattern.findall(line)
                for match in matches:
                    # 清理和標準化電話號碼，但保留原始格式用於判斷
                    if self._is_phone_number(match):
                        phones.append(match.strip())
        
        # 去重並保持順序
        seen = set()
        unique_phones = []
        for phone in phones:
            if phone not in seen:
                seen.add(phone)
                unique_phones.append(phone)
        
        return unique_phones[:3]  # 最多返回3個電話號碼
    
    def _is_phone_number(self, text: str) -> bool:
        """判斷文字是否為電話號碼"""
        # 移除所有非數字字符進行判斷
        digits_only = re.sub(r'[^\d]', '', text)
        
        # 台灣電話號碼特徵
        if len(digits_only) >= 9 and len(digits_only) <= 11:
            # 手機號碼：09開頭（10位）
            if digits_only.startswith('09') and len(digits_only) == 10:
                return True
            # 手機號碼：091開頭（9位，舊格式）
            if digits_only.startswith('091') and len(digits_only) == 9:
                return True
            # 市話：02-08開頭（9-11位）
            if digits_only.startswith(('02', '03', '04', '05', '06', '07', '08')):
                return True
        
        return False
    
    def classify_phone_type(self, phone: str) -> str:
        """根據電話號碼格式判斷類型"""
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # 手機號碼：09開頭（10位）或091開頭（9位舊格式）
        if (digits_only.startswith('09') and len(digits_only) == 10) or \
           (digits_only.startswith('091') and len(digits_only) == 9):
            return 'mobile'
        elif digits_only.startswith(('02', '03', '04', '05', '06', '07', '08')):
            return 'company'
        else:
            # 預設為公司電話
            return 'company'
    
    def extract_multiple_departments_from_text(self, text: str) -> List[str]:
        """從文字中提取多個部門名稱，支援換行符分隔"""
        departments = []
        
        # 首先按換行符分割文字，處理換行符分隔的部門
        lines = text.split('\n')
        
        # 對每一行進行部門名稱檢查
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 檢查整行是否為部門名稱
            if self._is_department_name(line):
                departments.append(line)
                continue
        
        # 如果沒有找到明顯的部門，使用正則表達式提取
        if not departments:
            for pattern in self.department_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    cleaned_dept = match.strip()
                    if cleaned_dept and len(cleaned_dept) > 1:
                        departments.append(cleaned_dept)
        
        # 去重並保持順序
        seen = set()
        unique_departments = []
        for dept in departments:
            if dept not in seen:
                seen.add(dept)
                unique_departments.append(dept)
        
        return unique_departments[:3]  # 最多返回3個部門
    
    def _is_department_name(self, text: str) -> bool:
        """判斷文字是否為部門名稱"""
        # 部門關鍵字
        dept_keywords = ['部', '處', '司', '課', '組', '中心', '事業群', '事業部', '營業部', '業務部', 
                        '技術部', '研發部', '行政部', '人事部', '財務部', '會計部', '資訊部', '企劃部']
        
        # 檢查是否包含部門關鍵字且長度合理
        if any(keyword in text for keyword in dept_keywords) and 2 <= len(text) <= 20:
            # 排除明顯不是部門的文字（包含數字、電話、郵件等）
            if not re.search(r'[\d@./-]', text) and not self._is_phone_number(text):
                return True
        
        return False
    
    def extract_multiple_addresses_from_text(self, text: str) -> List[str]:
        """從文字中提取多個地址，支援換行符分隔"""
        addresses = []
        
        # 首先按換行符分割文字，處理換行符分隔的地址
        lines = text.split('\n')
        
        # 對每一行進行地址檢查
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 檢查整行是否為地址
            if self._is_address(line):
                addresses.append(line)
                continue
        
        # 如果沒有找到明顯的地址，使用正則表達式提取
        if not addresses:
            for pattern in self.address_patterns:
                matches = pattern.findall(text)
                for match in matches:
                    cleaned_addr = match.strip()
                    if cleaned_addr and len(cleaned_addr) > 5:  # 地址最短長度
                        addresses.append(cleaned_addr)
        
        # 去重並保持順序
        seen = set()
        unique_addresses = []
        for addr in addresses:
            if addr not in seen:
                seen.add(addr)
                unique_addresses.append(addr)
        
        return unique_addresses[:2]  # 最多返回2個地址
    
    def _is_address(self, text: str) -> bool:
        """判斷文字是否為地址"""
        # 台灣地址關鍵字
        address_keywords = ['市', '區', '鄉', '鎮', '路', '街', '巷', '弄', '號', '樓', '縣', '村', '里']
        city_keywords = ['台北', '新北', '桃園', '台中', '台南', '高雄', '基隆', '新竹', '苗栗', 
                        '彰化', '南投', '雲林', '嘉義', '屏東', '宜蘭', '花蓮', '台東', '澎湖', '金門', '連江']
        
        # 檢查是否包含地址關鍵字且長度合理
        if (any(keyword in text for keyword in address_keywords) or 
            any(city in text for city in city_keywords)) and len(text) > 5:
            # 排除明顯不是地址的文字（純數字、純英文、電話號碼等）
            if (not re.match(r'^[\d\s\-\(\)]+$', text) and 
                not re.match(r'^[a-zA-Z\s]+$', text) and 
                not self._is_phone_number(text) and
                not self._is_department_name(text)):
                return True
        
        return False
    
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
            
            # 如果已經是有效的JSON格式，直接返回
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                pass
            
            # 只在必要時進行標準化
            replacements = [
                (r"'([^']*)':", r'"\1":'),  # 'key': -> "key":
                (r":\s*'([^']*)'", r': "\1"'),  # : 'value' -> : "value"
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
        
        # 先進行基本的欄位映射
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
        
        # 進行智能字串提取（增強功能）
        full_text = ' '.join(str(v) for v in raw_data.values() if v)
        self._enhance_with_intelligent_extraction(mapped_fields, full_text, raw_data)
        
        return mapped_fields
    
    def _enhance_with_intelligent_extraction(self, mapped_fields: Dict[str, str], full_text: str, raw_data: Dict = None):
        """使用智能提取增強映射結果"""
        try:
            # 智能提取多個電話號碼並進行語義分類
            phones = self.field_mapper.extract_multiple_phones_from_text(full_text)
            
            # 分類電話號碼
            mobile_phones = []
            company_phones = []
            
            for phone in phones:
                phone_type = self.field_mapper.classify_phone_type(phone)
                if phone_type == 'mobile':
                    mobile_phones.append(phone)
                else:
                    company_phones.append(phone)
            
            # 分配到對應欄位
            if mobile_phones and 'mobile_phone' not in mapped_fields:
                mapped_fields['mobile_phone'] = mobile_phones[0]
            
            if company_phones:
                if 'company_phone1' not in mapped_fields and len(company_phones) > 0:
                    mapped_fields['company_phone1'] = company_phones[0]
                if 'company_phone2' not in mapped_fields and len(company_phones) > 1:
                    mapped_fields['company_phone2'] = company_phones[1]
            
            # 智能分離多欄位內容
            self._split_multifield_content(mapped_fields, raw_data)
                        
        except Exception as e:
            # 智能提取失敗時不影響基本映射功能
            self.logger.debug(f"智能提取失敗，使用基本映射: {e}")
            pass
    
    def _split_multifield_content(self, mapped_fields: Dict[str, str], raw_data: Dict = None):
        """分離多欄位內容（部門、地址、備註）"""
        if not raw_data:
            return
            
        # 分離部門
        if 'department1' in mapped_fields and '\n' in mapped_fields['department1']:
            dept_lines = [line.strip() for line in mapped_fields['department1'].split('\n') if line.strip()]
            if len(dept_lines) > 1:
                mapped_fields['department1'] = dept_lines[0]
                if len(dept_lines) > 1:
                    mapped_fields['department2'] = dept_lines[1]
                if len(dept_lines) > 2:
                    mapped_fields['department3'] = dept_lines[2]
        
        # 分離地址
        if 'company_address1' in mapped_fields and '\n' in mapped_fields['company_address1']:
            addr_lines = [line.strip() for line in mapped_fields['company_address1'].split('\n') if line.strip()]
            if len(addr_lines) > 1:
                mapped_fields['company_address1'] = addr_lines[0]
                mapped_fields['company_address2'] = addr_lines[1]
        
        # 分離備註
        if 'note1' in mapped_fields and '\n' in mapped_fields['note1']:
            note_lines = [line.strip() for line in mapped_fields['note1'].split('\n') if line.strip()]
            if len(note_lines) > 1:
                mapped_fields['note1'] = note_lines[0]
                mapped_fields['note2'] = note_lines[1]
        
        # 分離電話（如果在同一欄位中）
        for field_name in ['mobile_phone', 'company_phone1']:
            if field_name in mapped_fields and '\n' in mapped_fields[field_name]:
                phone_lines = [line.strip() for line in mapped_fields[field_name].split('\n') if line.strip()]
                if len(phone_lines) > 1:
                    mapped_fields[field_name] = phone_lines[0]
                    # 分類第二個電話
                    second_phone = phone_lines[1]
                    phone_type = self.field_mapper.classify_phone_type(second_phone)
                    if phone_type == 'mobile' and 'mobile_phone' not in mapped_fields:
                        mapped_fields['mobile_phone'] = second_phone
                    elif phone_type == 'company' and 'company_phone2' not in mapped_fields:
                        mapped_fields['company_phone2'] = second_phone

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
        
        # 提取公司電話（如果沒有找到手機號碼）
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
        mobile_phone, company_phone = self.text_analyzer.extract_phone_numbers(full_text)
        if mobile_phone:
            parsed_fields['mobile_phone'] = mobile_phone
        if company_phone:
            parsed_fields['company_phone1'] = company_phone
        
        email = self.text_analyzer.extract_email(full_text)
        if email:
            parsed_fields['email'] = email
        
        line_id = self.text_analyzer.extract_line_id(full_text)
        if line_id:
            parsed_fields['line_id'] = line_id
        
        address_1, address_2 = self.text_analyzer.extract_address(lines)
        if address_1:
            parsed_fields['company_address1'] = address_1
        if address_2:
            parsed_fields['company_address2'] = address_2
        
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
                parsed_fields['note1'] = '\n'.join(remaining_text)
        
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
        front_priority_fields = ['name', 'company_name', 'position', 'mobile_phone', 'company_phone1', 'email']
        
        for field in front_priority_fields:
            if front_data.get(field):
                merged_data[field] = front_data[field]
            elif back_data.get(field):
                merged_data[field] = back_data[field]
        
        # 其他欄位取非空值或合併
        other_fields = ['line_id', 'company_address1', 'company_address2', 'note1']
        for field in other_fields:
            front_value = front_data.get(field, "")
            back_value = back_data.get(field, "")
            
            if front_value and back_value:
                if field == 'note1':
                    merged_data[field] = f"{front_value}\n{back_value}"
                else:
                    # 選擇較長的值，通常包含更多信息
                    merged_data[field] = front_value if len(front_value) > len(back_value) else back_value
            elif front_value:
                merged_data[field] = front_value
            elif back_value:
                merged_data[field] = back_value
        
        return merged_data
