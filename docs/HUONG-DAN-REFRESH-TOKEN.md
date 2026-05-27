# Hướng dẫn refresh Page Access Token (mỗi ~50 ngày)

> **Khi nào dùng doc này?** Khi GitHub auto tạo Issue tiêu đề "FB Page Token sắp hết hạn", hoặc khi bài đăng tự nhiên fail hết với error "Invalid OAuth access token".

> **Thời gian:** ~5 phút (vì chị đã quen flow này từ lần đầu setup)

---

## 5 bước nhanh

### Bước 1 — Vào Graph API Explorer

Mở: **https://developers.facebook.com/tools/explorer/**

Đảm bảo đã login Facebook bằng account Admin (chị Nông Quỳnh Trang).

---

### Bước 2 — Setup panel phải

| Field | Giá trị |
|---|---|
| Meta App | **`TMUN Auto Post`** ⚠️ (KHÔNG phải ClaudeTrang) — đây là App Live đang dùng cho production |
| User or Page | **Page Access Token** → chọn **Trà Thảo Mộc Uyên Nhiên chính hãng** |
| Permissions | Đảm bảo có đủ 7 scope: `read_insights`, `pages_show_list`, `business_management`, `pages_read_engagement`, `pages_read_user_content`, `pages_manage_posts`, `pages_manage_engagement` |

> ⚠️ **QUAN TRỌNG**: PHẢI chọn app `TMUN Auto Post` (ID 2079680712645253, đã Live Mode). Nếu chọn nhầm `ClaudeTrang` (App ID 953696197460822, ở Development Mode), token mới sẽ KHÔNG cho bài public với người ngoài. Em đã verify điểm này 2026-05-27.

→ Bấm **Generate Access Token** màu xanh.

→ Popup hiện ra → Continue → tick Page Thảo Mộc Uyên Nhiên chính hãng → Done.

---

### Bước 3 — Copy token mới

Token mới xuất hiện ở ô **"Mã truy cập"** trên cùng panel phải. Đây là Page Token mới sống 60 ngày.

**KHÔNG paste vào chat hay email** — copy thẳng vào clipboard.

---

### Bước 4 — Update GitHub Secret

1. Mở: https://github.com/quynhtrangls95-beep/tmun-social-hub/settings/secrets/actions
2. Tìm secret tên **`FB_PAGE_ACCESS_TOKEN`**
3. Bấm **Update** (icon bút chì bên phải tên secret)
4. Paste token mới vào ô **Secret** (đè lên token cũ)
5. Bấm **Update secret**

→ Token cũ bị overwrite, secret mới active ngay lập tức cho workflow tiếp theo.

---

### Bước 5 — Verify

1. Mở: https://github.com/quynhtrangls95-beep/tmun-social-hub/actions/workflows/token-health-check.yml
2. Bấm **Run workflow** → branch `main` → **Run workflow**
3. Đợi 30 giây → click vào run mới → tab Summary → phải hiện:
   ```
   OK: Token healthy
   - Type: PAGE
   - Page ID: 1063264180209204
   - Valid: True
   - Days remaining: 60 days
   ```
4. Quay lại tab Issues của repo → đóng (close) issue "FB Page Token sắp hết hạn" cũ.

→ **Xong.** Hệ thống chạy lại bình thường.

---

## Verify trên Token Debugger (optional)

Nếu chị muốn double-check trong UI Facebook:

1. Mở https://developers.facebook.com/tools/debug/accesstoken/
2. Paste token mới → bấm Gỡ lỗi
3. Verify:
   - Loại: **Page**
   - ID trang: **1063264180209204** (Thảo Mộc Uyên Nhiên chính hãng)
   - Hết hạn: ~60 ngày sau
   - Phạm vi: có đủ 7 scope

---

## Nếu chị muốn upgrade lên Never-expire

Doc này hướng dẫn refresh 60 ngày. Nếu chị mệt vì làm lại 6 lần/năm, có thể **upgrade lên Never-expire** (làm 1 lần dùng mãi):

1. Lấy App Secret từ dashboard ClaudeTrang → Cài đặt → Cơ bản
2. Chạy PowerShell script local (em sẽ viết nếu chị yêu cầu)
3. Lưu kết quả vào GitHub Secret

→ Khi nào chị muốn, nói em "upgrade token Never-expire" — em hướng dẫn ngay.

---

## Troubleshooting

| Lỗi | Nguyên nhân | Fix |
|---|---|---|
| Bấm Generate Access Token → popup không hiện | Chị bị logout FB → login lại |
| Token mới Expire chỉ 1-2h | Chị chọn sai dropdown "User Token" thay vì "Page Token" | Quay lại Bước 2 chọn lại |
| Update GitHub Secret xong vẫn lỗi | Workflow đang chạy cache token cũ | Chạy tay workflow `publish` để force refresh |
| Token vừa lấy đã chết | Trùng thời điểm FB security check | Đợi 5 phút, generate lại |
