"""
增强测试用例自动生成器
基于业务需求分析和探索结果自动生成高质量的测试用例
"""

import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TestPriority(Enum):
    """测试优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


class TestStatus(Enum):
    """测试状态"""
    PLANNED = "planned"
    READY = "ready"
    EXECUTING = "executing"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    priority: TestPriority = TestPriority.MEDIUM
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    estimated_duration: float = 30.0
    created_at: str = ""
    updated_at: str = ""
    status: TestStatus = TestStatus.PLANNED
    dependencies: List[str] = field(default_factory=list)
    coverage_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': self.steps,
            'assertions': self.assertions,
            'variables': self.variables,
            'priority': self.priority.value,
            'category': self.category,
            'tags': self.tags,
            'estimated_duration': self.estimated_duration,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'coverage_metadata': self.coverage_metadata
        }


@dataclass
class TestSuite:
    """测试套件"""
    id: str
    name: str
    description: str
    test_cases: List[str] = field(default_factory=list)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'test_cases': self.test_cases,
            'category': self.category,
            'tags': self.tags,
            'execution_order': self.execution_order,
            'metadata': self.metadata
        }


class TestCaseGenerator(ABC):
    """测试用例生成器抽象基类"""
    
    @abstractmethod
    async def generate_test_cases(self, analysis_results: Dict[str, Any], 
                                 exploration_data: Dict[str, Any]) -> List[TestCase]:
        """生成测试用例"""
        pass


class IntelligentTestCaseGenerator(TestCaseGenerator):
    """智能测试用例生成器"""
    
    def __init__(self):
        self.test_case_templates = self._initialize_test_templates()
        self.business_patterns = self._initialize_business_patterns()
        self.element_actions = self._initialize_element_actions()
        
    def _initialize_test_templates(self) -> Dict[str, Any]:
        """初始化测试模板"""
        return {
            'login': {
                'name': '用户登录测试',
                'description': '测试用户登录功能',
                'priority': TestPriority.CRITICAL,
                'category': 'authentication',
                'tags': ['login', 'authentication', 'security'],
                'steps': [
                    {'action': 'type', 'target': 'username_input', 'value': '${username}', 'description': '输入用户名'},
                    {'action': 'type', 'target': 'password_input', 'value': '${password}', 'description': '输入密码'},
                    {'action': 'click', 'target': 'login_button', 'description': '点击登录按钮'},
                    {'action': 'wait', 'target': 'dashboard', 'wait_time': 5, 'description': '等待登录成功'}
                ],
                'assertions': [
                    {'type': 'urlContains', 'value': 'dashboard', 'description': '验证URL包含dashboard'},
                    {'type': 'textVisible', 'value': '欢迎回来', 'description': '验证欢迎信息显示'}
                ],
                'variables': {
                    'username': 'testuser',
                    'password': 'TestPass123!'
                }
            },
            'search': {
                'name': '搜索功能测试',
                'description': '测试网站搜索功能',
                'priority': TestPriority.HIGH,
                'category': 'search',
                'tags': ['search', 'discovery', 'ui'],
                'steps': [
                    {'action': 'type', 'target': 'search_input', 'value': '${search_term}', 'description': '输入搜索关键词'},
                    {'action': 'click', 'target': 'search_button', 'description': '点击搜索按钮'},
                    {'action': 'wait', 'target': 'search_results', 'wait_time': 3, 'description': '等待搜索结果'}
                ],
                'assertions': [
                    {'type': 'elementExists', 'value': 'search_results_container', 'description': '验证搜索结果容器存在'},
                    {'type': 'textVisible', 'value': '${search_term}', 'description': '验证搜索结果包含关键词'}
                ],
                'variables': {
                    'search_term': 'test product'
                }
            },
            'form_submission': {
                'name': '表单提交测试',
                'description': '测试表单提交和数据验证',
                'priority': TestPriority.HIGH,
                'category': 'data_entry',
                'tags': ['form', 'submission', 'validation'],
                'steps': [
                    {'action': 'type', 'target': 'name_field', 'value': '${name}', 'description': '输入姓名'},
                    {'action': 'type', 'target': 'email_field', 'value': '${email}', 'description': '输入邮箱'},
                    {'action': 'type', 'target': 'phone_field', 'value': '${phone}', 'description': '输入电话'},
                    {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'}
                ],
                'assertions': [
                    {'type': 'textVisible', 'value': '提交成功', 'description': '验证提交成功消息'},
                    {'type': 'urlContains', 'value': '/success', 'description': '验证跳转到成功页面'}
                ],
                'variables': {
                    'name': 'Test User',
                    'email': 'test@example.com',
                    'phone': '13800138000'
                }
            },
            'navigation': {
                'name': '页面导航测试',
                'description': '测试网站导航和页面跳转',
                'priority': TestPriority.MEDIUM,
                'category': 'navigation',
                'tags': ['navigation', 'ui', 'usability'],
                'steps': [
                    {'action': 'click', 'target': 'home_link', 'description': '点击首页链接'},
                    {'action': 'wait', 'target': 'home_page', 'wait_time': 3, 'description': '等待首页加载'},
                    {'action': 'click', 'target': 'dashboard_link', 'description': '点击仪表盘链接'},
                    {'action': 'wait', 'target': 'dashboard_page', 'wait_time': 3, 'description': '等待仪表盘加载'},
                    {'action': 'click', 'target': 'profile_link', 'description': '点击个人资料链接'},
                    {'action': 'wait', 'target': 'profile_page', 'wait_time': 3, 'description': '等待个人资料加载'}
                ],
                'assertions': [
                    {'type': 'urlContains', 'value': '/home', 'description': '验证首页URL'},
                    {'type': 'urlContains', 'value': '/dashboard', 'description': '验证仪表盘URL'},
                    {'type': 'urlContains', 'value': '/profile', 'description': '验证个人资料URL'}
                ]
            },
            'data_validation': {
                'name': '数据验证测试',
                'description': '测试输入验证和数据完整性',
                'priority': TestPriority.HIGH,
                'category': 'validation',
                'tags': ['validation', 'data_integrity', 'security'],
                'steps': [
                    {'action': 'type', 'target': 'email_field', 'value': 'invalid_email', 'description': '输入无效邮箱'},
                    {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'},
                    {'action': 'wait', 'target': 'error_message', 'wait_time': 2, 'description': '等待错误消息'}
                ],
                'assertions': [
                    {'type': 'textVisible', 'value': '请输入有效的邮箱地址', 'description': '验证邮箱验证错误'},
                    {'type': 'elementExists', 'value': 'email_error', 'description': '验证邮箱错误显示'}
                ]
            }
        }
    
    def _initialize_business_patterns(self) -> Dict[str, Any]:
        """初始化业务模式"""
        return {
            'e-commerce': {
                'keywords': ['product', 'cart', 'order', 'payment', 'checkout', 'buy', 'purchase'],
                'test_categories': ['product_search', 'cart_management', 'checkout_process', 'payment'],
                'priority_tests': ['product_search', 'cart_management', 'checkout_process']
            },
            'social_media': {
                'keywords': ['post', 'share', 'like', 'comment', 'friend', 'profile', 'timeline'],
                'test_categories': ['post_creation', 'social_interaction', 'profile_management'],
                'priority_tests': ['post_creation', 'profile_management']
            },
            'cms': {
                'keywords': ['content', 'article', 'page', 'publish', 'edit', 'admin'],
                'test_categories': ['content_management', 'user_management', 'publishing'],
                'priority_tests': ['content_management', 'publishing']
            },
            'application': {
                'keywords': ['user', 'role', 'permission', 'settings', 'config', 'feature'],
                'test_categories': ['user_management', 'permission_control', 'settings'],
                'priority_tests': ['user_management', 'permission_control']
            }
        }
    
    def _initialize_element_actions(self) -> Dict[str, List[str]]:
        """初始化元素操作映射"""
        return {
            'button': ['click', 'hover', 'right_click', 'double_click'],
            'input': ['type', 'clear', 'focus', 'blur'],
            'select': ['select_option', 'deselect_option'],
            'link': ['click', 'verify_url'],
            'form': ['submit', 'reset', 'validate'],
            'checkbox': ['check', 'uncheck', 'verify_status'],
            'radio': ['select', 'verify_selection'],
            'textarea': ['type', 'clear', 'verify_content'],
            'image': ['click', 'verify_alt', 'verify_src'],
            'table': ['verify_row_count', 'verify_cell_content', 'sort_column'],
            'div': ['verify_content', 'verify_visibility']
        }
    
    async def generate_test_cases(self, analysis_results: Dict[str, Any], 
                                 exploration_data: Dict[str, Any]) -> List[TestCase]:
        """生成测试用例"""
        logger.info("开始生成测试用例...")
        
        test_cases = []
        
        try:
            # 获取业务特征
            business_features = analysis_results.get('detected_features', [])
            
            # 获取探索数据
            explored_pages = exploration_data.get('pages', [])
            interactive_elements = exploration_data.get('elements', [])
            
            # 基于业务特征生成测试用例
            for feature in business_features:
                feature_test_cases = await self._generate_feature_test_cases(
                    feature, business_features, exploration_data
                )
                test_cases.extend(feature_test_cases)
            
            # 基于页面生成测试用例
            for page in explored_pages:
                page_test_cases = await self._generate_page_test_cases(
                    page, business_features, interactive_elements
                )
                test_cases.extend(page_test_cases)
            
            # 生成业务流程测试用例
            workflow_test_cases = await self._generate_workflow_test_cases(
                business_features, exploration_data
            )
            test_cases.extend(workflow_test_cases)
            
            # 生成边界条件和异常测试用例
            edge_test_cases = await self._generate_edge_test_cases(
                business_features, interactive_elements
            )
            test_cases.extend(edge_test_cases)
            
            # 去重和排序
            test_cases = self._deduplicate_and_sort_test_cases(test_cases)
            
            # 生成测试套件
            test_suites = await self._generate_test_suites(test_cases)
            
            logger.info(f"成功生成 {len(test_cases)} 个测试用例")
            
            return test_cases
            
        except Exception as e:
            logger.error(f"生成测试用例时发生错误: {e}")
            return []
    
    async def _generate_feature_test_cases(self, feature: Dict[str, Any], 
                                         all_features: List[Dict[str, Any]], 
                                         exploration_data: Dict[str, Any]) -> List[TestCase]:
        """基于特征生成测试用例"""
        test_cases = []
        
        try:
            feature_name = feature.get('name', '')
            category = feature.get('category', '')
            priority = feature.get('priority', 5)
            
            # 根据特征类型生成测试用例
            if category == 'authentication':
                login_test_case = await self._generate_login_test_case(feature)
                test_cases.append(login_test_case)
                
                # 生成密码重置测试用例
                password_reset_case = await self._generate_password_reset_test_case(feature)
                test_cases.append(password_reset_case)
                
                # 生成注册测试用例
                registration_case = await self._generate_registration_test_case(feature)
                test_cases.append(registration_case)
                
            elif category == 'data_entry':
                form_test_case = await self._generate_form_test_case(feature)
                test_cases.append(form_test_case)
                
                # 生成数据验证测试用例
                validation_case = await self._generate_data_validation_test_case(feature)
                test_cases.append(validation_case)
                
            elif category == 'search':
                search_test_case = await self._generate_search_test_case(feature)
                test_cases.append(search_test_case)
                
                # 生成高级搜索测试用例
                advanced_search_case = await self._generate_advanced_search_test_case(feature)
                test_cases.append(advanced_search_case)
                
            elif category == 'navigation':
                navigation_test_case = await self._generate_navigation_test_case(feature)
                test_cases.append(navigation_test_case)
                
                # 生成面包屑导航测试用例
                breadcrumb_case = await self._generate_breadcrumb_test_case(feature)
                test_cases.append(breadcrumb_case)
                
            elif category == 'data_display':
                # 生成数据表格测试用例
                table_test_case = await self._generate_table_test_case(feature)
                test_cases.append(table_test_case)
                
                # 生成分页测试用例
                pagination_case = await self._generate_pagination_test_case(feature)
                test_cases.append(pagination_case)
                
            elif category == 'profile_settings':
                profile_test_case = await self._generate_profile_test_case(feature)
                test_cases.append(profile_test_case)
                
                # 生成设置保存测试用例
                settings_save_case = await self._generate_settings_save_test_case(feature)
                test_cases.append(settings_save_case)
            
            # 为每个测试用例添加特征标签
            for test_case in test_cases:
                test_case.tags.append(f"feature_{feature_name}")
                test_case.tags.append(category)
                test_case.priority = TestPriority(priority)
                test_case.category = category
                test_case.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
                test_case.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            logger.warning(f"为特征 {feature_name} 生成测试用例时发生错误: {e}")
        
        return test_cases
    
    async def _generate_login_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成登录测试用例"""
        template = self.test_case_templates['login'].copy()
        
        test_case = TestCase(
            id=f"login_test_{int(time.time())}",
            name=template['name'],
            description=template['description'],
            steps=template['steps'].copy(),
            assertions=template['assertions'].copy(),
            variables=template['variables'].copy(),
            priority=template['priority'],
            category=template['category'],
            tags=template['tags'].copy()
        )
        
        # 基于探索结果调整测试用例
        explored_pages = []  # 这里应该从exploration_data获取
        
        # 如果发现社交登录，添加社交登录测试
        if any('social' in page.get('url', '') for page in explored_pages):
            social_login_step = {
                'action': 'click',
                'target': 'social_login_button',
                'description': '点击社交登录按钮'
            }
            test_case.steps.insert(2, social_login_step)
        
        # 添加基于特征的步骤
        feature_elements = feature.get('elements', [])
        if any(elem.get('type') == 'remember_me' for elem in feature_elements):
            remember_step = {
                'action': 'click',
                'target': 'remember_me_checkbox',
                'description': '记住我选项'
            }
            test_case.steps.insert(2, remember_step)
        
        return test_case
    
    async def _generate_password_reset_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成密码重置测试用例"""
        test_case = TestCase(
            id=f"password_reset_test_{int(time.time())}",
            name="密码重置测试",
            description="测试密码重置功能",
            priority=TestPriority.HIGH,
            category="authentication",
            tags=["password", "reset", "security"]
        )
        
        # 添加密码重置步骤
        test_case.steps = [
            {'action': 'click', 'target': 'forgot_password_link', 'description': '点击忘记密码链接'},
            {'action': 'type', 'target': 'email_input', 'value': '${email}', 'description': '输入邮箱地址'},
            {'action': 'click', 'target': 'reset_button', 'description': '点击重置密码按钮'},
            {'action': 'wait', 'target': 'success_message', 'wait_time': 3, 'description': '等待重置成功消息'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': '密码重置链接已发送', 'description': '验证重置成功消息'},
            {'type': 'urlContains', 'value': '/reset-password', 'description': '验证重置页面URL'}
        ]
        
        test_case.variables = {
            'email': 'test@example.com'
        }
        
        return test_case
    
    async def _generate_registration_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成注册测试用例"""
        test_case = TestCase(
            id=f"registration_test_{int(time.time())}",
            name="用户注册测试",
            description="测试用户注册功能",
            priority=TestPriority.HIGH,
            category="authentication",
            tags=["registration", "signup", "user"]
        )
        
        # 添加注册步骤
        test_case.steps = [
            {'action': 'click', 'target': 'register_link', 'description': '点击注册链接'},
            {'action': 'type', 'target': 'username_field', 'value': '${username}', 'description': '输入用户名'},
            {'action': 'type', 'target': 'email_field', 'value': '${email}', 'description': '输入邮箱'},
            {'action': 'type', 'target': 'password_field', 'value': '${password}', 'description': '输入密码'},
            {'action': 'type', 'target': 'confirm_password_field', 'value': '${password}', 'description': '确认密码'},
            {'action': 'click', 'target': 'register_button', 'description': '点击注册按钮'},
            {'action': 'wait', 'target': 'welcome_message', 'wait_time': 5, 'description': '等待欢迎消息'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': '注册成功', 'description': '验证注册成功消息'},
            {'type': 'urlContains', 'value': '/welcome', 'description': '验证欢迎页面URL'}
        ]
        
        test_case.variables = {
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password': 'NewPass123!'
        }
        
        return test_case
    
    async def _generate_form_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成表单测试用例"""
        template = self.test_case_templates['form_submission'].copy()
        
        test_case = TestCase(
            id=f"form_test_{int(time.time())}",
            name=template['name'],
            description=template['description'],
            steps=template['steps'].copy(),
            assertions=template['assertions'].copy(),
            variables=template['variables'].copy(),
            priority=template['priority'],
            category=template['category'],
            tags=template['tags'].copy()
        )
        
        # 基于表单字段动态调整
        form_elements = feature.get('elements', [])
        form_field_names = [elem.get('name', '') for elem in form_elements if elem.get('type') == 'input']
        
        # 如果发现日期字段，添加日期字段测试
        if any('date' in name for name in form_field_names):
            date_step = {
                'action': 'type',
                'target': 'date_field',
                'value': '2023-12-25',
                'description': '输入日期'
            }
            test_case.steps.insert(3, date_step)
        
        # 如果发现文件上传字段，添加文件上传测试
        if any('file' in name for name in form_field_names):
            file_step = {
                'action': 'upload_file',
                'target': 'file_field',
                'value': '${test_file}',
                'description': '上传测试文件'
            }
            test_case.steps.insert(3, file_step)
            test_case.variables['test_file'] = 'test_file.txt'
        
        return test_case
    
    async def _generate_data_validation_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成数据验证测试用例"""
        template = self.test_case_templates['data_validation'].copy()
        
        test_case = TestCase(
            id=f"validation_test_{int(time.time())}",
            name=template['name'],
            description=template['description'],
            steps=template['steps'].copy(),
            assertions=template['assertions'].copy(),
            priority=template['priority'],
            category=template['category'],
            tags=template['tags'].copy()
        )
        
        # 基于字段类型添加更多验证测试
        form_elements = feature.get('elements', [])
        
        # 添加多种输入验证测试
        validation_steps = []
        
        # 邮箱验证
        email_field = next((elem for elem in form_elements if 'email' in elem.get('name', '')), None)
        if email_field:
            validation_steps.extend([
                {'action': 'type', 'target': email_field.get('name'), 'value': 'invalid-email', 'description': '输入无效邮箱格式'},
                {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'},
                {'action': 'wait', 'target': 'email_error', 'wait_time': 2, 'description': '等待邮箱错误消息'},
                {'action': 'clear', 'target': email_field.get('name'), 'description': '清空邮箱字段'},
                {'action': 'type', 'target': email_field.get('name'), 'value: ' 'test@example.com', 'description': '输入有效邮箱'},
                {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'}
            ])
        
        # 长度验证
        if any('name' in elem.get('name', '') for elem in form_elements):
            validation_steps.extend([
                {'action': 'type', 'target': 'name_field', 'value': 'A', 'description': '输入过短名称'},
                {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'},
                {'action': 'clear', 'target': 'name_field', 'description': '清空名称字段'},
                {'action': 'type', 'target': 'name_field', 'value': 'ThisIsAVeryLongNameThatExceedsTheMaximumAllowedLength', 'description': '输入过长名称'},
                {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'}
            ])
        
        test_case.steps.extend(validation_steps)
        
        return test_case
    
    async def _generate_search_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成搜索测试用例"""
        template = self.test_case_templates['search'].copy()
        
        test_case = TestCase(
            id=f"search_test_{int(time.time())}",
            name=template['name'],
            description=template['description'],
            steps=template['steps'].copy(),
            assertions=template['assertions'].copy(),
            variables=template['variables'].copy(),
            priority=template['priority'],
            category=template['category'],
            tags=template['tags'].copy()
        )
        
        # 添加搜索范围测试
        additional_steps = [
            {'action': 'type', 'target': 'search_input', 'value: ' 'test product', 'description': '输入产品搜索关键词'},
            {'action': 'select', 'target': 'search_scope', 'value: ' 'products', 'description': '选择搜索范围'},
            {'action': 'click', 'target': 'search_button', 'description': '点击搜索按钮'},
            {'action': 'wait', 'target': 'search_results', 'wait_time': 3, 'description': '等待搜索结果'}
        ]
        
        test_case.steps.extend(additional_steps)
        
        # 添加搜索结果验证
        additional_assertions = [
            {'type': 'elementExists', 'value': 'product_results', 'description': '验证产品结果容器'},
            {'type': 'textVisible', 'value': 'test product', 'description': '验证搜索结果包含关键词'},
            {'type': 'elementExists', 'value': 'search_pagination', 'description': '验证搜索分页'}
        ]
        
        test_case.assertions.extend(additional_assertions)
        
        return test_case
    
    async def _generate_advanced_search_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成高级搜索测试用例"""
        test_case = TestCase(
            id=f"advanced_search_test_{int(time.time())}",
            name="高级搜索测试",
            description="测试高级搜索功能",
            priority=TestPriority.MEDIUM,
            category="search",
            tags=["search", "advanced", "filter"]
        )
        
        # 添加高级搜索步骤
        test_case.steps = [
            {'action': 'click', 'target': 'advanced_search_link', 'description': '点击高级搜索链接'},
            {'action': 'type', 'target': 'search_keyword', 'value: ' 'test', 'description': '输入搜索关键词'},
            {'action': 'select', 'target': 'category_filter', 'value: ' 'electronics', 'description': '选择类别筛选'},
            {'action': 'select', 'target': 'price_range', 'value: ' '0-100', 'description': '选择价格范围'},
            {'action': 'click', 'target': 'advanced_search_button', 'description: ' '点击高级搜索按钮'},
            {'action': 'wait', 'target': 'advanced_results', 'wait_time': 5, 'description': '等待高级搜索结果'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': 'test', 'description': '验证结果包含关键词'},
            {'type': 'textVisible', 'value': 'electronics', 'description': '验证类别筛选有效'},
            {'type': 'elementExists', 'value': 'price_filter_results', 'description': '验证价格筛选结果'}
        ]
        
        return test_case
    
    async def _generate_navigation_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成导航测试用例"""
        template = self.test_case_templates['navigation'].copy()
        
        test_case = TestCase(
            id=f"navigation_test_{int(time.time())}",
            name=template['name'],
            description=template['description'],
            steps=template['steps'].copy(),
            assertions=template['assertions'].copy(),
            priority=template['priority'],
            category=template['category'],
            tags=template['tags'].copy()
        )
        
        # 添加面包屑导航验证
        breadcrumb_assertion = {
            'type': 'textVisible',
            'value': 'Home > Dashboard > Profile',
            'description': '验证面包屑导航'
        }
        test_case.assertions.append(breadcrumb_assertion)
        
        return test_case
    
    async def _generate_breadcrumb_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成面包屑导航测试用例"""
        test_case = TestCase(
            id=f"breadcrumb_test_{int(time.time())}",
            name="面包屑导航测试",
            description="测试面包屑导航功能",
            priority=TestPriority.LOW,
            category="navigation",
            tags=["navigation", "breadcrumb", "ui"]
        )
        
        test_case.steps = [
            {'action': 'click', 'target': 'home_breadcrumb', 'description': '点击首页面包屑'},
            {'action': 'wait', 'target': 'home_page', 'wait_time': 2, 'description': '等待首页加载'},
            {'action': 'click', 'target': 'category_breadcrumb', 'description': '点击类别面包屑'},
            {'action': 'wait', 'target': 'category_page', 'wait_time': 2, 'description': '等待类别页面加载'},
            {'action': 'click', 'target': 'subcategory_breadcrumb', 'description': '点击子类别面包屑'},
            {'action': 'wait', 'target': 'subcategory_page', 'wait_time': 2, 'description': '等待子类别页面加载'}
        ]
        
        test_case.assertions = [
            {'type': 'urlContains', 'value': '/home', 'description': '验证首页URL'},
            {'type': 'urlContains', 'value': '/category', 'description': '验证类别URL'},
            {'type': 'urlContains', 'value': '/subcategory', 'description': '验证子类别URL'}
        ]
        
        return test_case
    
    async def _generate_table_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成表格测试用例"""
        test_case = TestCase(
            id=f"table_test_{int(time.time())}",
            name="数据表格测试",
            description="测试数据表格功能",
            priority=TestPriority.MEDIUM,
            category="data_display",
            tags=["table", "data", "display"]
        )
        
        test_case.steps = [
            {'action': 'verify', 'target': 'data_table', 'validation_type': 'row_count', 'expected_value': '10', 'description': '验证表格行数'},
            {'action': 'verify', 'target': 'data_table', 'validation_type': 'column_count', 'expected_value': '5', 'description': '验证表格列数'},
            {'action': 'click', 'target': 'sort_name_column', 'description': '点击名称列排序'},
            {'action': 'wait', 'target': 'table_sorted', 'wait_time': 2, 'description': '等待表格排序'},
            {'action': 'click', 'target': 'filter_button', 'description': '点击筛选按钮'},
            {'action': 'type', 'target': 'filter_input', 'value: ' 'test', 'description': '输入筛选关键词'},
            {'action': 'click', 'target': 'apply_filter', 'description': '应用筛选'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': 'No results found', 'description': '验证无结果时显示'},
            {'type': 'elementExists', 'value': 'table_pagination', 'description': '验证表格分页'}
        ]
        
        return test_case
    
    async def _generate_pagination_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成分页测试用例"""
        test_case = TestCase(
            id=f"pagination_test_{int(time.time())}",
            name="分页功能测试",
            description="测试分页功能",
            priority=TestPriority.MEDIUM,
            category="data_display",
            tags=["pagination", "navigation", "data"]
        )
        
        test_case.steps = [
            {'action': 'verify', 'target': 'pagination_info', 'validation_type': 'page_count', 'expected_value': '5', 'description': '验证总页数'},
            {'action': 'click', 'target': 'next_page_button', 'description': '点击下一页'},
            {'action': 'wait', 'target': 'page_2', 'wait_time': 2, 'description': '等待第二页加载'},
            {'action': 'click', 'target': 'last_page_button', 'description': '点击最后一页'},
            {'action': 'wait', 'target': 'final_page', 'wait_time': 2, 'description': '等待最后一页加载'},
            {'action': 'click', 'target': 'first_page_button', 'description': '点击第一页'},
            {'action': 'wait', 'target': 'page_1', 'wait_time': 2, 'description': '等待第一页加载'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': 'Page 1', 'description': '验证当前页码显示'},
            {'type': 'elementExists', 'target': 'previous_button_disabled', 'description': '验证前一页按钮禁用状态'},
            {'type': 'elementExists', 'target': 'next_button_enabled', 'description': '验证下一页按钮启用状态'}
        ]
        
        return test_case
    
    async def _generate_profile_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成个人资料测试用例"""
        test_case = TestCase(
            id=f"profile_test_{int(time.time())}",
            name="个人资料测试",
            description="测试个人资料管理功能",
            priority=TestPriority.MEDIUM,
            category="profile_settings",
            tags=["profile", "user", "settings"]
        )
        
        test_case.steps = [
            {'action': 'click', 'target': 'profile_tab', 'description': '点击个人资料标签'},
            {'action': 'type', 'target': 'name_field', 'value: ' 'Updated Name', 'description': '更新姓名'},
            {'action': 'type', 'target': 'bio_field', 'value: ' 'Test bio text', 'description': '更新简介'},
            {'action': 'click', 'target': 'save_profile_button', 'description': '保存个人资料'},
            {'action': 'wait', 'target': 'profile_updated', 'wait_time': 3, 'description': '等待更新成功'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': '个人资料已更新', 'description': '验证更新成功消息'},
            {'type': 'textVisible', 'value: ' 'Updated Name', 'description': '验证姓名更新显示'}
        ]
        
        return test_case
    
    async def _generate_settings_save_test_case(self, feature: Dict[str, Any]) -> TestCase:
        """生成设置保存测试用例"""
        test_case = TestCase(
            id=f"settings_save_test_{int(time.time())}",
            name="设置保存测试",
            description="测试设置保存功能",
            priority=TestPriority.LOW,
            category="profile_settings",
            tags=["settings", "save", "profile"]
        )
        
        test_case.steps = [
            {'action': 'click', 'target': 'settings_tab', 'description': '点击设置标签'},
            {'action': 'toggle', 'target': 'notification_switch', 'description: ' '切换通知开关'},
            {'action': 'select', 'target': 'language_select', 'value: ' 'zh-CN', 'description': '选择语言'},
            {'action': 'click', 'target': 'save_settings_button', 'description': '保存设置'},
            {'action': 'wait', 'target': 'settings_saved', 'wait_time': 3, 'description': '等待设置保存'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value': '设置已保存', 'description': '验证保存成功消息'},
            {'type': 'elementExists', 'target': 'notification_switch_on', 'description': '验证通知开关状态'}
        ]
        
        return test_case
    
    async def _generate_page_test_cases(self, page: Dict[str, Any], 
                                      business_features: List[Dict[str, Any]], 
                                      interactive_elements: List[Dict[str, Any]]) -> List[TestCase]:
        """基于页面生成测试用例"""
        test_cases = []
        
        try:
            page_url = page.get('url', '')
            page_type = page.get('type', 'unknown')
            
            # 生成页面基本测试
            basic_test_case = await self._generate_page_basic_test_case(page)
            test_cases.append(basic_test_case)
            
            # 生成页面元素测试
            elements_test_case = await self._generate_page_elements_test_case(page, interactive_elements)
            test_cases.append(elements_test_case)
            
            # 基于页面类型生成特定测试
            if page_type == 'login':
                login_specific_test = await self._generate_login_page_test_case(page)
                test_cases.append(login_specific_test)
            elif page_type == 'form':
                form_specific_test = await self._generate_form_page_test_case(page)
                test_cases.append(form_specific_test)
            elif page_type == 'search':
                search_specific_test = await self._generate_search_page_test_case(page)
                test_cases.append(search_specific_test)
            
        except Exception as e:
            logger.warning(f"为页面 {page_url} 生成测试用例时发生错误: {e}")
        
        return test_cases
    
    async def _generate_page_basic_test_case(self, page: Dict[str, Any]) -> TestCase:
        """生成页面基本测试用例"""
        test_case = TestCase(
            id=f"page_basic_{int(time.time())}",
            name=f"页面基本测试 - {page.get('title', 'Unknown')}",
            description=f"测试页面 {page.get('url', '')} 的基本功能",
            priority=TestPriority.LOW,
            category="basic",
            tags=["basic", "page"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target': page.get('url'), 'description': '导航到页面'},
            {'action': 'wait', 'target': 'page_load', 'wait_time': 5, 'description': '等待页面加载'},
            {'action': 'verify', 'target': 'page_title', 'validation_type': 'equals', 'expected_value': page.get('title'), 'description': '验证页面标题'},
            {'action': 'verify', 'target': 'page_url', 'validation_type': 'contains', 'expected_value': page.get('url'), 'description': '验证页面URL'}
        ]
        
        return test_case
    
    async def _generate_page_elements_test_case(self, page: Dict[str, Any], 
                                              interactive_elements: List[Dict[str, Any]]) -> TestCase:
        """生成页面元素测试用例"""
        test_case = TestCase(
            id=f"page_elements_{int(time.time())}",
            name=f"页面元素测试 - {page.get('title', 'Unknown')}",
            description=f"测试页面 {page.get('url', '')} 的交互元素",
            priority=TestPriority.MEDIUM,
            category="elements",
            tags=["elements", "interactive"]
        )
        
        steps = []
        assertions = []
        
        # 为每个可交互元素生成测试步骤
        for element in interactive_elements[:5]:  # 限制数量以避免测试用例过长
            element_id = element.get('id', '')
            element_type = element.get('type', 'unknown')
            
            if element_type == 'button':
                steps.append({
                    'action': 'click',
                    'target': element_id,
                    'description': f'点击按钮: {element.get("text", "")}'
                })
                steps.append({
                    'action': 'wait',
                    'target': 'page_stable',
                    'wait_time': 2,
                    'description': '等待页面稳定'
                })
            elif element_type == 'input':
                steps.append({
                    'action': 'type',
                    'target': element_id,
                    'value: ' 'test_value',
                    'description': f'输入测试值到: {element.get("name", "")}'
                })
        
        test_case.steps = steps
        test_case.assertions = assertions
        
        return test_case
    
    async def _generate_login_page_test_case(self, page: Dict[str, Any]) -> TestCase:
        """生成登录页面特定测试用例"""
        test_case = TestCase(
            id=f"login_page_{int(time.time())}",
            name=f"登录页面测试 - {page.get('title', 'Unknown')}",
            description=f"测试登录页面 {page.get('url', '')}",
            priority=TestPriority.HIGH,
            category="authentication",
            tags=["login", "authentication", "page"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target': page.get('url'), 'description': '导航到登录页面'},
            {'action': 'verify', 'target': 'login_form', 'validation_type': 'exists', 'description': '验证登录表单存在'},
            {'action': 'verify', 'target': 'username_input', 'validation_type': 'exists', 'description': '验证用户名输入框存在'},
            {'action': 'verify', 'target': 'password_input', 'validation_type': 'exists', 'description': '验证密码输入框存在'},
            {'action': 'verify', 'target': 'submit_button', 'validation_type': 'exists', 'description': '验证提交按钮存在'},
            {'action': 'type', 'target': 'username_input', 'value: ' 'testuser', 'description': '输入用户名'},
            {'action': 'type', 'target': 'password_input', 'value: ' 'TestPass123!', 'description': '输入密码'},
            {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'}
        ]
        
        return test_case
    
    async def _generate_form_page_test_case(self, page: Dict[str, Any]) -> TestCase:
        """生成表单页面特定测试用例"""
        test_case = TestCase(
            id=f"form_page_{int(time.time())}",
            name=f"表单页面测试 - {page.get('title', 'Unknown')}",
            description=f"测试表单页面 {page.get('url', '')}",
            priority=TestPriority.HIGH,
            category="data_entry",
            tags=["form", "data_entry", "page"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target': page.get('url'), 'description': '导航到表单页面'},
            {'action': 'verify', 'target': 'form_element', 'validation_type': 'exists', 'description': '验证表单存在'},
            {'action': 'verify', 'target': 'form_fields', 'validation_type': 'count', 'expected_value: ' '5', 'description': '验证表单字段数量'},
            {'action': 'fill_form', 'target: ' 'main_form', 'description': '填写表单'},
            {'action': 'click', 'target': 'submit_button', 'description': '点击提交按钮'}
        ]
        
        return test_case
    
    async def _generate_search_page_test_case(self, page: Dict[str, Any]) -> TestCase:
        """生成搜索页面特定测试用例"""
        test_case = TestCase(
            id=f"search_page_{int(time.time())}",
            name=f"搜索页面测试 - {page.get('title', 'Unknown')}",
            description=f"测试搜索页面 {page.get('url', '')}",
            priority=TestPriority.HIGH,
            category="search",
            tags=["search", "page"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target': page.get('url'), 'description': '导航到搜索页面'},
            {'action': 'verify', 'target': 'search_input', 'validation_type': 'exists', 'description': '验证搜索输入框存在'},
            {'action': 'type', 'target': 'search_input', 'value: ' 'test search term', 'description': '输入搜索关键词'},
            {'action': 'click', 'target': 'search_button', 'description': '点击搜索按钮'},
            {'action': 'wait', 'target': 'search_results', 'wait_time': 5, 'description': '等待搜索结果'}
        ]
        
        return test_case
    
    async def _generate_workflow_test_cases(self, business_features: List[Dict[str, Any]], 
                                          exploration_data: Dict[str, Any]) -> List[TestCase]:
        """生成业务流程测试用例"""
        test_cases = []
        
        try:
            # 识别用户注册流程
            registration_workflow = await self._generate_registration_workflow()
            test_cases.append(registration_workflow)
            
            # 识别用户登录流程
            login_workflow = await self._generate_login_workflow()
            test_cases.append(login_workflow)
            
            # 识别数据提交流程
            submission_workflow = await self._generate_data_submission_workflow()
            test_cases.append(submission_workflow)
            
            # 识别搜索和浏览流程
            search_workflow = await self._generate_search_workflow()
            test_cases.append(search_workflow)
            
        except Exception as e:
            logger.warning(f"生成业务流程测试用例时发生错误: {e}")
        
        return test_cases
    
    async def _generate_registration_workflow(self) -> TestCase:
        """生成用户注册流程测试用例"""
        test_case = TestCase(
            id=f"registration_workflow_{int(time.time())}",
            name="用户注册流程测试",
            description="测试完整的用户注册流程",
            priority=TestPriority.CRITICAL,
            category="workflow",
            tags=["workflow", "registration", "end_to_end"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target: ' '/register', 'description': '导航到注册页面'},
            {'action': 'verify', 'target': 'registration_form', 'validation_type': 'exists', 'description': '验证注册表单存在'},
            {'action': 'type', 'target': 'username_field', 'value: ' 'newuser123', 'description': '输入用户名'},
            {'action': 'type', 'target': 'email_field', 'value: ' 'newuser@example.com', 'description': '输入邮箱'},
            {'action': 'type', 'target': 'password_field', 'value: ' 'NewPass123!', 'description': '输入密码'},
            {'action': 'type', 'target': 'confirm_password_field', 'value: ' 'NewPass123!', 'description': '确认密码'},
            {'action': 'check', 'target': 'terms_checkbox', 'description': '同意条款'},
            {'action': 'click', 'target': 'register_button', 'description': '点击注册按钮'},
            {'action': 'wait', 'target': 'registration_success', 'wait_time': 5, 'description': '等待注册成功'},
            {'action': 'verify', 'target': 'welcome_message', 'validation_type': 'visible', 'description': '验证欢迎消息'},
            {'action': 'click', 'target': 'login_link', 'description': '点击登录链接'},
            {'action': 'type', 'target': 'username_field', 'value: ' 'newuser123', 'description': '输入用户名'},
            {'action': 'type', 'target': 'password_field', 'value: ' 'NewPass123!', 'description': '输入密码'},
            {'action': 'click', 'target': 'login_button', 'description': '点击登录按钮'},
            {'action': 'wait', 'target': 'user_dashboard', 'wait_time': 5, 'description': '等待用户仪表盘'}
        ]
        
        test_case.assertions = [
            {'type': 'urlContains', 'value: ' '/welcome', 'description': '验证注册后跳转到欢迎页面'},
            {'type': 'textVisible', 'value: ' '注册成功', 'description': '验证注册成功消息'},
            {'type': 'urlContains', 'value: ' '/dashboard', 'description': '验证登录后跳转到仪表盘'}
        ]
        
        test_case.estimated_duration = 60.0
        
        return test_case
    
    async def _generate_login_workflow(self) -> TestCase:
        """生成用户登录流程测试用例"""
        test_case = TestCase(
            id=f"login_workflow_{int(time.time())}",
            name="用户登录流程测试",
            description="测试完整的用户登录流程",
            priority=TestPriority.CRITICAL,
            category="workflow",
            tags=["workflow", "login", "end_to_end"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target: ' '/login', 'description': '导航到登录页面'},
            {'action': 'verify', 'target': 'login_form', 'validation_type': 'exists', 'description': '验证登录表单存在'},
            {'action': 'type', 'target': 'username_field', 'value: ' 'testuser', 'description': '输入用户名'},
            {'action': 'type', 'target': 'password_field', 'value: ' 'TestPass123!', 'description': '输入密码'},
            {'action': 'click', 'target': 'login_button', 'description': '点击登录按钮'},
            {'action': 'wait', 'target': 'user_dashboard', 'wait_time': 5, 'description': '等待用户仪表盘'},
            {'action': 'verify', 'target': 'user_profile_link', 'validation_type': 'exists', 'description': '验证用户资料链接'},
            {'action': 'click', 'target': 'user_profile_link', 'description': '点击用户资料链接'},
            {'action': 'wait', 'target': 'profile_page', 'wait_time': 3, 'description': '等待个人资料页面'},
            {'action': 'click', 'target': 'logout_button', 'description': '点击退出按钮'},
            {'action': 'wait', 'target: ' 'login_page', 'wait_time': 3, 'description': '等待返回登录页面'}
        ]
        
        test_case.assertions = [
            {'type': 'urlContains', 'value: ' '/dashboard', 'description': '验证登录后跳转到仪表盘'},
            {'type': 'textVisible', 'value: ' '欢迎回来', 'description': '验证欢迎信息'},
            {'type': 'urlContains', 'value: ' '/login', 'description': '验证退出后返回登录页面'}
        ]
        
        test_case.estimated_duration = 45.0
        
        return test_case
    
    async def _generate_data_submission_workflow(self) -> TestCase:
        """生成数据提交流程测试用例"""
        test_case = TestCase(
            id=f"data_submission_workflow_{int(time.time())}",
            name="数据提交流程测试",
            description="测试完整的数据提交流程",
            priority=TestPriority.HIGH,
            category="workflow",
            tags=["workflow", "data_submission", "end_to_end"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target: ' '/create', 'description': '导航到创建页面'},
            {'action': 'type', 'target': 'title_field', 'value: ' 'Test Data', 'description': '输入标题'},
            {'action': 'type', 'target': 'description_field', 'value: ' 'This is a test data entry', 'description': '输入描述'},
            {'action': 'type', 'target': 'category_field', 'value: ' 'test', 'description': '输入类别'},
            {'action': 'upload', 'target': 'file_field', 'value: ' 'test_file.txt', 'description': '上传文件'},
            {'action': 'click', 'target': 'save_draft_button', 'description': '保存草稿'},
            {'action': 'wait', 'target': 'draft_saved', 'wait_time': 3, 'description': '等待草稿保存'},
            {'action': 'click', 'target': 'edit_button', 'description': '点击编辑按钮'},
            {'action': 'type', 'target': 'description_field', 'value: ' 'Updated description', 'description': '更新描述'},
            {'action': 'click', 'target': 'publish_button', 'description': '点击发布按钮'},
            {'action': 'wait', 'target': 'published', 'wait_time': 5, 'description': '等待发布完成'},
            {'action': 'navigate', 'target: ' '/list', 'description': '导航到列表页面'},
            {'action': 'verify', 'target': 'data_list', 'validation_type': 'contains', 'expected_value: ' 'Test Data', 'description': '验证数据在列表中显示'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value: ' '草稿已保存', 'description': '验证草稿保存成功'},
            {'type': 'textVisible', 'value: ' '已发布', 'description': '验证发布成功'},
            {'type': 'textVisible', 'value: ' 'Test Data', 'description': '验证数据在列表中显示'}
        ]
        
        test_case.estimated_duration = 90.0
        
        return test_case
    
    async def _generate_search_workflow(self) -> TestCase:
        """生成搜索流程测试用例"""
        test_case = TestCase(
            id=f"search_workflow_{int(time.time())}",
            name="搜索流程测试",
            description="测试完整的搜索和浏览流程",
            priority=TestPriority.HIGH,
            category="workflow",
            tags=["workflow", "search", "end_to_end"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target: ' '/search', 'description': '导航到搜索页面'},
            {'action': 'type', 'target': 'search_input', 'value: ' 'test keyword', 'description': '输入搜索关键词'},
            {'action': 'click', 'target': 'search_button', 'description': '点击搜索按钮'},
            {'action': 'wait', 'target: 'search_results', 'wait_time': 5, 'description': '等待搜索结果'},
            {'action': 'verify', 'target: 'result_count', 'validation_type': 'greater_than', 'expected_value: ' '0', 'description': '验证有搜索结果'},
            {'action': 'click', 'target': 'first_result', 'description': '点击第一个结果'},
            {'action': 'wait', 'target: 'result_page', 'wait_time': 3, 'description': '等待结果页面'},
            {'action': 'verify', 'target: 'result_content', 'validation_type': 'contains', 'expected_value: ' 'test keyword', 'description': '验证结果包含关键词'},
            {'action': 'click', 'target: 'back_button', 'description': '点击返回按钮'},
            {'action': 'wait', 'target: 'search_results', 'wait_time': 3, 'description': '等待返回搜索结果'},
            {'action': 'type', 'target': 'search_input', 'value: ' 'another keyword', 'description': '输入另一个关键词'},
            {'action': 'click', 'target': 'advanced_search_button', 'description': '点击高级搜索按钮'},
            {'action': 'select', 'target: 'category_filter', 'value: ' 'category1', 'description': '选择类别筛选'},
            {'action': 'click', 'target: 'apply_filter', 'description': '应用筛选'},
            {'action': 'wait', 'target: 'filtered_results', 'wait_time': 5, 'description': '等待筛选结果'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value: ' 'test keyword', 'description': '验证搜索结果显示'},
            {'type': 'textVisible', 'value: ' 'another keyword', 'description': '验证高级搜索结果'},
            {'type': 'textVisible', 'value: ' 'category1', 'description': '验证类别筛选结果'}
        ]
        
        test_case.estimated_duration = 60.0
        
        return test_case
    
    async def _generate_edge_test_cases(self, business_features: List[Dict[str, Any]], 
                                      interactive_elements: List[Dict[str, Any]]) -> List[TestCase]:
        """生成边界条件和异常测试用例"""
        test_cases = []
        
        try:
            # 生成错误处理测试用例
            error_handling_test = await self._generate_error_handling_test_case()
            test_cases.append(error_handling_test)
            
            # 生成性能测试用例
            performance_test = await self._generate_performance_test_case()
            test_cases.append(performance_test)
            
            # 生成兼容性测试用例
            compatibility_test = await self._generate_compatibility_test_case()
            test_cases.append(compatibility_test)
            
            # 生成安全性测试用例
            security_test = await self._generate_security_test_case()
            test_cases.append(security_test)
            
        except Exception as e:
            logger.warning(f"生成边界测试用例时发生错误: {e}")
        
        return test_cases
    
    async def _generate_error_handling_test_case(self) -> TestCase:
        """生成错误处理测试用例"""
        test_case = TestCase(
            id=f"error_handling_{int(time.time())}",
            name="错误处理测试",
            description="测试系统的错误处理机制",
            priority=TestPriority.HIGH,
            category="error_handling",
            tags=["error", "exception", "handling"]
        )
        
        test_case.steps = [
            {'action': 'navigate', 'target: ' '/login', 'description': '导航到登录页面'},
            {'action': 'type', 'target: ' 'username_field', 'value: ' '', 'description': '输入空用户名'},
            {'action': 'type', 'target: ' 'password_field', 'value: ' '', 'description': '输入空密码'},
            {'action': 'click', 'target: ' 'login_button', 'description': '点击登录按钮'},
            {'action': 'wait', 'target: ' 'error_message', 'wait_time': 3, 'description': '等待错误消息'},
            {'action': 'verify', 'target: ' 'error_message', 'validation_type': 'visible', 'description': '验证错误消息显示'},
            {'action': 'type', 'target: ' 'username_field', 'value: ' 'invalid_user', 'description': '输入无效用户名'},
            {'action': 'type', 'target: ' 'password_field', 'value: ' 'wrong_password', 'description': '输入错误密码'},
            {'action': 'click', 'target: ' 'login_button', 'description': '点击登录按钮'},
            {'action': 'wait', 'target: ' 'error_message', 'wait_time': 3, 'description': '等待错误消息'},
            {'action': 'verify', 'target: ' 'error_message', 'validation_type': 'contains', 'expected_value: ' '用户名或密码错误', 'description': '验证登录错误消息'},
            {'action': 'navigate', 'target: ' 'nonexistent_page', 'description': '导航到不存在的页面'},
            {'action': 'wait', 'target: ' 'not_found', 'wait_time': 3, 'description': '等待404页面'},
            {'action': 'verify', 'target: ' '404_message', 'validation_type': 'visible', 'description': '验证404页面显示'}
        ]
        
        test_case.assertions = [
            {'type': 'textVisible', 'value: ' '请输入用户名', 'description': '验证空用户名错误'},
            {'type': 'textVisible', 'value: ' '请输入密码', 'description': '验证空密码错误'},
            {'type': 'textVisible', 'value: ' '404', 'description': '验证404页面'}
        ]
        
        return test_case
    
    async def _generate_performance_test_case(self) -> TestCase:
        """生成性能测试用例"""
        test_case = TestCase(
            id=f"performance_{int(time.time())}",
            name="性能测试",
            description="测试系统性能和响应时间",
            priority=TestPriority.LOW,
            category="performance",
            tags=["performance", "response_time", "speed"]
        )
        
        test_case.steps = [
            {'action': 'measure', 'target: ' 'page_load_time', 'description': '测量页面加载时间'},
            {'action': 'navigate', 'target: ' '/', 'description': '导航到首页'},
            {'action': 'wait', 'target: ' 'page_load', 'wait_time: ' '10', 'description': '等待页面加载完成'},
            {'action': 'measure', 'target: ' 'load_time', 'description': '记录首页加载时间'},
            {'action': 'navigate', 'target: ' '/dashboard', 'description': '导航到仪表盘'},
            {'action': 'wait', 'target: ' 'dashboard_load', 'wait_time: ' '10', 'description': '等待仪表盘加载'},
            {'action': 'measure', 'target: ' 'dashboard_load_time', 'description': '记录仪表盘加载时间'},
            {'action': 'navigate', 'target: ' '/large_table', 'description': '导航到大数据表格页面'},
            {'action': 'wait', 'target: ' 'table_load', 'wait_time: ' '15', 'description': '等待表格加载'},
            {'action': 'measure', 'target: ' 'table_load_time', 'description': '记录表格加载时间'},
            {'action': 'repeat', 'target: ' 'navigation_test', 'count: ' '10', 'description': '重复导航测试'}
        ]
        
        test_case.assertions = [
            {'type': 'performance', 'metric: ' 'load_time', 'threshold: ' '3', 'operator: ' '<', 'description': '验证首页加载时间小于3秒'},
            {'type': 'performance', 'metric: ' 'dashboard_load_time', 'threshold: ' '5', 'operator: ' '<', 'description': '验证仪表盘加载时间小于5秒'},
            {'type': 'performance', 'metric: ' 'table_load_time', 'threshold: ' '8', 'operator: ' '<', 'description': '验证表格加载时间小于8秒'}
        ]
        
        return test_case
    
    async def _generate_compatibility_test_case(self) -> TestCase:
        """生成兼容性测试用例"""
        test_case = TestCase(
            id=f"compatibility_{int(time.time())}",
            name="兼容性测试",
            description="测试在不同浏览器和设备上的兼容性",
            priority=TestPriority.MEDIUM,
            category="compatibility",
            tags=["compatibility", "cross_browser", "responsive"]
        )
        
        test_case.steps = [
            {'action': 'browser_test', 'target: ' 'chrome', 'description': 'Chrome浏览器测试'},
            {'action': 'navigate', 'target: ' '/', 'description': '导航到首页'},
            {'action': 'verify', 'target: ' 'page_elements', 'validation_type': 'visible', 'description': '验证页面元素显示'},
            {'action': 'browser_test', 'target: ' 'firefox', 'description': 'Firefox浏览器测试'},
            {'action': 'navigate', 'target: ' '/', 'description': '导航到首页'},
            {'action': 'verify', 'target: ' 'page_elements', 'validation_type': 'visible', 'description': '验证页面元素显示'},
            {'action': 'browser_test', 'target: ' 'safari', 'description': 'Safari浏览器测试'},
            {'action': 'navigate', 'target: ' '/', 'description': '导航到首页'},
            {'action': 'verify', 'target: ' 'page_elements', 'validation_type': 'visible', 'description': '验证页面元素显示'},
            {'action': 'responsive_test', 'target: ' 'mobile', 'description': '移动设备测试'},
            {'action': 'navigate', 'target: ' '/', 'description': '导航到首页'},
            {'action': 'verify', 'target: ' 'mobile_layout', 'validation_type: ' 'responsive', 'description': '验证移动端布局'}
        ]
        
        return test_case
    
    async def _generate_security_test_case(self) -> TestCase:
        """生成安全性测试用例"""
        test_case = TestCase(
            id=f"security_{int(time.time())}",
            name="安全性测试",
            description="测试系统的安全性机制",
            priority=TestPriority.CRITICAL,
            category="security",
            tags=["security", "vulnerability", "protection"]
        )
        
        test_case.steps = [
            {'action': 'security_test', 'target: ' 'sql_injection', 'description': 'SQL注入测试'},
            {'action': 'type', 'target: ' 'username_field', 'value: ' 'test OR 1=1--', 'description': '输入SQL注入 payload'},
            {'action': 'type', 'target: ' 'password_field', 'value: ' 'password', 'description': '输入密码'},
            {'action': 'click', 'target: ' 'login_button', 'description': '点击登录按钮'},
            {'action': 'verify', 'target: ' 'error_handling', 'validation_type': 'proper', 'description': '验证SQL注入被正确处理'},
            {'action': 'security_test', 'target: ' 'xss', 'description': 'XSS攻击测试'},
            {'action': 'type', 'target: ' 'comment_field', 'value: ' '<script>alert("XSS")</script>', 'description': '输入XSS payload'},
            {'action': 'click', 'target: ' 'submit_button', 'description': '点击提交按钮'},
            {'action': 'verify', 'target: ' 'xss_prevention', 'validation_type': 'encoded', 'description': '验证XSS被正确编码'},
            {'action': 'security_test', 'target: ' 'csrf', 'description': 'CSRF测试'},
            {'action': 'navigate', 'target: ' '/malicious', 'description': '导航到恶意页面'},
            {'action': 'verify', 'target: ' 'csrf_protection', 'validation_type': 'enabled', 'description': '验证CSRF保护生效'}
        ]
        
        return test_case
    
    def _deduplicate_and_sort_test_cases(self, test_cases: List[TestCase]) -> List[TestCase]:
        """去重和排序测试用例"""
        # 基于ID去重
        unique_cases = {}
        for test_case in test_cases:
            unique_cases[test_case.id] = test_case
        
        # 转换为列表并排序
        unique_test_cases = list(unique_cases.values())
        
        # 按优先级排序
        priority_order = {
            TestPriority.CRITICAL: 1,
            TestPriority.HIGH: 2,
            TestPriority.MEDIUM: 3,
            TestPriority.LOW: 4,
            TestPriority.OPTIONAL: 5
        }
        
        unique_test_cases.sort(key=lambda x: priority_order.get(x.priority, 6))
        
        return unique_test_cases
    
    async def _generate_test_suites(self, test_cases: List[TestCase]) -> List[TestSuite]:
        """生成测试套件"""
        suites = []
        
        try:
            # 按类别分组
            category_groups = {}
            for test_case in test_cases:
                category = test_case.category
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(test_case.id)
            
            # 创建测试套件
            for category, case_ids in category_groups.items():
                suite = TestSuite(
                    id=f"suite_{category}_{int(time.time())}",
                    name=f"{category} 测试套件",
                    description=f"包含所有{category}相关的测试用例",
                    test_cases=case_ids,
                    category=category,
                    tags=[category, "suite"],
                    execution_order=case_ids
                )
                suites.append(suite)
            
            # 创建端到端测试套件
            e2e_cases = [tc.id for tc in test_cases if tc.priority == TestPriority.CRITICAL][:5]
            if e2e_cases:
                e2e_suite = TestSuite(
                    id=f"suite_e2e_{int(time.time())}",
                    name="端到端测试套件",
                    description="包含所有端到端测试用例",
                    test_cases=e2e_cases,
                    category="end_to_end",
                    tags=["end_to_end", "suite"],
                    execution_order=e2e_cases
                )
                suites.append(e2e_suite)
            
        except Exception as e:
            logger.warning(f"生成测试套件时发生错误: {e}")
        
        return suites
    
    async def optimize_test_cases(self, test_cases: List[TestCase], 
                                 optimization_strategy: str = 'priority') -> List[TestCase]:
        """优化测试用例"""
        try:
            if optimization_strategy == 'priority':
                # 按优先级排序
                sorted_cases = sorted(test_cases, key=lambda x: x.priority.value)
            elif optimization_strategy == 'duration':
                # 按执行时间排序
                sorted_cases = sorted(test_cases, key=lambda x: x.estimated_duration)
            elif optimization_strategy == 'coverage':
                # 按覆盖率排序
                sorted_cases = sorted(test_cases, key=lambda x: x.coverage_metadata.get('coverage_score', 0), reverse=True)
            else:
                # 默认排序
                sorted_cases = test_cases
            
            return sorted_cases
            
        except Exception as e:
            logger.warning(f"优化测试用例时发生错误: {e}")
            return test_cases


# 工厂函数
def create_test_case_generator() -> IntelligentTestCaseGenerator:
    """创建智能测试用例生成器"""
    return IntelligentTestCaseGenerator()