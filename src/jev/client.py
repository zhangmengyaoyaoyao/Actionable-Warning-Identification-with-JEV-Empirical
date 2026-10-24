"""Thin wrapper around TypeSafeClient for JEV Choice / Score / Noul calls."""

import os
import time
from typing import Any, Optional

import src.config  # noqa: F401  # load .env via python-dotenv
from src.jev.questions import (
    QUESTION_ID_CHOICE,
    QUESTION_ID_NOUL,
    QUESTION_ID_SCORE,
    QUESTION_IDS,
    build_questions,
    questions_for_request,
)


def _to_plain(obj: Any) -> Any:
    """Convert SDK / pydantic response objects into plain JSON-serializable data."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(v) for v in obj]
    for method_name in ("model_dump", "dict", "to_dict"):
        method = getattr(obj, method_name, None)
        if callable(method):
            try:
                dumped = method() if method_name != "model_dump" else method(mode="json")
            except TypeError:
                dumped = method()
            return _to_plain(dumped)
    if hasattr(obj, "__dict__"):
        return _to_plain(
            {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        )
    return str(obj)


class JevClient:
    """Call JEV via TypeSafe system_one with Choice, Score, and Noul in one request."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "jev-latest",
        base_url: Optional[str] = None,
        max_retries: int = 15,
        retry_sleep: float = 3.0,
    ):
        from typesafe_sdk import TypeSafeClient

        self.model = model
        self.max_retries = max_retries
        self.retry_sleep = retry_sleep
        self.api_key = (
            api_key
            or os.environ.get("TYPESAFE_API_KEY")
            or os.environ.get("JEV_API_KEY")
            or os.environ.get("LLM_API_KEY")
        )
        if not self.api_key:
            raise SystemExit(
                "未找到 TypeSafe/JEV API key。请设置环境变量 TYPESAFE_API_KEY "
                "（或 JEV_API_KEY / LLM_API_KEY），或使用 --api-key。"
            )

        kwargs = {"api_key": self.api_key, "model": model}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = TypeSafeClient(**kwargs)

    def close(self):
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def __enter__(self):
        enter = getattr(self._client, "__enter__", None)
        if callable(enter):
            enter()
        return self

    def __exit__(self, exc_type, exc, tb):
        exit_ = getattr(self._client, "__exit__", None)
        if callable(exit_):
            return exit_(exc_type, exc, tb)
        self.close()
        return False

    def classify_warning(self, state: str) -> dict:
        """
        Ask Choice, Score, and Noul about the same warning state in one call.

        Returns a plain dict with the full request/response plus per-primitive
        ``answers`` keyed by choice / score / noul.
        """
        questions = build_questions()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.system_one(
                    state=state,
                    questions=questions,
                    model=self.model,
                )
                payload = _to_plain(response)
                if not isinstance(payload, dict):
                    payload = {"raw": payload}

                answers = payload.get("answers")
                if answers is None and "choices" in payload:
                    answers = payload.get("choices")
                if not isinstance(answers, dict):
                    answers = {}

                per_primitive = {}
                for primitive, question_id in QUESTION_IDS.items():
                    if question_id in answers:
                        per_primitive[primitive] = answers[question_id]

                return {
                    "request": {
                        "model": self.model,
                        "state": state,
                        "questions": questions_for_request(questions),
                    },
                    "response": payload,
                    "answers": per_primitive,
                    # Convenience aliases for the three answers.
                    "answer_choice": per_primitive.get("choice"),
                    "answer_score": per_primitive.get("score"),
                    "answer_noul": per_primitive.get("noul"),
                }
            except Exception as exc:
                last_error = exc
                print(
                    f"JEV call failed (attempt {attempt}/{self.max_retries}): {exc}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_sleep)

        raise RuntimeError(
            f"JEV call failed after {self.max_retries} retries: {last_error}"
        )


# Keep question id constants importable for callers that still expect them.
__all__ = [
    "JevClient",
    "QUESTION_ID_CHOICE",
    "QUESTION_ID_SCORE",
    "QUESTION_ID_NOUL",
]
