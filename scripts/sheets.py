"""
Google Sheets wrapper qua Apps Script Web App.

Tai sao Apps Script thay vi Sheets API:
- Khong can Service Account / GCP setup
- Chi cua chi share Web App URL la dung duoc
- Dependency: chi 1 secret SHEETS_WEBHOOK_URL

Web App endpoint (xem apps-script/Code.gs):
  GET  ?action=list_pending     -> [{row, ts, caption, image_urls, channel, ...}]
  POST {action: "mark_posted", row, post_id, posted_at}
  POST {action: "save_insights", row, reach, impressions, reactions, comments, shares, link_clicks}
  POST {action: "log", level, message}
"""

import os
import json
import logging
import requests

log = logging.getLogger(__name__)


class SheetError(Exception):
    pass


class SocialSheet:
    def __init__(self, webhook_url: str | None = None):
        self.url = webhook_url or os.getenv("SHEETS_WEBHOOK_URL", "").strip()
        if not self.url:
            raise SheetError(
                "Thieu SHEETS_WEBHOOK_URL. Setup Apps Script Web App truoc (xem README)."
            )

    def _post(self, payload: dict, timeout=60) -> dict:
        resp = requests.post(self.url, json=payload, timeout=timeout)
        if resp.status_code != 200:
            raise SheetError(f"Apps Script HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            body = resp.json()
        except json.JSONDecodeError:
            raise SheetError(f"Apps Script response khong phai JSON: {resp.text[:200]}")
        if not body.get("ok", False):
            raise SheetError(f"Apps Script tra loi: {body.get('error', 'unknown')}")
        return body

    def _get(self, params: dict, timeout=60) -> dict:
        resp = requests.get(self.url, params=params, timeout=timeout)
        if resp.status_code != 200:
            raise SheetError(f"Apps Script HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            body = resp.json()
        except json.JSONDecodeError:
            raise SheetError(f"Apps Script response khong phai JSON: {resp.text[:200]}")
        if not body.get("ok", False):
            raise SheetError(f"Apps Script tra loi: {body.get('error', 'unknown')}")
        return body

    # -----------------------------------------------------------------
    # Lich dang
    # -----------------------------------------------------------------

    def list_pending(self) -> list[dict]:
        """Lay danh sach bai dang trang thai 'Pending' va da den gio (gio dang <= now)."""
        body = self._get({"action": "list_pending"})
        return body.get("data", [])

    def get_image(self, name: str) -> dict:
        """
        Lay 1 anh tu folder Drive TMUN-Anh-FB theo TEN FILE.
        Tra ve {id, name, mime, size, base64} hoac raise SheetError.

        Match: exact name -> contains (case-insensitive).
        """
        body = self._get({"action": "get_image", "name": name})
        return body.get("data", {})

    def list_images(self) -> list[dict]:
        """Liet ke anh trong folder (khong kem base64)."""
        body = self._get({"action": "list_images"})
        return body.get("data", [])

    def list_posted_for_report(self) -> list[dict]:
        """Lay danh sach bai da dang trong 30 ngay gan nhat de fetch insights."""
        body = self._get({"action": "list_posted"})
        return body.get("data", [])

    def mark_posted(self, row: int, post_id: str, posted_at: str) -> None:
        self._post({
            "action": "mark_posted",
            "row": row,
            "post_id": post_id,
            "posted_at": posted_at,
        })

    def mark_failed(self, row: int, error: str) -> None:
        self._post({
            "action": "mark_failed",
            "row": row,
            "error": error[:500],
        })

    def save_insights(self, post_id: str, insights: dict) -> None:
        """Ghi insights vao sheet 'Bao cao' (append hoac update neu da co)."""
        self._post({
            "action": "save_insights",
            "post_id": post_id,
            "insights": insights,
        })

    def log(self, level: str, message: str) -> None:
        """Ghi 1 dong log vao sheet 'Logs'."""
        try:
            self._post({"action": "log", "level": level, "message": message[:1000]})
        except Exception as e:
            log.warning("Khong ghi duoc log vao Sheet: %s", e)
