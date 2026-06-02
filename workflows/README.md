# TMUN FB Post Planner — Multi-Agent Workflow

Workflow lập kế hoạch + sinh + đánh giá caption Facebook cho thương hiệu **Thảo Mộc Uyên Nhiên**, dùng được ở Claude Code và export sang dự án **Cowork**.

## Tệp

- **`tmun-fb-post-planner.workflow.js`** — Script standalone, 100% self-contained, không phụ thuộc file ngoài. Copy nguyên tệp sang dự án khác là chạy được.

## Workflow Pattern

```
┌──────────┐    ┌────────────┐    ┌──────────┐    ┌─────────────┐
│  Brief   │ → │  Generate   │ → │  Judge    │ → │ Synthesize  │
│ 1 agent  │    │  N parallel │    │ N parallel│    │ 1 agent     │
└──────────┘    └────────────┘    └──────────┘    └─────────────┘
   ↓               ↓                  ↓                ↓
hook angle    drafts (3)        scores per draft   winner JSON
core msg     full caption       (brand_voice,      + ready-to-
CTA hint     hashtags          anti_tpcn,         schedule
              char count        viral_hook,
                                ra_don)
```

## Đặc điểm

✅ **Không có side effect** — chỉ generate + chấm điểm, không tự đăng FB, không tự POST Sheet  
✅ **Brand-aware** — nhúng sẵn context TMUN (slogan, SKU, giá, hotline, voice)  
✅ **Anti-TPCN filter cứng** — caption nào dính từ cấm (mát gan/giải độc/thanh nhiệt/ngủ ngon/chữa/trị) → bị reject  
✅ **Parameterized** — args truyền topic / audience / image_name / n_variants  
✅ **Output ready-to-schedule** — winner JSON có full caption + hashtags, chị chỉ copy/paste vào Sheet

## Args

```json
{
  "topic": "lifestyle-cham-buoi-toi",
  "audience": "phụ nữ 30-50, bận rộn cả ngày, tìm 1 nhịp đêm",
  "image_name": "matngu_01.jpg",
  "n_variants": 3
}
```

| Field | Default | Mô tả |
|---|---|---|
| `topic` | `"lifestyle-cham"` | Chủ đề bài (vd: `san-pham`, `nguon-goc-mau-son`, `cam-nhan-vi-tra`) |
| `audience` | `"phụ nữ 30-50..."` | Đối tượng cụ thể |
| `image_name` | `""` | Tên file ảnh trong Drive `TMUN-Anh-FB` (vd `matngu_01.jpg`) |
| `n_variants` | `3` | Số variant generate (2-5) |

## Output JSON

```json
{
  "input": { "topic": "...", "audience": "...", "image_name": "...", "n_variants": 3 },
  "brief": {
    "hook_angle": "...",
    "core_message": "...",
    "cta_suggestion": "...",
    "brand_elements_to_emphasize": ["..."]
  },
  "winner": {
    "full_text": "🌿 Hook... \n\nBody...\n\nCTA...\n\n#hashtags",
    "char_count": 287,
    "hashtags": ["#ThaoMocUyenNhien", "#..."],
    "score": {
      "brand_voice": 9,
      "anti_tpcn": 10,
      "viral_hook": 8,
      "ra_don": 8,
      "total": 9,
      "would_post": true,
      "comments": "..."
    }
  },
  "all_variants": [...],
  "rejected_count": 1,
  "next_step": "Approve caption → POST add_row Apps Script..."
}
```

## Chạy ở Claude Code

```
Workflow({
  scriptPath: "D:\\thaomocuyennhien.com\\social-hub\\workflows\\tmun-fb-post-planner.workflow.js",
  args: { topic: "...", audience: "...", image_name: "...", n_variants: 3 }
})
```

## Export sang Cowork

1. Copy `tmun-fb-post-planner.workflow.js` sang dự án Cowork
2. Place trong folder workflows của dự án đó
3. Invoke với args tương tự

File hoàn toàn self-contained — schemas, brand context, prompt templates đều nhúng trong script.

## Sau khi có winner

1. Mở Sheet `TMUN - Social Hub` → tab `Lich dang`
2. Add row mới:
   - **Caption** = `winner.full_text`
   - **Anh** = `image_name` (vd `matngu_01.jpg`)
   - **Ngày + Giờ** = chị quyết
   - **Status** = `Pending`
3. Cron `publish.py` tự đăng đúng giờ

Hoặc POST trực tiếp qua Apps Script `action=add_row` nếu chị muốn tự động hóa thêm 1 lớp nữa.

## Cấu trúc agents trong workflow

| Agent | Phase | Schema output | Mục đích |
|---|---|---|---|
| `brief` | Brief | `BRIEF_SCHEMA` | Sinh hook angle + core message + CTA hint |
| `gen-1..N` | Generate (parallel) | `DRAFT_SCHEMA` | N caption variants độc lập |
| `judge-1..N` | Judge (parallel) | `SCORE_SCHEMA` | Chấm 4 tiêu chí, filter anti-TPCN |

Tổng cost ~30-60k tokens/run (3 variants).
