# Hướng dẫn cài đặt GitHub Actions (server cron miễn phí)

> **Mục đích:** Deploy script Python lên GitHub Actions để chạy tự động — không cần PC chị bật 24/7, không cần VPS, hoàn toàn miễn phí.

> **Thời gian:** ~10 phút

> **Tiền đề:** Chị đã có:
> - GitHub account (`quynhtrangls95-beep` — đã có sẵn từ repo thaomocuyennhien)
> - `FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN` (từ HUONG-DAN-LAY-TOKEN.md)
> - `SHEETS_WEBHOOK_URL` (từ HUONG-DAN-GOOGLE-SHEET.md)

---

## Bước 1 — Tạo repo private

1. Vào https://github.com/new
2. Repository name: `tmun-social-hub`
3. **Private** ✅ (quan trọng — vì sẽ chứa secrets gián tiếp)
4. Description: `Auto đăng bài & báo cáo FB cho Thảo Mộc Uyên Nhiên`
5. **KHÔNG tick** "Add a README" / "Add .gitignore" / "Add license" (vì code đã có sẵn)
6. Bấm **Create repository**

---

## Bước 2 — Push code từ máy chị lên GitHub

Mở PowerShell trong folder `D:\thaomocuyennhien.com\social-hub\`:

```powershell
cd D:\thaomocuyennhien.com\social-hub
git init
git add .
git commit -m "Initial: TMUN Social Hub"
git branch -M main
git remote add origin https://github.com/quynhtrangls95-beep/tmun-social-hub.git
git push -u origin main
```

Lần đầu push → GitHub có thể hỏi đăng nhập:
- Username: `quynhtrangls95-beep`
- Password: dùng **Personal Access Token** (không phải password Github thường)
  - Tạo tại: https://github.com/settings/tokens/new
  - Note: `tmun-deploy`
  - Expiration: 90 days
  - Scopes: tick `repo` (full)
  - Generate → copy token → paste vào prompt password

---

## Bước 3 — Cài 3 GitHub Secrets

1. Vào repo: https://github.com/quynhtrangls95-beep/tmun-social-hub
2. Tab **Settings** (trên cùng repo, sát phải)
3. Sidebar trái: **Secrets and variables → Actions**
4. Bấm **New repository secret** lần lượt 3 lần:

| Name | Value |
|---|---|
| `FB_PAGE_ID` | (paste Page ID từ token guide) |
| `FB_PAGE_ACCESS_TOKEN` | (paste Page Access Token — token dài bắt đầu bằng `EAA...`) |
| `SHEETS_WEBHOOK_URL` | (paste URL Web App từ sheet guide — dạng `https://script.google.com/macros/s/.../exec`) |

Sau khi cài xong, mục Secrets sẽ hiện 3 secret tên trên (nội dung không xem lại được — đúng).

---

## Bước 4 — Test workflow chạy tay

1. Vào tab **Actions** trên repo
2. Lần đầu sẽ hiện cảnh báo "Workflows aren't being run on this forked repository" → bấm **I understand my workflows, go ahead and enable them**
3. Sidebar trái có 2 workflow:
   - **Dang bai Facebook tu dong**
   - **Bao cao Insights Facebook**
4. Bấm vào "Dang bai Facebook tu dong"
5. Bên phải bấm **Run workflow** → branch `main` → **Run workflow** (xanh)
6. Đợi 30-60 giây → click vào run mới xuất hiện
7. Xem log:
   - Nếu OK: log có dòng `Page OK: Thảo Mộc Uyên Nhiên (...)`
   - Nếu fail: copy error gửi em debug

Test tương tự với "Bao cao Insights Facebook".

---

## Bước 5 — Verify cron đã active

1. Tab Actions của repo
2. Sidebar trái → bấm workflow "Dang bai Facebook tu dong"
3. Bên phải có dòng "This workflow has a `workflow_dispatch` event trigger"
4. Sau khi workflow chạy 1 lần thành công, GitHub sẽ tự enable cron schedule
5. Cron tiếp theo sẽ chạy theo lịch:
   - **publish.py**: mỗi 15 phút từ 7h-23h VN
   - **report.py**: 7h sáng VN + 22h tối VN mỗi ngày

> ⚠️ GitHub Actions có thể delay cron 5-10 phút khi server tải nặng — đăng bài có thể đến chậm 10 phút so với giờ chị set trong Sheet. Đây là giới hạn của GitHub free tier, không sửa được.

---

## Bước 6 — Theo dõi sức khỏe hệ thống

Mỗi tuần chị check 3 thứ:

1. **Tab Actions trên GitHub** — workflow gần nhất có ✅ xanh không? Nếu đỏ → click vào xem error → gửi em.
2. **Sheet `Logs`** — có dòng `ERROR` nào trong 7 ngày qua không?
3. **Sheet `Lich dang`** — có bài nào Status = `Failed` không?

Token Page Access Token theoretically không hết hạn, nhưng nếu chị đổi password FB hoặc revoke app → token chết. Triệu chứng: tất cả bài fail với error "Invalid OAuth access token".

→ Khi đó chỉ cần làm lại bước 3-5 của HUONG-DAN-LAY-TOKEN.md (5 phút) + update lại secret `FB_PAGE_ACCESS_TOKEN` trên GitHub.

---

## Chi phí thực tế

| Tài nguyên | Free tier | Tiêu thụ dự kiến | Còn dư |
|---|---|---|---|
| GitHub Actions (private repo) | 2000 phút/tháng | ~600-900 phút/tháng | ✅ |
| Google Apps Script | 90 phút runtime/ngày | ~5 phút/ngày | ✅ |
| Google Sheets | Không giới hạn | — | ✅ |
| Facebook Graph API | Rate limit ~200 calls/giờ/user | ~10 calls/giờ peak | ✅ |

→ **Chi phí: 0đ/tháng** cho phase 1.

---

## Checklist hoàn thành

- [ ] Tạo repo private `tmun-social-hub`
- [ ] Push code lên GitHub
- [ ] Add 3 secrets: FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, SHEETS_WEBHOOK_URL
- [ ] Run workflow `publish` thủ công → thấy log "Page OK"
- [ ] Run workflow `report` thủ công → thấy log "Fetch insights"
- [ ] Verify cron sẽ tự chạy theo lịch

Xong → hệ thống đã live. Quay lại Sheet, đổi 1 bài thử thành Pending với giờ là 5 phút sau, đợi xem có tự đăng không!
