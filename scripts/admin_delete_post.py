"""
Xoa 1 post tren FB Page (utility ad-hoc, dung khi can xoa bai test hoac
bai dang nham).

Goi: DELETE /{post_id}?access_token=...
Tra ve: {"success": true} neu OK.

Env:
  FB_PAGE_ACCESS_TOKEN  - bat buoc
  POST_ID               - bat buoc, dang {page_id}_{post_id}

Usage tu GitHub Actions workflow_dispatch (xem .github/workflows/admin_delete_post.yml):
  POST_ID=1063264180209204_122106271035302926 python scripts/admin_delete_post.py
"""

from __future__ import annotations

import os
import sys
import logging
import requests

from fb_api import GRAPH_API_BASE, FacebookAPIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("admin_delete_post")


def _emit_summary(line: str) -> None:
    f = os.getenv("GITHUB_STEP_SUMMARY")
    if not f:
        return
    try:
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")
    except Exception:
        pass


def main() -> int:
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    post_id = os.getenv("POST_ID", "").strip()

    if not token:
        log.error("Thieu FB_PAGE_ACCESS_TOKEN")
        return 2
    if not post_id:
        log.error("Thieu POST_ID. Format: {page_id}_{post_id}")
        return 2
    if "_" not in post_id:
        log.error("POST_ID phai co format {page_id}_{post_id}, vd: 1063264180209204_122106271035302926")
        return 2

    url = f"{GRAPH_API_BASE}/{post_id}"
    log.info("DELETE %s", url)
    try:
        resp = requests.delete(url, params={"access_token": token}, timeout=30)
    except requests.RequestException as e:
        log.error("Network error: %s", e)
        _emit_summary(f"❌ Network error: {e}")
        return 1

    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:500]}

    if resp.status_code == 200 and body.get("success"):
        log.info("Xoa thanh cong post %s", post_id)
        _emit_summary(f"✅ Da xoa post `{post_id}` khoi Page")
        return 0

    err = body.get("error", {})
    msg = err.get("message", "Unknown error")
    code = err.get("code")
    log.error("FB API loi: status=%d code=%s msg=%s body=%s", resp.status_code, code, msg, body)
    _emit_summary(f"❌ Xoa fail: code={code}, message={msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
