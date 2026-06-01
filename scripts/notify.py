"""
Notification dispatcher cho TMUN Social Hub.

Phase 1: Telegram (chi Trang chon).
Sau nay them kenh (Zalo OA, Email) chi can:
  1. Them function send_<kenh>(message)
  2. Them branch trong send()
  3. Set env NOTIFY_CHANNEL=<kenh>

Env vars can:
  TELEGRAM_BOT_TOKEN  — tu BotFather (vd "1234567890:ABC...")
  TELEGRAM_CHAT_ID    — chat ID cua nguoi nhan (int hoac string)
  NOTIFY_CHANNEL      — optional, default "telegram"
"""

from __future__ import annotations

import os
import logging
import requests

log = logging.getLogger(__name__)


class NotifyError(Exception):
    pass


def _trunc(s: str, max_len: int = 4000) -> str:
    """Telegram giới hạn 4096 chars/message. Cắt an toàn."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 20] + "\n…(rút gọn)"


def send_telegram(message: str, parse_mode: str = "HTML") -> dict:
    """Gửi message qua Telegram Bot API. Raise NotifyError nếu fail."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token:
        raise NotifyError("Thiếu env TELEGRAM_BOT_TOKEN")
    if not chat_id:
        raise NotifyError("Thiếu env TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": _trunc(message),
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
    except requests.RequestException as e:
        raise NotifyError(f"Network: {e}") from e

    if resp.status_code != 200:
        raise NotifyError(f"Telegram HTTP {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    if not body.get("ok"):
        raise NotifyError(
            f"Telegram API: {body.get('description', 'unknown')} (code={body.get('error_code')})"
        )
    return body.get("result", {})


def discover_telegram_chat_id() -> list[dict]:
    """
    Helper: gọi getUpdates để tìm chat_id của các user đã nhắn bot.
    Chạy sau khi chị đã /start bot và nhắn 1 câu bất kỳ.
    Trả về list các (chat_id, name) tìm được.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise NotifyError("Thiếu env TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        resp = requests.get(url, timeout=30)
    except requests.RequestException as e:
        raise NotifyError(f"Network: {e}") from e
    body = resp.json()
    if not body.get("ok"):
        raise NotifyError(f"Telegram API: {body.get('description')}")
    seen: dict[int, dict] = {}
    for upd in body.get("result", []):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        if cid is None:
            continue
        seen[cid] = {
            "chat_id": cid,
            "type": chat.get("type"),
            "name": (
                chat.get("title")
                or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")]))
                or chat.get("username")
                or "Unknown"
            ),
            "username": chat.get("username"),
        }
    return list(seen.values())


def send(message: str) -> dict:
    """Dispatch theo NOTIFY_CHANNEL (default telegram)."""
    channel = os.getenv("NOTIFY_CHANNEL", "telegram").strip().lower()
    if channel == "telegram":
        return send_telegram(message)
    raise NotifyError(f"Kênh chưa support: {channel}")


if __name__ == "__main__":
    # CLI tien ich:
    #   python notify.py discover  -> liet ke chat_id da nhan bot
    #   python notify.py test      -> gui 1 tin nhan test
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python notify.py [discover|test]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "discover":
        chats = discover_telegram_chat_id()
        if not chats:
            print(
                "Khong tim thay chat_id. Hay /start bot va gui 1 tin nhan cho bot truoc, "
                "roi chay lai 'discover' trong vong 24h."
            )
            sys.exit(1)
        print(f"Tim thay {len(chats)} chat:")
        for c in chats:
            print(f"  - chat_id={c['chat_id']} type={c['type']} name={c['name']!r}")
    elif cmd == "test":
        result = send_telegram(
            "✅ <b>TMUN Bot test</b>\nHệ thống thông báo Telegram đã hoạt động."
        )
        print(f"OK, message_id={result.get('message_id')}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
