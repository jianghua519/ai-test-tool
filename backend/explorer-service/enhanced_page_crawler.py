"""
增强页面爬虫 - 支持BFS/DFS导航策略和智能链接发现
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse
import re
import asyncio
from abc import ABC, abstractmethod
import json
import time
from collections import deque
import logging

from playwright.async_api import Page, BrowserContext, ElementHandle


logger = logging.getLogger(__name__)


@dataclass
class PageAnalysisResult:
    """页面分析结果"""
    url: str
    title: str
    links: List[Dict[str, Any]] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    interactive_elements: List[Dict[str, Any]] = field(default_factory=list)
    meta_tags: Dict[str, str] = field(default_factory=dict)
    page_features: Dict[str, Any] = field(default_factory=dict)
    content_type: str = "unknown"
    response_code: int = 200
    load_time: float = 0.0
    page_size: int = 0


class NavigationStrategy(ABC):
    """导航策略抽象基类"""
    
    @abstractmethod
    async def should_follow_link(self, url: str, page: Page, strategy_config: Dict[str, Any]) -> bool:
        """判断是否应该跟随链接"""
        pass
    
    @abstractmethod
    async def get_priority_links(self, links: List[Dict[str, Any]], page: Page) -> List[Dict[str, Any]]:
        """获取优先级最高的链接"""
        pass
    
    @abstractmethod
    async def should_stop_exploration(self, stats: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """判断是否应该停止探索"""
        pass


class BFSNavigationStrategy(NavigationStrategy):
    """广度优先搜索导航策略"""
    
    def __init__(self, max_depth: int = 3, max_pages: int = 20):
        self.max_depth = max_depth
        self.max_pages = max_pages
    
    async def should_follow_link(self, url: str, page: Page, strategy_config: Dict[str, Any]) -> bool:
        """BFS策略：优先发现所有链接"""
        # 基本URL过滤
        if not self._is_valid_url(url):
            return False
        
        # 检查重复URL
        visited_urls = strategy_config.get('visited_urls', set())
        if url in visited_urls:
            return False
        
        # BFS深度控制
        current_depth = strategy_config.get('current_depth', 0)
        if current_depth >= self.max_depth:
            return False
        
        return True
    
    async def get_priority_links(self, links: List[Dict[str, Any]], page: Page) -> List[Dict[str, Any]]:
        """BFS策略：按原始顺序优先"""
        return links
    
    async def should_stop_exploration(self, stats: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """BFS停止条件"""
        return stats.get('total_pages', 0) >= self.max_pages


class DFSNavigationStrategy(NavigationStrategy):
    """深度优先搜索导航策略"""
    
    def __init__(self, max_depth: int = 5, max_pages: int = 20):
        self.max_depth = max_depth
        self.max_pages = max_pages
    
    async def should_follow_link(self, url: str, page: Page, strategy_config: Dict[str, Any]) -> bool:
        """DFS策略：优先深入探索"""
        if not self._is_valid_url(url):
            return False
        
        visited_urls = strategy_config.get('visited_urls', set())
        if url in visited_urls:
            return False
        
        current_depth = strategy_config.get('current_depth', 0)
        if current_depth >= self.max_depth:
            return False
        
        # DFS优先选择看起来像主要导航的链接
        link_text = url.lower()
        priority_signals = [
            r'(dashboard|profile|settings|home|main|primary)',
            r'\/[a-z]+$',
        ]
        
        has_priority = any(re.search(pattern, link_text) for pattern in priority_signals)
        
        return has_priority or current_depth < 2
    
    async def get_priority_links(self, links: List[Dict[str, Any]], page: Page) -> List[Dict[str, Any]]:
        """DFS策略：优先选择重要的链接"""
        def get_priority_score(link: Dict[str, Any]) -> int:
            url = link.get('url', '').lower()
            text = link.get('text', '').lower()
            
            score = 0
            
            # 基本链接类型优先级
            if any(keyword in text for keyword in ['login', 'signin', 'auth']):
                score += 100
            elif any(keyword in url for keyword in ['dashboard', 'home', 'main']):
                score += 80
            elif any(keyword in text for keyword in ['profile', 'account', 'settings']):
                score += 60
            elif len(text.strip()) > 10:  # 长文本链接
                score += 20
            
            # URL结构优先级
            if url.endswith('/'):
                score += 10
            
            # 避免外部链接
            if link.get('is_external', False):
                score -= 50
            
            return score
        
        return sorted(links, key=get_priority_score, reverse=True)
    
    async def should_stop_exploration(self, stats: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """DFS停止条件"""
        return stats.get('total_pages', 0) >= self.max_pages


class AdaptiveNavigationStrategy(NavigationStrategy):
    """自适应混合导航策略"""
    
    def __init__(self, max_depth: int = 4, max_pages: int = 30):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.detection_threshold = 0.7
        
    async def should_follow_link(self, url: str, page: Page, strategy_config: Dict[str, Any]) -> bool:
        """自适应策略：根据页面内容动态选择"""
        if not self._is_valid_url(url):
            return False
        
        visited_urls = strategy_config.get('visited_urls', set())
        if url in visited_urls:
            return False
        
        current_depth = strategy_config.get('current_depth', 0)
        if current_depth >= self.max_depth:
            return False
        
        # 页面分析
        page_features = strategy_config.get('page_features', {})
        content_type = page_features.get('content_type', 'unknown')
        
        # 根据内容类型调整策略
        if content_type == 'dashboard':
            # 仪表盘页面使用BFS
            return self._is_valid_dashboard_link(url, page)
        elif content_type == 'list':
            # 列表页面使用深度优先
            return self._is_valid_list_link(url, page)
        else:
            # 通用页面混合策略
            return await self._should_follow_adaptive(url, page, strategy_config)
    
    async def get_priority_links(self, links: List[Dict[str, Any]], page: Page) -> List[Dict[str, Any]]:
        """自适应策略：智能排序链接"""
        # 计算每个链接的重要性分数
        scored_links = []
        for link in links:
            score = await self._calculate_link_importance(link, page)
            scored_links.append((score, link))
        
        # 按分数排序
        scored_links.sort(key=lambda x: x[0], reverse=True)
        return [link for score, link in scored_links]
    
    async def should_stop_exploration(self, stats: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """自适应停止条件"""
        # 动态调整停止条件
        if stats.get('total_pages', 0) >= self.max_pages:
            return True
        
        # 如果发现大量重复内容，提前停止
        duplication_rate = stats.get('content_duplication_rate', 0)
        if duplication_rate > 0.8:
            return True
        
        return False
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL有效性"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def _is_valid_dashboard_link(self, url: str, page: Page) -> bool:
        """验证仪表盘链接"""
        return self._is_valid_url(url)
    
    def _is_valid_list_link(self, url: str, page: Page) -> bool:
        """验证列表页面链接"""
        return self._is_valid_url(url) and not url.endswith(('edit', 'delete', 'create'))
    
    async def _should_follow_adaptive(self, url: str, page: Page, strategy_config: Dict[str, Any]) -> bool:
        """自适应链接判断"""
        # 基于链接文本和URL的启发式规则
        link_text = url.lower()
        
        # 优先选择这些类型的链接
        priority_patterns = [
            r'login|signin|auth',
            r'dashboard|home|main',
            r'profile|account',
            r'settings|config',
            r'create|new',
            r'edit|modify',
        ]
        
        for pattern in priority_patterns:
            if re.search(pattern, link_text):
                return True
        
        # 检查链接在页面中的位置和可见性
        try:
            elements = await page.query_selector_all(f'a[href="{url}"], button[href="{url}"]')
            for element in elements:
                # 检查元素是否可见
                if await element.is_visible():
                    # 检查是否在主要内容区域
                    bounding_box = await element.bounding_box()
                    if bounding_box and bounding_box['height'] > 0 and bounding_box['width'] > 0:
                        return True
        except:
            pass
        
        return False
    
    async def _calculate_link_importance(self, link: Dict[str, Any], page: Page) -> float:
        """计算链接重要性分数"""
        url = link.get('url', '')
        text = link.get('text', '')
        title = link.get('title', '')
        
        score = 0.0
        
        # URL特征
        if any(keyword in url.lower() for keyword in ['login', 'auth', 'signin']):
            score += 0.9
        elif any(keyword in url.lower() for keyword in ['dashboard', 'home', 'main']):
            score += 0.8
        elif any(keyword in url.lower() for keyword in ['profile', 'account']):
            score += 0.7
        elif any(keyword in url.lower() for keyword in ['settings', 'config']):
            score += 0.6
        else:
            score += 0.3
        
        # 文本特征
        if text:
            text_lower = text.lower()
            if len(text_lower) > 20:  # 长文本链接
                score += 0.2
            if any(keyword in text_lower for keyword in ['login', 'sign in', 'get started']):
                score += 0.5
        
        # 位置特征（如果页面已加载）
        try:
            elements = await page.query_selector_all(f'a[href="{url}"], button[href="{url}"]')
            for element in elements:
                if await element.is_visible():
                    # 检查是否在主要内容区域
                    element_rect = await element.bounding_box()
                    page_rect = await page.bounding_box()
                    
                    if element_rect and page_rect:
                        # 计算相对位置
                        relative_x = element_rect['x'] / page_rect['width']
                        relative_y = element_rect['y'] / page_rect['height']
                        
                        # 主要内容区域通常在中间50%区域
                        if 0.25 <= relative_x <= 0.75 and 0.25 <= relative_y <= 0.75:
                            score += 0.2
        except:
            pass
        
        return min(score, 1.0)


class EnhancedPageCrawler:
    """增强页面爬虫，支持多种导航策略"""
    
    def __init__(self, strategy: NavigationStrategy):
        self.strategy = strategy
        self.session_context: Optional[BrowserContext] = None
        self.browser: Optional[Browser] = None
        
    async def initialize(self) -> None:
        """初始化浏览器环境"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = async_playwright()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            self.session_context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.session_context:
                await self.session_context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def crawl_page(self, url: str, strategy_config: Dict[str, Any] = None) -> PageAnalysisResult:
        """爬取单个页面"""
        if strategy_config is None:
            strategy_config = {}
        
        start_time = time.time()
        result = PageAnalysisResult(url=url)
        
        try:
            if not self.session_context:
                await self.initialize()
            
            page = await self.session_context.new_page()
            
            # 设置页面超时和拦截器
            await page.set_default_timeout(30000)
            
            # 页面加载
            response = await page.goto(url, wait_until='networkidle', timeout=15000)
            
            if response:
                result.response_code = response.status
                result.content_type = response.headers.get('content-type', 'unknown')
                result.page_size = len(await response.text())
            
            # 等待页面稳定
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # 获取页面信息
            result.title = await page.title()
            
            # 解析页面内容
            await self._analyze_page_content(page, result)
            
            # 分析页面特征
            await self._analyze_page_features(page, result, strategy_config)
            
            result.load_time = time.time() - start_time
            
            # 清理页面
            await page.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error crawling page {url}: {e}")
            result.response_code = 500
            result.error = str(e)
            return result
    
    async def _analyze_page_content(self, page: Page, result: PageAnalysisResult) -> None:
        """分析页面内容"""
        try:
            # 提取链接
            await self._extract_links(page, result)
            
            # 提取表单
            await self._extract_forms(page, result)
            
            # 提取可交互元素
            await self._extract_interactive_elements(page, result)
            
            # 提取meta标签
            await self._extract_meta_tags(page, result)
            
        except Exception as e:
            logger.error(f"Error analyzing page content: {e}")
    
    async def _extract_links(self, page: Page, result: PageAnalysisResult) -> None:
        """提取页面链接"""
        try:
            # 使用多种方法提取链接
            link_selectors = [
                'a[href]',
                'area[href]',
                '[role="link"]',
                'button:not([type="submit"])',  # 排除提交按钮
            ]
            
            for selector in link_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if not href:
                            continue
                        
                        # 标准化链接
                        normalized_url = self._normalize_url(href)
                        if not normalized_url:
                            continue
                        
                        # 检查链接类型
                        is_external = await self._is_external_link(normalized_url)
                        
                        # 获取链接文本
                        text = await element.inner_text()
                        text = text.strip() if text else ''
                        
                        # 获取标题
                        title = await element.get_attribute('title')
                        
                        # 获取链接的重要性分数
                        importance = await self._calculate_link_importance(page, element, normalized_url)
                        
                        link_info = {
                            'url': normalized_url,
                            'text': text[:200],  # 限制文本长度
                            'title': title or '',
                            'is_external': is_external,
                            'importance': importance,
                            'element_count': len(await page.query_selector_all(f'a[href="{href}"], area[href="{href}"]')),
                            'normalized': True
                        }
                        
                        # 检查是否已存在相同链接
                        if not any(link['url'] == normalized_url for link in result.links):
                            result.links.append(link_info)
                        
                    except Exception as e:
                        logger.warning(f"Error processing link element: {e}")
                        continue
            
            # 清理和排序链接
            result.links = await self.strategy.get_priority_links(result.links, page)
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
    
    async def _extract_forms(self, page: Page, result: PageAnalysisResult) -> None:
        """提取表单信息"""
        try:
            forms = await page.query_selector_all('form')
            
            for form in forms:
                try:
                    action = await form.get_attribute('action') or ''
                    method = (await form.get_attribute('method') or 'get').lower()
                    
                    # 提取表单字段
                    fields = []
                    inputs = await form.query_selector_all('input, select, textarea')
                    
                    for input_field in inputs:
                        try:
                            field_type = await input_field.get_attribute('type') or 'text'
                            field_name = await input_field.get_attribute('name') or ''
                            field_id = await input_field.get_attribute('id') or ''
                            field_placeholder = await input_field.get_attribute('placeholder') or ''
                            field_required = await input_field.get_attribute('required') is not None
                            
                            field_info = {
                                'type': field_type,
                                'name': field_name,
                                'id': field_id,
                                'placeholder': field_placeholder,
                                'required': field_required,
                                'selector': await input_field.evaluate('el => el.outerHTML')
                            }
                            
                            fields.append(field_info)
                            
                        except Exception as e:
                            logger.warning(f"Error processing form field: {e}")
                            continue
                    
                    # 查找提交按钮
                    submit_buttons = await form.query_selector_all('button[type="submit"], input[type="submit"]')
                    submit_button = None
                    if submit_buttons:
                        first_button = submit_buttons[0]
                        submit_button = await first_button.inner_text()
                        submit_button = submit_button.strip() if submit_button else 'Submit'
                    
                    form_info = {
                        'action': action,
                        'method': method,
                        'selector': await form.evaluate('el => el.outerHTML'),
                        'fields_count': len(fields),
                        'fields': fields,
                        'has_submit_button': submit_button is not None,
                        'submit_button_text': submit_button
                    }
                    
                    result.forms.append(form_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing form: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting forms: {e}")
    
    async def _extract_interactive_elements(self, page: Page, result: PageAnalysisResult) -> None:
        """提取可交互元素"""
        try:
            interactive_selectors = [
                'button',
                'input:not([type="hidden"])',
                'select',
                'textarea',
                'a[href]',
                '[role="button"]',
                '[role="link"]',
                '[onclick]',
                '[addEventListener]'
            ]
            
            for selector in interactive_selectors:
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    try:
                        tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                        
                        if not await element.is_visible():
                            continue
                        
                        # 获取元素选择器
                        element_id = await element.get_attribute('id')
                        element_class = await element.get_attribute('class')
                        
                        # 生成CSS选择器
                        css_selector = await self._generate_css_selector(element)
                        
                        element_info = {
                            'tag': tag_name,
                            'selector': css_selector,
                            'text': (await element.inner_text()).strip()[:100],
                            'type': await element.get_attribute('type'),
                            'attributes': await self._get_element_attributes(element),
                            'is_clickable': True,  # 简化处理
                            'is_input': tag_name in ['input', 'select', 'textarea'],
                            'element_id': element_id,
                            'element_class': element_class
                        }
                        
                        result.interactive_elements.append(element_info)
                        
                    except Exception as e:
                        logger.warning(f"Error processing interactive element: {e}")
                        continue
            
            # 去重
            unique_elements = []
            seen_selectors = set()
            
            for element in result.interactive_elements:
                selector = element['selector']
                if selector not in seen_selectors:
                    unique_elements.append(element)
                    seen_selectors.add(selector)
            
            result.interactive_elements = unique_elements
            
        except Exception as e:
            logger.error(f"Error extracting interactive elements: {e}")
    
    async def _extract_meta_tags(self, page: Page, result: PageAnalysisResult) -> None:
        """提取meta标签"""
        try:
            meta_tags = await page.query_selector_all('meta')
            
            for meta in meta_tags:
                try:
                    name = await meta.get_attribute('name') or await meta.get_attribute('property')
                    content = await meta.get_attribute('content')
                    
                    if name and content:
                        result.meta_tags[name] = content
                        
                except Exception as e:
                    logger.warning(f"Error processing meta tag: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting meta tags: {e}")
    
    async def _analyze_page_features(self, page: Page, result: PageAnalysisResult, strategy_config: Dict[str, Any]) -> None:
        """分析页面特征"""
        try:
            # 检测页面类型
            page_type = await self._detect_page_type(page)
            result.page_features['page_type'] = page_type
            
            # 检测登录特征
            has_login = await self._detect_login_features(page)
            result.page_features['has_login'] = has_login
            
            # 检测表单特征
            form_count = len(result.forms)
            result.page_features['form_count'] = form_count
            
            # 检测导航结构
            nav_structure = await self._analyze_navigation_structure(page)
            result.page_features['navigation_structure'] = nav_structure
            
            # 检测内容类型
            content_type = await self._detect_content_type(page)
            result.page_features['content_type'] = content_type
            
            # 更新策略配置中的页面特征
            strategy_config['page_features'] = result.page_features
            
        except Exception as e:
            logger.error(f"Error analyzing page features: {e}")
    
    async def _detect_page_type(self, page: Page) -> str:
        """检测页面类型"""
        try:
            # 检查标题
            title = await page.title().lower()
            if any(keyword in title for keyword in ['login', 'signin', 'auth']):
                return 'login'
            elif any(keyword in title for keyword in ['dashboard', 'home', 'main']):
                return 'dashboard'
            elif any(keyword in title for keyword in ['settings', 'config', 'preferences']):
                return 'settings'
            elif any(keyword in title for keyword in ['form', 'register', 'signup']):
                return 'form'
            elif any(keyword in title for keyword in ['search', 'find', 'browse']):
                return 'search'
            
            # 检查URL模式
            url = page.url.lower()
            if any(pattern in url for pattern in ['/login/', '/signin/', '/auth/']):
                return 'login'
            elif any(pattern in url for pattern in ['/dashboard/', '/home/', '/main/']):
                return 'dashboard'
            
            # 检查页面结构
            if await page.query_selector('form'):
                return 'form'
            elif await page.query_selector('[data-testid="dashboard"]'):
                return 'dashboard'
            elif await page.query_selector('input[type="search"]'):
                return 'search'
            elif await page.query_selector('table'):
                return 'list'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error detecting page type: {e}")
            return 'unknown'
    
    async def _detect_login_features(self, page: Page) -> bool:
        """检测登录特征"""
        try:
            login_selectors = [
                'input[type="password"]',
                'input[name*="password"]',
                'input[id*="password"]',
                'input[placeholder*="password"]',
                'input[type="email"]',
                'input[name*="email"]',
                'input[id*="email"]',
                'input[placeholder*="email"]',
                'input[type="text"]',
                'input[name*="username"]',
                'input[id*="username"]',
                'input[placeholder*="username"]',
            ]
            
            for selector in login_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting login features: {e}")
            return False
    
    async def _analyze_navigation_structure(self, page: Page) -> Dict[str, Any]:
        """分析导航结构"""
        try:
            nav_elements = await page.query_selector_all('nav, [role="navigation"], .nav, .navigation')
            
            nav_info = {
                'nav_count': len(nav_elements),
                'has_main_navigation': len(nav_elements) > 0,
                'navigation_links': []
            }
            
            for nav in nav_elements:
                try:
                    links = await nav.query_selector_all('a[href]')
                    for link in links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if href and text:
                            nav_info['navigation_links'].append({
                                'url': href,
                                'text': text.strip()
                            })
                except Exception as e:
                    logger.warning(f"Error analyzing navigation: {e}")
                    continue
            
            return nav_info
            
        except Exception as e:
            logger.error(f"Error analyzing navigation structure: {e}")
            return {'nav_count': 0, 'has_main_navigation': False, 'navigation_links': []}
    
    async def _detect_content_type(self, page: Page) -> str:
        """检测内容类型"""
        try:
            # 检查主要内容区域
            main_content_selectors = [
                'main',
                '[role="main"]',
                '.main',
                '.content',
                '[data-testid="content"]',
                '.container'
            ]
            
            for selector in main_content_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        # 获取元素内容
                        content = await element.inner_text()
                        
                        # 分析内容特征
                        if 'login' in content.lower():
                            return 'login'
                        elif any(keyword in content.lower() for keyword in ['dashboard', 'overview', 'summary']):
                            return 'dashboard'
                        elif any(keyword in content.lower() for keyword in ['list', 'table', 'grid']):
                            return 'list'
                        elif any(keyword in content.lower() for keyword in ['form', 'input', 'submit']):
                            return 'form'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error detecting content type: {e}")
            return 'unknown'
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """标准化URL"""
        try:
            # 处理锚点链接
            if url.startswith('#'):
                return None
            
            # 处理javascript链接
            if url.lower().startswith('javascript:'):
                return None
            
            # 处理mailto/tel等特殊链接
            if re.match(r'^(mailto|tel|sms|ftp):', url.lower()):
                return None
            
            # 相对URL转绝对URL
            base_url = "http://localhost"  # 需要传入实际的base_url
            absolute_url = urljoin(base_url, url)
            
            # 移除fragment
            parsed = urlparse(absolute_url)
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                None,
                parsed.query,
                None
            ))
            
            # 只允许http和https
            if parsed.scheme not in ['http', 'https']:
                return None
            
            return clean_url
            
        except Exception:
            return None
    
    async def _is_external_link(self, url: str) -> bool:
        """判断是否为外部链接"""
        try:
            parsed = urlparse(url)
            return parsed.netloc != "localhost"  # 需要比较实际的域名
        except:
            return True
    
    async def _calculate_link_importance(self, page: Page, element: ElementHandle, url: str) -> float:
        """计算链接重要性"""
        importance = 0.0
        
        try:
            # 检查链接文本
            text = await element.inner_text()
            if text:
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ['login', 'sign in', 'get started']):
                    importance += 0.8
                elif any(keyword in text_lower for keyword in ['dashboard', 'home', 'main']):
                    importance += 0.7
                elif any(keyword in text_lower for keyword in ['profile', 'account']):
                    importance += 0.6
                elif len(text_lower) > 20:  # 长文本
                    importance += 0.2
            
            # 检查位置
            bounding_box = await element.bounding_box()
            if bounding_box and bounding_box['height'] > 0 and bounding_box['width'] > 0:
                # 检查是否在主要内容区域
                page_box = await page.bounding_box()
                if page_box:
                    relative_x = bounding_box['x'] / page_box['width']
                    relative_y = bounding_box['y'] / page_box['height']
                    
                    if 0.25 <= relative_x <= 0.75 and 0.25 <= relative_y <= 0.75:
                        importance += 0.1
            
            # 检查是否在新标签页打开
            target = await element.get_attribute('target')
            if target and target == '_blank':
                importance += 0.1
            
            # 检查是否是外部链接
            if await self._is_external_link(url):
                importance -= 0.3
            
            return min(importance, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating link importance: {e}")
            return 0.0
    
    async def _generate_css_selector(self, element: ElementHandle) -> str:
        """生成CSS选择器"""
        try:
            # 简化的选择器生成
            selector_parts = []
            
            # 添加标签名
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            selector_parts.append(tag_name)
            
            # 添加ID
            element_id = await element.get_attribute('id')
            if element_id:
                selector_parts.append(f'#{element_id}')
            
            # 添加类名
            element_class = await element.get_attribute('class')
            if element_class:
                classes = element_class.split()
                for cls in classes:
                    selector_parts.append(f'.{cls}')
            
            return ' '.join(selector_parts)
            
        except Exception as e:
            logger.error(f"Error generating CSS selector: {e}")
            return 'unknown'
    
    async def _get_element_attributes(self, element: ElementHandle) -> Dict[str, str]:
        """获取元素属性"""
        try:
            attributes = {}
            
            # 获取常见的属性
            common_attrs = ['type', 'name', 'id', 'class', 'placeholder', 'value', 'href', 'src']
            
            for attr in common_attrs:
                value = await element.get_attribute(attr)
                if value:
                    attributes[attr] = value
            
            return attributes
            
        except Exception as e:
            logger.error(f"Error getting element attributes: {e}")
            return {}


# 工厂函数
def create_crawler(strategy_type: str = 'adaptive', **kwargs) -> EnhancedPageCrawler:
    """创建爬虫实例"""
    if strategy_type == 'bfs':
        strategy = BFSNavigationStrategy(**kwargs)
    elif strategy_type == 'dfs':
        strategy = DFSNavigationStrategy(**kwargs)
    else:  # adaptive
        strategy = AdaptiveNavigationStrategy(**kwargs)
    
    return EnhancedPageCrawler(strategy)