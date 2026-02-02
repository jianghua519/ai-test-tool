"""
智能业务需求分析器
分析用户输入的业务描述，并生成相应的探索和测试策略
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import asyncio
import time

logger = logging.getLogger(__name__)


@dataclass
class BusinessFeature:
    """业务特征"""
    name: str
    description: str
    category: str  # 'authentication', 'navigation', 'data_entry', 'search', etc.
    priority: int  # 1-10, 10 highest
    elements: List[Dict[str, Any]] = field(default_factory=list)
    test_scenarios: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """分析结果"""
    business_description: str
    detected_features: List[BusinessFeature] = field(default_factory=list)
    exploration_strategy: Dict[str, Any] = field(default_factory=dict)
    test_targets: List[str] = field(default_factory=list)
    priority_areas: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    analysis_timestamp: str = ""
    suggested_actions: List[str] = field(default_factory=list)


class BusinessRequirementAnalyzer:
    """业务需求分析器"""
    
    def __init__(self):
        self.feature_patterns = self._initialize_feature_patterns()
        self.content_patterns = self._initialize_content_patterns()
        
    def _initialize_feature_patterns(self) -> Dict[str, Dict[str, Any]]:
        """初始化业务特征模式"""
        return {
            'authentication': {
                'keywords': ['login', 'signin', 'auth', 'authenticate', 'password', 'username', 'email', 'credential'],
                'patterns': [
                    r'login\s+with\s+(username|email|user\s+id)\s+and\s+password',
                    r'sign\s+in\s+using\s+(username|email)',
                    r'authentication\s+(required|needed|process)',
                    r'forgot\s+password\s+link',
                    r'register\s+(new|create)\s+account',
                    r'sign\s+up\s+for'
                ],
                'indicators': [
                    'input[type="password"]',
                    'input[name*="password"]',
                    'input[name*="username"]',
                    'input[name*="email"]',
                    'button:contains("Login")',
                    'button:contains("Sign in")',
                    'a:contains("Forgot password")',
                    'a:contains("Sign up")'
                ],
                'priority': 9,
                'description': '用户认证相关功能'
            },
            'navigation': {
                'keywords': ['navigation', 'menu', 'sidebar', 'dashboard', 'home', 'main', 'navigate'],
                'patterns': [
                    r'navigation\s+(menu|bar|tabs)',
                    r'side\s+(menu|sidebar|bar)',
                    r'main\s+(menu|navigation)',
                    r'dashboard\s+(overview|main)',
                    r'home\s+(page|screen)',
                    r'main\s+(screen|page|view)'
                ],
                'indicators': [
                    'nav',
                    '[role="navigation"]',
                    '.nav',
                    '.navigation',
                    '.sidebar',
                    '.menu',
                    'dashboard',
                    'home',
                    'main'
                ],
                'priority': 7,
                'description': '页面导航和菜单功能'
            },
            'data_entry': {
                'keywords': ['form', 'input', 'submit', 'register', 'create', 'add', 'insert'],
                'patterns': [
                    r'(form|input|enter|fill)\s+(data|information|details)',
                    r'(create|add|insert|submit)\s+(new|item|record)',
                    r'register\s+(new|user|account)',
                    r'submit\s+(form|data|information)',
                    r'(input|enter)\s+(field|value)'
                ],
                'indicators': [
                    'form',
                    'input[type!="hidden"]',
                    'textarea',
                    'select',
                    'button[type="submit"]',
                    '.form-control',
                    '.input-group'
                ],
                'priority': 8,
                'description': '数据录入和表单提交功能'
            },
            'search': {
                'keywords': ['search', 'filter', 'find', 'lookup', 'query', 'search box'],
                'patterns': [
                    r'search\s+(for|by|using)',
                    r'(find|lookup|query)\s+(item|record|data)',
                    r'filter\s+(by|using)',
                    r'search\s+(box|input|field)',
                    r'advanced\s+search',
                    r'search\s+(results|list)'
                ],
                'indicators': [
                    'input[type="search"]',
                    'input[placeholder*="search"]',
                    '.search',
                    '.find',
                    'button:contains("Search")',
                    'button:contains("Filter")'
                ],
                'priority': 6,
                'description': '搜索和筛选功能'
            },
            'data_display': {
                'keywords': ['list', 'table', 'grid', 'view', 'show', 'display', 'report'],
                'patterns': [
                    r'(list|table|grid|view)\s+(of|data|items)',
                    r'(show|display|present)\s+(data|information|results)',
                    r'(view|browse)\s+(records|items)',
                    r'(report|summary|overview)\s+(dashboard|main)',
                    r'(data|information)\s+(list|table|grid)'
                ],
                'indicators': [
                    'table',
                    'ul',
                    'ol',
                    '.list',
                    '.table',
                    '.grid',
                    '.view',
                    '.display'
                ],
                'priority': 5,
                'description': '数据展示和列表功能'
            },
            'action_buttons': {
                'keywords': ['button', 'action', 'click', 'submit', 'save', 'delete', 'edit', 'update'],
                'patterns': [
                    r'(click|press|tap)\s+(button|link)',
                    r'(save|submit)\s+(data|form|information)',
                    r'(edit|modify|update)\s+(record|item)',
                    r'(delete|remove)\s+(item|record)',
                    r'(create|add|new)\s+(button|action)',
                    r'(action|button)\s+(menu|toolbar)'
                ],
                'indicators': [
                    'button',
                    '.btn',
                    '.action',
                    '[role="button"]',
                    '.submit',
                    '.save',
                    '.edit',
                    '.delete'
                ],
                'priority': 6,
                'description': '按钮操作和交互功能'
            },
            'profile_settings': {
                'keywords': ['profile', 'settings', 'preferences', 'account', 'config', 'personal'],
                'patterns': [
                    r'(profile|account)\s+(page|settings|information)',
                    r'(settings|preferences|config)\s+(page|screen)',
                    r'personal\s+(information|details|data)',
                    r'account\s+(settings|preferences)',
                    r'(edit|update)\s+(profile|account)'
                ],
                'indicators': [
                    'profile',
                    'settings',
                    'preferences',
                    'account',
                    'config',
                    'personal'
                ],
                'priority': 4,
                'description': '个人资料和设置功能'
            },
            'notifications': {
                'keywords': ['notification', 'alert', 'message', 'warning', 'error', 'success'],
                'patterns': [
                    r'(notification|alert|message|warning|error|success)\s+(display|shown|shown)',
                    r'(show|display|present)\s+(notification|alert|message)',
                    r'(error|warning|success)\s+(message|notification)',
                    r'notification\s+(center|panel)',
                    r'system\s+(alert|notification)'
                ],
                'indicators': [
                    '.notification',
                    '.alert',
                    '.message',
                    '.warning',
                    '.error',
                    '.success'
                ],
                'priority': 3,
                'description': '通知和消息功能'
            }
        }
    
    def _initialize_content_patterns(self) -> Dict[str, List[str]]:
        """初始化内容模式"""
        return {
            'login_pages': [
                r'/login',
                r'/signin',
                r'/auth',
                r'/authenticate',
                r'/sign-in',
                r'/log-in',
                r'/welcome'
            ],
            'dashboard_pages': [
                r'/dashboard',
                r'/home',
                r'/main',
                r'/overview',
                r'/summary',
                r'/index',
                r'/console'
            ],
            'form_pages': [
                r'/form',
                r'/create',
                r'/new',
                r'/add',
                r'/register',
                r'/signup',
                r'/apply'
            ],
            'list_pages': [
                r'/list',
                r'/browse',
                r'/search',
                r'/results',
                r'/items',
                r'/records',
                r'/data'
            ],
            'settings_pages': [
                r'/settings',
                r'/preferences',
                r'/config',
                r'/profile',
                r'/account',
                r'/options'
            ]
        }
    
    async def analyze_business_description(self, description: str) -> AnalysisResult:
        """分析业务描述"""
        logger.info(f"Analyzing business description: {description[:100]}...")
        
        start_time = time.time()
        
        result = AnalysisResult(
            business_description=description,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        try:
            # 文本预处理
            processed_text = self._preprocess_text(description)
            
            # 特征检测
            detected_features = await self._detect_features(processed_text, description)
            result.detected_features = detected_features
            
            # 生成探索策略
            exploration_strategy = await self._generate_exploration_strategy(detected_features)
            result.exploration_strategy = exploration_strategy
            
            # 识别测试目标
            test_targets = await self._identify_test_targets(detected_features)
            result.test_targets = test_targets
            
            # 确定优先级区域
            priority_areas = await self._determine_priority_areas(detected_features)
            result.priority_areas = priority_areas
            
            # 计算置信度分数
            result.confidence_score = await self._calculate_confidence_score(detected_features, description)
            
            # 生成建议操作
            result.suggested_actions = await self._generate_suggested_actions(detected_features)
            
            logger.info(f"Analysis completed in {time.time() - start_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing business description: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 转换为小写
        text = text.lower()
        
        # 移除特殊字符，保留字母、数字、空格
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # 标准化空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除常见停用词
        stopwords = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'let', 'get', 'go', 'make', 'take', 'see', 'come', 'know', 'think', 'look', 'want', 'need', 'use', 'work', 'try', 'feel', 'become', 'leave', 'call', 'keep', 'let', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'show', 'hear', 'play', 'run', 'move', 'live', 'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose', 'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand', 'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'open', 'walk', 'win', 'offer', 'remember', 'love', 'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send', 'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill', 'remain']
        
        words = text.split()
        words = [word for word in words if word not in stopwords]
        
        return ' '.join(words)
    
    async def _detect_features(self, processed_text: str, original_description: str) -> List[BusinessFeature]:
        """检测业务特征"""
        detected_features = []
        
        # 基于关键词检测特征
        for feature_name, feature_data in self.feature_patterns.items():
            feature = await self._analyze_feature(
                feature_name, 
                feature_data, 
                processed_text, 
                original_description
            )
            
            if feature and feature.priority > 3:  # 只保留优先级高于3的特征
                detected_features.append(feature)
        
        # 按优先级排序
        detected_features.sort(key=lambda x: x.priority, reverse=True)
        
        return detected_features
    
    async def _analyze_feature(self, feature_name: str, feature_data: Dict[str, Any], 
                              processed_text: str, original_description: str) -> Optional[BusinessFeature]:
        """分析单个业务特征"""
        score = 0
        elements = []
        
        # 检查关键词匹配
        keyword_matches = 0
        for keyword in feature_data['keywords']:
            if keyword in processed_text:
                keyword_matches += 1
                score += 1
        
        # 检查模式匹配
        pattern_matches = 0
        for pattern in feature_data['patterns']:
            if re.search(pattern, processed_text):
                pattern_matches += 1
                score += 2
        
        # 检查描述中的上下文
        context_matches = 0
        if feature_name in processed_text:
            context_matches += 1
            score += 1
        
        # 计算总分
        total_score = keyword_matches + (pattern_matches * 2) + context_matches
        
        # 确定特征是否应该包含
        if total_score >= 2:
            # 提取相关元素
            elements = await self._extract_elements_for_feature(feature_name, original_description)
            
            # 生成测试场景
            test_scenarios = await self._generate_test_scenarios(feature_name, elements)
            
            return BusinessFeature(
                name=feature_name,
                description=feature_data['description'],
                category=feature_name,
                priority=min(feature_data['priority'], 10),
                elements=elements,
                test_scenarios=test_scenarios,
                keywords=feature_data['keywords']
            )
        
        return None
    
    async def _extract_elements_for_feature(self, feature_name: str, description: str) -> List[Dict[str, Any]]:
        """为特征提取相关元素"""
        elements = []
        
        # 基于特征名称生成可能的元素
        if feature_name == 'authentication':
            elements.extend([
                {'type': 'input', 'name': 'username', 'description': '用户名输入框'},
                {'type': 'input', 'name': 'password', 'description': '密码输入框'},
                {'type': 'button', 'name': 'login', 'description': '登录按钮'},
                {'type': 'link', 'name': 'forgot_password', 'description': '忘记密码链接'},
                {'type': 'link', 'name': 'register', 'description': '注册链接'}
            ])
        elif feature_name == 'navigation':
            elements.extend([
                {'type': 'nav', 'name': 'main_menu', 'description': '主导航菜单'},
                {'type': 'link', 'name': 'dashboard', 'description': '仪表盘链接'},
                {'type': 'link', 'name': 'profile', 'description': '个人资料链接'},
                {'type': 'link', 'name': 'settings', 'description': '设置链接'}
            ])
        elif feature_name == 'data_entry':
            elements.extend([
                {'type': 'form', 'name': 'main_form', 'description': '主表单'},
                {'type': 'input', 'name': 'field_name', 'description': '字段名称输入'},
                {'type': 'button', 'name': 'submit', 'description': '提交按钮'},
                {'type': 'button', 'name': 'cancel', 'description': '取消按钮'}
            ])
        elif feature_name == 'search':
            elements.extend([
                {'type': 'input', 'name': 'search_query', 'description': '搜索输入框'},
                {'type': 'button', 'name': 'search_button', 'description': '搜索按钮'},
                {'type': 'button', 'name': 'filter', 'description': '筛选按钮'}
            ])
        elif feature_name == 'data_display':
            elements.extend([
                {'type': 'table', 'name': 'data_table', 'description': '数据表格'},
                {'type': 'link', 'name': 'view_details', 'description': '查看详情链接'},
                {'type': 'button', 'name': 'edit', 'description': '编辑按钮'},
                {'type': 'button', 'name': 'delete', 'description': '删除按钮'}
            ])
        elif feature_name == 'profile_settings':
            elements.extend([
                {'type': 'form', 'name': 'profile_form', 'description': '个人资料表单'},
                {'type': 'input', 'name': 'name', 'description': '姓名输入'},
                {'type': 'input', 'name': 'email', 'description': '邮箱输入'},
                {'type': 'button', 'name': 'save', 'description': '保存按钮'}
            ])
        
        return elements
    
    async def _generate_test_scenarios(self, feature_name: str, elements: List[Dict[str, Any]]) -> List[str]:
        """为特征生成测试场景"""
        scenarios = []
        
        if feature_name == 'authentication':
            scenarios.extend([
                '用户使用正确的用户名和密码登录成功',
                '用户使用错误的用户名或密码登录失败',
                '用户点击忘记密码链接',
                '用户点击注册链接创建新账户'
            ])
        elif feature_name == 'navigation':
            scenarios.extend([
                '用户通过主导航菜单访问不同页面',
                '用户能够导航到仪表盘页面',
                '用户能够访问个人资料页面',
                '用户能够访问设置页面'
            ])
        elif feature_name == 'data_entry':
            scenarios.extend([
                '用户能够填写表单并成功提交',
                '用户能够验证表单输入验证',
                '用户能够取消表单提交',
                '表单提交后数据正确保存'
            ])
        elif feature_name == 'search':
            scenarios.extend([
                '用户能够在搜索框输入关键词进行搜索',
                '用户能够使用筛选功能',
                '搜索结果显示正确的结果',
                '搜索结果能够分页显示'
            ])
        elif feature_name == 'data_display':
            scenarios.extend([
                '数据表格正确显示所有记录',
                '用户能够查看单个记录的详细信息',
                '用户能够编辑记录',
                '用户能够删除记录'
            ])
        elif feature_name == 'profile_settings':
            scenarios.extend([
                '用户能够查看和编辑个人资料',
                '用户能够更新邮箱地址',
                '用户能够保存个人资料设置',
                '个人资料更新后数据正确保存'
            ])
        
        return scenarios
    
    async def _generate_exploration_strategy(self, detected_features: List[BusinessFeature]) -> Dict[str, Any]:
        """生成探索策略"""
        strategy = {
            'navigation_strategy': 'adaptive',
            'max_depth': 3,
            'max_pages': 20,
            'focus_areas': [],
            'priority_links': [],
            'avoid_patterns': [],
            'timeouts': {
                'page_load': 30000,
                'element_wait': 10000,
                'network_idle': 10000
            }
        }
        
        # 根据检测到的特征确定探索策略
        if any(f.category == 'authentication' for f in detected_features):
            strategy['navigation_strategy'] = 'bfs'
            strategy['max_depth'] = 4
            strategy['max_pages'] = 15
            strategy['focus_areas'].append('login_pages')
            strategy['priority_links'].extend(['login', 'signin', 'auth'])
        
        if any(f.category == 'data_display' for f in detected_features):
            strategy['navigation_strategy'] = 'dfs'
            strategy['max_depth'] = 5
            strategy['max_pages'] = 25
            strategy['focus_areas'].extend(['list_pages', 'data_pages'])
        
        if any(f.category == 'navigation' for f in detected_features):
            strategy['focus_areas'].append('navigation_areas')
            strategy['priority_links'].extend(['dashboard', 'home', 'main'])
        
        # 避免的链接模式
        strategy['avoid_patterns'] = [
            r'admin',
            r'api',
            r'v[0-9]+',
            r'static',
            r'assets',
            r'css',
            r'js',
            r'images',
            r'download',
            r'report'
        ]
        
        return strategy
    
    async def _identify_test_targets(self, detected_features: List[BusinessFeature]) -> List[str]:
        """识别测试目标"""
        targets = []
        
        # 基于特征生成测试目标
        for feature in detected_features:
            feature_targets = []
            
            if feature.category == 'authentication':
                feature_targets.extend([
                    'login_page',
                    'authentication_flow',
                    'password_reset',
                    'registration_page'
                ])
            elif feature.category == 'navigation':
                feature_targets.extend([
                    'main_navigation',
                    'dashboard_access',
                    'page_transitions',
                    'menu_functionality'
                ])
            elif feature.category == 'data_entry':
                feature_targets.extend([
                    'form_submission',
                    'input_validation',
                    'data_persistence',
                    'form_navigation'
                ])
            elif feature.category == 'search':
                feature_targets.extend([
                    'search_functionality',
                    'filter_options',
                    'result_display',
                    'search_performance'
                ])
            elif feature.category == 'data_display':
                feature_targets.extend([
                    'data_table_view',
                    'record_management',
                    'pagination',
                    'data_export'
                ])
            elif feature.category == 'profile_settings':
                feature_targets.extend([
                    'profile_management',
                    'settings_update',
                    'password_change',
                    'preferences_save'
                ])
            
            targets.extend(feature_targets)
        
        # 去重
        return list(set(targets))
    
    async def _determine_priority_areas(self, detected_features: List[BusinessFeature]) -> List[str]:
        """确定优先级区域"""
        priority_areas = []
        
        # 按优先级排序的特征
        sorted_features = sorted(detected_features, key=lambda x: x.priority, reverse=True)
        
        for feature in sorted_features:
            if feature.priority >= 8:
                priority_areas.append(f"{feature.name}_high_priority")
            elif feature.priority >= 6:
                priority_areas.append(f"{feature.name}_medium_priority")
            elif feature.priority >= 4:
                priority_areas.append(f"{feature.name}_low_priority")
        
        return priority_areas
    
    async def _calculate_confidence_score(self, detected_features: List[BusinessFeature], description: str) -> float:
        """计算置信度分数"""
        if not detected_features:
            return 0.0
        
        # 基于特征数量和优先级计算
        total_priority = sum(feature.priority for feature in detected_features)
        max_possible_priority = len(detected_features) * 10
        
        # 基于描述长度和质量调整
        description_score = min(len(description) / 500, 1.0)  # 500字符为满分
        
        # 计算基础分数
        base_score = total_priority / max_possible_priority
        
        # 综合计算
        confidence_score = (base_score * 0.7 + description_score * 0.3)
        
        return min(confidence_score, 1.0)
    
    async def _generate_suggested_actions(self, detected_features: List[BusinessFeature]) -> List[str]:
        """生成建议操作"""
        actions = []
        
        # 基于检测到的特征生成建议
        if any(f.category == 'authentication' for f in detected_features):
            actions.append("配置测试用户账户和权限")
            actions.append("准备测试用的用户名和密码数据集")
        
        if any(f.category == 'data_entry' for f in detected_features):
            actions.append("准备表单测试数据集")
            actions.append("验证表单输入验证规则")
        
        if any(f.category == 'data_display' for f in detected_features):
            actions.append("准备测试数据集以确保有足够的数据展示")
            actions.append("配置分页和排序功能测试")
        
        if any(f.category == 'navigation' for f in detected_features):
            actions.append("验证所有导航链接的有效性")
            actions.append("测试页面间的状态保持")
        
        # 通用建议
        actions.extend([
            "确保测试环境与生产环境一致",
            "准备好测试数据管理策略",
            "配置测试结果的收集和分析",
            "制定异常情况的处理方案"
        ])
        
        return actions
    
    async def update_analysis_with_results(self, original_analysis: AnalysisResult, 
                                         exploration_results: Dict[str, Any]) -> AnalysisResult:
        """根据探索结果更新分析"""
        # 基于实际的探索结果调整分析
        updated_analysis = AnalysisResult(
            business_description=original_analysis.business_description,
            detected_features=original_analysis.detected_features,
            exploration_strategy=original_analysis.exploration_strategy,
            test_targets=original_analysis.test_targets,
            priority_areas=original_analysis.priority_areas,
            confidence_score=original_analysis.confidence_score,
            analysis_timestamp=original_analysis.analysis_timestamp,
            suggested_actions=original_analysis.suggested_actions
        )
        
        # 基于探索结果调整置信度
        if exploration_results.get('total_pages', 0) > 0:
            # 增加置信度如果成功探索了页面
            updated_analysis.confidence_score = min(
                updated_analysis.confidence_score + 0.1,
                1.0
            )
        
        # 基于发现的内容调整优先级
        discovered_content_types = exploration_results.get('content_types', [])
        if 'login' in discovered_content_types:
            # 如果发现了登录页面，提高认证功能的优先级
            for feature in updated_analysis.detected_features:
                if feature.category == 'authentication':
                    feature.priority = min(feature.priority + 2, 10)
        
        return updated_analysis


# 工厂函数
def create_business_analyzer() -> BusinessRequirementAnalyzer:
    """创建业务需求分析器实例"""
    return BusinessRequirementAnalyzer()