# Hướng dẫn tạo Google Sheet + Apps Script

> **Mục đích:** Tạo Sheet "TMUN - Social Hub" làm trung tâm điều khiển — chị nhập lịch đăng tại đây, hệ thống tự đọc và đăng FB; sau đó tự ghi báo cáo về cùng Sheet.

> **Thời gian:** ~10 phút

---

## Bước 1 — Tạo Google Sheet mới

1. Vào https://sheets.new (sẽ tạo Sheet rỗng và auto save vào Drive)
2. Đặt tên Sheet: **TMUN - Social Hub**
3. Sheet hiển thị 1 tab `Sheet1` mặc định — để nguyên, Apps Script sẽ tự xử lý

---

## Bước 2 — Paste Apps Script

1. Trong Sheet, vào menu **Extensions → Apps Script**
2. Editor Apps Script mở tab mới
3. Trong file `Code.gs` mặc định — **xóa hết** code mặc định
4. Mở file `social-hub/apps-script/Code.gs` (em đã viết sẵn) → **copy toàn bộ**
5. Paste vào Apps Script editor
6. Bấm **Save** (Ctrl+S) hoặc icon dĩa mềm — Project name đặt là `TMUN Social Hub`

---

## Bước 3 — Chạy initSheets() để tạo 4 tab chuẩn

1. Trong Apps Script editor, ở thanh trên có dropdown "Select function" → chọn **initSheets**
2. Bấm nút **Run** (▶)
3. Lần đầu chạy → popup "Authorization required" → bấm **Review permissions**
4. Chọn tài khoản Google của chị
5. Hiện cảnh báo "Google hasn't verified this app" → bấm **Advanced** → **Go to TMUN Social Hub (unsafe)**
6. Bấm **Allow** ở popup permission cuối cùng

→ Quay lại Sheet, sẽ thấy 4 tab mới:
- **Lich dang** — nơi chị nhập nội dung
- **Bao cao** — hệ thống tự ghi insights vào đây
- **Phan tich** — pivot tự động từ Bao cao
- **Logs** — log debug

Tab `Sheet1` mặc định có thể xóa (chuột phải → Delete sheet).

---

## Bước 4 — Deploy Web App

1. Trong Apps Script editor, góc trên phải bấm **Deploy → New deployment**
2. Bên trái có icon ⚙️ Select type → chọn **Web app**
3. Điền form:
   - **Description**: `TMUN Social Hub v1`
   - **Execute as**: **Me** (tài khoản chị)
   - **Who has access**: **Anyone**
4. Bấm **Deploy**
5. Hiện popup "Authorize access" → bấm **Authorize access** → chọn tài khoản → Advanced → Allow
6. Sau khi deploy xong, hiện **Web app URL**, dạng:
   ```
   https://script.google.com/macros/s/AKfycbxxxxxxxxxx/exec
   ```
7. **Copy URL này** → gửi em (đây là `SHEETS_WEBHOOK_URL`)

⚠️ Lưu ý: URL này là semi-public — bất kỳ ai có URL đều gọi được. Tuy nhiên URL khó đoán (random 80 ký tự), không có quyền xem Sheet trực tiếp, chỉ gọi được các action đã define trong code. An toàn cho use case này.

---

## Bước 5 — Test nhanh

Mở URL Web App vừa copy, thêm `?action=ping` ở cuối:
```
https://script.google.com/macros/s/AKfycbxxxxxxxxxx/exec?action=ping
```

Phải hiện:
```json
{"ok": true, "message": "pong"}
```

Nếu hiện trang đăng nhập Google → chị deploy sai (Execute as Me + Anyone). Quay lại bước 4.

---

## Bước 6 — Cách chị dùng Sheet hàng ngày

Mở tab **Lich dang**, nhập 1 bài mới theo cấu trúc:

| STT | Ngay | Gio | Caption | Anh | Link gan | Channel | Post Type | Dang bai | Chu de | Status | Post ID | Posted At | Error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 28/05/2026 | 09:00 | "Sáng nay anh chị thử Thanh Can Thất Vị..." | https://thaomocuyennhien.com/images/banner-thanh-can.jpg | https://thaomocuyennhien.com/dat-hang | FB | photo | anh-don | san-pham | **Pending** | _(trống)_ | _(trống)_ | _(trống)_ |

**Quy tắc:**
- **Ngay**: định dạng `dd/MM/yyyy` hoặc kéo từ ô calendar
- **Gio**: định dạng `HH:mm` (vd `09:00`, `19:30`)
- **Caption**: nội dung bài đăng FB. Hỗ trợ xuống dòng (Alt+Enter trong ô)
- **Anh**: 1 URL ảnh public (Google Drive share public, hoặc URL trên website thaomocuyennhien.com). Nhiều ảnh phân tách bằng dấu `|` hoặc xuống dòng
- **Link gan**: link để gắn vào bài (link đặt hàng, blog...). Để trống nếu không cần
- **Channel**: chọn `FB` từ dropdown
- **Post Type**: chọn từ dropdown — `photo` / `carousel` / `link` / `text`
- **Dang bai**: chọn từ dropdown — dùng để phân tích sau (`anh-don` / `carousel` / `video` / `reel` / `text-thuong`)
- **Chu de**: chọn từ dropdown — phân tích hiệu quả theo chủ đề (`san-pham` / `educational` / `lifestyle` / `testimonial` / ...)
- **Status**: chọn **Pending** để hệ thống biết đăng
- **Post ID / Posted At / Error**: ĐỂ TRỐNG — hệ thống tự fill

Sau khi đăng xong, Status sẽ tự đổi thành **Posted**, kèm Post ID + thời gian đăng thực tế.

Nếu lỗi → Status = **Failed** + cột Error có lý do (vd "ảnh không truy cập được", "token hết hạn").

---

## Bước 7 — Cách upload ảnh để có URL public

Hai cách:

**Cách A — Dùng ảnh có sẵn trên website thaomocuyennhien.com:**
- URL trực tiếp dạng `https://thaomocuyennhien.com/images/abc.jpg`
- An toàn nhất, FB load ổn

**Cách B — Upload ảnh mới qua Google Drive:**
1. Upload ảnh vào Drive
2. Click phải → Share → Anyone with the link → Viewer
3. Copy URL share (dạng `https://drive.google.com/file/d/XXX/view`)
4. **Chuyển sang URL trực tiếp**: thay thành `https://drive.google.com/uc?export=view&id=XXX`
5. Paste URL trực tiếp này vào cột Anh

Hoặc dùng Cloudinary/Imgur free để upload nhanh hơn — em hỗ trợ chị setup sau.

---

## Checklist hoàn thành

- [ ] Tạo Sheet "TMUN - Social Hub"
- [ ] Paste Code.gs vào Apps Script
- [ ] Chạy initSheets() → có 4 tab
- [ ] Deploy Web App: Execute as Me, Anyone
- [ ] Test URL `?action=ping` → trả `pong`
- [ ] Gửi `SHEETS_WEBHOOK_URL` cho Claude
- [ ] Nhập thử 1 bài Pending vào tab `Lich dang`

Xong → quay lại README.md để cài GitHub Actions.
