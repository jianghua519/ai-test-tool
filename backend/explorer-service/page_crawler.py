"""
页面爬虫
用于自动发现页面中的链接、表单和可交互元素
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse
import re


@dataclass
class LinkInfo:
    """链接信息"""
    url: str
    text: str
    selector: str
    type: str  # 'internal', 'external', 'anchor'
    attributes: Dict[str, str]


@dataclass
class FormInfo:
    """表单信息"""
    action: str
    method: str
    selector: str
    fields: List[Dict[str, Any]]
    submit_button: Optional[str] = None


@dataclass
class InteractiveElement:
    """可交互元素信息"""
    tag: str
    selector: str
    text: str
    type: Optional[str]
    attributes: Dict[str, str]
    is_clickable: bool
    is_input: bool


class PageCrawler:
    """页面爬虫，用于发现页面元素"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.discovered_elements: Dict[str, Any] = {
            "links": [],
            "forms": [],
            "interactive_elements": []
        }

    def is_internal_link(self, url: str) -> bool:
        """检查是否为内部链接"""
        parsed = urlparse(url)
        return parsed.netloc == "" or parsed.netloc == self.base_domain

    def normalize_url(self, url: str) -> Optional[str]:
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
            absolute_url = urljoin(self.base_url, url)

            # 移除fragment和部分query参数
            parsed = urlparse(absolute_url)
            # 保留重要的query参数
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

    def should_ignore_url(self, url: str) -> bool:
        """判断URL是否应该被忽略"""
        ignore_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|tar|gz)$',
            r'#',
            r'^javascript:',
            r'^mailto:',
            r'^tel:',
            r'/logout',
            r'/signout',
        ]

        for pattern in ignore_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    async def crawl_links(self, page_content: str) -> List[LinkInfo]:
        """爬取页面中的链接"""
        links = []

        # 这里使用简化的实现，实际应该使用Playwright的API
        # 这是一个伪实现，实际需要与Playwright集成

        # 模拟发现的链接
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(page_content, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                normalized = self.normalize_url(href)

                if normalized and not self.should_ignore_url(normalized):
                    link_type = 'internal' if self.is_internal_link(normalized) else 'external'

                    # 生成CSS选择器（简化）
                    selector = self._generate_selector(a_tag)

                    link_info = LinkInfo(
                        url=normalized,
                        text=a_tag.get_text(strip=True),
                        selector=selector,
                        type=link_type,
                        attributes={k: v for k, v in a_tag.attrs.items() if k != 'href'}
                    )

                    if link_type == 'internal':
                        links.append(link_info)

        except Exception as e:
            print(f"Error crawling links: {e}")

        return links

    async def crawl_forms(self, page_content: str) -> List[FormInfo]:
        """爬取页面中的表单"""
        forms = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')

            for form in soup.find_all('form'):
                action = form.get('action', '')
                method = form.get('method', 'GET').upper()

                # 标准化action URL
                normalized_action = self.normalize_url(action)
                if not normalized_action:
                    normalized_action = self.base_url

                # 提取表单字段
                fields = []
                for input_tag in form.find_all(['input', 'select', 'textarea']):
                    field_type = input_tag.get('type', 'text')
                    field_name = input_tag.get('name', '')
                    field_id = input_tag.get('id', '')

                    if field_name or field_id:
                        fields.append({
                            'type': field_type,
                            'name': field_name,
                            'id': field_id,
                            'selector': self._generate_selector(input_tag)
                        })

                # 查找提交按钮
                submit_button = None
                for button in form.find_all(['button', 'input']):
                    if button.get('type') == 'submit' or button.get('type') is None:
                        if button.name == 'button' or (button.get('value') or button.get_text()):
                            submit_button = self._generate_selector(button)
                            break

                # 生成表单选择器
                selector = self._generate_selector(form)

                form_info = FormInfo(
                    action=normalized_action,
                    method=method,
                    selector=selector,
                    fields=fields,
                    submit_button=submit_button
                )

                forms.append(form_info)

        except Exception as e:
            print(f"Error crawling forms: {e}")

        return forms

    async def crawl_interactive_elements(self, page) -> List[InteractiveElement]:
        """爬取页面中的可交互元素"""
        elements = []

        # 定义可交互的元素类型
        interactive_tags = ['a', 'button', 'input', 'select', 'textarea']
        interactive_types = ['button', 'submit', 'reset', 'checkbox', 'radio', 'file']

        try:
            # 这里需要传入Playwright的Page对象
            # 实际实现应该使用Playwright的API
            pass

        except Exception as e:
            print(f"Error crawling interactive elements: {e}")

        return elements

    def _generate_selector(self, element) -> str:
        """生成元素的CSS选择器"""
        # 简化的选择器生成逻辑
        # 实际应该使用更智能的方法

        id_attr = element.get('id')
        if id_attr:
            return f"#{id_attr}"

        class_attr = element.get('class')
        if class_attr:
            classes = class_attr.split()
            if classes:
                return f".{'.'.join(classes)}"

        tag = element.name if hasattr(element, 'name') else 'div'
        return tag

    async def analyze_page(self, page, url: str) -> Dict[str, Any]:
        """分析页面并返回发现的所有元素"""
        result = {
            "url": url,
            "links": [],
            "forms": [],
            "interactive_elements": []
        }

        try:
            # 获取页面内容
            content = await page.content()

            # 爬取链接
            result["links"] = await self.crawl_links(content)

            # 爬取表单
            result["forms"] = await self.crawl_forms(content)

            # 爬取可交互元素
            result["interactive_elements"] = await self.crawl_interactive_elements(page)

            # 统计信息
            result["stats"] = {
                "links_count": len(result["links"]),
                "forms_count": len(result["forms"]),
                "interactive_elements_count": len(result["interactive_elements"]),
                "internal_links": sum(1 for l in result["links"] if l.type == 'internal'),
                "external_links": sum(1 for l in result["links"] if l.type == 'external')
            }

        except Exception as e:
            print(f"Error analyzing page: {e}")
            result["error"] = str(e)

        return result
