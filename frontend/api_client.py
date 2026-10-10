"""Small synchronous client for the VedaVerse FastAPI backend."""

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
API_BASE_URL = os.getenv("VEDAVERSE_API_URL", "http://127.0.0.1:8000").rstrip("/")


class APIError(RuntimeError):
    def __init__(self, status_code: int | None, message, *, detail=None):
        self.detail = message if detail is None else detail
        if isinstance(message, list):
            message = "The request was invalid."
        super().__init__(str(message))
        self.status_code = status_code


def request_api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {"Accept": "application/json"}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{API_BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=180) as response:
            raw = response.read()
    except HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
            detail = result.get("detail", "")
            message = detail if isinstance(detail, str) else "The request was invalid."
        except (ValueError, UnicodeDecodeError):
            detail = "The backend returned an error."
            message = detail
        raise APIError(exc.code, message, detail=detail) from None
    except (URLError, TimeoutError, OSError):
        raise APIError(None, "Could not connect to the VedaVerse backend.") from None

    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise APIError(None, "The backend returned an unreadable response.") from None


def register(email: str, username: str, password: str):
    return request_api("POST", "/api/auth/register", payload={
        "email": email, "username": username, "password": password,
    })


def login(username_or_email: str, password: str):
    return request_api("POST", "/api/auth/login", payload={
        "username_or_email": username_or_email, "password": password,
    })


def get_me(token: str):
    return request_api("GET", "/api/auth/me", token=token)


def get_conversations(token: str):
    return request_api("GET", "/api/conversations", token=token)


def create_conversation(token: str):
    return request_api("POST", "/api/conversations", token=token,
                       payload={"title": "New Conversation"})


def delete_conversation(token: str, conversation_id: str):
    return request_api("DELETE", f"/api/conversations/{conversation_id}", token=token)


def get_messages(token: str, conversation_id: str):
    return request_api("GET", f"/api/conversations/{conversation_id}/messages", token=token)


def send_message(token: str, conversation_id: str, content: str):
    return request_api("POST", f"/api/conversations/{conversation_id}/messages",
                       token=token, payload={"content": content})
