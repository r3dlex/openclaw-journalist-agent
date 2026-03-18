"""Tests for the article extraction pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipeline_runner.config import PipelineSettings
from pipeline_runner.pipelines.article import build_article_pipeline, run_article_pipeline


class TestArticlePipeline:
    def test_pipeline_has_steps(self) -> None:
        pipeline = build_article_pipeline(handoff=False)
        names = [s.name for s in pipeline._steps]
        assert "fetch_url" in names
        assert "extract_content" in names

    def test_pipeline_with_handoff(self) -> None:
        pipeline = build_article_pipeline(handoff=True)
        names = [s.name for s in pipeline._steps]
        assert "librarian_handoff" in names

    def test_pipeline_without_handoff(self) -> None:
        pipeline = build_article_pipeline(handoff=False)
        names = [s.name for s in pipeline._steps]
        assert "librarian_handoff" not in names

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_end_to_end_extraction(self, mock_get: MagicMock, settings: PipelineSettings) -> None:
        """Integration test: full article extraction with mocked HTTP."""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is the main article content that should be extracted by the pipeline.
                It needs to be long enough to pass the 100 char threshold for content selection.</p>
            </article>
        </body>
        </html>
        """
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        pipeline = build_article_pipeline(settings, handoff=False)
        result = pipeline.run({
            "settings": settings,
            "url": "https://example.com/article",
            "pipeline_name": "article_extraction",
        })

        assert result.success
        assert "Test Article" in result.context.get("title", "")
        assert "main article content" in result.context.get("content", "")
        assert result.context["fetch_tier"] == 1
