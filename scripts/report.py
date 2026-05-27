"""
Script fetch insights cua tat ca bai da dang -> ghi vao Sheet "Bao cao".

Chay moi sang 7h va moi toi 22h qua GitHub Actions.

Logic:
1. Lay danh sach bai da dang (status='Posted') trong 30 ngay gan nhat
2. Voi moi post_id: goi Graph API insights, ghi vao sheet 'Bao cao'
3. Sheet 'Phan tich' tu pivot tu sheet 'Bao cao' (chi can refresh)
"""

from __future__ import annotations

import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fb_api import FacebookPage, FacebookAPIError
from sheets import SocialSheet, SheetError

TZ = ZoneInfo("Asia/Ho_Chi_Minh")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("report")


def main() -> int:
    try:
        fb = FacebookPage()
        sheet = SocialSheet()
    except (FacebookAPIError, SheetError) as e:
        log.error("Khong init duoc: %s", e)
        return 1

    try:
        posted = sheet.list_posted_for_report()
    except SheetError as e:
        log.error("Khong doc duoc Sheet: %s", e)
        return 1

    if not posted:
        log.info("Chua co bai nao de fetch insights")
        return 0

    log.info("Fetch insights cho %d bai", len(posted))
    ok_count = 0
    fail_count = 0

    for item in posted:
        post_id = item.get("post_id")
        if not post_id:
            continue
        try:
            insights = fb.get_post_insights(post_id)
            insights["updated_at"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

            engagement = insights["reactions"] + insights["comments"] + insights["shares"]
            reach = insights["reach"] or 1
            insights["engagement_rate"] = round(engagement * 100 / reach, 2)
            insights["click_rate"] = round(insights["link_clicks"] * 100 / reach, 2)

            sheet.save_insights(post_id, insights)
            ok_count += 1
            log.info(
                "Post %s: reach=%d, react=%d, cmt=%d, share=%d, click=%d, ER=%.2f%%",
                post_id, insights["reach"], insights["reactions"],
                insights["comments"], insights["shares"], insights["link_clicks"],
                insights["engagement_rate"],
            )
        except FacebookAPIError as e:
            log.error("Post %s: %s", post_id, e)
            fail_count += 1
        except SheetError as e:
            log.error("Post %s: khong ghi Sheet duoc: %s", post_id, e)
            fail_count += 1

    sheet.log("INFO", f"Report run: {ok_count} ok, {fail_count} fail")
    log.info("Xong: %d ok, %d fail", ok_count, fail_count)
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
