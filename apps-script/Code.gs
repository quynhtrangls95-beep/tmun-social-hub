/**
 * Thao Moc Uyen Nhien - Social Hub
 * Google Apps Script Web App
 *
 * Cach setup (chi Quynh Trang lam 1 lan):
 *  1. Mo Google Sheet TMUN - Social Hub
 *  2. Extensions -> Apps Script -> paste file nay vao Code.gs
 *  3. Chay function initSheets() 1 lan -> tao 4 tab voi header chuan
 *  4. Deploy -> New deployment -> Type: Web app
 *     - Execute as: Me (quynhtrangls95@gmail.com)
 *     - Who has access: Anyone
 *     -> Copy Web App URL gui em
 *  5. Moi lan sua code -> Deploy -> Manage deployments -> Edit -> New version
 */

const TZ = "Asia/Ho_Chi_Minh";

const SHEET_SCHEDULE = "Lich dang";
const SHEET_REPORT = "Bao cao";
const SHEET_ANALYSIS = "Phan tich";
const SHEET_LOGS = "Logs";

// Folder Drive chua anh dang FB. Apps Script chay as chi nen
// folder co the PRIVATE (chi chi share voi minh) — an toan hon.
const DRIVE_FOLDER_ID = "1AemHaJ_-1Mt6ce9QnHrhchvm2b3TPBEF"; // TMUN-Anh-FB

const SCHEDULE_HEADER = [
  "STT", "Ngay", "Gio", "Caption", "Anh (URL, nhieu anh cach |)",
  "Link gan", "Channel", "Post Type", "Dang bai", "Chu de",
  "Status", "Post ID", "Posted At", "Error",
];

const REPORT_HEADER = [
  "Post ID", "Posted At", "Caption (preview)", "Dang bai", "Chu de",
  "Reach", "Impressions", "Reactions", "Comments", "Shares",
  "Link Clicks", "Engagement Rate (%)", "Click Rate (%)", "Updated At",
];

const LOGS_HEADER = ["Timestamp", "Level", "Message"];

// =====================================================================
// SETUP - chay 1 lan
// =====================================================================

function initSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  ensureSheetWithHeader_(ss, SHEET_SCHEDULE, SCHEDULE_HEADER);
  ensureSheetWithHeader_(ss, SHEET_REPORT, REPORT_HEADER);
  ensureSheetWithHeader_(ss, SHEET_LOGS, LOGS_HEADER);
  setupAnalysisSheet_(ss);
  applySchedulingValidation_(ss);

  SpreadsheetApp.getUi().alert(
    "Setup xong! 4 tab da duoc tao.\n\n" +
    "Tiep theo: Deploy -> New deployment -> Web app -> " +
    "Execute as Me, Anyone -> copy URL gui Claude."
  );
}

function ensureSheetWithHeader_(ss, name, header) {
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
  }
  sh.getRange(1, 1, 1, header.length)
    .setValues([header])
    .setFontWeight("bold")
    .setBackground("#1f4e3d")
    .setFontColor("#ffffff");
  sh.setFrozenRows(1);
  sh.autoResizeColumns(1, header.length);
}

