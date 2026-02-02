"""
智能交互元素识别器
识别和分析页面中的可交互元素，生成精准的测试步骤
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from urllib.parse import urljoin, urlparse
import asyncio
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InteractiveElement:
    """可交互元素信息"""
    element_id: str
    tag: str
    css_selector: str
    text: str
    value: str
    element_type: str  # 'button', 'input', 'link', 'form', 'select', etc.
    xpath: str
    attributes: Dict[str, str]
    position: Dict[str, float]  # x, y, width, height
    visibility: bool
    interactability: bool
    importance_score: float
    confidence_score: float
    suggested_actions: List[str] = field(default_factory=list)
    test_priority: int = 5  # 1-10, 10 highest
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.element_id,
            'tag': self.tag,
            'css_selector': self.css_selector,
            'text': self.text,
            'value': self.value,
            'type': self.element_type,
            'xpath': self.xpath,
            'attributes': self.attributes,
            'position': self.position,
            'visibility': self.visibility,
            'interactability': self.interactability,
            'importance_score': self.importance_score,
            'confidence_score': self.confidence_score,
            'suggested_actions': self.suggested_actions,
            'test_priority': self.test_priority
        }


@dataclass
class ElementAction:
    """元素操作"""
    action_type: str  # 'click', 'type', 'select', 'wait', 'assert'
    target_element: InteractiveElement
    value: Optional[str] = None
    description: str = ""
    expected_result: str = ""
    validation_rules: List[str] = field(default_factory=list)
    wait_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'action_type': self.action_type,
            'target_element': self.target_element.to_dict(),
            'value': self.value,
            'description': self.description,
            'expected_result': self.expected_result,
            'validation_rules': self.validation_rules,
            'wait_time': self.wait_time
        }


class ElementRecognizer(ABC):
    """元素识别器抽象基类"""
    
    @abstractmethod
    async def recognize_elements(self, page_content: str, page_url: str) -> List[InteractiveElement]:
        """识别页面元素"""
        pass
    
    @abstractmethod
    async def generate_actions(self, elements: List[InteractiveElement], context: Dict[str, Any]) -> List[ElementAction]:
        """生成元素操作"""
        pass


class PlaywrightElementRecognizer(ElementRecognizer):
    """基于Playwright的元素识别器"""
    
    def __init__(self):
        self.element_selectors = {
            'buttons': [
                'button',
                'input[type="button"]',
                'input[type="submit"]',
                'input[type="reset"]',
                'button[type="button"]',
                '.btn',
                '.button',
                '[role="button"]',
                '.action-button',
                '.submit-button'
            ],
            'inputs': [
                'input[type!="hidden"]',
                'input:not([type="hidden"])',
                'textarea',
                'select',
                'input[type="text"]',
                'input[type="email"]',
                'input[type="password"]',
                'input[type="number"]',
                'input[type="date"]',
                'input[type="time"]',
                'input[type="url"]',
                'input[type="tel"]',
                '.form-control',
                '.input-group',
                '.input-field'
            ],
            'links': [
                'a[href]',
                'area[href]',
                '[role="link"]',
                '.nav-link',
                '.menu-link',
                '.link',
                'a:not([href="#"])',
                'a:not([href^="javascript:"])'
            ],
            'forms': [
                'form',
                '.form',
                '.registration-form',
                '.login-form',
                '.search-form'
            ],
            'navigation': [
                'nav',
                '[role="navigation"]',
                '.nav',
                '.navigation',
                '.menu',
                '.sidebar',
                '.main-nav'
            ],
            'data_tables': [
                'table',
                '.data-table',
                '.results-table',
                '.list-table',
                'table[class*="table"]'
            ],
            'interactive_elements': [
                '[onclick]',
                '[addEventListener]',
                '[ng-click]',
                '[data-action]',
                '[data-test]',
                '[data-testid]',
                '[data-cy]',
                '[qa-]'
            ]
        }
    
    async def recognize_elements(self, page_content: str, page_url: str) -> List[InteractiveElement]:
        """识别页面元素"""
        elements = []
        
        try:
            # 这里应该使用实际的Playwright页面对象
            # 现在是模拟实现，基于HTML内容识别
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 识别各种类型的元素
            button_elements = self._identify_button_elements(soup)
            input_elements = self._identify_input_elements(soup)
            link_elements = self._identify_link_elements(soup)
            form_elements = self._identify_form_elements(soup)
            table_elements = self._identify_table_elements(soup)
            interactive_elements = self._identify_interactive_elements(soup)
            
            # 合并所有元素
            all_elements = button_elements + input_elements + link_elements + form_elements + table_elements + interactive_elements
            
            # 去重和排序
            elements = self._deduplicate_elements(all_elements)
            
            # 计算元素重要性和置信度
            elements = await self._calculate_element_scores(elements, page_url)
            
            logger.info(f"Recognized {len(elements)} interactive elements")
            
            return elements
            
        except Exception as e:
            logger.error(f"Error recognizing elements: {e}")
            return []
    
    def _identify_button_elements(self, soup) -> List[InteractiveElement]:
        """识别按钮元素"""
        elements = []
        
        for selector in self.element_selectors['buttons']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'button')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _identify_input_elements(self, soup) -> List[InteractiveElement]:
        """识别输入元素"""
        elements = []
        
        for selector in self.element_selectors['inputs']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'input')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _identify_link_elements(self, soup) -> List[InteractiveElement]:
        """识别链接元素"""
        elements = []
        
        for selector in self.element_selectors['links']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'link')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _identify_form_elements(self, soup) -> List[InteractiveElement]:
        """识别表单元素"""
        elements = []
        
        for selector in self.element_selectors['forms']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'form')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _identify_table_elements(self, soup) -> List[InteractiveElement]:
        """识别表格元素"""
        elements = []
        
        for selector in self.element_selectors['data_tables']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'table')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _identify_interactive_elements(self, soup) -> List[InteractiveElement]:
        """识别交互元素"""
        elements = []
        
        for selector in self.element_selectors['interactive_elements']:
            for element in soup.select(selector):
                element_info = self._extract_element_info(element, 'interactive')
                if element_info:
                    elements.append(element_info)
        
        return elements
    
    def _extract_element_info(self, element, element_type: str) -> Optional[InteractiveElement]:
        """提取元素信息"""
        try:
            # 生成唯一ID
            element_id = f"{element_type}_{hash(str(element))}"
            
            # 获取标签名
            tag = element.name or 'unknown'
            
            # 生成CSS选择器
            css_selector = self._generate_css_selector(element)
            
            # 获取文本内容
            text = element.get_text(strip=True)
            
            # 获取值
            value = element.get('value', '')
            
            # 获取所有属性
            attributes = dict(element.attrs)
            
            # 获取位置信息（模拟）
            position = {
                'x': 0,
                'y': 0,
                'width': 100,
                'height': 30
            }
            
            # 判断可见性（简化）
            visibility = self._check_visibility(element)
            
            # 判断可交互性（简化）
            interactability = self._check_interactability(element)
            
            element_info = InteractiveElement(
                element_id=element_id,
                tag=tag,
                css_selector=css_selector,
                text=text,
                value=value,
                element_type=element_type,
                xpath=self._generate_xpath(element),
                attributes=attributes,
                position=position,
                visibility=visibility,
                interactability=interactability,
                importance_score=0.0,
                confidence_score=0.0,
                suggested_actions=[],
                test_priority=5
            )
            
            return element_info
            
        except Exception as e:
            logger.warning(f"Error extracting element info: {e}")
            return None
    
    def _generate_css_selector(self, element) -> str:
        """生成CSS选择器"""
        selector_parts = []
        
        # 添加标签名
        if element.name:
            selector_parts.append(element.name)
        
        # 添加ID
        element_id = element.get('id')
        if element_id:
            selector_parts.append(f'#{element_id}')
        
        # 添加类名
        element_class = element.get('class')
        if element_class:
            classes = element_class if isinstance(element_class, list) else [element_class]
            for cls in classes:
                if cls.strip():
                    selector_parts.append(f'.{cls.strip()}')
        
        # 如果选择器太泛，添加更多特异性
        if len(selector_parts) <= 1:
            # 添加属性选择器
            for attr in ['name', 'type', 'placeholder']:
                attr_value = element.get(attr)
                if attr_value:
                    selector_parts.append(f'[{attr}="{attr_value}"]')
                    break
        
        return ' '.join(selector_parts)
    
    def _generate_xpath(self, element) -> str:
        """生成XPath"""
        try:
            # 简化的XPath生成
            parts = []
            
            # 获取层级路径
            current = element
            while current.parent:
                siblings = current.parent.find_all(current.name, recursive=False)
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    parts.append(f'{current.name}[{index}]')
                else:
                    parts.append(current.name)
                current = current.parent
            
            parts.reverse()
            xpath = '//' + '/'.join(parts)
            
            return xpath
            
        except Exception as e:
            logger.warning(f"Error generating XPath: {e}")
            return '//'
    
    def _check_visibility(self, element) -> bool:
        """检查元素可见性"""
        try:
            # 检查是否有隐藏的样式
            style = element.get('style', '')
            if 'display:none' in style or 'visibility:hidden' in style:
                return False
            
            # 检查是否有hidden类
            classes = element.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            
            if 'hidden' in classes or 'd-none' in classes:
                return False
            
            # 检查是否在隐藏的父元素中
            parent = element.parent
            while parent:
                parent_style = parent.get('style', '')
                if 'display:none' in parent_style or 'visibility:hidden' in parent_style:
                    return False
                parent = parent.parent
            
            return True
            
        except Exception:
            return True  # 默认认为是可见的
    
    def _check_interactability(self, element) -> bool:
        """检查元素可交互性"""
        try:
            # 检查是否有disabled属性
            if element.get('disabled'):
                return False
            
            # 检查是否有readonly属性（针对输入元素）
            if element.name in ['input', 'textarea', 'select']:
                if element.get('readonly'):
                    return False
            
            # 检查是否有disabled类
            classes = element.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            
            if 'disabled' in classes or 'form-control' in classes:
                return False
            
            return True
            
        except Exception:
            return True  # 默认认为是可交互的
    
    def _deduplicate_elements(self, elements: List[InteractiveElement]) -> List[InteractiveElement]:
        """去重元素"""
        unique_elements = []
        seen_selectors = set()
        
        for element in elements:
            selector = element.css_selector
            if selector not in seen_selectors:
                unique_elements.append(element)
                seen_selectors.add(selector)
        
        return unique_elements
    
    async def _calculate_element_scores(self, elements: List[InteractiveElement], page_url: str) -> List[InteractiveElement]:
        """计算元素分数"""
        for element in elements:
            # 计算重要性分数
            importance_score = await self._calculate_importance_score(element, page_url)
            element.importance_score = importance_score
            
            # 计算置信度分数
            confidence_score = await self._calculate_confidence_score(element)
            element.confidence_score = confidence_score
            
            # 确定测试优先级
            element.test_priority = self._determine_test_priority(element)
            
            # 生成建议操作
            element.suggested_actions = await self._generate_suggested_actions(element)
        
        return elements
    
    async def _calculate_importance_score(self, element: InteractiveElement, page_url: str) -> float:
        """计算元素重要性分数"""
        score = 0.0
        
        # 基于元素类型
        type_scores = {
            'button': 0.7,
            'input': 0.8,
            'link': 0.6,
            'form': 0.9,
            'table': 0.5,
            'interactive': 0.4
        }
        
        score += type_scores.get(element.element_type, 0.3)
        
        # 基于文本内容
        if element.text:
            text_lower = element.text.lower()
            
            # 高优先级关键词
            high_priority_keywords = [
                'login', 'signin', 'submit', 'register', 'create', 'add',
                'save', 'delete', 'edit', 'update', 'search', 'filter'
            ]
            
            for keyword in high_priority_keywords:
                if keyword in text_lower:
                    score += 0.2
                    break
            
            # 中等优先级关键词
            medium_priority_keywords = [
                'home', 'dashboard', 'profile', 'settings', 'account',
                'view', 'detail', 'more', 'next', 'previous'
            ]
            
            for keyword in medium_priority_keywords:
                if keyword in text_lower:
                    score += 0.1
                    break
        
        # 基于元素属性
        if 'required' in element.attributes:
            score += 0.2
        
        if 'name' in element.attributes:
            name_lower = element.attributes['name'].lower()
            if any(keyword in name_lower for keyword in ['username', 'password', 'email', 'search']):
                score += 0.2
        
        if 'type' in element.attributes:
            element_type = element.attributes['type'].lower()
            if element_type in ['submit', 'button', 'password']:
                score += 0.1
        
        # 基于页面上下文
        page_path = urlparse(page_url).path.lower()
        
        # 登录页面
        if any(keyword in page_path for keyword in ['login', 'auth', 'signin']):
            if element.element_type in ['input', 'button']:
                score += 0.3
        
        # 表单页面
        if any(keyword in page_path for keyword in ['form', 'register', 'create']):
            if element.element_type in ['input', 'form']:
                score += 0.2
        
        # 数据页面
        if any(keyword in page_path for keyword in ['list', 'table', 'search']):
            if element.element_type in ['table', 'input']:
                score += 0.1
        
        return min(score, 1.0)
    
    async def _calculate_confidence_score(self, element: InteractiveElement) -> float:
        """计算置信度分数"""
        score = 1.0
        
        # 基于选择器特异性
        if '#' in element.css_selector:
            score += 0.1  # ID选择器
        elif '.' in element.css_selector:
            score += 0.05  # 类选择器
        
        # 基于元素完整信息
        if element.text and element.element_type == 'button':
            score += 0.1
        
        if element.element_type == 'input' and 'type' in element.attributes:
            score += 0.1
        
        # 基于属性完整性
        attribute_count = len(element.attributes)
        score += min(attribute_count * 0.02, 0.1)
        
        return min(score, 1.0)
    
    def _determine_test_priority(self, element: InteractiveElement) -> int:
        """确定测试优先级"""
        # 基于重要性分数确定优先级
        if element.importance_score >= 0.8:
            return 10
        elif element.importance_score >= 0.7:
            return 9
        elif element.importance_score >= 0.6:
            return 8
        elif element.importance_score >= 0.5:
            return 7
        elif element.importance_score >= 0.4:
            return 6
        elif element.importance_score >= 0.3:
            return 5
        elif element.importance_score >= 0.2:
            return 4
        elif element.importance_score >= 0.1:
            return 3
        else:
            return 1
    
    async def _generate_suggested_actions(self, element: InteractiveElement) -> List[str]:
        """生成建议操作"""
        actions = []
        
        # 基于元素类型生成操作
        if element.element_type == 'button':
            actions.extend(['click', 'hover'])
            if 'submit' in element.text.lower():
                actions.append('submit_form')
        
        elif element.element_type == 'input':
            actions.extend(['type_text', 'clear'])
            if element.attributes.get('type') == 'password':
                actions.append('type_password')
            elif element.attributes.get('type') == 'email':
                actions.append('type_email')
        
        elif element.element_type == 'link':
            actions.append('click')
            actions.append('verify_url')
        
        elif element.element_type == 'form':
            actions.extend(['submit_form', 'fill_form'])
        
        elif element.element_type == 'table':
            actions.extend(['verify_data', 'sort_column', 'filter_data'])
        
        # 基于元素属性添加操作
        if 'required' in element.attributes:
            actions.append('validate_required')
        
        if element.element_type == 'input' and 'placeholder' in element.attributes:
            actions.append('validate_placeholder')
        
        return list(set(actions))
    
    async def generate_actions(self, elements: List[InteractiveElement], context: Dict[str, Any]) -> List[ElementAction]:
        """生成元素操作"""
        actions = []
        
        try:
            # 按优先级排序元素
            sorted_elements = sorted(elements, key=lambda x: x.test_priority, reverse=True)
            
            for element in sorted_elements:
                if element.importance_score >= 0.3:  # 只处理重要性较高的元素
                    element_actions = await self._generate_element_actions(element, context)
                    actions.extend(element_actions)
            
            # 为特定元素序列生成连续操作
            sequence_actions = await self._generate_sequence_actions(elements, context)
            actions.extend(sequence_actions)
            
            logger.info(f"Generated {len(actions)} element actions")
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating actions: {e}")
            return []
    
    async def _generate_element_actions(self, element: InteractiveElement, context: Dict[str, Any]) -> List[ElementAction]:
        """为单个元素生成操作"""
        actions = []
        
        try:
            # 基于元素类型生成基本操作
            if element.element_type == 'button':
                action = ElementAction(
                    action_type='click',
                    target_element=element,
                    description=f"点击按钮: {element.text}",
                    expected_result="按钮点击成功",
                    validation_rules=[
                        "verify_element_not_present",
                        "verify_page_change"
                    ]
                )
                actions.append(action)
                
                # 如果是提交按钮，添加表单提交操作
                if any(keyword in element.text.lower() for keyword in ['submit', 'login', 'signin']):
                    form_action = ElementAction(
                        action_type='submit_form',
                        target_element=element,
                        description=f"提交表单: {element.text}",
                        expected_result="表单提交成功",
                        validation_rules=[
                            "verify_form_submission",
                            "verify_success_message"
                        ]
                    )
                    actions.append(form_action)
            
            elif element.element_type == 'input':
                # 输入框操作
                input_action = ElementAction(
                    action_type='type',
                    target_element=element,
                    value=await self._generate_test_value(element),
                    description=f"在输入框中输入: {await self._generate_test_value(element)}",
                    expected_result="输入成功",
                    validation_rules=[
                        "verify_input_value",
                        "verify_field_focus"
                    ]
                )
                actions.append(input_action)
                
                # 如果是必填字段，添加验证操作
                if 'required' in element.attributes:
                    validation_action = ElementAction(
                        action_type='validate',
                        target_element=element,
                        description=f"验证必填字段: {element.attributes.get('name', '')}",
                        expected_result="字段验证通过",
                        validation_rules=[
                            "verify_required_field"
                        ]
                    )
                    actions.append(validation_action)
            
            elif element.element_type == 'link':
                link_action = ElementAction(
                    action_type='click',
                    target_element=element,
                    description=f"点击链接: {element.text}",
                    expected_result="页面跳转成功",
                    validation_rules=[
                        "verify_url_change",
                        "verify_page_load"
                    ]
                )
                actions.append(link_action)
            
            elif element.element_type == 'form':
                form_action = ElementAction(
                    action_type='fill_form',
                    target_element=element,
                    description="填写表单",
                    expected_result="表单填写完成",
                    validation_rules=[
                        "verify_form_filled",
                        "verify_submit_button_enabled"
                    ]
                )
                actions.append(form_action)
            
        except Exception as e:
            logger.warning(f"Error generating actions for element {element.element_id}: {e}")
        
        return actions
    
    async def _generate_test_value(self, element: InteractiveElement) -> str:
        """生成测试值"""
        element_type = element.element_type
        attributes = element.attributes
        
        # 基于输入类型生成测试值
        input_type = attributes.get('type', 'text')
        
        if input_type == 'email':
            return 'test@example.com'
        elif input_type == 'password':
            return 'TestPass123!'
        elif input_type == 'number':
            return '12345'
        elif input_type == 'tel':
            return '13800138000'
        elif input_type == 'url':
            return 'https://example.com'
        elif input_type == 'date':
            return '2023-12-25'
        elif input_type == 'time':
            return '14:30'
        else:
            # 基于名称生成测试值
            name = attributes.get('name', '').lower()
            if 'username' in name or 'user' in name:
                return 'testuser'
            elif 'name' in name:
                return 'Test User'
            elif 'phone' in name or 'mobile' in name:
                return '13800138000'
            else:
                return 'testvalue'
    
    async def _generate_sequence_actions(self, elements: List[InteractiveElement], context: Dict[str, Any]) -> List[ElementAction]:
        """生成序列操作"""
        actions = []
        
        try:
            # 识别可能的操作序列
            # 例如：登录序列 = 输入用户名 -> 输入密码 -> 点击登录
            
            # 寻找登录序列
            username_elements = [e for e in elements if e.element_type == 'input' and 
                               ('username' in e.attributes.get('name', '').lower() or 
                                'user' in e.attributes.get('name', '').lower())]
            
            password_elements = [e for e in elements if e.element_type == 'input' and 
                               'password' in e.attributes.get('type', '').lower()]
            
            login_buttons = [e for e in elements if e.element_type == 'button' and 
                           any(keyword in e.text.lower() for keyword in ['login', 'signin', 'submit'])]
            
            if username_elements and password_elements and login_buttons:
                # 生成登录序列
                username_action = ElementAction(
                    action_type='type',
                    target_element=username_elements[0],
                    value='testuser',
                    description="输入用户名",
                    wait_time=1.0
                )
                actions.append(username_action)
                
                password_action = ElementAction(
                    action_type='type',
                    target_element=password_elements[0],
                    value='TestPass123!',
                    description="输入密码",
                    wait_time=1.0
                )
                actions.append(password_action)
                
                login_action = ElementAction(
                    action_type='click',
                    target_element=login_buttons[0],
                    description="点击登录按钮",
                    wait_time=2.0,
                    expected_result="登录成功"
                )
                actions.append(login_action)
            
            # 寻找搜索序列
            search_inputs = [e for e in elements if e.element_type == 'input' and 
                           ('search' in e.attributes.get('name', '').lower() or 
                            'search' in e.attributes.get('type', '').lower())]
            
            search_buttons = [e for e in elements if e.element_type == 'button' and 
                             'search' in e.text.lower()]
            
            if search_inputs and search_buttons:
                search_action = ElementAction(
                    action_type='type',
                    target_element=search_inputs[0],
                    value='test search term',
                    description="输入搜索关键词"
                )
                actions.append(search_action)
                
                search_button_action = ElementAction(
                    action_type='click',
                    target_element=search_buttons[0],
                    description="点击搜索按钮"
                )
                actions.append(search_button_action)
            
        except Exception as e:
            logger.warning(f"Error generating sequence actions: {e}")
        
        return actions


class IntelligentElementRecognizer:
    """智能元素识别器 - 结合多个识别器的结果"""
    
    def __init__(self):
        self.playwright_recognizer = PlaywrightElementRecognizer()
        self.context_cache = {}
    
    async def recognize_and_analyze(self, page_content: str, page_url: str, business_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """识别并分析页面元素"""
        try:
            if business_context is None:
                business_context = {}
            
            # 识别元素
            elements = await self.playwright_recognizer.recognize_elements(page_content, page_url)
            
            # 生成操作
            actions = await self.playwright_recognizer.generate_actions(elements, business_context)
            
            # 分析元素模式
            element_patterns = await self._analyze_element_patterns(elements)
            
            # 生成测试建议
            test_suggestions = await self._generate_test_suggestions(elements, actions, business_context)
            
            result = {
                'page_url': page_url,
                'total_elements': len(elements),
                'high_priority_elements': len([e for e in elements if e.test_priority >= 8]),
                'elements': [element.to_dict() for element in elements],
                'actions': [action.to_dict() for action in actions],
                'element_patterns': element_patterns,
                'test_suggestions': test_suggestions,
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 缓存结果
            self.context_cache[page_url] = result
            
            logger.info(f"Element analysis completed for {page_url}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in intelligent element recognition: {e}")
            return {}
    
    async def _analyze_element_patterns(self, elements: List[InteractiveElement]) -> Dict[str, Any]:
        """分析元素模式"""
        patterns = {
            'element_type_distribution': {},
            'position_clusters': [],
            'interaction_patterns': [],
            'form_patterns': [],
            'navigation_patterns': []
        }
        
        try:
            # 元素类型分布
            type_counts = {}
            for element in elements:
                element_type = element.element_type
                type_counts[element_type] = type_counts.get(element_type, 0) + 1
            
            patterns['element_type_distribution'] = type_counts
            
            # 位置聚类（简化）
            positions = [(e.position['x'], e.position['y']) for e in elements if e.visibility]
            if positions:
                # 简单的网格聚类
                grid_size = 100
                grid_clusters = defaultdict(list)
                
                for x, y in positions:
                    grid_x = int(x / grid_size) * grid_size
                    grid_y = int(y / grid_size) * grid_size
                    grid_clusters[(grid_x, grid_y)].append((x, y))
                
                patterns['position_clusters'] = list(grid_clusters.keys())
            
            # 交互模式
            button_elements = [e for e in elements if e.element_type == 'button']
            form_elements = [e for e in elements if e.element_type == 'form']
            
            if button_elements:
                patterns['interaction_patterns'] = {
                    'total_buttons': len(button_elements),
                    'high_priority_buttons': len([b for b in button_elements if b.test_priority >= 8])
                }
            
            if form_elements:
                patterns['form_patterns'] = {
                    'total_forms': len(form_elements),
                    'avg_inputs_per_form': len([e for e in elements if e.element_type == 'input']) / max(len(form_elements), 1)
                }
            
        except Exception as e:
            logger.warning(f"Error analyzing element patterns: {e}")
        
        return patterns
    
    async def _generate_test_suggestions(self, elements: List[InteractiveElement], actions: List[ElementAction], 
                                      business_context: Dict[str, Any]) -> List[str]:
        """生成测试建议"""
        suggestions = []
        
        try:
            # 基于元素数量生成建议
            if len(elements) < 5:
                suggestions.append("页面交互元素较少，建议检查页面是否加载完整")
            elif len(elements) > 50:
                suggestions.append("页面交互元素较多，建议分批进行测试")
            
            # 基于表单元素生成建议
            form_elements = [e for e in elements if e.element_type in ['form', 'input']]
            if form_elements:
                suggestions.append("检测到表单元素，建议进行表单验证和提交测试")
            
            # 基于按钮元素生成建议
            button_elements = [e for e in elements if e.element_type == 'button']
            if button_elements:
                high_priority_buttons = [b for b in button_elements if b.test_priority >= 8]
                if high_priority_buttons:
                    suggestions.append(f"检测到 {len(high_priority_buttons)} 个高优先级按钮，建议优先测试")
            
            # 基于业务上下文生成建议
            if business_context.get('has_login') and not any(e.element_type == 'input' and 'password' in str(e.attributes.get('type', '')).lower() for e in elements):
                suggestions.append("业务上下文显示需要登录，但未检测到密码输入框，建议检查页面加载状态")
            
            # 基于操作序列生成建议
            if any(action.action_type == 'type' for action in actions):
                suggestions.append("检测到输入操作，建议验证输入验证和字段限制")
            
            if any(action.action_type == 'click' for action in actions):
                suggestions.append("检测到点击操作，建议验证页面跳转和状态变化")
            
            # 通用测试建议
            suggestions.extend([
                "建议验证所有高优先级元素的交互功能",
                "建议检查页面在不同浏览器中的兼容性",
                "建议验证错误处理和异常情况",
                "建议检查性能和响应时间"
            ])
            
        except Exception as e:
            logger.warning(f"Error generating test suggestions: {e}")
        
        return suggestions


# 工厂函数
def create_element_recognizer() -> IntelligentElementRecognizer:
    """创建智能元素识别器"""
    return IntelligentElementRecognizer()