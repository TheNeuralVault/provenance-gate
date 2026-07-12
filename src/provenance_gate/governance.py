from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from provenance_gate.authority import AuthorityModel
from provenance_gate.pipeline import PipelineState
from provenance_gate.session import SessionScope


def requires_authority(
    action: str,
    model: AuthorityModel | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator: require that a given governance action is authorized
    by the AuthorityModel before the function executes.

    Usage:

        @requires_authority("enforce_pipeline")
        def enforce(...):
            ...

    Raises PermissionError on violation.
    """
    if model is None:
        model = AuthorityModel()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ok, info = model.check(action)
            if not ok:
                raise PermissionError(f"Authority violation: {info}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def governed_step(
    step: str,
    pipeline: PipelineState,
    *,
    authority: AuthorityModel | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator: enforce that a function represents a governed pipeline step.

    It will:
        - require "enforce_pipeline" authority
        - advance the pipeline with provided evidence (from kwargs)
        - attach the result to the function return metadata

    Expected function signature:

        @governed_step("BUILD", pipeline)
        def build_step(*, evidence: EvidenceArtifact, session: SessionScope):
            ...

    The decorator will:
        - call pipeline.advance(step, evidence)
        - raise on violation
        - return the original function result, plus governance info if desired
    """
    if authority is None:
        authority = AuthorityModel()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Authority check
            ok, info = authority.check("enforce_pipeline")
            if not ok:
                raise PermissionError(f"Authority violation: {info}")

            # Extract evidence and optional session
            evidence = kwargs.get("evidence")
            session: SessionScope | None = kwargs.get("session")

            # Advance pipeline
            ok, advance_info = pipeline.advance(step=step, evidence=evidence)
            if not ok:
                raise RuntimeError(f"Pipeline violation: {advance_info}")

            # If a session is provided, record via session (which may write to ledger)
            if session is not None:
                session.attach_metadata("last_governed_step", step)

            result = func(*args, **kwargs)

            # Optionally attach governance info to result if it's a dict
            if isinstance(result, dict):
                result.setdefault("_governance", {})
                result["_governance"]["pipeline"] = advance_info

            return result

        return wrapper

    return decorator
