"""
Facebook Graph API wrapper cho Thao Moc Uyen Nhien.

Chuc nang:
- Dang anh don (single photo + caption) len Page
- Dang nhieu anh (multi-photo post)
- Dang text-only (link post co preview)
- Dang link (link post co caption rieng)
- Fetch insights cua 1 post

Yeu cau:
- FB_PAGE_ID: id cua Fanpage (lay tu Page settings)
- FB_PAGE_ACCESS_TOKEN: long-lived Page token (xem HUONG-DAN-LAY-TOKEN.md)

Graph API version: v21.0 (stable 2025-2026)
"""

import os
import time
import logging
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

log = logging.getLogger(__name__)


class FacebookAPIError(Exception):
    """Loi tu Graph API - co the la sai token, sai params, hoac rate limit."""

    def __init__(self, message: str, response: dict | None = None):
        super().__init__(message)
        self.response = response or {}


def _request(method: str, url: str, *, params=None, data=None, files=None, timeout=60) -> dict:
    """Goi Graph API, tu retry 2 lan neu rate limit hoac 5xx."""
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            resp = requests.request(method, url, params=params, data=data, files=files, timeout=timeout)
            if resp.status_code >= 500:
                raise FacebookAPIError(f"Server error {resp.status_code}", resp.json() if resp.text else {})

            body = resp.json() if resp.text else {}
            if resp.status_code >= 400:
                err = body.get("error", {})
                code = err.get("code")
                if code in (4, 17, 32, 613):
                    wait = 2 ** attempt * 5
                    log.warning("Rate limit, retry sau %ds (attempt %d/3)", wait, attempt + 1)
                    time.sleep(wait)
                    continue
                raise FacebookAPIError(err.get("message", "Loi khong xac dinh"), body)
            return body
        except requests.RequestException as e:
            last_err = e
            log.warning("Network error attempt %d: %s", attempt + 1, e)
            time.sleep(2 ** attempt * 3)

    raise FacebookAPIError(f"Khong goi duoc API sau 3 lan: {last_err}")


class FacebookPage:
    def __init__(self, page_id: str | None = None, access_token: str | None = None):
        self.page_id = page_id or os.getenv("FB_PAGE_ID", "").strip()
        self.access_token = access_token or os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()

        if not self.page_id or not self.access_token:
            raise FacebookAPIError(
                "Thieu FB_PAGE_ID hoac FB_PAGE_ACCESS_TOKEN. "
                "Xem HUONG-DAN-LAY-TOKEN.md de lay token."
            )

    def _url(self, path: str) -> str:
        return f"{GRAPH_API_BASE}/{path.lstrip('/')}"

    # -----------------------------------------------------------------
    # Dang bai
    # -----------------------------------------------------------------

    def post_text(self, message: str, link: str | None = None) -> str:
        """Dang text-only (co the kem link). Tra ve post_id dang {pageid}_{postid}."""
        data = {"message": message, "access_token": self.access_token}
        if link:
            data["link"] = link
        body = _request("POST", self._url(f"{self.page_id}/feed"), data=data)
        return body["id"]

    def post_single_photo(self, image_url: str, caption: str, published: bool = True) -> str:
        """Dang 1 anh tu URL kem caption. Tra ve post_id (page_post_id)."""
        data = {
            "url": image_url,
            "caption": caption,
            "published": "true" if published else "false",
            "access_token": self.access_token,
        }
        body = _request("POST", self._url(f"{self.page_id}/photos"), data=data)
        return body.get("post_id") or body.get("id")

    def post_multi_photo(self, image_urls: list[str], caption: str) -> str:
        """Dang nhieu anh (carousel) trong 1 post. Tra ve post_id."""
        if not image_urls:
            raise FacebookAPIError("image_urls rong")
        if len(image_urls) > 10:
            raise FacebookAPIError("Toi da 10 anh / post")

        media_ids = []
        for url in image_urls:
            data = {"url": url, "published": "false", "access_token": self.access_token}
            body = _request("POST", self._url(f"{self.page_id}/photos"), data=data)
            media_ids.append(body["id"])

        feed_data = {
            "message": caption,
            "access_token": self.access_token,
        }
        for idx, mid in enumerate(media_ids):
            feed_data[f"attached_media[{idx}]"] = f'{{"media_fbid":"{mid}"}}'

        feed_body = _request("POST", self._url(f"{self.page_id}/feed"), data=feed_data)
        return feed_body["id"]

    # -----------------------------------------------------------------
    # Insights
    # -----------------------------------------------------------------

    def get_post_insights(self, post_id: str) -> dict:
        """
        Lay insights cua 1 post. Tra ve dict:
        {
            "reach": int,
            "impressions": int,
            "reactions": int,  # like + love + wow + ...
            "comments": int,
            "shares": int,
            "link_clicks": int,
            "video_views": int,
        }
        """
        metrics = [
            "post_impressions_unique",         # reach
            "post_impressions",                # impressions
            "post_reactions_by_type_total",    # reactions detail
            "post_clicks_by_type",             # clicks breakdown
        ]
        params = {
            "metric": ",".join(metrics),
            "access_token": self.access_token,
        }
        body = _request("GET", self._url(f"{post_id}/insights"), params=params)

        result = {
            "reach": 0,
            "impressions": 0,
            "reactions": 0,
            "comments": 0,
            "shares": 0,
            "link_clicks": 0,
            "video_views": 0,
        }
        for item in body.get("data", []):
            name = item.get("name")
            values = item.get("values", [])
            if not values:
                continue
            v = values[0].get("value", 0)
            if name == "post_impressions_unique":
                result["reach"] = int(v or 0)
            elif name == "post_impressions":
                result["impressions"] = int(v or 0)
            elif name == "post_reactions_by_type_total" and isinstance(v, dict):
                result["reactions"] = int(sum(v.values()))
            elif name == "post_clicks_by_type" and isinstance(v, dict):
                result["link_clicks"] = int(v.get("link clicks", 0) or 0)

        engagement_meta = self._get_engagement_summary(post_id)
        result["comments"] = engagement_meta["comments"]
        result["shares"] = engagement_meta["shares"]
        return result

    def _get_engagement_summary(self, post_id: str) -> dict:
        """Comments va shares phai lay tu /post endpoint, KHONG co trong insights."""
        params = {
            "fields": "comments.summary(true).limit(0),shares",
            "access_token": self.access_token,
        }
        body = _request("GET", self._url(post_id), params=params)
        comments = body.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = body.get("shares", {}).get("count", 0)
        return {"comments": int(comments), "shares": int(shares)}

    # -----------------------------------------------------------------
    # Verify token
    # -----------------------------------------------------------------

    def verify_token(self) -> dict:
        """Goi /me de check token con song khong. Tra ve {id, name, category}."""
        params = {"fields": "id,name,category,fan_count", "access_token": self.access_token}
        return _request("GET", self._url(self.page_id), params=params)
