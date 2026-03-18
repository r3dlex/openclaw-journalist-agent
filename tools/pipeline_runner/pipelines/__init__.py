"""Pre-built pipelines for common Journalist workflows."""

from pipeline_runner.pipelines.article import build_article_pipeline
from pipeline_runner.pipelines.news import build_news_pipeline
from pipeline_runner.pipelines.weather import build_weather_pipeline

__all__ = [
    "build_article_pipeline",
    "build_news_pipeline",
    "build_weather_pipeline",
]
