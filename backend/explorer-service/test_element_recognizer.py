"""
元素识别器测试
测试交互元素智能识别功能
"""

import pytest
from element_recognizer import ElementRecognizer, ElementType, SelectorGenerator
from form_field_detector import FormFieldDetector, FieldType
from page_layout_analyzer import PageLayoutAnalyzer, PageRegion


class TestSelectorGenerator:
    """选择器生成器测试"""

    def test_generate_id_selector(self):
        """测试生成ID选择器"""
        generator = SelectorGenerator()

        element_data = {
            "tag": "div",
            "id": "test-id",
            "class": [],
            "name": "",
            "type": ""
        }

        selectors = generator.generate_selectors(element_data)
        assert "#test-id" in selectors

    def test_generate_class_selector(self):
        """测试生成类选择器"""
        generator = SelectorGenerator()

        element_data = {
            "tag": "div",
            "id": "",
            "class": ["container", "main"],
            "name": "",
            "type": ""
        }

        selectors = generator.generate_selectors(element_data)
        assert ".container.main" in selectors

    def test_generate_data_testid_selector(self):
        """测试生成data-testid选择器"""
        generator = SelectorGenerator()

        element_data = {
            "tag": "button",
            "id": "",
            "class": [],
            "data-testid": "submit-btn",
            "name": "",
            "type": ""
        }

        selectors = generator.generate_selectors(element_data)
        assert "[data-testid='submit-btn']" in selectors

    def test_selector_scoring(self):
        """测试选择器打分"""
        generator = SelectorGenerator()

        # ID选择器应该有最高分
        id_score = generator.score_selector("#test-id")

        # 类选择器应该有中等分
        class_score = generator.score_selector(".test-class")

        # 标签选择器应该有最低分
        tag_score = generator.score_selector("div")

        assert id_score > class_score > tag_score

    def test_get_best_selector(self):
        """测试获取最佳选择器"""
        generator = SelectorGenerator()

        selectors = ["div", ".test-class", "#test-id", "[data-testid='test']"]

        best = generator.get_best_selector(selectors)

        # ID选择器应该是最佳的
        assert best == "#test-id"


class TestElementRecognizer:
    """元素识别器测试"""

    def test_initialization(self):
        """测试识别器初始化"""
        recognizer = ElementRecognizer()
        assert len(recognizer.interactive_tags) > 0
        assert len(recognizer.type_patterns) > 0

    def test_identify_button(self):
        """测试识别按钮"""
        recognizer = ElementRecognizer()

        element_data = {
            "tag": "button",
            "text": "Submit",
            "id": "submit-btn",
            "name": "",
            "class": [],
            "aria-label": ""
        }

        # 使用mock元素
        from bs4 import BeautifulSoup
        element = BeautifulSoup('<button id="submit-btn">Submit</button>', 'html.parser').find('button')

        recognized = recognizer.recognize_element(element)

        assert recognized.type == ElementType.BUTTON
        assert recognized.is_clickable
        assert recognized.is_interactive

    def test_identify_link(self):
        """测试识别链接"""
        recognizer = ElementRecognizer()

        from bs4 import BeautifulSoup
        element = BeautifulSoup('<a href="/page">Link</a>', 'html.parser').find('a')

        recognized = recognizer.recognize_element(element)

        assert recognized.type == ElementType.LINK
        assert recognized.is_clickable

    def test_identify_input_text(self):
        """测试识别文本输入框"""
        recognizer = ElementRecognizer()

        from bs4 import BeautifulSoup
        element = BeautifulSoup('<input type="text" name="username">', 'html.parser').find('input')

        recognized = recognizer.recognize_element(element)

        assert recognized.type == ElementType.INPUT
        assert recognized.is_interactive

    def test_identify_checkbox(self):
        """测试识别复选框"""
        recognizer = ElementRecognizer()

        from bs4 import BeautifulSoup
        element = BeautifulSoup('<input type="checkbox" name="agree">', 'html.parser').find('input')

        recognized = recognizer.recognize_element(element)

        assert recognized.type == ElementType.CHECKBOX
        assert recognized.is_interactive

    def test_selector_generation_for_element(self):
        """测试为元素生成选择器"""
        recognizer = ElementRecognizer()

        from bs4 import BeautifulSoup
        element = BeautifulSoup('<button id="submit-btn">Submit</button>', 'html.parser').find('button')

        recognized = recognizer.recognize_element(element)

        # 应该生成ID选择器
        assert "#submit-btn" == recognized.selector
        assert recognized.confidence > 0.5


