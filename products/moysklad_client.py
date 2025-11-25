import json
import threading
import time
from collections import deque, defaultdict
from contextlib import contextmanager
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from requests import Response
from requests.auth import HTTPBasicAuth


class MoyskladClientError(Exception):
    """Base error for Moysklad client failures."""


class MoyskladRateLimitError(MoyskladClientError):
    """Raised when we cannot satisfy Moysklad rate limits."""


class MoyskladCircuitOpenError(MoyskladClientError):
    """Raised when we intentionally stop repeating identical failing requests."""


class _SlidingWindowThrottle:
    """
    Tracks how many calls happened in the last `window_seconds` and blocks
    until a new slot is available.
    """

    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps = deque()
        self._lock = threading.Lock()

    def wait_for_slot(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                window_start = now - self.window_seconds
                while self._timestamps and self._timestamps[0] < window_start:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_calls:
                    self._timestamps.append(now)
                    return

                sleep_for = self.window_seconds - (now - self._timestamps[0]) + 0.001

            time.sleep(max(sleep_for, 0.05))


class _ConcurrencyGate:
    """Wrapper around bounded semaphore to express a concurrency limit."""

    def __init__(self, limit: int):
        self._semaphore = threading.BoundedSemaphore(value=max(limit, 1))

    @contextmanager
    def checkout(self):
        self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()


class _FailureTracker:
    """
    Tracks identical HTTP failures per minute to avoid triggering Moysklad's
    auto-block for >200 identical errors.
    """

    def __init__(self, threshold: int = 100, window_seconds: int = 60):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self._failures = defaultdict(deque)
        self._lock = threading.Lock()

    def register(self, signature: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._failures[signature]
            bucket.append(now)
            cutoff = now - self.window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            return len(bucket) >= self.threshold

    def reset(self, signature: str) -> None:
        with self._lock:
            self._failures.pop(signature, None)


class MoyskladClient:
    """
    Centralized HTTP client for Moysklad JSON API with built-in enforcement
    of documented limits (rate, concurrency, payload sizes, compression).
    """

    BASE_HEADERS = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }

    def __init__(
        self,
        login: str,
        password: str,
        *,
        max_requests_per_window: int = 45,
        window_seconds: float = 3.0,
        max_parallel_user: int = 5,
        max_parallel_account: int = 20,
        max_request_body_bytes: int = 20 * 1024 * 1024,
        max_header_bytes: int = 8 * 1024,
        max_identical_failures_per_minute: int = 100,
    ):
        self._auth = HTTPBasicAuth(login, password)
        self._session = requests.Session()
        self._session.auth = self._auth
        self._session.headers.update(self.BASE_HEADERS)
        self._session.headers.setdefault(
            "User-Agent",
            getattr(settings, "MOYSKLAD_USER_AGENT", "derek-api/1.0"),
        )

        self._body_limit = max_request_body_bytes
        self._header_limit = max_header_bytes
        self._throttle = _SlidingWindowThrottle(max_requests_per_window, window_seconds)
        self._user_gate = _ConcurrencyGate(max_parallel_user)
        self._account_gate = _ConcurrencyGate(max_parallel_account)
        self._failures = _FailureTracker(
            threshold=max_identical_failures_per_minute, window_seconds=60
        )
        self._retry_backoff_base = 0.5
        self._max_retries = 5

    @contextmanager
    def _reserve_slot(self):
        with self._account_gate.checkout():
            with self._user_gate.checkout():
                self._throttle.wait_for_slot()
                yield

    def _ensure_limits(self, headers: Optional[Dict[str, str]], data: Any, json_payload: Any):
        """
        Validates request headers/body sizes before sending.
        """
        merged_headers = dict(self._session.headers)
        if headers:
            merged_headers.update(headers)

        header_size = len(
            "\r\n".join(f"{k}: {v}" for k, v in merged_headers.items()).encode("utf-8")
        )
        if header_size > self._header_limit:
            raise MoyskladClientError(
                f"Request headers exceed {self._header_limit} bytes (got {header_size})."
            )

        body_bytes = 0
        if data is not None:
            if isinstance(data, bytes):
                body_bytes = len(data)
            elif isinstance(data, str):
                body_bytes = len(data.encode("utf-8"))
            else:
                raise MoyskladClientError(
                    "Unsupported data payload type. Use bytes or string, or pass json=..."
                )
        elif json_payload is not None:
            serialized = json.dumps(json_payload, ensure_ascii=False).encode("utf-8")
            body_bytes = len(serialized)

        if body_bytes > self._body_limit:
            raise MoyskladClientError(
                f"Request body exceeds {self._body_limit} bytes (got {body_bytes})."
            )

    def _signature(self, method: str, url: str, status_code: int) -> str:
        parsed = requests.utils.urlparse(url)
        return f"{method.upper()}:{parsed.path}:{status_code}"

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        json: Any = None,
        timeout: int = 60,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        self._ensure_limits(headers, data, json)

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt < self._max_retries:
            attempt += 1
            with self._reserve_slot():
                response = None
                try:
                    response = self._session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        json=json,
                        timeout=timeout,
                        params=params,
                    )
                except requests.RequestException as exc:
                    last_error = exc
                    sleep_for = self._retry_backoff_base * (2 ** (attempt - 1))
                    time.sleep(min(sleep_for, 5))
                    continue

            if response is None:
                continue

            if response.status_code == 429:
                last_error = MoyskladRateLimitError(
                    "Received HTTP 429 from Moysklad. Will retry with backoff."
                )
                time.sleep(min(2 ** attempt, 10))
                continue

            signature = self._signature(method, url, response.status_code)
            if response.status_code >= 500:
                if self._failures.register(signature):
                    raise MoyskladCircuitOpenError(
                        "Circuit breaker opened due to repeating errors from Moysklad."
                    )
                last_error = MoyskladClientError(
                    f"Server error {response.status_code}: {response.text[:200]}"
                )
                time.sleep(min(2 ** attempt, 10))
                continue

            try:
                response.raise_for_status()
                self._failures.reset(signature)
                return response
            except requests.HTTPError as exc:
                last_error = MoyskladClientError(
                    f"HTTP error {response.status_code}: {response.text[:200]}"
                )
                if response.status_code >= 400 and response.status_code < 500:
                    # client error, do not retry endlessly
                    break

        raise last_error or MoyskladClientError("Unknown Moysklad client failure.")

    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        response = self.request("GET", url, **kwargs)
        return response.json()

    def get_binary(self, url: str, **kwargs) -> bytes:
        response = self.request("GET", url, **kwargs)
        return response.content


moysklad_client = MoyskladClient(
    login=settings.MOYSKLAD_LOGIN,
    password=settings.MOYSKLAD_PASSWORD,
)