function setupAnalysisSheet_(ss) {
  let sh = ss.getSheetByName(SHEET_ANALYSIS);
  if (!sh) sh = ss.insertSheet(SHEET_ANALYSIS);
  sh.clear();

  sh.getRange("A1").setValue("PHAN TICH HIEU QUA CONTENT")
    .setFontSize(16).setFontWeight("bold").setFontColor("#1f4e3d");

  const PLACEHOLDER = '"Chua co du lieu — pivot se hien sau khi co bai dang dau tien va co insights"';

  // 1. Hieu qua theo dang bai
  sh.getRange("A3").setValue("1. Engagement Rate trung binh theo Dang bai")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A4").setFormula(
    `=IFERROR(QUERY('${SHEET_REPORT}'!A:N, "SELECT D, AVG(L), AVG(M), COUNT(A) WHERE D IS NOT NULL GROUP BY D LABEL D 'Dang bai', AVG(L) 'ER TB (%)', AVG(M) 'CR TB (%)', COUNT(A) 'So bai'", 1), ${PLACEHOLDER})`
  );

  // 2. Hieu qua theo chu de
  sh.getRange("F3").setValue("2. Engagement Rate trung binh theo Chu de")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("F4").setFormula(
    `=IFERROR(QUERY('${SHEET_REPORT}'!A:N, "SELECT E, AVG(L), AVG(M), COUNT(A) WHERE E IS NOT NULL GROUP BY E LABEL E 'Chu de', AVG(L) 'ER TB (%)', AVG(M) 'CR TB (%)', COUNT(A) 'So bai'", 1), ${PLACEHOLDER})`
  );

  // 3. Top 10 bai engagement cao nhat
  sh.getRange("A12").setValue("3. TOP 10 bai Engagement Rate cao nhat (30 ngay)")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A13").setFormula(
    `=IFERROR(QUERY('${SHEET_REPORT}'!A:N, "SELECT B, C, D, E, F, L ORDER BY L DESC LIMIT 10 LABEL B 'Posted', C 'Caption', D 'Dang', E 'Chu de', F 'Reach', L 'ER (%)'", 1), ${PLACEHOLDER})`
  );

  // 4. Top 10 bai ra click nhieu nhat
  sh.getRange("A26").setValue("4. TOP 10 bai ra Click nhieu nhat (kha nang ra don)")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A27").setFormula(
    `=IFERROR(QUERY('${SHEET_REPORT}'!A:N, "SELECT B, C, D, E, K, M ORDER BY K DESC LIMIT 10 LABEL B 'Posted', C 'Caption', D 'Dang', E 'Chu de', K 'Clicks', M 'CR (%)'", 1), ${PLACEHOLDER})`
  );

  // 5. Hieu qua theo gio dang
  sh.getRange("A40").setValue("5. Engagement Rate trung binh theo Gio dang")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A41").setFormula(
    `=IFERROR(QUERY('${SHEET_REPORT}'!A:N, "SELECT HOUR(B), AVG(L), COUNT(A) WHERE B IS NOT NULL GROUP BY HOUR(B) ORDER BY HOUR(B) LABEL HOUR(B) 'Gio', AVG(L) 'ER TB (%)', COUNT(A) 'So bai'", 1), ${PLACEHOLDER})`
  );

  sh.setFrozenRows(2);
}

function applySchedulingValidation_(ss) {
  const sh = ss.getSheetByName(SHEET_SCHEDULE);
  const lastRow = Math.max(sh.getMaxRows(), 500);

  // Channel = FB (phase 1)
  const channelRange = sh.getRange(2, 7, lastRow - 1, 1);
  channelRange.setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(["FB"], true).build()
  );

  // Post Type
  const typeRange = sh.getRange(2, 8, lastRow - 1, 1);
  typeRange.setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(["photo", "carousel", "link", "text"], true).build()
  );

  // Dang bai (cho phan tich)
  const formRange = sh.getRange(2, 9, lastRow - 1, 1);
  formRange.setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(["anh-don", "carousel", "video", "reel", "text-thuong"], true).build()
  );

  // Chu de
  const topicRange = sh.getRange(2, 10, lastRow - 1, 1);
  topicRange.setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList([
        "san-pham", "educational", "lifestyle", "testimonial",
        "behind-the-scenes", "promo", "story-thuong-hieu",
      ], true).build()
  );

  // Status
  const statusRange = sh.getRange(2, 11, lastRow - 1, 1);
  statusRange.setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(["Pending", "Posted", "Failed", "Skip"], true).build()
  );
}

// =====================================================================
// WEB APP ENDPOINTS
// =====================================================================