class TestFormFieldDetector:
    """表单字段检测器测试"""

    def test_initialization(self):
        """测试检测器初始化"""
        detector = FormFieldDetector()
        assert len(detector.field_patterns) > 0

    def test_detect_username_field(self):
        """测试检测用户名字段"""
        detector = FormFieldDetector()

        field_info = {
            "name": "username",
            "type": "text",
            "id": "",
            "placeholder": ""
        }

        detection = detector.detect_field_type(field_info)

        assert detection.type == FieldType.USERNAME
        assert detection.confidence >= 0.7

    def test_detect_password_field(self):
        """测试检测密码字段"""
        detector = FormFieldDetector()

        field_info = {
            "name": "password",
            "type": "password",
            "id": "",
            "placeholder": ""
        }

        detection = detector.detect_field_type(field_info)

        assert detection.type == FieldType.PASSWORD
        assert detection.confidence >= 0.9

    def test_detect_email_field(self):
        """测试检测邮箱字段"""
        detector = FormFieldDetector()

        field_info = {
            "name": "email",
            "type": "email",
            "id": "",
            "placeholder": ""
        }

        detection = detector.detect_field_type(field_info)

        assert detection.type == FieldType.EMAIL
        assert detection.confidence >= 0.8

    def test_generate_test_suggestions(self):
        """测试生成测试建议"""
        detector = FormFieldDetector()

        field_info = {
            "name": "email",
            "type": "email",
            "id": "",
            "placeholder": ""
        }

        detection = detector.detect_field_type(field_info)

        # 应该生成测试值建议
        assert len(detection.suggestions) > 0

    def test_get_test_data_for_fields(self):
        """测试为字段生成测试数据"""
        detector = FormFieldDetector()

        detections = [
            detector.detect_field_type({"name": "username", "type": "text"}),
            detector.detect_field_type({"name": "password", "type": "password"}),
            detector.detect_field_type({"name": "email", "type": "email"})
        ]

        test_data = detector.get_test_data_for_fields(detections)

        # 应该为所有字段生成测试数据
        assert len(test_data) == 3
        assert "username" in test_data
        assert "password" in test_data
        assert "email" in test_data


class TestPageLayoutAnalyzer:
    """页面布局分析器测试"""

    def test_initialization(self):
        """测试分析器初始化"""
        analyzer = PageLayoutAnalyzer()
        assert len(analyzer.semantic_tags) > 0
        assert len(analyzer.class_patterns) > 0

    def test_detect_login_form(self):
        """测试检测登录表单"""
        analyzer = PageLayoutAnalyzer()

        from bs4 import BeautifulSoup
        html = '''
        <form action="/login">
            <input type="text" name="username">
            <input type="password" name="password">
            <button type="submit">Login</button>
        </form>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        login_form = analyzer._detect_login_form(soup)

        assert login_form is not None
        assert login_form.type == PageRegion.FORM

    def test_detect_search_form(self):
        """测试检测搜索表单"""
        analyzer = PageLayoutAnalyzer()

        from bs4 import BeautifulSoup
        html = '''
        <form action="/search">
            <input type="text" name="search" placeholder="Search...">
            <button type="submit">Search</button>
        </form>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        search_form = analyzer._detect_search_form(soup)

        assert search_form is not None
        assert search_form.type == PageRegion.FORM

    def test_analyze_page_layout(self):
        """测试分析页面布局"""
        analyzer = PageLayoutAnalyzer()

        from bs4 import BeautifulSoup
        html = '''
        <html>
        <header>Header</header>
        <nav>Navigation</nav>
        <main>Main Content</main>
        <footer>Footer</footer>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        report = analyzer.analyze_page(str(soup))

        assert "regions" in report
        assert report["total_regions"] > 0

    def test_generate_test_actions(self):
        """测试生成测试操作建议"""
        analyzer = PageLayoutAnalyzer()

        from bs4 import BeautifulSoup
        html = '''
        <html>
        <header><a href="/home">Home</a></header>
        <main>
            <form id="login">
                <input type="text" name="username">
                <input type="password" name="password">
            </form>
        </main>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')

        actions = analyzer.suggest_test_actions(str(soup))

        # 应该生成表单测试和导航测试建议
        assert len(actions) > 0


# 运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
