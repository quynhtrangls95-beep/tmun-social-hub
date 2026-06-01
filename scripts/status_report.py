"""
Daily status report cho TMUN Social Hub.

Goi Apps Script `daily_summary` + check FB token -> compose Telegram message.
Chay tu GitHub Actions sang 7h va toi 21h VN.

Env vars:
  SHEETS_WEBHOOK_URL   - Apps Script Web App URL
  FB_PAGE_ID           - dung de verify token cua Page nao
  FB_PAGE_ACCESS_TOKEN - dung de check days remaining
  TELEGRAM_BOT_TOKEN   - bot token tu BotFather
  TELEGRAM_CHAT_ID     - chat id cua chi
  REPORT_TIME_LABEL    - optional "sang" hoac "toi", default tu gio VN
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from check_token import check_token
from notify import send_telegram, NotifyError
from sheets import SheetError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("status_report")

TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def fetch_daily_summary() -> dict:
    """Goi Apps Script action=daily_summary."""
    url = os.getenv("SHEETS_WEBHOOK_URL", "").strip()
    if not url:
        raise SheetError("Thieu SHEETS_WEBHOOK_URL")
    resp = requests.get(url, params={"action": "daily_summary"}, timeout=60)
    if resp.status_code != 200:
        raise SheetError(f"Apps Script HTTP {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    if not body.get("ok"):
        raise SheetError(f"Apps Script: {body.get('error', 'unknown')}")
    return body.get("data", {})


def fetch_token_status() -> dict | None:
    """Goi FB debug_token. Tra ve dict hoac None neu fail."""
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    if not token:
        return None
    try:
        return check_token(token)
    except Exception as e:
        log.warning("Khong check duoc token: %s", e)
        return None


def _esc(s: str) -> str:
    """Escape HTML cho Telegram parse_mode=HTML."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_pending_item(it: dict, show_date: bool = False) -> str:
    cap = _esc(it.get("caption_preview", "").replace("\n", " ")[:60])
    gio = _esc(it.get("gio", "??:??"))
    stt = _esc(it.get("stt", "?"))
    prefix = f"{_esc(it.get('ngay', ''))} " if show_date else ""
    return f"   • {prefix}<b>{gio}</b> · STT {stt} · {cap}…"


def _format_posted_item(it: dict) -> str:
    cap = _esc(it.get("caption_preview", "").replace("\n", " ")[:60])
    posted_at = _esc(it.get("posted_at", "").split(" ")[1] if " " in it.get("posted_at", "") else "")
    stt = _esc(it.get("stt", "?"))
    return f"   • <b>{posted_at}</b> · STT {stt} · {cap}…"


