"""
Diagnose: lay full info ve Page + bai dang gan nhat de debug van de "khong public".

Output ra GitHub Step Summary de hien thi trong tab Actions.

Goi:
  python scripts/diagnose.py [post_id]
  -> Neu khong truyen post_id: lay bai gan nhat tu Sheet "Bao cao"
"""

from __future__ import annotations

import os
import sys
import json
import logging
import requests

from fb_api import GRAPH_API_BASE, FacebookPage, FacebookAPIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("diagnose")


def fetch_post_full(token: str, post_id: str) -> dict:
    """Lay toan bo metadata cua 1 post."""
    fields = [
        "id",
        "message",
        "created_time",
        "permalink_url",
        "is_published",
        "is_hidden",
        "is_expired",
        "is_eligible_for_promotion",
        "privacy",
        "status_type",
        "promotion_status",
        "feed_targeting",
        "targeting",
        "from",
        "attachments{type,media_type,url}",
    ]
    url = f"{GRAPH_API_BASE}/{post_id}"
    params = {"fields": ",".join(fields), "access_token": token}
    resp = requests.get(url, params=params, timeout=30)
    return resp.json()


def fetch_page_full(token: str, page_id: str) -> dict:
    """Lay info ve Page de check Published status."""
    fields = [
        "id",
        "name",
        "username",
        "category",
        "fan_count",
        "followers_count",
        "is_published",
        "is_verified",
        "verification_status",
        "country_page_likes",
        "country_restricted",
        "age_restricted",
        "global_brand_page_name",
        "global_brand_root_id",
        "is_owned",
        "restricted_country_codes",
        "link",
        "about",
        "founded",
        "tasks",
    ]
    url = f"{GRAPH_API_BASE}/{page_id}"
    params = {"fields": ",".join(fields), "access_token": token}
    resp = requests.get(url, params=params, timeout=30)
    return resp.json()


def fetch_recent_posts(token: str, page_id: str, limit: int = 5) -> dict:
    """Lay danh sach bai gan nhat tren Page."""
    url = f"{GRAPH_API_BASE}/{page_id}/posts"
    params = {
        "fields": "id,message,created_time,is_published,is_hidden,permalink_url,privacy",
        "limit": limit,
        "access_token": token,
    }
    resp = requests.get(url, params=params, timeout=30)
    return resp.json()


