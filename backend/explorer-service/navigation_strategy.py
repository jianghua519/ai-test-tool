"""
导航策略
定义网站探索的导航逻辑（BFS/DFS混合策略）
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import random


class NavigationStrategy(Enum):
    """导航策略类型"""
    BFS = "bfs"  # 广度优先
    DFS = "dfs"  # 深度优先
    MIXED = "mixed"  # 混合策略
    PRIORITY = "priority"  # 基于优先级


class NavigationPlanner:
    """导航规划器"""

    def __init__(self, strategy: NavigationStrategy = NavigationStrategy.MIXED):
        self.strategy = strategy
        self.priority_keywords = {
            "high": ["login", "signin", "sign-in", "register", "signup", "dashboard", "checkout", "cart"],
            "medium": ["search", "filter", "profile", "settings", "account"],
            "low": ["about", "contact", "help", "faq", "terms", "privacy"]
        }

    def calculate_link_priority(self, link_info: Dict[str, Any]) -> int:
        """计算链接的优先级分数"""
        score = 0
        url = link_info.get('url', '').lower()
        text = link_info.get('text', '').lower()

        # 基于关键词评分
        for level, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in url or keyword in text:
                    if level == 'high':
                        score += 10
                    elif level == 'medium':
                        score += 5
                    else:
                        score += 2

        # 链接类型评分
        link_type = link_info.get('type', '')
        if link_type == 'internal':
            score += 3
        elif link_type == 'external':
            score -= 5

        # URL深度评分（越浅越好）
        depth = link_info.get('depth', 0)
        score -= depth

        # 有文本的链接更好
        if text and len(text.strip()) > 0:
            score += 2

        return max(0, score)

    def sort_links_by_strategy(
        self,
        links: List[Dict[str, Any]],
        current_depth: int,
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """根据策略对链接进行排序"""

        if self.strategy == NavigationStrategy.BFS:
            # BFS：优先探索同一深度的页面
            return sorted(links, key=lambda x: (x.get('depth', 0), -self.calculate_link_priority(x)))

        elif self.strategy == NavigationStrategy.DFS:
            # DFS：优先探索更深的页面
            return sorted(links, key=lambda x: (-x.get('depth', 0), -self.calculate_link_priority(x)))

        elif self.strategy == NavigationStrategy.PRIORITY:
            # 基于优先级：按优先级分数排序
            return sorted(links, key=lambda x: -self.calculate_link_priority(x))

        else:  # MIXED
            # 混合策略：在当前深度优先，然后进入下一深度
            current_depth_links = [l for l in links if l.get('depth', 0) == current_depth]
            other_links = [l for l in links if l.get('depth', 0) != current_depth]

            # 当前深度按优先级排序
            current_depth_links = sorted(current_depth_links, key=lambda x: -self.calculate_link_priority(x))
            # 其他深度按深度和优先级排序
            other_links = sorted(other_links, key=lambda x: (x.get('depth', 0), -self.calculate_link_priority(x)))

            return current_depth_links + other_links

    def select_next_links(
        self,
        available_links: List[Dict[str, Any]],
        current_depth: int,
        max_depth: int,
        max_links: int = 5
    ) -> List[Dict[str, Any]]:
        """选择下一批要访问的链接"""

        # 过滤超出最大深度的链接
        valid_links = [l for l in available_links if l.get('depth', 0) <= max_depth]

        # 按策略排序
        sorted_links = self.sort_links_by_strategy(valid_links, current_depth, max_depth)

        # 选择前N个链接
        return sorted_links[:max_links]

    def should_explore_link(self, link_info: Dict[str, Any]) -> bool:
        """判断是否应该探索该链接"""

        url = link_info.get('url', '').lower()

        # 忽略特殊协议
        ignore_schemes = ['javascript:', 'mailto:', 'tel:', 'ftp:', 'data:']
        for scheme in ignore_schemes:
            if url.startswith(scheme):
                return False

        # 忽略特定路径
        ignore_paths = [
            '/logout', '/signout', '/logout.php',
            '/api/', '/ajax/', '/ajax'
        ]
        for path in ignore_paths:
            if path in url:
                return False

        # 忽略文件下载链接
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        for ext in file_extensions:
            if url.endswith(ext):
                return False

        return True

    def generate_test_suggestions(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于页面内容生成测试建议"""

        suggestions = []

        # 基于表单生成建议
        forms = page_data.get('forms', [])
        for form in forms:
            form_action = form.get('action', 'Unknown')
            fields = form.get('fields', [])

            if fields:
                # 登录表单检测
                if any('password' in f.get('type', '').lower() or 'password' in f.get('name', '').lower() or 'password' in f.get('id', '').lower() for f in fields):
                    suggestions.append({
                        "type": "form_test",
                        "description": f"Test login form at {form_action}",
                        "priority": "high",
                        "action": "submit_form",
                        "form": form
                    })

                # 注册表单检测
                if any('email' in f.get('type', '').lower() or 'email' in f.get('name', '').lower() or 'email' in f.get('id', '').lower() for f in fields):
                    suggestions.append({
                        "type": "form_test",
                        "description": f"Test registration form at {form_action}",
                        "priority": "high",
                        "action": "submit_form",
                        "form": form
                    })

                # 搜索表单检测
                if any('search' in f.get('name', '').lower() or 'search' in f.get('id', '').lower() for f in fields):
                    suggestions.append({
                        "type": "search_test",
                        "description": f"Test search functionality at {form_action}",
                        "priority": "medium",
                        "action": "search",
                        "form": form
                    })

        # 基于链接生成建议
        links = page_data.get('links', [])
        for link in links[:5]:  # 只考虑前5个链接
            link_text = link.get('text', '')
            link_url = link.get('url', '')

            if link_text:
                suggestions.append({
                    "type": "navigation_test",
                    "description": f"Navigate to: {link_text}",
                    "priority": "low",
                    "action": "navigate",
                    "url": link_url
                })

        return suggestions

    def get_strategy_description(self) -> str:
        """获取策略描述"""
        descriptions = {
            NavigationStrategy.BFS: "Breadth-First Search: Explores all pages at the current depth before going deeper",
            NavigationStrategy.DFS: "Depth-First Search: Explores as deep as possible before backtracking",
            NavigationStrategy.MIXED: "Mixed Strategy: Prioritizes current depth, then moves to next level",
            NavigationStrategy.PRIORITY: "Priority-Based: Prioritizes high-value pages (login, checkout, etc.)"
        }
        return descriptions.get(self.strategy, "Unknown strategy")


