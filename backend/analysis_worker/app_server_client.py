import asyncio
import json
from typing import Any, AsyncIterator

from backend.analysis_worker.app_server_protocol import (
    initialize_request,
    initialized_notification,
    thread_start_request,
    turn_interrupt_request,
    turn_start_request,
)
from backend.jobs.status import ERROR_APP_SERVER_PROTOCOL, ERROR_APP_SERVER_TIMEOUT, ERROR_APP_SERVER_UNAVAILABLE


class AppServerClientError(RuntimeError):
    def __init__(self, message: str, error_code: str = ERROR_APP_SERVER_PROTOCOL) -> None:
        super().__init__(message)
        self.error_code = error_code


class CodexAppServerClient:
    def __init__(self, endpoint: str, timeout_seconds: int = 900) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._request_id = 0
        self._websocket: Any = None
        self._pending_events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def connect(self) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise AppServerClientError(
                "Python package 'websockets' is required for app-server mode.",
                ERROR_APP_SERVER_UNAVAILABLE,
            ) from exc

        try:
            self._websocket = await websockets.connect(self.endpoint)
        except Exception as exc:
            raise AppServerClientError(f"Could not connect to Codex app-server: {exc}", ERROR_APP_SERVER_UNAVAILABLE) from exc

    async def close(self) -> None:
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

    async def _send(self, payload: dict[str, Any]) -> None:
        if self._websocket is None:
            raise AppServerClientError("Codex app-server websocket is not connected", ERROR_APP_SERVER_UNAVAILABLE)
        await self._websocket.send(json.dumps(payload, ensure_ascii=False))

    async def _request(self, payload: dict[str, Any], timeout_seconds: int | None = None) -> dict[str, Any]:
        await self._send(payload)
        request_id = payload.get("id")
        timeout = timeout_seconds or self.timeout_seconds
        try:
            while True:
                raw_message = await asyncio.wait_for(self._websocket.recv(), timeout=timeout)
                message = json.loads(raw_message)
                if "method" in message and message.get("id") is None:
                    await self._pending_events.put(message)
                    continue
                if message.get("id") != request_id:
                    await self._pending_events.put(message)
                    continue
                if "error" in message:
                    raise AppServerClientError(str(message["error"]), ERROR_APP_SERVER_PROTOCOL)
                return message.get("result") or {}
        except asyncio.TimeoutError as exc:
            raise AppServerClientError(f"Codex app-server request timed out: {payload.get('method')}", ERROR_APP_SERVER_TIMEOUT) from exc

    async def initialize(self) -> None:
        await self._request(initialize_request(self._next_id()), timeout_seconds=30)
        await self._send(initialized_notification())

    async def start_thread(self, model: str | None = None) -> str:
        result = await self._request(thread_start_request(self._next_id(), model=model), timeout_seconds=60)
        thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
        thread_id = result.get("threadId") or result.get("thread_id") or result.get("id") or thread.get("id")
        if not thread_id:
            raise AppServerClientError(f"thread/start returned no thread id: {result}", ERROR_APP_SERVER_PROTOCOL)
        return str(thread_id)

    async def start_turn(self, thread_id: str, input_text: str, cwd: str) -> str:
        result = await self._request(
            turn_start_request(self._next_id(), thread_id=thread_id, cwd=cwd, input_text=input_text),
            timeout_seconds=60,
        )
        turn = result.get("turn") if isinstance(result.get("turn"), dict) else {}
        turn_id = result.get("turnId") or result.get("turn_id") or result.get("id") or turn.get("id")
        if not turn_id:
            raise AppServerClientError(f"turn/start returned no turn id: {result}", ERROR_APP_SERVER_PROTOCOL)
        return str(turn_id)

    async def interrupt_turn(self, thread_id: str, turn_id: str) -> None:
        await self._request(
            turn_interrupt_request(self._next_id(), thread_id=thread_id, turn_id=turn_id),
            timeout_seconds=30,
        )

    async def events(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            if not self._pending_events.empty():
                yield await self._pending_events.get()
                continue
            try:
                raw_message = await asyncio.wait_for(self._websocket.recv(), timeout=self.timeout_seconds)
            except asyncio.TimeoutError as exc:
                raise AppServerClientError("Timed out while waiting for app-server events", ERROR_APP_SERVER_TIMEOUT) from exc
            yield json.loads(raw_message)