def compose_message(summary: dict, token_info: dict | None, is_morning: bool) -> str:
    today = summary.get("today", "")
    icon = "☀️" if is_morning else "🌙"
    when = "sáng" if is_morning else "tối"

    parts: list[str] = []
    parts.append(f"{icon} <b>TMUN Social Hub — Báo cáo {when} {_esc(today)}</b>")
    parts.append("")

    # ===== OVERDUE (uu tien hang dau, neu co la BAT THUONG) =====
    overdue = summary.get("overdue_pending", [])
    if overdue:
        parts.append(f"🚨 <b>{len(overdue)} bài Pending QUÁ GIỜ chưa đăng được:</b>")
        for it in overdue[:5]:
            parts.append(_format_pending_item(it, show_date=True))
        if len(overdue) > 5:
            parts.append(f"   … và {len(overdue) - 5} bài khác")
        parts.append("→ Cần check GitHub Actions log gần nhất")
        parts.append("")

    # ===== BUOI SANG: bao cao Posted hom qua + Pending hom nay =====
    if is_morning:
        posted_yesterday = summary.get("posted_yesterday", [])
        if posted_yesterday:
            parts.append(f"✅ Hôm qua đăng <b>{len(posted_yesterday)} bài</b>:")
            for it in posted_yesterday[:5]:
                parts.append(_format_posted_item(it))
            if len(posted_yesterday) > 5:
                parts.append(f"   … +{len(posted_yesterday) - 5}")
        else:
            parts.append("⚠️ Hôm qua KHÔNG đăng bài nào (bình thường nếu chưa lên lịch)")
        parts.append("")

        pending_today = summary.get("pending_today", [])
        if pending_today:
            parts.append(f"📅 Hôm nay {len(pending_today)} bài chờ đăng:")
            for it in pending_today[:5]:
                parts.append(_format_pending_item(it))
        else:
            parts.append("📭 Hôm nay CHƯA có bài nào trong lịch")
        parts.append("")
    else:
        # ===== BUOI TOI: bao cao Posted hom nay + Pending ngay mai =====
        posted_today = summary.get("posted_today", [])
        if posted_today:
            parts.append(f"✅ Hôm nay đã đăng <b>{len(posted_today)} bài</b>:")
            for it in posted_today[:5]:
                parts.append(_format_posted_item(it))
        else:
            parts.append("⚠️ Hôm nay CHƯA đăng bài nào")
        parts.append("")

        pending_tomorrow = summary.get("pending_tomorrow", [])
        if pending_tomorrow:
            parts.append(f"📅 Ngày mai {len(pending_tomorrow)} bài đã lên lịch:")
            for it in pending_tomorrow[:5]:
                parts.append(_format_pending_item(it))
        else:
            parts.append("📭 Ngày mai CHƯA có bài nào trong lịch")
        parts.append("")

    # ===== STATS =====
    stats: list[str] = []
    stats.append(f"📈 7 ngày qua: {summary.get('posted_last_7_days', 0)} Posted")
    if summary.get("failed_last_7_days", 0) > 0:
        stats.append(f"❌ {summary.get('failed_last_7_days', 0)} Failed")
    stats.append(f"📋 Tổng Pending: {summary.get('total_pending', 0)} (còn {summary.get('upcoming_pending', 0)} sắp tới)")
    parts.append(" · ".join(stats))

    # ===== TOKEN =====
    if token_info:
        days = token_info.get("days_remaining", -1)
        if days == -1:
            parts.append("🔑 FB Token: không bao giờ hết hạn ✅")
        elif days <= 7:
            parts.append(f"🔑 🚨 FB Token CHỈ CÒN <b>{days} ngày</b> — refresh GẤP")
        elif days <= 14:
            parts.append(f"🔑 ⚠️ FB Token còn {days} ngày — nên refresh sớm")
        else:
            parts.append(f"🔑 FB Token còn {days} ngày ✅")
    else:
        parts.append("🔑 ⚠️ Không check được FB Token")

    parts.append("")

    # ===== VERDICT =====
    if overdue or (token_info and 0 <= token_info.get("days_remaining", -1) <= 7):
        parts.append("⚠️ <b>Cần action — xem các mục có 🚨/⚠️</b>")
    else:
        parts.append("✅ <b>Hệ thống OK, chị không cần làm gì.</b>")

    return "\n".join(parts)


def _emit_gh_summary(line: str) -> None:
    f = os.getenv("GITHUB_STEP_SUMMARY")
    if not f:
        return
    try:
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")
    except Exception:
        pass


def main() -> int:
    # Quyet dinh sang hay toi
    label = os.getenv("REPORT_TIME_LABEL", "").strip().lower()
    if label in ("sang", "morning"):
        is_morning = True
    elif label in ("toi", "evening", "night"):
        is_morning = False
    else:
        hour_vn = datetime.now(TZ).hour
        is_morning = hour_vn < 14  # 0-13 = sang, 14-23 = toi

    log.info("Bao cao %s (is_morning=%s)", "sang" if is_morning else "toi", is_morning)

    try:
        summary = fetch_daily_summary()
    except SheetError as e:
        log.error("Khong lay duoc summary: %s", e)
        # Van thu gui canh bao
        try:
            send_telegram(
                f"🚨 <b>TMUN Report fail</b>\nKhong doc duoc Google Sheet:\n<code>{_esc(str(e))}</code>"
            )
        except NotifyError:
            pass
        return 1

    token_info = fetch_token_status()
    message = compose_message(summary, token_info, is_morning)

    log.info("Message length: %d chars", len(message))
    _emit_gh_summary(message)

    try:
        result = send_telegram(message)
        log.info("Sent: message_id=%s", result.get("message_id"))
    except NotifyError as e:
        log.error("Gui Telegram fail: %s", e)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