class AdaptiveNavigator:
    """自适应导航器，根据页面特征动态调整策略"""

    def __init__(self):
        self.planner = NavigationPlanner(NavigationStrategy.MIXED)
        self.strategy_history = []

    def detect_page_type(self, page_data: Dict[str, Any]) -> str:
        """检测页面类型"""
        links = page_data.get('links', [])
        forms = page_data.get('forms', [])

        if forms:
            return "form_page"
        elif len(links) > 20:
            return "navigation_page"
        elif len(links) <= 5:
            return "content_page"
        else:
            return "mixed_page"

    def adapt_strategy(self, page_data: Dict[str, Any]) -> NavigationStrategy:
        """根据页面类型自适应调整策略"""
        page_type = self.detect_page_type(page_data)

        if page_type == "form_page":
            # 表单页面：使用优先级策略，优先测试表单
            self.planner.strategy = NavigationStrategy.PRIORITY
        elif page_type == "navigation_page":
            # 导航页面：使用BFS，广泛探索
            self.planner.strategy = NavigationStrategy.BFS
        elif page_type == "content_page":
            # 内容页面：跳过，快速到达下一页
            self.planner.strategy = NavigationStrategy.DFS
        else:
            # 混合页面：使用混合策略
            self.planner.strategy = NavigationStrategy.MIXED

        self.strategy_history.append({
            "page_type": page_type,
            "strategy": self.planner.strategy.value
        })

        return self.planner.strategy
