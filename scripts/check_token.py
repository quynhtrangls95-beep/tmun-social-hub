"""
Check tinh trang Page Access Token: con bao nhieu ngay nua thi het han.

Chay weekly tu GitHub Actions. Neu token con < 14 ngay -> tao GitHub Issue
trong repo de canh bao chi Quynh Trang.

Exit code:
  0 - Token con > 14 ngay, OK
  1 - Token con <= 14 ngay, can alert (GitHub Actions se tao issue)
  2 - Token chet/sai, can xu ly ngay
"""

from __future__ import annotations

import os
import sys
import json
import logging
from datetime import datetime, timezone
import requests

from fb_api import GRAPH_API_BASE, FacebookAPIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("check_token")

ALERT_THRESHOLD_DAYS = 14


def check_token(token: str) -> dict:
    """
    Goi /debug_token de check token. Tra ve:
    {
        "is_valid": bool,
        "expires_at": int (unix ts, 0 = never),
        "days_remaining": int (-1 neu never expire),
        "type": "PAGE" | "USER" | "APP",
        "scopes": [str],
        "page_id": str | None,
    }
    """
    url = f"{GRAPH_API_BASE}/debug_token"
    params = {"input_token": token, "access_token": token}
    resp = requests.get(url, params=params, timeout=30)
    body = resp.json()
    if "data" not in body:
        raise FacebookAPIError(f"Debug token loi: {body}")

    d = body["data"]
    expires_at = int(d.get("expires_at", 0) or 0)
    now = int(datetime.now(timezone.utc).timestamp())

    if expires_at == 0:
        days_remaining = -1  # never expire
    else:
        days_remaining = max(0, (expires_at - now) // 86400)

    return {
        "is_valid": bool(d.get("is_valid", False)),
        "expires_at": expires_at,
        "days_remaining": days_remaining,
        "type": d.get("type", "UNKNOWN"),
        "scopes": d.get("scopes", []),
        "page_id": d.get("profile_id"),
    }


def main() -> int:
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    expected_page_id = os.getenv("FB_PAGE_ID", "").strip()

    if not token:
        log.error("Thieu FB_PAGE_ACCESS_TOKEN")
        return 2

    try:
        info = check_token(token)
    except Exception as e:
        log.error("Khong check duoc token: %s", e)
        _emit_github_summary(error=str(e))
        return 2

    if not info["is_valid"]:
        log.error("Token KHONG hop le (da chet hoac bi revoke)")
        _emit_github_summary(error="Token da chet", info=info)
        return 2

    if expected_page_id and info["page_id"] and info["page_id"] != expected_page_id:
        log.error(
            "Page ID khong khop: token cua Page %s, mong cho %s",
            info["page_id"], expected_page_id,
        )
        _emit_github_summary(error="Page ID khong khop", info=info)
        return 2

    days = info["days_remaining"]
    if days == -1:
        log.info("Token NEVER EXPIRE - khoe.")
        _emit_github_summary(info=info)
        return 0

    if days <= ALERT_THRESHOLD_DAYS:
        expires_str = datetime.fromtimestamp(info["expires_at"], tz=timezone.utc).strftime("%Y-%m-%d")
        log.warning("Token con %d ngay (het han %s) - CAN REFRESH NGAY", days, expires_str)
        _emit_github_summary(
            warning=f"Token con {days} ngay, het han {expires_str}",
            info=info,
        )
        return 1

    log.info("Token con %d ngay - OK", days)
    _emit_github_summary(info=info)
    return 0


def _emit_github_summary(info: dict | None = None, warning: str = "", error: str = "") -> None:
    """Ghi summary ra GITHUB_STEP_SUMMARY de hien trong tab Actions."""
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    lines: list[str] = ["# FB Page Token Health Check\n"]
    if error:
        lines.append(f"## CRITICAL: {error}\n")
    elif warning:
        lines.append(f"## WARNING: {warning}\n")
    else:
        lines.append("## OK: Token healthy\n")

    if info:
        if info.get("days_remaining", -1) == -1:
            days_str = "Never expire"
        else:
            days_str = f"{info['days_remaining']} days"
        lines.extend([
            f"- **Type**: {info.get('type', 'UNKNOWN')}",
            f"- **Page ID**: {info.get('page_id', 'N/A')}",
            f"- **Valid**: {info.get('is_valid', False)}",
            f"- **Days remaining**: {days_str}",
            f"- **Scopes**: {', '.join(info.get('scopes', []))}",
        ])

    with open(summary_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
