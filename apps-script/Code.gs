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

  // 1. Hieu qua theo dang bai
  sh.getRange("A3").setValue("1. Engagement Rate trung binh theo Dang bai")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A4").setFormula(
    `=QUERY('${SHEET_REPORT}'!A:N, "SELECT D, AVG(L), AVG(M), COUNT(A) WHERE D IS NOT NULL GROUP BY D LABEL D 'Dang bai', AVG(L) 'ER TB (%)', AVG(M) 'CR TB (%)', COUNT(A) 'So bai'", 1)`
  );

  // 2. Hieu qua theo chu de
  sh.getRange("F3").setValue("2. Engagement Rate trung binh theo Chu de")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("F4").setFormula(
    `=QUERY('${SHEET_REPORT}'!A:N, "SELECT E, AVG(L), AVG(M), COUNT(A) WHERE E IS NOT NULL GROUP BY E LABEL E 'Chu de', AVG(L) 'ER TB (%)', AVG(M) 'CR TB (%)', COUNT(A) 'So bai'", 1)`
  );

  // 3. Top 10 bai engagement cao nhat
  sh.getRange("A12").setValue("3. TOP 10 bai Engagement Rate cao nhat (30 ngay)")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A13").setFormula(
    `=QUERY('${SHEET_REPORT}'!A:N, "SELECT B, C, D, E, F, L ORDER BY L DESC LIMIT 10 LABEL B 'Posted', C 'Caption', D 'Dang', E 'Chu de', F 'Reach', L 'ER (%)'", 1)`
  );

  // 4. Top 10 bai ra click nhieu nhat
  sh.getRange("A26").setValue("4. TOP 10 bai ra Click nhieu nhat (kha nang ra don)")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A27").setFormula(
    `=QUERY('${SHEET_REPORT}'!A:N, "SELECT B, C, D, E, K, M ORDER BY K DESC LIMIT 10 LABEL B 'Posted', C 'Caption', D 'Dang', E 'Chu de', K 'Clicks', M 'CR (%)'", 1)`
  );

  // 5. Hieu qua theo gio dang
  sh.getRange("A40").setValue("5. Engagement Rate trung binh theo Gio dang")
    .setFontWeight("bold").setBackground("#d9b471");
  sh.getRange("A41").setFormula(
    `=QUERY('${SHEET_REPORT}'!A:N, "SELECT HOUR(B), AVG(L), COUNT(A) WHERE B IS NOT NULL GROUP BY HOUR(B) ORDER BY HOUR(B) LABEL HOUR(B) 'Gio', AVG(L) 'ER TB (%)', COUNT(A) 'So bai'", 1)`
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
