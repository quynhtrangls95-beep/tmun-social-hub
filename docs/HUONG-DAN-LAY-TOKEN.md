# Hướng dẫn lấy Facebook Page Access Token

> **Mục đích:** Lấy 2 giá trị `FB_PAGE_ID` và `FB_PAGE_ACCESS_TOKEN` để hệ thống tự đăng bài lên Fanpage **Trà Thảo Mộc Uyên Nhiên chính hãng**.

> **Thời gian:** Chị làm khoảng **10-15 phút**.

> ⚠️ **Lifecycle token:** Token Page Access mặc định sống **60 ngày**, không phải vĩnh viễn. Có thể upgrade Never-expire qua App Secret (xem cuối doc). Khi token sắp hết hạn, GitHub auto tạo Issue cảnh báo + chị làm theo [`HUONG-DAN-REFRESH-TOKEN.md`](HUONG-DAN-REFRESH-TOKEN.md) (5 phút).

> **Ai làm được:** Chị Quỳnh Trang phải là **Admin Fanpage** Thảo Mộc Uyên Nhiên. (Đã confirm xong.)

---

## Bước 1 — Tạo Meta App

1. Vào https://developers.facebook.com/apps/
2. Bấm nút **Create App** (góc trên phải, màu xanh)
3. Use case: chọn **Other** → bấm Next
4. App type: chọn **Business** → bấm Next
5. Điền:
   - App name: `TMUN Social Hub`
   - App contact email: email của chị
   - Business portfolio: (để trống được, chọn No business portfolio nếu chưa có)
6. Bấm **Create app** → xác minh password

→ App đã được tạo. Ghi nhớ App ID hiển thị ở dashboard.

---

## Bước 2 — Add product "Facebook Login for Business"

1. Trong dashboard app vừa tạo, kéo xuống mục **Add products to your app**
2. Tìm **Facebook Login for Business** → bấm **Set up**
3. Bên trái menu, chọn **Facebook Login for Business** → **Settings**
4. Trong "Valid OAuth Redirect URIs", paste:
   ```
   https://developers.facebook.com/tools/explorer/callback
   ```
5. Bấm Save changes

---

## Bước 3 — Lấy User Access Token

1. Vào https://developers.facebook.com/tools/explorer/
2. Góc trên phải:
   - **Meta App**: chọn `TMUN Social Hub`
   - **User or Page**: chọn `User Token`
3. Bấm **Add a Permission** → tick các quyền:
   - ✅ `pages_show_list`
   - ✅ `pages_read_engagement`
   - ✅ `pages_manage_posts`
   - ✅ `pages_manage_engagement`
   - ✅ `read_insights`
   - ✅ `business_management`
4. Bấm **Generate Access Token** (màu xanh)
5. Facebook popup hiện ra → bấm **Continue as [tên chị]** → tick Fanpage **Thảo Mộc Uyên Nhiên** → **Continue** → **Save**
6. Token sẽ xuất hiện trong ô **Access Token**. Copy lại token này — gọi là **USER_TOKEN** (token này chỉ sống 1-2 giờ, bước tiếp theo sẽ đổi thành long-lived)

---

## Bước 4 — Đổi User Token thành Long-Lived (60 ngày)

1. Trong Graph API Explorer, vẫn còn USER_TOKEN ở ô Access Token
2. Bên dưới có chữ **Debug** màu xanh — bấm vào
3. Trang Access Token Debugger mở ra, kéo xuống cuối có nút **Extend Access Token** → bấm
4. Một token mới xuất hiện → copy lại — gọi là **LONG_LIVED_USER_TOKEN** (sống 60 ngày)

---

## Bước 5 — Đổi tiếp thành Page Access Token (KHÔNG HẾT HẠN)

> Đây là bước quan trọng — Page Access Token được derive từ Long-Lived User Token sẽ **không có expiry date**, dùng vĩnh viễn (trừ khi chị đổi pass FB hoặc revoke quyền).

1. Quay lại https://developers.facebook.com/tools/explorer/
2. Paste **LONG_LIVED_USER_TOKEN** vào ô Access Token (đè lên token cũ)
3. Trong ô query phía dưới, gõ:
   ```
   me/accounts
   ```
4. Bấm nút **Submit** (mũi tên xanh bên phải)
5. Response sẽ liệt kê tất cả Fanpage chị quản lý, dạng:
   ```json
   {
     "data": [
       {
         "access_token": "EAAxxx...rất dài...",   ← đây là PAGE_ACCESS_TOKEN
         "category": "Health/beauty",
         "id": "123456789012345",                  ← đây là PAGE_ID
         "name": "Thảo Mộc Uyên Nhiên",
         ...
       }
     ]
   }
   ```
