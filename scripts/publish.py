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
import base64
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

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


def parse_image_refs(raw: str) -> list[dict]:
    """
    Cot 'Anh' co the chua:
      - URL public (vd https://thaomocuyennhien.com/banner.jpg)
      - Ten file trong folder Drive TMUN-Anh-FB (vd matngu_01.jpg)
      - Hon hop ca 2, phan tach bang `|` hoac newline.

    Tra ve list of {"type": "url"|"file", "value": str}.
    """
    if not raw:
        return []
    refs: list[dict] = []
    for chunk in raw.replace("\n", "|").split("|"):
        s = chunk.strip()
        if not s:
            continue
        if s.lower().startswith(("http://", "https://")):
            refs.append({"type": "url", "value": s})
        else:
            refs.append({"type": "file", "value": s})
    return refs


def parse_image_urls(raw: str) -> list[str]:
    """Backward-compat: chi tra URL (bo file refs)."""
    return [r["value"] for r in parse_image_refs(raw) if r["type"] == "url"]


def resolve_image_binary(ref: dict, sheet: SocialSheet) -> tuple[bytes, str]:
    """
    Convert image ref -> (bytes, filename). Dung cho binary upload.
    URL -> fetch GET. File -> goi Apps Script get_image -> decode base64.
    Raise on failure.
    """
    if ref["type"] == "url":
        url = ref["value"]
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FacebookAPIError(f"Khong fetch duoc URL {url}: {e}") from e
        filename = url.rsplit("/", 1)[-1].split("?", 1)[0] or "image.jpg"
        return resp.content, filename
    else:
        name = ref["value"]
        try:
            img = sheet.get_image(name)
        except SheetError as e:
            raise FacebookAPIError(f"Khong lay duoc anh '{name}' tu Drive: {e}") from e
        if not img.get("base64"):
            raise FacebookAPIError(f"Apps Script tra ve khong co base64 cho '{name}'")
        try:
            data = base64.b64decode(img["base64"])
        except Exception as e:
            raise FacebookAPIError(f"Decode base64 fail cho '{name}': {e}") from e
        return data, img.get("name") or name


def publish_one(fb: FacebookPage, sheet: SocialSheet, item: dict) -> tuple[bool, str, str]:
    """
    Dang 1 bai. Tra ve (success, post_id, error_msg).

    item co cac field tu Sheet:
      row       - so dong trong Sheet
      caption   - noi dung bai dang
      images    - URL public, ten file Drive, hoac mix (phan tach `|`)
      link      - link gan vao bai (vd: link dat hang)
      channel   - 'FB' (phase 1 chi co FB)
      post_type - 'text' | 'photo' | 'carousel' | 'link'

    Logic anh:
      - Tat ca URL -> URL flow (giu logic cu, nhanh hon)
      - Co bat ky tham chieu file -> binary flow (fetch URL + Drive thanh bytes)
    """
    caption = (item.get("caption") or "").strip()
    refs = parse_image_refs(item.get("images") or "")
    link = (item.get("link") or "").strip() or None
    post_type = (item.get("post_type") or "").strip().lower()

    has_file_ref = any(r["type"] == "file" for r in refs)
    n_images = len(refs)

    if not post_type:
        if n_images >= 2:
            post_type = "carousel"
        elif n_images == 1:
            post_type = "photo"
        elif link:
            post_type = "link"
        else:
            post_type = "text"

    log.info(
        "Row %s: dang dang post_type=%s, %d anh (mode=%s)",
        item.get("row"), post_type, n_images, "binary" if has_file_ref else "url",
    )

    try:
        if post_type == "carousel":
            if n_images < 2:
                return False, "", "Carousel can it nhat 2 anh"
            if has_file_ref:
                binaries = [resolve_image_binary(r, sheet) for r in refs]
                post_id = fb.post_multi_photo_binary(binaries, caption)
            else:
                urls = [r["value"] for r in refs]
                post_id = fb.post_multi_photo(urls, caption)
        elif post_type == "photo":
            if n_images == 0:
                return False, "", "Photo can 1 anh"
            if has_file_ref:
                img_bytes, fname = resolve_image_binary(refs[0], sheet)
                post_id = fb.post_single_photo_binary(img_bytes, fname, caption)
            else:
                post_id = fb.post_single_photo(refs[0]["value"], caption)
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

    # RATE LIMIT: chi dang MAX_POSTS_PER_RUN bai/run de tranh dồn dập tren FB Page.
    # Default 1 — cron mỗi 5 phút rải đều, không bao giờ burst.
    # Set env MAX_POSTS_PER_RUN cao hơn nếu muốn catch-up nhanh sau outage.
    max_posts = int(os.getenv("MAX_POSTS_PER_RUN", "1"))
    total_pending = len(pending)
    pending = pending[:max_posts]

    if total_pending > max_posts:
        log.info(
            "Rate limit: %d bai overdue, chi dang %d bai dau (oldest first). "
            "%d bai con lai cho run cron sau.",
            total_pending, max_posts, total_pending - max_posts,
        )
        _emit_summary_line(
            f"\n📋 Co **{total_pending} bai** overdue. Rate limit `MAX_POSTS_PER_RUN={max_posts}` → "
            f"dang **{max_posts}** bai dau, {total_pending - max_posts} bai cho run sau.\n"
        )
    else:
        log.info("Co %d bai can dang", total_pending)
        _emit_summary_line(f"\n📋 Co **{total_pending} bai** can dang.\n")

    success_count = 0
    fail_count = 0

    for item in pending:
        row = item.get("row")
        ok, post_id, err = publish_one(fb, sheet, item)
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