function doGet(e) {
  const action = (e.parameter.action || "").trim();
  try {
    if (action === "list_pending") return jsonResponse_({ ok: true, data: listPending_() });
    if (action === "list_posted") return jsonResponse_({ ok: true, data: listPosted_() });
    if (action === "daily_summary") return jsonResponse_({ ok: true, data: dailySummary_() });
    if (action === "get_image") return jsonResponse_({ ok: true, data: getImage_(e.parameter.name || "") });
    if (action === "list_images") return jsonResponse_({ ok: true, data: listImages_() });
    if (action === "ping") return jsonResponse_({ ok: true, message: "pong" });
    return jsonResponse_({ ok: false, error: "Unknown action: " + action });
  } catch (err) {
    return jsonResponse_({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  let payload;
  try {
    payload = JSON.parse(e.postData.contents);
  } catch (_) {
    return jsonResponse_({ ok: false, error: "Body khong phai JSON" });
  }
  const action = (payload.action || "").trim();
  try {
    if (action === "mark_posted") return jsonResponse_(markPosted_(payload));
    if (action === "mark_failed") return jsonResponse_(markFailed_(payload));
    if (action === "save_insights") return jsonResponse_(saveInsights_(payload));
    if (action === "log") return jsonResponse_(logRow_(payload));
    if (action === "add_row") return jsonResponse_(addRow_(payload));
    if (action === "bulk_add") return jsonResponse_(bulkAdd_(payload));
    if (action === "reset_pending") return jsonResponse_(resetPending_(payload));
    if (action === "delete_row") return jsonResponse_(deleteRow_(payload));
    return jsonResponse_({ ok: false, error: "Unknown action: " + action });
  } catch (err) {
    return jsonResponse_({ ok: false, error: String(err) });
  }
}

function jsonResponse_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// =====================================================================
// BUSINESS LOGIC
// =====================================================================

function listPending_() {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const data = sh.getDataRange().getValues();
  const now = new Date();
  const out = [];

  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    const status = (r[10] || "").toString().trim();
    if (status !== "Pending") continue;

    const ngay = r[1];
    const gio = r[2];
    const scheduledAt = combineDateTime_(ngay, gio);
    if (!scheduledAt || scheduledAt > now) continue;

    out.push({
      row: i + 1,
      caption: r[3] || "",
      images: r[4] || "",
      link: r[5] || "",
      channel: r[6] || "FB",
      post_type: r[7] || "",
      form: r[8] || "",
      topic: r[9] || "",
    });
  }
  return out;
}

function listPosted_() {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const data = sh.getDataRange().getValues();
  const cutoff = new Date(Date.now() - 30 * 86400 * 1000);
  const out = [];

  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    const status = (r[10] || "").toString().trim();
    if (status !== "Posted") continue;
    const postId = (r[11] || "").toString().trim();
    if (!postId) continue;

    const postedAt = parseTimestamp_(r[12]);
    if (postedAt && postedAt < cutoff) continue;

    out.push({
      row: i + 1,
      post_id: postId,
      posted_at: r[12] || "",
      caption: (r[3] || "").toString().substring(0, 100),
      form: r[8] || "",
      topic: r[9] || "",
    });
  }
  return out;
}

function dailySummary_() {
  /**
   * Tong hop thong tin cho daily report Telegram.
   * Tra ve {
   *   today, now_iso,
   *   pending_today[], pending_tomorrow[], overdue_pending[],
   *   posted_yesterday[], posted_today[],
   *   posted_last_7_days, failed_last_7_days,
   *   total_pending, upcoming_pending
   * }
   */
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const data = sh.getDataRange().getValues();
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const tomorrow = new Date(today.getTime() + 86400000);
  const yesterday = new Date(today.getTime() - 86400000);
  const sevenDaysAgo = new Date(today.getTime() - 7 * 86400000);

  const todayStr = Utilities.formatDate(today, TZ, "yyyy-MM-dd");
  const yesterdayStr = Utilities.formatDate(yesterday, TZ, "yyyy-MM-dd");
  const tomorrowStr = Utilities.formatDate(tomorrow, TZ, "yyyy-MM-dd");

  const out = {
    today: todayStr,
    now_iso: Utilities.formatDate(now, TZ, "yyyy-MM-dd HH:mm:ss"),
    pending_today: [],
    pending_tomorrow: [],
    overdue_pending: [],
    posted_yesterday: [],
    posted_today: [],
    posted_last_7_days: 0,
    failed_last_7_days: 0,
    total_pending: 0,
    upcoming_pending: 0,
  };

  for (let i = 1; i < data.length; i++) {
    const r = data[i];
    const ngay = r[1];
    const gio = r[2];
    const captionPreview = (r[3] || "").toString().substring(0, 100);
    const status = (r[10] || "").toString().trim();
    const postId = (r[11] || "").toString().trim();
    const postedAt = r[12];
    const stt = r[0];
    const form = r[8] || "";
    const topic = r[9] || "";

    const dateStr = ngay instanceof Date ? Utilities.formatDate(ngay, TZ, "yyyy-MM-dd") : "";
    const gioStr = gio instanceof Date ? Utilities.formatDate(gio, TZ, "HH:mm") : String(gio || "");

    if (status === "Pending") {
      out.total_pending++;
      const scheduled = combineDateTime_(ngay, gio);
      const item = {
        row: i + 1, stt: stt, ngay: dateStr, gio: gioStr,
        caption_preview: captionPreview, form: form, topic: topic,
      };
      if (scheduled && scheduled < now) {
        out.overdue_pending.push(item);
      } else {
        out.upcoming_pending++;
        if (dateStr === todayStr) out.pending_today.push(item);
        else if (dateStr === tomorrowStr) out.pending_tomorrow.push(item);
      }
    }

    if (status === "Posted") {
      const pDate = parseTimestamp_(postedAt);
      const pDateStr = pDate ? Utilities.formatDate(pDate, TZ, "yyyy-MM-dd") : "";
      const item = {
        row: i + 1, stt: stt, post_id: postId,
        posted_at: pDate ? Utilities.formatDate(pDate, TZ, "yyyy-MM-dd HH:mm") : "",
        caption_preview: captionPreview, form: form, topic: topic,
      };
      if (pDateStr === todayStr) out.posted_today.push(item);
      else if (pDateStr === yesterdayStr) out.posted_yesterday.push(item);
      if (pDate && pDate >= sevenDaysAgo) out.posted_last_7_days++;
    }

    if (status === "Failed") {
      const scheduled = combineDateTime_(ngay, gio);
      if (scheduled && scheduled >= sevenDaysAgo) out.failed_last_7_days++;
    }
  }

  return out;
}

function getImage_(name) {
  /**
   * Lay file anh tu folder TMUN-Anh-FB theo TEN FILE.
   * Tra ve {name, mime, size, base64}.
   * Neu khong tim thay -> throw error.
   *
   * Match: tim file co title EXACT name, neu khong co thi tim file
   * co title contains name (case-insensitive).
   */
  if (!name) throw new Error("Thieu tham so 'name'");
  const folder = DriveApp.getFolderById(DRIVE_FOLDER_ID);

  // Pass 1: exact match
  const exactIter = folder.getFilesByName(name);
  if (exactIter.hasNext()) {
    return _fileToObj_(exactIter.next());
  }

  // Pass 2: contains (case-insensitive). De chi co the go "matngu" thay vi "matngu_01.jpg"
  const nameLower = name.toLowerCase();
  const allFiles = folder.getFiles();
  while (allFiles.hasNext()) {
    const f = allFiles.next();
    if (f.getName().toLowerCase().includes(nameLower)) {
      return _fileToObj_(f);
    }
  }

  throw new Error(`Khong tim thay anh "${name}" trong folder TMUN-Anh-FB`);
}

function _fileToObj_(file) {
  const blob = file.getBlob();
  return {
    id: file.getId(),
    name: file.getName(),
    mime: blob.getContentType(),
    size: blob.getBytes().length,
    base64: Utilities.base64Encode(blob.getBytes()),
  };
}

function listImages_() {
  /**
   * Liet ke tat ca file anh trong folder TMUN-Anh-FB.
   * Tra ve [{name, id, mime, size, modified_at}] — KHONG kem base64 (de tranh response qua lon).
   * Dung de Claude xem co bai nao chua dung de viet caption.
   */
  const folder = DriveApp.getFolderById(DRIVE_FOLDER_ID);
  const files = folder.getFiles();
  const out = [];
  while (files.hasNext()) {
    const f = files.next();
    const mime = f.getMimeType();
    if (!mime.startsWith("image/")) continue;
    out.push({
      id: f.getId(),
      name: f.getName(),
      mime: mime,
      size: f.getSize(),
      modified_at: Utilities.formatDate(f.getLastUpdated(), TZ, "yyyy-MM-dd HH:mm:ss"),
    });
  }
  return out;
}

function markPosted_(p) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  sh.getRange(p.row, 11).setValue("Posted");
  sh.getRange(p.row, 12).setValue(p.post_id);
  sh.getRange(p.row, 13).setValue(p.posted_at);
  sh.getRange(p.row, 14).setValue("");
  return { ok: true };
}

