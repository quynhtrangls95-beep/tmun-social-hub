"""
Script dang bai Facebook tu dong.

Chay moi 15 phut qua GitHub Actions. Logic:
1. Lay danh sach 'Pending' tu Google Sheet (chi nhung bai da den gio)
2. Voi moi bai: dang len FB Page, ghi post_id ve Sheet
3. Neu loi -> mark Failed + ghi log

Cach chay local de test:
  set FB_PAGE_ID=...
  set FB_PAGE_ACCESS_TOKEN=...
  set SHEETS_WEBHOOK_URL=...
  python scripts/publish.py
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fb_api import FacebookPage, FacebookAPIError
from sheets import SocialSheet, SheetError


def _emit_summary_line(line: str) -> None:
    """Ghi 1 dong vao GitHub Step Summary de hien trong tab Actions."""
    f = os.getenv("GITHUB_STEP_SUMMARY")
    if not f:
        return
    try:
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")
    except Exception:
        pass

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("publish")


def parse_image_urls(raw: str) -> list[str]:
    """Cot 'Anh' co the la 1 URL hoac nhieu URL phan tach bang | hoac newline."""
    if not raw:
        return []
    parts: list[str] = []
    for chunk in raw.replace("\n", "|").split("|"):
        s = chunk.strip()
        if s.startswith("http"):
            parts.append(s)
    return parts


def publish_one(fb: FacebookPage, item: dict) -> tuple[bool, str, str]:
    """
    Dang 1 bai. Tra ve (success, post_id, error_msg).

    item co cac field tu Sheet:
      row       - so dong trong Sheet
      caption   - noi dung bai dang
      images    - 1 hoac nhieu URL anh (cach nhau bang |)
      link      - link gan vao bai (vd: link dat hang)
      channel   - 'FB' (phase 1 chi co FB)
      post_type - 'text' | 'photo' | 'carousel' | 'link'
    """
    caption = (item.get("caption") or "").strip()
    images = parse_image_urls(item.get("images") or "")
    link = (item.get("link") or "").strip() or None
    post_type = (item.get("post_type") or "").strip().lower()

    if not post_type:
        if len(images) >= 2:
            post_type = "carousel"
        elif len(images) == 1:
            post_type = "photo"
        elif link:
            post_type = "link"
        else:
            post_type = "text"

    log.info("Row %s: dang dang post_type=%s, %d anh", item.get("row"), post_type, len(images))

    try:
        if post_type == "carousel":
            if len(images) < 2:
                return False, "", "Carousel can it nhat 2 anh"
            post_id = fb.post_multi_photo(images, caption)
        elif post_type == "photo":
            if not images:
                return False, "", "Photo can 1 anh"
            post_id = fb.post_single_photo(images[0], caption)
        elif post_type == "link":
            if not link:
                return False, "", "Link post can field 'link'"
            post_id = fb.post_text(caption, link=link)
        else:
            if not caption:
                return False, "", "Text post can caption"
            post_id = fb.post_text(caption, link=link)
        return True, post_id, ""
    except FacebookAPIError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", f"Loi khong xac dinh: {e}"


def main() -> int:
    try:
        fb = FacebookPage()
        sheet = SocialSheet()
    except (FacebookAPIError, SheetError) as e:
        log.error("Khong init duoc: %s", e)
        return 1

    try:
        page_info = fb.verify_token()
        token_type = page_info.get("_token_type", "UNKNOWN")
        expires_at = page_info.get("_token_expires_at", 0)
        scopes = page_info.get("_token_scopes", [])
        log.info(
            "Page OK: %s (id=%s, token_type=%s, expires_at=%s, scopes=%s)",
            page_info.get("name"), page_info.get("id"), token_type, expires_at, ",".join(scopes),
        )
        _emit_summary_line(f"✅ Token OK — type={token_type}, scopes={','.join(scopes)}")
    except FacebookAPIError as e:
        log.error("Token KHONG hop le: %s", e)
        sheet.log("ERROR", f"Token FB sai: {e}")
        _emit_summary_line(f"❌ Token FAIL — {e}")
        return 1

    try:
        pending = sheet.list_pending()
    except SheetError as e:
        log.error("Khong doc duoc Sheet: %s", e)
        return 1

    if not pending:
        log.info("Khong co bai nao den gio dang. Bye.")
        return 0

    log.info("Co %d bai can dang", len(pending))
    success_count = 0
    fail_count = 0

    _emit_summary_line(f"\n📋 Co **{len(pending)} bai** can dang.\n")

    for item in pending:
        row = item.get("row")
        ok, post_id, err = publish_one(fb, item)
        if ok:
            posted_at = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
            try:
                sheet.mark_posted(row, post_id, posted_at)
                log.info("Row %s: OK post_id=%s", row, post_id)
                _emit_summary_line(f"- ✅ Row {row}: posted, post_id=`{post_id}`")
                success_count += 1
            except SheetError as e:
                log.error("Da dang FB nhung khong cap nhat Sheet duoc: %s", e)
                _emit_summary_line(f"- ⚠️ Row {row}: posted_id={post_id} NHUNG khong update Sheet: {e}")
                fail_count += 1
        else:
            log.error("Row %s: FAIL - %s", row, err)
            _emit_summary_line(f"- ❌ Row {row}: FAIL — {err}")
            try:
                sheet.mark_failed(row, err)
            except SheetError as se:
                log.error("Khong mark Failed duoc: %s", se)
            fail_count += 1

    sheet.log("INFO", f"Publish run: {success_count} ok, {fail_count} fail")
    log.info("Xong: %d ok, %d fail", success_count, fail_count)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