def emit_summary(post: dict, page: dict, recent: dict) -> None:
    """Ghi ra GitHub Step Summary."""
    f = os.getenv("GITHUB_STEP_SUMMARY")
    if not f:
        print(json.dumps({"post": post, "page": page, "recent": recent}, indent=2, ensure_ascii=False))
        return

    lines: list[str] = []

    # ====== PAGE INFO ======
    lines.append("# Page Status\n")
    if page.get("error"):
        lines.append(f"❌ ERROR: {page['error'].get('message', 'Unknown')}\n")
    else:
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| Name | {page.get('name', 'N/A')} |")
        lines.append(f"| Username | {page.get('username', 'N/A')} |")
        lines.append(f"| Category | {page.get('category', 'N/A')} |")
        lines.append(f"| **is_published** | **{page.get('is_published', 'unknown')}** |")
        lines.append(f"| **is_unpublished** | **{page.get('is_unpublished', 'unknown')}** |")
        lines.append(f"| is_verified | {page.get('is_verified', False)} |")
        lines.append(f"| verification_status | {page.get('verification_status', 'N/A')} |")
        lines.append(f"| fan_count | {page.get('fan_count', 0)} |")
        lines.append(f"| followers_count | {page.get('followers_count', 0)} |")
        lines.append(f"| link | {page.get('link', 'N/A')} |")
        lines.append(f"| about | {(page.get('about') or '')[:100]} |")
        tasks = page.get("tasks", [])
        lines.append(f"| tasks | {', '.join(tasks) if tasks else 'N/A'} |")
        lines.append(f"| **country_restricted** | **{page.get('country_restricted', 'N/A')}** |")
        lines.append(f"| **age_restricted** | **{page.get('age_restricted', 'N/A')}** |")
        lines.append(f"| **restricted_country_codes** | **{page.get('restricted_country_codes', 'N/A')}** |")
        lines.append(f"| is_owned | {page.get('is_owned', 'N/A')} |")
        lines.append(f"| global_brand_page_name | {page.get('global_brand_page_name', 'N/A')} |")

    # ====== POST INFO ======
    lines.append("\n# Post Status\n")
    if post.get("error"):
        lines.append(f"❌ ERROR: {post['error'].get('message', 'Unknown')}\n")
    else:
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| ID | `{post.get('id', 'N/A')}` |")
        lines.append(f"| created_time | {post.get('created_time', 'N/A')} |")
        lines.append(f"| permalink_url | {post.get('permalink_url', 'N/A')} |")
        lines.append(f"| **is_published** | **{post.get('is_published', 'unknown')}** |")
        lines.append(f"| **is_hidden** | **{post.get('is_hidden', 'unknown')}** |")
        lines.append(f"| is_expired | {post.get('is_expired', 'unknown')} |")
        lines.append(f"| is_eligible_for_promotion | {post.get('is_eligible_for_promotion', 'unknown')} |")
        lines.append(f"| status_type | {post.get('status_type', 'N/A')} |")
        privacy = post.get("privacy", {})
        if privacy:
            lines.append(f"| **privacy.value** | **{privacy.get('value', 'N/A')}** |")
            lines.append(f"| privacy.description | {privacy.get('description', 'N/A')} |")
            lines.append(f"| privacy.friends | {privacy.get('friends', 'N/A')} |")
            lines.append(f"| privacy.allow | {privacy.get('allow', 'N/A')} |")
            lines.append(f"| privacy.deny | {privacy.get('deny', 'N/A')} |")
        attachments = (post.get("attachments") or {}).get("data", [])
        for i, att in enumerate(attachments):
            lines.append(f"| attachment[{i}].type | {att.get('type', 'N/A')} |")
            lines.append(f"| attachment[{i}].media_type | {att.get('media_type', 'N/A')} |")
        feed_targeting = post.get("feed_targeting")
        targeting = post.get("targeting")
        if feed_targeting:
            lines.append(f"| **feed_targeting** | **`{json.dumps(feed_targeting, ensure_ascii=False)}`** |")
        if targeting:
            lines.append(f"| **targeting** | **`{json.dumps(targeting, ensure_ascii=False)}`** |")
        if not feed_targeting and not targeting:
            lines.append(f"| feed_targeting / targeting | (khong co - bai khong bi target restrict) |")

    # ====== RECENT POSTS ======
    lines.append("\n# 5 bai gan nhat tren Page\n")
    if recent.get("error"):
        lines.append(f"❌ ERROR: {recent['error'].get('message', 'Unknown')}\n")
    else:
        posts = recent.get("data", [])
        lines.append(f"Tong: **{len(posts)} bai**\n")
        for p in posts:
            lines.append(f"- `{p.get('id', 'N/A')}` | published={p.get('is_published', '?')} | hidden={p.get('is_hidden', '?')} | privacy={p.get('privacy', {}).get('value', '?')} | {p.get('permalink_url', 'N/A')}")
            lines.append(f"  - {(p.get('message') or '')[:80]}...")

    # ====== DIAGNOSIS ======
    lines.append("\n# Diagnosis\n")
    page_pub = page.get("is_published")
    page_unpub = page.get("is_unpublished")
    post_pub = post.get("is_published")
    post_hidden = post.get("is_hidden")
    privacy_value = post.get("privacy", {}).get("value", "")

    issues: list[str] = []
    if page_unpub is True:
        issues.append("🔴 **Page dang UNPUBLISHED** — vao Page Settings -> Visibility -> Publish Page")
    elif page_pub is False:
        issues.append("🔴 **Page is_published = false** — Page chua go live")
    if post_pub is False:
        issues.append("🔴 **Post is_published = false** — bai dang o trang thai unpublished")
    if post_hidden is True:
        issues.append("🔴 **Post is_hidden = true** — bai bi an khoi News Feed")
    if privacy_value and privacy_value != "EVERYONE":
        issues.append(f"🔴 **Post privacy = {privacy_value}** — KHONG public, can update sang EVERYONE")

    if not issues:
        if page_pub is True and post_pub is True and not post_hidden:
            issues.append("✅ **Tat ca metadata co ve OK** — co the do FB caching/delay (doi 5-10 phut), hoac do tu khoa moi (FB review cho Page moi)")

    for issue in issues:
        lines.append(f"\n{issue}")

    with open(f, "a", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")


def main() -> int:
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    post_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv("POST_ID", "").strip()

    if not token or not page_id:
        log.error("Thieu FB_PAGE_ACCESS_TOKEN hoac FB_PAGE_ID")
        return 1

    # Neu khong co post_id, dung post gan nhat
    if not post_id:
        log.info("Khong co POST_ID, lay bai gan nhat tren Page")
        recent = fetch_recent_posts(token, page_id, limit=1)
        posts = recent.get("data", [])
        if posts:
            post_id = posts[0]["id"]
            log.info("Dung post_id: %s", post_id)
        else:
            log.error("Page khong co bai nao")
            return 1

    log.info("Fetching post %s...", post_id)
    post = fetch_post_full(token, post_id)

    log.info("Fetching page %s...", page_id)
    page = fetch_page_full(token, page_id)

    log.info("Fetching recent posts...")
    recent = fetch_recent_posts(token, page_id, limit=5)

    emit_summary(post, page, recent)
    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