function markFailed_(p) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  sh.getRange(p.row, 11).setValue("Failed");
  sh.getRange(p.row, 14).setValue(p.error || "");
  return { ok: true };
}

function saveInsights_(p) {
  const postId = (p.post_id || "").toString();
  const ins = p.insights || {};
  if (!postId) return { ok: false, error: "Thieu post_id" };

  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_REPORT);
  const data = sh.getDataRange().getValues();

  // Tim row co Post ID khop -> update; khong co -> append
  let targetRow = -1;
  for (let i = 1; i < data.length; i++) {
    if ((data[i][0] || "").toString() === postId) {
      targetRow = i + 1;
      break;
    }
  }

  const scheduleMeta = lookupScheduleByPostId_(postId);
  const row = [
    postId,
    scheduleMeta.posted_at,
    scheduleMeta.caption,
    scheduleMeta.form,
    scheduleMeta.topic,
    ins.reach || 0,
    ins.impressions || 0,
    ins.reactions || 0,
    ins.comments || 0,
    ins.shares || 0,
    ins.link_clicks || 0,
    ins.engagement_rate || 0,
    ins.click_rate || 0,
    ins.updated_at || nowString_(),
  ];

  if (targetRow > 0) {
    sh.getRange(targetRow, 1, 1, row.length).setValues([row]);
  } else {
    sh.appendRow(row);
  }
  return { ok: true };
}

