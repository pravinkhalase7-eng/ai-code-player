from typing import Any


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        error: str,
        detail: str,
        code: str,
        missing_keys: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.error = error
        self.detail = detail
        self.code = code
        self.missing_keys = missing_keys or []
        self.extra = extra or {}
