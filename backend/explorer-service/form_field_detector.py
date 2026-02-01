"""
表单字段检测器
识别表单字段的类型（用户名、密码、邮箱等）
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class FieldType(Enum):
    """表单字段类型"""
    USERNAME = "username"
    PASSWORD = "password"
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP = "zip"
    COUNTRY = "country"
    COMPANY = "company"
    WEBSITE = "website"
    SEARCH = "search"
    DATE = "date"
    NUMBER = "number"
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    HIDDEN = "hidden"
    UNKNOWN = "unknown"


@dataclass
class FieldDetection:
    """字段检测结果"""
    type: FieldType
    confidence: float  # 0.0 - 1.0
    selector: str
    name: str
    id: str
    attributes: Dict[str, Any]
    suggestions: List[str]


class FormFieldDetector:
    """表单字段检测器"""

    def __init__(self):
        # 字段类型关键词映射
        self.field_patterns = {
            FieldType.USERNAME: {
                "keywords": ["username", "user", "login", "email", "userid", "user_id"],
                "types": ["text", "email"],
                "min_confidence": 0.7
            },
            FieldType.PASSWORD: {
                "keywords": ["password", "passwd", "pwd", "pass", "secret"],
                "types": ["password"],
                "min_confidence": 0.9
            },
            FieldType.EMAIL: {
                "keywords": ["email", "e-mail", "mail", "contact"],
                "types": ["email"],
                "min_confidence": 0.8
            },
            FieldType.PHONE: {
                "keywords": ["phone", "tel", "telephone", "mobile", "cell"],
                "types": ["tel", "tel"],
                "min_confidence": 0.7
            },
            FieldType.NAME: {
                "keywords": ["name", "fullname", "full_name"],
                "types": ["text"],
                "min_confidence": 0.7
            },
            FieldType.FIRST_NAME: {
                "keywords": ["firstname", "first_name", "fname", "givenname"],
                "types": ["text"],
                "min_confidence": 0.8
            },
            FieldType.LAST_NAME: {
                "keywords": ["lastname", "last_name", "lname", "surname", "familyname"],
                "types": ["text"],
                "min_confidence": 0.8
            },
            FieldType.ADDRESS: {
                "keywords": ["address", "street", "addr"],
                "types": ["text"],
                "min_confidence": 0.7
            },
            FieldType.CITY: {
                "keywords": ["city", "town", "locality"],
                "types": ["text"],
                "min_confidence": 0.7
            },
            FieldType.STATE: {
                "keywords": ["state", "province", "region"],
                "types": ["text"],
                "min_confidence": 0.7
            },
            FieldType.ZIP: {
                "keywords": ["zip", "postal", "postcode", "zip_code", "postal_code"],
                "types": ["text", "number"],
                "min_confidence": 0.7
            },
            FieldType.COUNTRY: {
                "keywords": ["country", "nation"],
                "types": ["text", "select"],
                "min_confidence": 0.7
            },
            FieldType.COMPANY: {
                "keywords": ["company", "organization", "org", "business"],
                "types": ["text"],
                "min_confidence": 0.7
            },
            FieldType.WEBSITE: {
                "keywords": ["website", "url", "site", "link"],
                "types": ["url"],
                "min_confidence": 0.7
            },
            FieldType.SEARCH: {
                "keywords": ["search", "find", "query", "q"],
                "types": ["text", "search"],
                "min_confidence": 0.8
            },
            FieldType.DATE: {
                "keywords": ["date", "dob", "birthday", "birth_date"],
                "types": ["date", "text"],
                "min_confidence": 0.7
            },
            FieldType.NUMBER: {
                "keywords": ["number", "qty", "quantity", "amount", "count"],
                "types": ["number"],
                "min_confidence": 0.6
            },
        }

    def detect_field_type(self, field_info: Dict[str, Any]) -> FieldDetection:
        """检测字段类型"""
        # 提取字段信息
        name = field_info.get('name', '').lower()
        field_id = field_info.get('id', '').lower()
        field_type = field_info.get('type', 'text').lower()
        placeholder = field_info.get('placeholder', '').lower()
        aria_label = field_info.get('aria-label', '').lower()

        # 组合所有可用的标识信息
        identifiers = [name, field_id, placeholder, aria_label]

        best_match = None
        best_confidence = 0.0

        # 遍历所有字段类型模式
        for field_type, pattern in self.field_patterns.items():
            confidence = self._calculate_confidence(
                identifiers, field_type, pattern
            )

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = field_type

        # 如果置信度太低，使用基本类型推断
        if not best_match or best_confidence < 0.3:
            best_match = self._infer_from_type(field_type, field_info)

        # 生成建议
        suggestions = self._generate_suggestions(best_match, field_info)

        return FieldDetection(
            type=best_match or FieldType.UNKNOWN,
            confidence=best_confidence,
            selector=field_info.get('selector', ''),
            name=field_info.get('name', ''),
            id=field_info.get('id', ''),
            attributes=field_info,
            suggestions=suggestions
        )

    def _calculate_confidence(
        self,
        identifiers: List[str],
        field_type: FieldType,
        pattern: Dict[str, Any]
    ) -> float:
        """计算字段类型的置信度"""
        confidence = 0.0
        keywords = pattern["keywords"]
        valid_types = pattern["types"]

        for identifier in identifiers:
            if identifier:
                # 检查关键词匹配
                for keyword in keywords:
                    if keyword in identifier:
                        # 完全匹配给予更高分
                        if identifier == keyword:
                            confidence += 0.8
                        # 部分匹配给予中等分
                        elif keyword in identifier:
                            confidence += 0.5

        # 检查input类型匹配
        for identifier in identifiers:
            if identifier and identifier in valid_types:
                confidence += 0.3

        # 规范化置信度
        return min(confidence, 1.0)

    def _infer_from_type(self, input_type: str, field_info: Dict[str, Any]) -> FieldType:
        """根据input类型推断字段类型"""
        type_mapping = {
            "password": FieldType.PASSWORD,
            "email": FieldType.EMAIL,
            "tel": FieldType.PHONE,
            "url": FieldType.WEBSITE,
            "number": FieldType.NUMBER,
            "date": FieldType.DATE,
            "checkbox": FieldType.CHECKBOX,
            "radio": FieldType.RADIO,
            "file": FieldType.FILE,
            "hidden": FieldType.HIDDEN,
            "select": FieldType.SELECT,
            "textarea": FieldType.TEXTAREA,
        }

        return type_mapping.get(input_type, FieldType.TEXT)

    def _generate_suggestions(
        self,
        field_type: FieldType,
        field_info: Dict[str, Any]
    ) -> List[str]:
        """生成字段建议"""
        suggestions = []

        # 基于字段类型的建议
        test_values = {
            FieldType.USERNAME: ["testuser", "john_doe", "demo_user"],
            FieldType.PASSWORD: ["Test@123", "P@ssw0rd", "Secure123"],
            FieldType.EMAIL: ["test@example.com", "user@domain.com", "test.user@mail.org"],
            FieldType.PHONE: ["1234567890", "+1-555-123-4567", "(555) 123-4567"],
            FieldType.NAME: ["John Doe", "Jane Smith", "Test User"],
            FieldType.FIRST_NAME: ["John", "Jane", "Test"],
            FieldType.LAST_NAME: ["Doe", "Smith", "User"],
            FieldType.ADDRESS: ["123 Main St", "456 Oak Ave", "789 Test Blvd"],
            FieldType.CITY: ["New York", "Los Angeles", "Chicago"],
            FieldType.STATE: ["NY", "CA", "IL"],
            FieldType.ZIP: ["10001", "90210", "60601"],
            FieldType.COUNTRY: ["USA", "Canada", "United States"],
            FieldType.COMPANY: ["Acme Corp", "Test Company", "Demo Inc"],
            FieldType.WEBSITE: ["https://example.com", "http://test.org"],
            FieldType.SEARCH: ["test query", "search term", "demo search"],
            FieldType.DATE: ["2024-01-01", "01/01/2024", "2024年1月1日"],
            FieldType.NUMBER: ["123", "456", "789"],
        }

        if field_type in test_values:
            suggestions.extend(test_values[field_type])

        # 基于属性的建议
        if field_info.get('required'):
            suggestions.append("This field is required - ensure it is filled")

        if field_info.get('pattern'):
            suggestions.append(f"Field has pattern: {field_info.get('pattern')}")

        min_length = field_info.get('minlength')
        max_length = field_info.get('maxlength')
        if min_length or max_length:
            suggestion = f"Length constraint"
            if min_length:
                suggestion += f": min {min_length}"
            if max_length:
                suggestion += f", max {max_length}"
            suggestions.append(suggestion)

        return suggestions

    def detect_form_fields(self, form_data: Dict[str, Any]) -> List[FieldDetection]:
        """检测表单中的所有字段"""
        fields = form_data.get('fields', [])
        detections = []

        for field in fields:
            detection = self.detect_field_type(field)
            detections.append(detection)

        return detections

    def get_test_data_for_fields(self, detections: List[FieldDetection]) -> Dict[str, str]:
        """为检测到的字段生成测试数据"""
        test_data = {}

        test_values = {
            FieldType.USERNAME: "testuser",
            FieldType.PASSWORD: "Test@123",
            FieldType.EMAIL: "test@example.com",
            FieldType.PHONE: "1234567890",
            FieldType.NAME: "Test User",
            FieldType.FIRST_NAME: "Test",
            FieldType.LAST_NAME: "User",
            FieldType.ADDRESS: "123 Main St",
            FieldType.CITY: "New York",
            FieldType.STATE: "NY",
            FieldType.ZIP: "10001",
            FieldType.COUNTRY: "USA",
            FieldType.COMPANY: "Test Company",
            FieldType.WEBSITE: "https://example.com",
            FieldType.SEARCH: "test query",
            FieldType.DATE: "2024-01-01",
            FieldType.NUMBER: "123",
            FieldType.TEXT: "test text",
        }

        for detection in detections:
            # 使用字段的name或id作为键
            key = detection.name or detection.id or str(len(test_data))
            value = test_values.get(detection.type, "test")
            test_data[key] = value

        return test_data