function lookupScheduleByPostId_(postId) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const data = sh.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if ((data[i][11] || "").toString() === postId) {
      return {
        caption: (data[i][3] || "").toString().substring(0, 100),
        form: data[i][8] || "",
        topic: data[i][9] || "",
        posted_at: data[i][12] || "",
      };
    }
  }
  return { caption: "", form: "", topic: "", posted_at: "" };
}

function addRow_(p) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const lastRow = sh.getLastRow();
  const newRowNum = lastRow + 1;
  const stt = lastRow;  // header chiem row 1, neu lastRow=1 thi stt=1

  const ngayValue = parseInputDate_(p.ngay);
  const row = [
    stt,
    ngayValue || p.ngay || "",
    p.gio || "",
    p.caption || "",
    p.images || p.anh || "",
    p.link || "",
    (p.channel || "FB").toUpperCase(),
    p.post_type || "photo",
    p.dang_bai || p.form || "anh-don",
    p.chu_de || p.topic || "san-pham",
    p.status || "Pending",
    "",  // Post ID - he thong tu fill
    "",  // Posted At
    "",  // Error
  ];
  sh.getRange(newRowNum, 1, 1, row.length).setValues([row]);
  return { ok: true, row: newRowNum, stt: stt };
}

function bulkAdd_(p) {
  if (!Array.isArray(p.items)) {
    return { ok: false, error: "Field 'items' phai la array" };
  }
  const results = [];
  for (const item of p.items) {
    try {
      results.push(addRow_(item));
    } catch (e) {
      results.push({ ok: false, error: String(e) });
    }
  }
  return { ok: true, count: results.length, results: results };
}

function parseInputDate_(s) {
  if (!s) return null;
  if (Object.prototype.toString.call(s) === "[object Date]") return s;
  s = String(s).trim();

  // Try ISO format YYYY-MM-DD
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]));

  // Try VN format dd/MM/yyyy
  m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return new Date(parseInt(m[3]), parseInt(m[2]) - 1, parseInt(m[1]));

  // Try VN short dd-MM-yyyy
  m = s.match(/^(\d{1,2})-(\d{1,2})-(\d{4})/);
  if (m) return new Date(parseInt(m[3]), parseInt(m[2]) - 1, parseInt(m[1]));

  return null;
}

function resetPending_(p) {
  /**
   * Mark row Failed/Skip back to Pending de retry.
   * Payload: { row: N } HOAC { rows: [N1, N2, ...] }
   * Cung clear cot Error de log sach.
   */
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  const rows = p.rows || (p.row ? [p.row] : []);
  if (rows.length === 0) return { ok: false, error: "Thieu field 'row' hoac 'rows'" };

  for (const r of rows) {
    sh.getRange(r, 11).setValue("Pending");  // K = Status
    sh.getRange(r, 14).setValue("");          // N = Error - clear
  }
  return { ok: true, reset_count: rows.length };
}

function deleteRow_(p) {
  /**
   * Xoa han 1 row trong Lich dang (vd duplicate, hoac bai bo).
   * Payload: { row: N }
   */
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_SCHEDULE);
  if (!p.row) return { ok: false, error: "Thieu field 'row'" };
  sh.deleteRow(p.row);
  return { ok: true };
}

