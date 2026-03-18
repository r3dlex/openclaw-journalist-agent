"""Tests for the core pipeline runner engine."""

from __future__ import annotations

from typing import Any

from pipeline_runner.runner import Pipeline, StepStatus


class PassStep:
    """A step that always succeeds."""

    name = "pass_step"

    def should_run(self, context: dict[str, Any]) -> bool:
        return True

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        context["passed"] = True
        return context


class FailStep:
    """A step that always fails."""

    name = "fail_step"

    def should_run(self, context: dict[str, Any]) -> bool:
        return True

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("intentional failure")


class SkipStep:
    """A step that always skips."""

    name = "skip_step"

    def should_run(self, context: dict[str, Any]) -> bool:
        return False

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        return context


class ContextStep:
    """A step that adds data to context."""

    name = "context_step"

    def __init__(self, key: str, value: Any) -> None:
        self._key = key
        self._value = value

    def should_run(self, context: dict[str, Any]) -> bool:
        return True

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        context[self._key] = self._value
        return context


class TestPipeline:
    def test_empty_pipeline(self) -> None:
        pipeline = Pipeline("empty")
        result = pipeline.run()
        assert result.success
        assert len(result.steps) == 0

    def test_single_passing_step(self) -> None:
        pipeline = Pipeline("test")
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert result.success
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.SUCCESS
        assert result.context["passed"] is True

    def test_chained_steps(self) -> None:
        pipeline = Pipeline("test")
        pipeline.add_step(ContextStep("a", 1))
        pipeline.add_step(ContextStep("b", 2))
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert result.success
        assert result.context["a"] == 1
        assert result.context["b"] == 2
        assert result.context["passed"] is True

    def test_skipped_step(self) -> None:
        pipeline = Pipeline("test")
        pipeline.add_step(SkipStep())
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert result.success
        assert result.steps[0].status == StepStatus.SKIPPED
        assert result.steps[1].status == StepStatus.SUCCESS

    def test_fail_fast(self) -> None:
        pipeline = Pipeline("test", fail_fast=True)
        pipeline.add_step(FailStep())
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert not result.success
        assert len(result.steps) == 1  # Second step never ran
        assert result.steps[0].status == StepStatus.FAILED
        assert "intentional failure" in result.steps[0].error

    def test_no_fail_fast(self) -> None:
        pipeline = Pipeline("test", fail_fast=False)
        pipeline.add_step(FailStep())
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert not result.success
        assert len(result.steps) == 2
        assert result.steps[0].status == StepStatus.FAILED
        assert result.steps[1].status == StepStatus.SUCCESS

    def test_initial_context(self) -> None:
        pipeline = Pipeline("test")
        pipeline.add_step(PassStep())
        result = pipeline.run({"initial_key": "initial_value"})
        assert result.context["initial_key"] == "initial_value"

    def test_duration_tracking(self) -> None:
        pipeline = Pipeline("test")
        pipeline.add_step(PassStep())
        result = pipeline.run()
        assert result.total_duration_ms >= 0
        assert result.steps[0].duration_ms >= 0

    def test_summary_output(self) -> None:
        pipeline = Pipeline("test", fail_fast=False)
        pipeline.add_step(PassStep())
        pipeline.add_step(FailStep())
        result = pipeline.run()
        summary = result.summary()
        assert "Pipeline: test" in summary
        assert "pass_step" in summary

    def test_failed_steps_property(self) -> None:
        pipeline = Pipeline("test", fail_fast=False)
        pipeline.add_step(PassStep())
        pipeline.add_step(FailStep())
        result = pipeline.run()
        assert len(result.failed_steps) == 1
        assert result.failed_steps[0].name == "fail_step"

    def test_method_chaining(self) -> None:
        pipeline = Pipeline("test")
        result = pipeline.add_step(PassStep()).add_step(ContextStep("x", 1))
        assert result is pipeline
