"""
页面布局分析器
识别页面功能区域（导航栏、侧边栏、内容区等）
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class PageRegion(Enum):
    """页面区域类型"""
    HEADER = "header"           # 页头/导航栏
    NAVIGATION = "navigation"   # 导航菜单
    SIDEBAR = "sidebar"         # 侧边栏
    MAIN_CONTENT = "main"        # 主要内容区
    CONTENT = "content"          # 内容区
    ARTICLE = "article"          # 文章区
    SECTION = "section"          # 分区
    ASIDE = "aside"            # 附加内容
    FOOTER = "footer"           # 页脚
    FORM = "form"               # 表单区
    TABLE = "table"             # 表格区
    LIST = "list"               # 列表区
    CARD = "card"               # 卡片区
    MODAL = "modal"             # 模态框
    DROPDOWN = "dropdown"       # 下拉菜单
    UNKNOWN = "unknown"         # 未知区域


@dataclass
class RegionInfo:
    """区域信息"""
    type: PageRegion
    selector: str
    text: str
    elements_count: int
    interactive_elements: List[str]
    attributes: Dict[str, Any]
    is_test_target: bool


class PageLayoutAnalyzer:
    """页面布局分析器"""

    def __init__(self):
        # 语义化标签映射
        self.semantic_tags = {
            "header": PageRegion.HEADER,
            "nav": PageRegion.NAVIGATION,
            "aside": PageRegion.ASIDE,
            "main": PageRegion.MAIN_CONTENT,
            "article": PageRegion.ARTICLE,
            "section": PageRegion.SECTION,
            "footer": PageRegion.FOOTER,
            "form": PageRegion.FORM,
            "table": PageRegion.TABLE,
        }

        # 常用类名模式
        self.class_patterns = {
            PageRegion.HEADER: ["header", "topbar", "navbar", "navigation", "nav"],
            PageRegion.NAVIGATION: ["nav", "menu", "navigation", "menu-bar"],
            PageRegion.SIDEBAR: ["sidebar", "side-bar", "aside", "left-panel", "right-panel"],
            PageRegion.MAIN_CONTENT: ["main", "content", "main-content", "content-area"],
            PageRegion.FOOTER: ["footer", "foot", "bottom", "site-footer"],
            PageRegion.CARD: ["card", "panel", "box", "widget"],
            PageRegion.FORM: ["form", "login-form", "register-form", "search-form"],
            PageRegion.MODAL: ["modal", "dialog", "popup", "overlay"],
            PageRegion.DROPDOWN: ["dropdown", "menu", "select-menu"],
        }

        # 交互元素标签
        self.interactive_tags = ["button", "a", "input", "select", "textarea"]

    def analyze_page(self, dom_content: str) -> Dict[str, Any]:
        """分析页面布局"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(dom_content, 'html.parser')

            regions = []

            # 检测语义化标签
            regions.extend(self._detect_semantic_regions(soup))

            # 检测基于类名的区域
            regions.extend(self._detect_class_based_regions(soup))

            # 检测重要功能区域
            login_form = self._detect_login_form(soup)
            if login_form:
                regions.append(login_form)

            search_form = self._detect_search_form(soup)
            if search_form:
                regions.append(search_form)

            # 生成报告
            report = {
                "total_regions": len(regions),
                "regions": [self._region_to_dict(r) for r in regions],
                "region_types": self._count_region_types(regions),
                "test_targets": [self._region_to_dict(r) for r in regions if r.is_test_target]
            }

            return report

        except Exception as e:
            print(f"Error analyzing page layout: {e}")
            return {
                "error": str(e),
                "regions": []
            }

    def _detect_semantic_regions(self, soup) -> List[RegionInfo]:
        """检测语义化HTML标签区域"""
        regions = []

        for tag_name, region_type in self.semantic_tags.items():
            elements = soup.find_all(tag_name)
            for element in elements:
                selector = self._generate_selector(element)
                text = element.get_text(strip=True)[:200]

                # 计算交互元素数量
                interactive = element.find_all(self.interactive_tags)

                region = RegionInfo(
                    type=region_type,
                    selector=selector,
                    text=text,
                    elements_count=len(element.find_all(True)),
                    interactive_elements=[self._generate_selector(e) for e in interactive[:5]],
                    attributes={k: v for k, v in element.attrs.items() if k != 'class'},
                    is_test_target=self._is_test_target(region_type, element)
                )
                regions.append(region)

        return regions

    def _detect_class_based_regions(self, soup) -> List[RegionInfo]:
        """检测基于类名的区域"""
        regions = []

        for region_type, patterns in self.class_patterns.items():
            for pattern in patterns:
                # 使用CSS选择器查找
                for attr in ['class', 'id']:
                    selector = f"[{attr}*='{pattern}']"
                    elements = soup.select(selector)

                    for element in elements:
                        # 避免重复
                        existing_selectors = {r.selector for r in regions}
                        element_selector = self._generate_selector(element)
                        if element_selector not in existing_selectors:
                            text = element.get_text(strip=True)[:200]
                            interactive = element.find_all(self.interactive_tags)

                            region = RegionInfo(
                                type=region_type,
                                selector=element_selector,
                                text=text,
                                elements_count=len(element.find_all(True)),
                                interactive_elements=[self._generate_selector(e) for e in interactive[:5]],
                                attributes={k: v for k, v in element.attrs.items() if k != 'class'},
                                is_test_target=self._is_test_target(region_type, element)
                            )
                            regions.append(region)

        return regions

    def _detect_login_form(self, soup) -> Optional[RegionInfo]:
        """检测登录表单区域"""
        # 查找包含密码输入框的表单
        forms = soup.find_all('form')

        for form in forms:
            password_input = form.find('input', {'type': 'password'})
            if password_input:
                # 找到登录表单
                selector = self._generate_selector(form)
                text = form.get_text(strip=True)[:200]

                region = RegionInfo(
                    type=PageRegion.FORM,
                    selector=selector,
                    text=text,
                    elements_count=len(form.find_all(True)),
                    interactive_elements=[self._generate_selector(e) for e in form.find_all(self.interactive_tags)],
                    attributes={k: v for k, v in form.attrs.items()},
                    is_test_target=True
                )
                return region

        return None

    def _detect_search_form(self, soup) -> Optional[RegionInfo]:
        """检测搜索表单区域"""
        # 查找包含搜索相关输入框的表单
        forms = soup.find_all('form')

        for form in forms:
            # 查找name或id包含search的输入框
            search_input = form.find('input', {'name': lambda x: x and 'search' in x.lower()})
            if not search_input:
                search_input = form.find('input', {'id': lambda x: x and 'search' in x.lower()})

            if search_input:
                selector = self._generate_selector(form)
                text = form.get_text(strip=True)[:200]

                region = RegionInfo(
                    type=PageRegion.FORM,
                    selector=selector,
                    text=text,
                    elements_count=len(form.find_all(True)),
                    interactive_elements=[self._generate_selector(e) for e in form.find_all(self.interactive_tags)],
                    attributes={k: v for k, v in form.attrs.items()},
                    is_test_target=True
                )
                return region

        return None

    def _is_test_target(self, region_type: PageRegion, element) -> bool:
        """判断区域是否为测试目标"""
        # 表单、导航、主要内容区通常是测试目标
        high_priority_regions = [
            PageRegion.FORM,
            PageRegion.NAVIGATION,
            PageRegion.MAIN_CONTENT,
            PageRegion.CARD,
            PageRegion.SIDEBAR
        ]

        return region_type in high_priority_regions

    def _generate_selector(self, element) -> str:
        """生成元素的CSS选择器"""
        # 优先使用ID
        if element.get('id'):
            return f"#{element.get('id')}"

        # 其次使用类名
        classes = element.get('class', [])
        if classes:
            return f".{'.'.join(classes[:2])}"  # 只使用前两个类名

        # 使用标签名
        return element.name if hasattr(element, 'name') else 'div'

    def _region_to_dict(self, region: RegionInfo) -> Dict[str, Any]:
        """将区域信息转换为字典"""
        return {
            "type": region.type.value,
            "selector": region.selector,
            "text": region.text,
            "elements_count": region.elements_count,
            "interactive_elements": region.interactive_elements,
            "attributes": region.attributes,
            "is_test_target": region.is_test_target
        }

    def _count_region_types(self, regions: List[RegionInfo]) -> Dict[str, int]:
        """统计各类型区域数量"""
        type_count = {}
        for region in regions:
            type_name = region.type.value
            type_count[type_name] = type_count.get(type_name, 0) + 1
        return type_count

    def get_priority_regions(self, dom_content: str) -> List[Dict[str, Any]]:
        """获取高优先级测试区域"""
        report = self.analyze_page(dom_content)
        priority_regions = []

        # 排序规则：is_test_target优先，然后按elements_count降序
        for region in report.get("regions", []):
            if region.get("is_test_target", False):
                priority_regions.append(region)

        # 按交互元素数量排序
        priority_regions.sort(
            key=lambda x: len(x.get("interactive_elements", [])),
            reverse=True
        )

        return priority_regions[:5]  # 返回前5个优先区域

    def suggest_test_actions(self, dom_content: str) -> List[Dict[str, Any]]:
        """基于页面布局建议测试操作"""
        suggestions = []
        report = self.analyze_page(dom_content)

        # 检测到的区域
        regions = report.get("regions", [])

        for region in regions:
            region_type = region.get("type")
            selector = region.get("selector")

            if region_type == "form":
                # 表单区域
                suggestions.append({
                    "action": "test_form",
                    "description": f"Test form at {selector}",
                    "selector": selector,
                    "priority": "high",
                    "region_type": region_type
                })

            elif region_type == "navigation" or region_type == "header":
                # 导航区域
                links = region.get("interactive_elements", [])
                if links:
                    suggestions.append({
                        "action": "test_navigation",
                        "description": f"Test navigation menu",
                        "selector": selector,
                        "priority": "medium",
                        "links_to_test": links[:5]  # 最多测试5个链接
                    })

            elif region_type == "main" or region_type == "content":
                # 主要内容区
                suggestions.append({
                    "action": "test_content",
                    "description": f"Test main content area",
                    "selector": selector,
                    "priority": "medium",
                    "region_type": region_type
                })

        # 去重
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            key = (suggestion.get("selector"), suggestion.get("action"))
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        return unique_suggestions