6. Tìm dòng có `"name": "Thảo Mộc Uyên Nhiên"`:
   - Copy giá trị `access_token` → đây là **FB_PAGE_ACCESS_TOKEN** chị cần
   - Copy giá trị `id` → đây là **FB_PAGE_ID** chị cần

---

## Bước 6 — Verify token đúng

1. Mở tab mới: https://developers.facebook.com/tools/debug/accesstoken/
2. Paste **FB_PAGE_ACCESS_TOKEN** → bấm **Debug**
3. Verify các trường:
   - **App**: ClaudeTrang ✅
   - **Type**: Page ✅
   - **Profile ID**: trùng với FB_PAGE_ID ✅
   - **Expires**: ~60 ngày sau ✅ (token Page mặc định sống 60 ngày)
   - **Scopes**: có đủ `pages_manage_posts`, `pages_read_engagement`, `read_insights` ✅

Nếu Expires < 24 giờ → chị chọn sai dropdown User Token thay vì Page Token. Quay lại bước 4 chọn lại.

---

## Bước 7 — Lưu 2 giá trị này

Mở Notepad, lưu 2 giá trị này tạm thời:

```
FB_PAGE_ID=123456789012345
FB_PAGE_ACCESS_TOKEN=EAAxxx...rất dài...
```

Sau đó gửi cho em qua Zalo/tin nhắn riêng để em add vào GitHub Secrets (TUYỆT ĐỐI KHÔNG public trên website, KHÔNG commit vào git).

⚠️ Nếu chị lỡ share token ở chỗ công khai → vào https://www.facebook.com/settings/?tab=business_tools để revoke app + làm lại từ Bước 1.

---

## Bước 8 — App Review (chỉ cần khi muốn dùng cho user khác)

Hiện tại app đang ở **Development mode** → chỉ chị (Admin app) dùng được. Chị **KHÔNG cần** request App Review vì hệ thống này chỉ phục vụ duy nhất Fanpage của chị, không cho user khác đăng nhập.

→ Không cần làm gì thêm. Skip section này.

---

## FAQ

**Q: Token có thật sự không hết hạn không?**  
A: **KHÔNG.** Em đã ghi sai ở bản doc cũ — Page Access Token mặc định sống **60 ngày**, không phải vĩnh viễn. Mỗi ~50 ngày chị cần refresh 1 lần (theo `HUONG-DAN-REFRESH-TOKEN.md`, 5 phút). GitHub auto tạo Issue cảnh báo khi còn <14 ngày.

Token cũng có thể chết sớm hơn 60 ngày nếu:
- Chị đổi mật khẩu Facebook
- Chị log out tất cả device
- Chị revoke quyền của app ClaudeTrang
- Facebook detect bất thường (đăng spam)

**Q: Có cách nào lấy Never-expire không?**  
A: Có — cần thêm bước với **App Secret**. App Secret là chuỗi nhạy cảm, không paste vào chat. Nếu chị muốn upgrade Never-expire, bảo Claude "viết script lấy token vĩnh viễn", em sẽ viết PowerShell script chạy local — chị chỉ paste App Secret vào terminal của chị, KHÔNG đi qua chat.

**Q: Sao em không dùng OAuth flow chuẩn?**  
A: OAuth flow cần web server + redirect URL có HTTPS. Hệ thống này chỉ chạy 1 user (chị) nên dùng cách lấy token tay đơn giản hơn và an toàn hơn.

**Q: Nếu sau này muốn thêm Instagram?**  
A: IG dùng chung Page Access Token này (qua Meta Graph API). Phase 2 em sẽ hướng dẫn chị link IG Business với Fanpage rồi enable trong code.

**Q: Page ID lấy nhanh hơn cách nào?**  
A: Vào Fanpage Thảo Mộc Uyên Nhiên → About → kéo xuống dưới cùng → mục "Page ID". Hoặc dùng cách Bước 5 (chính xác hơn).

---

## Checklist hoàn thành

- [ ] Tạo Meta App "TMUN Social Hub"
- [ ] Add product Facebook Login for Business
- [ ] Generate User Token với 6 permissions
- [ ] Extend User Token → Long-lived (60 ngày)
- [ ] Query `me/accounts` → lấy Page Access Token
- [ ] Verify Expires = **Never** trong Debugger
- [ ] Lưu FB_PAGE_ID + FB_PAGE_ACCESS_TOKEN
- [ ] Gửi 2 giá trị cho Claude qua kênh riêng

Xong checklist này → quay lại README.md để tiếp tục bước cài Google Sheet.