function logRow_(p) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_LOGS);
  sh.appendRow([nowString_(), p.level || "INFO", p.message || ""]);
  return { ok: true };
}

// =====================================================================
// HELPERS
// =====================================================================

function combineDateTime_(ngay, gio) {
  if (!ngay) return null;

  let date;
  if (Object.prototype.toString.call(ngay) === "[object Date]") {
    date = new Date(ngay.getTime());
  } else {
    date = new Date(ngay);
    if (isNaN(date.getTime())) return null;
  }

  if (gio) {
    if (Object.prototype.toString.call(gio) === "[object Date]") {
      date.setHours(gio.getHours(), gio.getMinutes(), 0, 0);
    } else {
      const m = String(gio).match(/(\d{1,2})[:h](\d{2})/);
      if (m) date.setHours(parseInt(m[1], 10), parseInt(m[2], 10), 0, 0);
    }
  }
  return date;
}

function parseTimestamp_(v) {
  if (!v) return null;
  if (Object.prototype.toString.call(v) === "[object Date]") return v;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

function nowString_() {
  return Utilities.formatDate(new Date(), TZ, "yyyy-MM-dd HH:mm:ss");
}

// =====================================================================
// SETUP DRIVE PERMISSIONS - chay 1 lan tu menu "Chay" cua Apps Script editor
// (function khong co _ suffix nen hien trong dropdown)
// Apps Script se popup Review permissions -> click Allow de cap quyen Drive.
// Sau khi cap quyen, endpoint get_image va list_images se hoat dong.
// =====================================================================
function setupDrivePermissions() {
  const folder = DriveApp.getFolderById(DRIVE_FOLDER_ID);
  const name = folder.getName();
  let fileCount = 0;
  const files = folder.getFiles();
  while (files.hasNext()) {
    files.next();
    fileCount++;
  }
  Logger.log("OK! Folder '" + name + "' co " + fileCount + " file.");
  return { folder: name, file_count: fileCount };
}

// =====================================================================
// RELIABLE CRON TRIGGER — bypass GitHub Actions schedule skip
//
// GitHub Actions docs: scheduled workflows */5 PHUT thuong bi skip
// khi runner busy. Apps Script time-driven trigger reliable hon nhieu.
//
// SETUP (chi Trang lam 1 lan):
//  1. Tao GitHub Personal Access Token (fine-grained):
//     - https://github.com/settings/personal-access-tokens/new
//     - Repository access: chi tmun-social-hub
//     - Permissions: Actions = Read and write
//     - Generate, copy PAT
//  2. Paste vao Script Properties:
//     - File > Project Properties > Script Properties (Apps Script editor moi: Settings > Script properties)
//     - Key: GITHUB_PAT, Value: <PAT>
//  3. Setup time-driven trigger:
//     - Triggers (icon dong ho ben trai editor) > Add Trigger
//     - Function: triggerPublishWorkflow
//     - Event source: Time-driven
//     - Type: Minutes timer > Every 5 minutes
//     - Save
//  4. (Optional) Lam tuong tu cho triggerStatusReport voi 2 triggers:
//     - Sang: Day timer > 7 AM
//     - Toi: Day timer > 9 PM
// =====================================================================

function triggerPublishWorkflow() {
  return _triggerWorkflow_("publish.yml");
}

function triggerStatusReport() {
  return _triggerWorkflow_("status_report.yml");
}

function _triggerWorkflow_(workflowFile) {
  const PAT = PropertiesService.getScriptProperties().getProperty("GITHUB_PAT");
  if (!PAT) {
    Logger.log("Thieu GITHUB_PAT trong Script Properties");
    return { ok: false, error: "Missing GITHUB_PAT" };
  }
  const REPO = "quynhtrangls95-beep/tmun-social-hub";
  const url = `https://api.github.com/repos/${REPO}/actions/workflows/${workflowFile}/dispatches`;
  const resp = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + PAT,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    payload: JSON.stringify({ ref: "main" }),
    muteHttpExceptions: true,
  });
  const code = resp.getResponseCode();
  const body = resp.getContentText();
  Logger.log(`Trigger ${workflowFile}: status=${code} body=${body.substring(0, 200)}`);
  if (code === 204) {
    return { ok: true, workflow: workflowFile };
  }
  return { ok: false, status: code, error: body };
}
