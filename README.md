# TMUN Social Hub

> Tự động đăng bài Facebook + báo cáo đo lường cho **Thảo Mộc Uyên Nhiên**.

Hệ thống cho phép chị Quỳnh Trang nhập lịch nội dung vào Google Sheet, hệ thống tự đăng FB đúng giờ, sau đó tự fetch insights ghi ngược về Sheet để phân tích dạng bài nào hiệu quả nhất.

---

## Kiến trúc

```
┌──────────────────────┐
│  Google Sheet        │  ← chị nhập lịch + caption + ảnh
│  (TMUN Social Hub)   │
└──────────┬───────────┘
           │ Apps Script Web App (REST endpoint)
           │
┌──────────▼───────────┐
│  GitHub Actions      │
│  - publish.py        │  cron mỗi 15ph: đọc Sheet, đăng FB
│  - report.py         │  cron 7h & 22h: fetch insights, ghi Sheet
└──────────┬───────────┘
           │ Meta Graph API v21.0
           │
┌──────────▼───────────┐
│  Facebook Fanpage    │
│  Thảo Mộc Uyên Nhiên │
└──────────────────────┘
```

---

## Components

| Folder | Mục đích |
|---|---|
| `scripts/fb_api.py` | Wrapper Facebook Graph API (post + insights) |
| `scripts/sheets.py` | Wrapper Google Sheet qua Apps Script Web App |
| `scripts/publish.py` | Cron đăng bài theo lịch trong Sheet |
| `scripts/report.py` | Cron fetch insights ghi vào Sheet "Bao cao" |
| `apps-script/Code.gs` | Code paste vào Google Apps Script (Sheet backend) |
| `.github/workflows/publish.yml` | Cron */15p chạy publish.py |
| `.github/workflows/report.yml` | Cron 7h & 22h chạy report.py |
| `docs/HUONG-DAN-LAY-TOKEN.md` | Hướng dẫn lấy FB Page Access Token |
| `docs/HUONG-DAN-GOOGLE-SHEET.md` | Hướng dẫn setup Sheet + Apps Script |
| `docs/HUONG-DAN-GITHUB.md` | Hướng dẫn push repo + cài secrets |

---

## Setup từ đầu (cho chị Quỳnh Trang)

Làm tuần tự 3 bước, mỗi bước ~10-20 phút. Tổng ~45 phút.

### Bước 1: Lấy Facebook Page Access Token
→ Đọc [`docs/HUONG-DAN-LAY-TOKEN.md`](docs/HUONG-DAN-LAY-TOKEN.md)

Kết quả: có 2 giá trị `FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN`

### Bước 2: Tạo Google Sheet + deploy Apps Script
→ Đọc [`docs/HUONG-DAN-GOOGLE-SHEET.md`](docs/HUONG-DAN-GOOGLE-SHEET.md)

Kết quả: có Sheet "TMUN - Social Hub" với 4 tab + URL `SHEETS_WEBHOOK_URL`

### Bước 3: Deploy lên GitHub Actions
→ Đọc [`docs/HUONG-DAN-GITHUB.md`](docs/HUONG-DAN-GITHUB.md)

Kết quả: workflows chạy tự động trên GitHub, miễn phí.

---

## Cách dùng hàng ngày

1. Mở Sheet "TMUN - Social Hub" → tab **Lich dang**
2. Thêm 1 row mới:
   - **Ngay**: ngày muốn đăng (28/05/2026)
   - **Gio**: giờ muốn đăng (09:00)
   - **Caption**: nội dung bài
   - **Anh**: URL ảnh public
   - **Link gan**: link đặt hàng (optional)
   - **Channel**: FB
   - **Post Type**: photo / carousel / link / text
   - **Dang bai**: anh-don / carousel / video / reel / text-thuong (để phân tích)
   - **Chu de**: san-pham / educational / lifestyle / testimonial / ...
   - **Status**: **Pending**
3. Đợi đến giờ → hệ thống auto đăng → Status chuyển thành **Posted**
4. 7h sáng hôm sau → tab **Bao cao** có sẵn insights bài đó
5. Tab **Phan tich** cho biết:
   - Dạng bài nào có ER (Engagement Rate) cao nhất
   - Chủ đề nào ra click nhiều nhất (→ ra đơn nhiều nhất)
   - Giờ nào đăng tốt nhất
   - Top 10 bài hot nhất 30 ngày qua

---

## Test local (cho dev)

```powershell
cd D:\thaomocuyennhien.com\social-hub

# Cài Python 3.12+ trước
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Set env tạm
$env:FB_PAGE_ID="123..."
$env:FB_PAGE_ACCESS_TOKEN="EAAxxx..."
$env:SHEETS_WEBHOOK_URL="https://script.google.com/macros/s/.../exec"

# Chạy publish (chỉ đăng bài có Status=Pending và đã đến giờ)
python scripts/publish.py

# Chạy report (fetch insights tất cả bài đã đăng trong 30 ngày)
python scripts/report.py
```

---

## Roadmap (sau khi phase 1 chạy ổn)

- **Phase 2**: Thêm Instagram khi có IG Business account link với Page
- **Phase 3**: Báo cáo tuần auto email/Zalo OA mỗi sáng thứ Hai
- **Phase 4**: TikTok (cần apply Content Posting API, ~1-2 tuần TikTok duyệt)
- **Phase 5**: AI gợi ý caption từ ảnh + best time để đăng dựa trên historical data

---

## Troubleshooting

| Triệu chứng | Nguyên nhân | Fix |
|---|---|---|
| Workflow GitHub Actions đỏ, log "Invalid OAuth access token" | FB token đã chết | Làm lại bước 3-5 của `HUONG-DAN-LAY-TOKEN.md`, update secret |
| Bài đăng được nhưng cột Post ID rỗng | Apps Script Web App URL sai hoặc deploy chưa "Anyone" | Re-deploy với Execute as Me + Anyone |
| Insights luôn = 0 | Post mới đăng <30 phút, FB chưa tổng hợp metric | Đợi cron 7h hôm sau |
| Status không chuyển từ Pending → Posted | publish.py chưa chạy (chưa đến cron tiếp theo) hoặc đã chạy nhưng fail | Vào tab Actions xem log run gần nhất |
| Cron không tự chạy mặc dù workflow_dispatch chạy được | Repo chưa active commit trong 60 ngày → GitHub disable cron tự động | Push 1 commit trống để activate lại |

---

## Bảo mật

- Token & URL secret **chỉ lưu ở GitHub Secrets** (encrypted at rest), không bao giờ commit code
- Apps Script Web App là semi-public nhưng URL random 80 ký tự, action validation strict, không có endpoint nguy hiểm
- Repo PRIVATE — chỉ chị Quỳnh Trang + collaborator được mời mới truy cập
- Page Access Token có scope hẹp: chỉ `pages_manage_posts` + `pages_read_engagement` + `read_insights` — không có quyền đọc inbox, không có quyền billing

---

Liên hệ: chị Quỳnh Trang — `quynhtrangls95@gmail.com`
