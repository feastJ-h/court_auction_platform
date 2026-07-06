from typing import Any


def initialize_request(request_id: int) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": request_id,
        "params": {
            "clientInfo": {
                "name": "court_auction_platform",
                "title": "Court Auction Platform",
                "version": "0.1.0",
            },
            "capabilities": {"experimentalApi": True},
        },
    }


def initialized_notification() -> dict[str, Any]:
    return {"jsonrpc": "2.0", "method": "initialized", "params": {}}


def thread_start_request(request_id: int, model: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if model:
        params["model"] = model
    return {"jsonrpc": "2.0", "method": "thread/start", "id": request_id, "params": params}


def turn_start_request(
    request_id: int,
    thread_id: str,
    cwd: str,
    input_text: str,
) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "turn/start",
        "id": request_id,
        "params": {
            "threadId": thread_id,
            "cwd": cwd,
            "input": [{"type": "text", "text": input_text}],
        },
    }


def turn_interrupt_request(request_id: int, thread_id: str, turn_id: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "method": "turn/interrupt",
        "id": request_id,
        "params": {"threadId": thread_id, "turnId": turn_id},
    }
