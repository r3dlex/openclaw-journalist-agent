"""Tests for the content extraction step."""

from __future__ import annotations

from pipeline_runner.steps.extract import ExtractContentStep


class TestExtractContentStep:
    def test_extracts_title(self) -> None:
        html = "<html><head><title>Test Title</title></head><body><p>Content</p></body></html>"
        step = ExtractContentStep()
        result = step.execute({"raw_html": html})
        assert result["title"] == "Test Title"

    def test_extracts_body_content(self) -> None:
        html = "<html><body><p>Hello world</p></body></html>"
        step = ExtractContentStep()
        result = step.execute({"raw_html": html})
        assert "Hello world" in result["content"]

    def test_removes_script_tags(self) -> None:
        html = "<html><body><script>alert('xss')</script><p>Content</p></body></html>"
        step = ExtractContentStep()
        result = step.execute({"raw_html": html})
        assert "alert" not in result["content"]
        assert "Content" in result["content"]

    def test_removes_nav_and_footer(self) -> None:
        html = """
        <html><body>
            <nav>Navigation</nav>
            <article><p>Main content</p></article>
            <footer>Footer</footer>
        </body></html>
        """
        step = ExtractContentStep()
        result = step.execute({"raw_html": html})
        assert "Navigation" not in result["content"]
        assert "Footer" not in result["content"]
        assert "Main content" in result["content"]

    def test_truncates_at_max_chars(self) -> None:
        html = "<html><body><p>" + "A" * 5000 + "</p></body></html>"
        step = ExtractContentStep(max_chars=100)
        result = step.execute({"raw_html": html})
        assert len(result["content"]) < 200
        assert "[Truncated]" in result["content"]

    def test_prefers_article_tag(self) -> None:
        html = """
        <html><body>
            <div>Sidebar noise</div>
            <article><p>Article content here with enough text to be selected</p>
            <p>More article content to make it long enough</p>
            <p>Even more content to be sure it exceeds 100 chars threshold</p></article>
        </body></html>
        """
        step = ExtractContentStep()
        result = step.execute({"raw_html": html})
        assert "Article content" in result["content"]

    def test_should_run(self) -> None:
        step = ExtractContentStep()
        assert step.should_run({"raw_html": "<html></html>"})
        assert not step.should_run({})

    def test_context_max_chars_override(self) -> None:
        html = "<html><body><p>" + "B" * 500 + "</p></body></html>"
        step = ExtractContentStep(max_chars=5000)
        result = step.execute({"raw_html": html, "max_chars": 50})
        assert len(result["content"]) < 100
