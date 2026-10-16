"""Thin wrapper around TypeSafeClient for JEV Choice calls."""

import os
import time
from typing import Any, Optional

import src.config  # noqa: F401  # load .env via python-dotenv
from src.jev.questions import QUESTION_ID, build_questions


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
    """Call JEV via TypeSafe system_one with a Choice question."""

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
        Ask JEV whether the warning state is actionable / unactionable / unknown.

        Returns a plain dict with the full response (model, answers, usage, ...)
        plus a small request summary for reproducibility. No post-processing.
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

                # Prefer answers / choices shapes from different SDK versions.
                answers = payload.get("answers")
                if answers is None and "choices" in payload:
                    answers = payload.get("choices")

                result = {
                    "request": {
                        "model": self.model,
                        "question_id": QUESTION_ID,
                        "state": state,
                        "questions": {
                            QUESTION_ID: {
                                "type": "choice",
                                "instructions": questions[QUESTION_ID].instructions,
                                "criteria": questions[QUESTION_ID].criteria,
                            }
                        },
                    },
                    "response": payload,
                }

                # Convenience mirror of the Choice answer if present.
                if isinstance(answers, dict) and QUESTION_ID in answers:
                    result["answer"] = answers[QUESTION_ID]

                return result
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
