"""
元素识别器
识别页面中的可交互元素并生成稳定的CSS选择器
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class ElementType(Enum):
    """元素类型"""
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    SELECT = "select"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE_INPUT = "file_input"
    IMAGE = "image"
    ICON = "icon"
    TAB = "tab"
    DROPDOWN = "dropdown"
    MENU = "menu"
    UNKNOWN = "unknown"


@dataclass
class RecognizedElement:
    """识别的元素"""
    type: ElementType
    selector: str
    text: str
    attributes: Dict[str, Any]
    is_clickable: bool
    is_interactive: bool
    confidence: float  # 识别置信度 0.0 - 1.0
    alternative_selectors: List[str]  # 备选选择器


class SelectorGenerator:
    """CSS选择器生成器"""

    # 选择器优先级权重
    SELECTOR_PRIORITIES = {
        "id": 100,
        "name": 80,
        "data-testid": 100,
        "data-cy": 90,
        "aria-label": 70,
        "class": 50,
        "tag": 10
    }

    def generate_selectors(self, element) -> List[str]:
        """为元素生成多个候选选择器"""
        selectors = []

        # 1. ID选择器（最高优先级）
        if element.get('id'):
            selectors.append(f"#{element['id']}")

        # 2. data-testid选择器
        if element.get('data-testid'):
            selectors.append(f"[data-testid='{element['data-testid']}']")

        # 3. data-cy选择器
        if element.get('data-cy'):
            selectors.append(f"[data-cy='{element['data-cy']}']")

        # 4. name属性选择器
        if element.get('name'):
            selectors.append(f"[name='{element['name']}']")

        # 5. 类名选择器
        classes = element.get('class', [])
        if classes:
            class_selector = "." + ".".join(classes)
            selectors.append(class_selector)

        # 6. 属性选择器（aria-label）
        if element.get('aria-label'):
            selectors.append(f"[aria-label='{element['aria-label']}']")

        # 7. 文本内容选择器
        text = element.get('text', '').strip()
        if text and len(text) < 50:  # 文本太长不适合作为选择器
            escaped_text = re.escape(text)
            # 链接用文本内容
            if element.get('tag') == 'a':
                selectors.append(f"a:has-text('{text}')")
            # 按钮用文本内容
            elif element.get('tag') == 'button':
                selectors.append(f"button:has-text('{text}')")

        # 8. 类型+属性组合选择器
        tag = element.get('tag', 'div')
        name = element.get('name')
        if name:
            selectors.append(f"{tag}[name='{name}']")

        # 去重并返回
        return list(dict.fromkeys(selectors))

    def score_selector(self, selector: str) -> int:
        """为选择器打分"""
        score = 0

        if selector.startswith('#'):
            score += self.SELECTOR_PRIORITIES["id"]
        elif '[data-testid=' in selector:
            score += self.SELECTOR_PRIORITIES["data-testid"]
        elif '[data-cy=' in selector:
            score += self.SELECTOR_PRIORITIES["data-cy"]
        elif "[name=" in selector:
            score += self.SELECTOR_PRIORITIES["name"]
        elif "[aria-label=" in selector:
            score += self.SELECTOR_PRIORITIES["aria-label"]
        elif selector.startswith('.'):
            score += self.SELECTOR_PRIORITIES["class"]
        else:
            score += self.SELECTOR_PRIORITIES["tag"]

        return score

    def get_best_selector(self, selectors: List[str]) -> str:
        """获取最佳选择器"""
        if not selectors:
            return "div"

        scored = [(s, self.score_selector(s)) for s in selectors]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]


class ElementRecognizer:
    """元素识别器"""

    def __init__(self):
        self.selector_generator = SelectorGenerator()

        # 交互元素标签
        self.interactive_tags = {
            'button', 'a', 'input', 'select', 'textarea',
            'option', 'label', 'details', 'summary'
        }

        # 元素类型模式
        self.type_patterns = {
            ElementType.BUTTON: {
                'tags': ['button', 'input[type="button"]', 'input[type="submit"]'],
                'classes': ['btn', 'button', 'clickable']
            },
            ElementType.LINK: {
                'tags': ['a'],
                'classes': ['link', 'nav-link', 'menu-link']
            },
            ElementType.INPUT: {
                'tags': ['input'],
                'types': ['text', 'email', 'tel', 'number', 'password', 'url', 'search']
            },
            ElementType.SELECT: {
                'tags': ['select'],
                'classes': ['dropdown', 'select']
            },
            ElementType.TEXTAREA: {
                'tags': ['textarea'],
                'classes': ['textarea', 'editor']
            },
            ElementType.CHECKBOX: {
                'tags': ['input[type="checkbox"]'],
                'classes': ['checkbox', 'check']
            },
            ElementType.RADIO: {
                'tags': ['input[type="radio"]'],
                'classes': ['radio']
            },
            ElementType.FILE_INPUT: {
                'tags': ['input[type="file"]'],
                'classes': ['file-upload', 'file-input']
            },
            ElementType.IMAGE: {
                'tags': ['img'],
                'classes': ['image', 'photo']
            },
            ElementType.ICON: {
                'tags': ['svg', 'i'],
                'classes': ['icon', 'glyphicon', 'fa', 'material-icon']
            },
        }

    def recognize_element(self, element) -> RecognizedElement:
        """识别单个元素"""
        # 提取元素属性
        tag = element.name if hasattr(element, 'name') else 'div'
        attributes = {k: v for k, v in element.attrs.items()}
        text = element.get_text(strip=True) if hasattr(element, 'get_text') else ""

        # 识别元素类型
        element_type = self._identify_element_type(tag, attributes, text)

        # 生成选择器
        element_data = {
            'tag': tag,
            'text': text[:50] if text else "",
            'id': attributes.get('id'),
            'name': attributes.get('name'),
            'class': attributes.get('class', []),
            'data-testid': attributes.get('data-testid'),
            'data-cy': attributes.get('data-cy'),
            'aria-label': attributes.get('aria-label'),
            'type': attributes.get('type')
        }

        selectors = self.selector_generator.generate_selectors(element_data)
        best_selector = self.selector_generator.get_best_selector(selectors)

        # 判断是否可点击和可交互
        is_clickable = self._is_clickable(tag, attributes, text)
        is_interactive = tag in self.interactive_tags or is_clickable

        # 计算置信度
        confidence = self._calculate_confidence(
            element_type, element_data, selectors
        )

        return RecognizedElement(
            type=element_type,
            selector=best_selector,
            text=text[:100],
            attributes=attributes,
            is_clickable=is_clickable,
            is_interactive=is_interactive,
            confidence=confidence,
            alternative_selectors=selectors[1:5]  # 保留4个备选选择器
        )

    def _identify_element_type(
        self,
        tag: str,
        attributes: Dict[str, Any],
        text: str
    ) -> ElementType:
        """识别元素类型"""
        input_type = attributes.get('type', '').lower()

        # 基于标签和类型
        if tag == 'button':
            return ElementType.BUTTON
        elif tag == 'a':
            return ElementType.LINK
        elif tag == 'input':
            if input_type == 'checkbox':
                return ElementType.CHECKBOX
            elif input_type == 'radio':
                return ElementType.RADIO
            elif input_type == 'file':
                return ElementType.FILE_INPUT
            else:
                return ElementType.INPUT
        elif tag == 'select':
            return ElementType.SELECT
        elif tag == 'textarea':
            return ElementType.TEXTAREA
        elif tag == 'img':
            return ElementType.IMAGE
        elif tag in ['svg', 'i']:
            return ElementType.ICON

        # 基于类名推断
        classes = ' '.join(attributes.get('class', [])).lower()
        for element_type, patterns in self.type_patterns.items():
            for pattern in patterns.get('classes', []):
                if pattern in classes:
                    return element_type

        return ElementType.UNKNOWN

    def _is_clickable(self, tag: str, attributes: Dict[str, Any], text: str) -> bool:
        """判断元素是否可点击"""
        # 明显可点击的元素
        if tag in ['button', 'a']:
            return True

        input_type = attributes.get('type', '').lower()
        if tag == 'input' and input_type in ['button', 'submit', 'reset', 'image']:
            return True

        # 检查onclick属性
        if attributes.get('onclick'):
            return True

        # 检查role属性
        role = attributes.get('role', '').lower()
        if role in ['button', 'link', 'checkbox', 'radio', 'switch']:
            return True

        # 检查class是否包含可点击相关的词
        classes = ' '.join(attributes.get('class', [])).lower()
        clickable_keywords = ['btn', 'button', 'click', 'clickable', 'trigger']
        if any(keyword in classes for keyword in clickable_keywords):
            return True

        # 检查cursor样式
        style = attributes.get('style', '').lower()
        if 'cursor' in style and 'pointer' in style:
            return True

        return False

    def _calculate_confidence(
        self,
        element_type: ElementType,
        element_data: Dict[str, Any],
        selectors: List[str]
    ) -> float:
        """计算识别置信度"""
        confidence = 0.0

        # 如果是未知类型，置信度降低
        if element_type == ElementType.UNKNOWN:
            confidence += 0.3
        else:
            confidence += 0.8

        # 根据选择器质量调整置信度
        if selectors:
            best_selector_score = self.selector_generator.score_selector(selectors[0])
            normalized_score = min(best_selector_score / 100, 1.0)
            confidence = (confidence + normalized_score) / 2

        return min(confidence, 1.0)

    def recognize_interactive_elements(self, dom_content: str) -> List[RecognizedElement]:
        """识别页面中的所有可交互元素"""
        elements = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(dom_content, 'html.parser')

            # 查找所有可能交互的元素
            potential_elements = soup.find_all(list(self.interactive_tags))

            for element in potential_elements:
                recognized = self.recognize_element(element)

                # 只保留置信度足够高的元素
                if recognized.confidence >= 0.5 and recognized.is_interactive:
                    elements.append(recognized)

        except Exception as e:
            print(f"Error recognizing elements: {e}")

        return elements

    def get_clickable_elements(self, dom_content: str) -> List[Dict[str, Any]]:
        """获取所有可点击元素"""
        elements = self.recognize_interactive_elements(dom_content)
        clickable = [e for e in elements if e.is_clickable]

        return [
            {
                "type": e.type.value,
                "selector": e.selector,
                "text": e.text,
                "confidence": e.confidence,
                "alternatives": e.alternative_selectors
            }
            for e in clickable
        ]

    def get_form_elements(self, dom_content: str) -> List[Dict[str, Any]]:
        """获取所有表单元素"""
        elements = self.recognize_interactive_elements(dom_content)
        form_elements = [
            e for e in elements
            if e.type in [ElementType.INPUT, ElementType.SELECT, ElementType.TEXTAREA,
                          ElementType.CHECKBOX, ElementType.RADIO, ElementType.FILE_INPUT]
        ]

        return [
            {
                "type": e.type.value,
                "selector": e.selector,
                "text": e.text,
                "confidence": e.confidence,
                "alternatives": e.alternative_selectors,
                "attributes": e.attributes
            }
            for e in form_elements
        ]

    def suggest_test_interactions(self, dom_content: str) -> List[Dict[str, Any]]:
        """建议测试交互"""
        suggestions = []

        # 获取可点击元素
        clickable = self.get_clickable_elements(dom_content)

        # 生成点击测试建议（前10个）
        for element in clickable[:10]:
            suggestions.append({
                "action": "click",
                "description": f"Click on {element['type']}",
                "selector": element['selector'],
                "text": element['text'],
                "priority": "medium"
            })

        # 获取表单元素
        form_elements = self.get_form_elements(dom_content)

        # 生成表单输入建议
        for element in form_elements:
            suggestions.append({
                "action": "fill",
                "description": f"Fill {element['type']} field",
                "selector": element['selector'],
                "priority": "low"
            })

        return suggestions
