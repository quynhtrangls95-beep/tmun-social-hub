# Hướng dẫn setup Telegram cho TMUN Daily Report

Chị Trang nhận tin nhắn **mỗi sáng 7h** và **mỗi tối 21h** tự động qua Telegram.

## Bước 1 — Tạo bot (1 phút)

1. Mở **Telegram** → tìm **`@BotFather`** (avatar xanh có ✓)
2. Gõ `/newbot` → Send
3. BotFather hỏi tên → trả lời: `TMUN Daily Report`
4. BotFather hỏi username → trả lời: `tmun_daily_report_bot`
   - Nếu trùng → thêm số: `tmun_daily_report_bot_2`, miễn kết thúc bằng `_bot`
5. BotFather trả lại 1 token dạng:
   ```
   1234567890:AAEhBP...xyz
   ```
   **→ Copy lại token này**

## Bước 2 — Start bot (10 giây)

1. BotFather sẽ kèm link đến bot mới tạo (vd `t.me/tmun_daily_report_bot`) → click vào
2. Bấm nút **Start** (hoặc gõ `/start`)
3. Gõ thêm 1 chữ bất kỳ, vd `hi` → Send

Việc này để Telegram tạo `chat_id` cho chị — bot mới có quyền nhắn tin lại được.

## Bước 3 — Lấy chat_id (em làm thay chị)

Sau khi chị paste TOKEN cho em, em chạy:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<token chị paste>"
python scripts/notify.py discover
```

Output:
```
Tim thay 1 chat:
  - chat_id=123456789 type=private name='Quynh Trang'
```

→ `chat_id` của chị là `123456789`. Em set vào GitHub Secrets.

## Bước 4 — Add 2 secrets vào GitHub

Em đẩy code xong sẽ hướng dẫn chị 1 lần duy nhất:

1. Vào https://github.com/quynhtrangls95-beep/tmun-social-hub/settings/secrets/actions
2. Click **`New repository secret`** lần lượt 2 lần:
   - Name: `TELEGRAM_BOT_TOKEN` · Secret: `<token>`
   - Name: `TELEGRAM_CHAT_ID` · Secret: `<chat_id>`
3. Done

## Bước 5 — Test ngay

Em chạy workflow tay từ GitHub Actions UI:

1. https://github.com/quynhtrangls95-beep/tmun-social-hub/actions/workflows/status_report.yml
2. Click **`Run workflow`** → để trống `label` → **Run workflow**
3. Đợi ~30 giây
4. Chị check Telegram → có tin nhắn báo cáo

## Trông như nào?

Tin nhắn buổi sáng (7h):

```
☀️ TMUN Social Hub — Báo cáo sáng 02/06/2026

✅ Hôm qua đăng 1 bài:
   • 19:00 · STT 9 · Đằng sau mỗi hộp Thảo Mộc Uyên Nhiên — đằng sau…

📅 Hôm nay 1 bài chờ đăng:
   • 19:00 · STT 10 · Cảm ơn tuần đầu cùng Thảo Mộc Uyên Nhiên…

📈 7 ngày qua: 6 Posted · 📋 Tổng Pending: 17 (còn 17 sắp tới)
🔑 FB Token còn 47 ngày ✅

✅ Hệ thống OK, chị không cần làm gì.
```

Tin nhắn buổi tối (21h) tương tự nhưng đổi sang "Hôm nay đã đăng X bài" + "Ngày mai chờ Y bài".

## Khi nào sẽ thấy 🚨?

| Tình huống | Hành động em đề xuất trong tin nhắn |
|---|---|
| Bài Pending **quá giờ** mà chưa đăng | Check log GitHub Actions, có thể workflow fail |
| FB Token còn **≤ 14 ngày** | Refresh token (xem `docs/HUONG-DAN-REFRESH-TOKEN.md`) |
| FB Token còn **≤ 7 ngày** | 🚨 GẤP, refresh ngay |

Chị KHÔNG cần kiểm tra hàng ngày — tin nhắn chỉ "ồn ào" khi có chuyện. Bình thường thì kết thúc bằng `✅ Hệ thống OK, chị không cần làm gì.`
