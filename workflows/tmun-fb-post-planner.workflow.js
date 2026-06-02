export const meta = {
  name: 'tmun-fb-post-planner',
  description: 'Multi-agent FB post planner cho Tra Thao Moc Uyen Nhien: brief -> N drafts -> judge brand_voice+anti_tpcn -> winner ready de schedule. Output JSON, KHONG co side effect.',
  phases: [
    { title: 'Brief', detail: 'Sinh angle viral + core message' },
    { title: 'Generate', detail: 'N caption variants song song' },
    { title: 'Judge', detail: 'Cham brand_voice + anti_tpcn + viral_hook + ra_don' },
    { title: 'Synthesize', detail: 'Chon winner pass filter' },
  ],
}

const input = args || {}
const topic = input.topic || 'lifestyle-cham'
const audience = input.audience || 'phu nu 30-50, ban ron, tim cham rai'
const imageName = input.image_name || ''
const N = Math.min(5, Math.max(2, input.n_variants || 3))

const BRAND_CONTEXT = `Thao Moc Uyen Nhien — tra thao moc Mau Son Lang Son.
Slogan: "Loi ru cua nui rung". 2 SKU: Thanh Can That Vi + Tam Tien Bao. Gia 250k/hop (~30 goi).
Brand voice: ngon ngu CAM NHAN/TRAI NGHIEM, am ap, cham rai. Hotline 0335 935 366. Web thaomocuyennhien.com/dat-hang.
TUYET DOI CAM: mat gan, giai doc, thanh nhiet, ngu ngon, chua, tri, dieu tri, cai thien (benh).`

const BRIEF_SCHEMA = {
  type: 'object',
  required: ['hook_angle', 'core_message', 'cta_suggestion'],
  properties: {
    hook_angle: { type: 'string' },
    core_message: { type: 'string' },
    cta_suggestion: { type: 'string' },
    brand_elements_to_emphasize: { type: 'array', items: { type: 'string' } },
  },
}

const DRAFT_SCHEMA = {
  type: 'object',
  required: ['hook', 'full_text', 'hashtags', 'char_count'],
  properties: {
    hook: { type: 'string' },
    body: { type: 'string' },
    cta: { type: 'string' },
    hashtags: { type: 'array', items: { type: 'string' } },
    full_text: { type: 'string' },
    char_count: { type: 'integer' },
  },
}

const SCORE_SCHEMA = {
  type: 'object',
  required: ['brand_voice', 'anti_tpcn', 'viral_hook', 'ra_don', 'total', 'would_post', 'comments'],
  properties: {
    brand_voice: { type: 'integer', minimum: 0, maximum: 10 },
    anti_tpcn: { type: 'integer', minimum: 0, maximum: 10 },
    viral_hook: { type: 'integer', minimum: 0, maximum: 10 },
    ra_don: { type: 'integer', minimum: 0, maximum: 10 },
    total: { type: 'integer' },
    would_post: { type: 'boolean' },
    comments: { type: 'string' },
  },
}

log(`Input: topic=${topic} | audience=${audience} | N=${N} | image=${imageName || '(none)'}`)

phase('Brief')
const brief = await agent(`${BRAND_CONTEXT}

Soan brief cho 1 bai FB:
- Topic: ${topic}
- Audience: ${audience}
- Image hint: ${imageName || '(khong co)'}

Tra ve JSON theo schema.`, { schema: BRIEF_SCHEMA, label: 'brief' })

phase('Generate')
const drafts = await parallel(Array.from({ length: N }, (_, i) => () =>
  agent(`${BRAND_CONTEXT}

Brief: ${JSON.stringify(brief)}

Viet caption FB BIEN THE so ${i + 1} (khac biet voi cac bien the khac).
YEU CAU:
- 150-350 tu
- Hook 1-2 dong dau viral, scroll-stop
- Body cam xuc / cam nhan (KHONG noi cong dung suc khoe)
- CTA goi mua + hotline 0335 935 366 + web thaomocuyennhien.com/dat-hang
- 3-6 hashtag (co #ThaoMocUyenNhien)
- Emoji 5-10 cai, khong spam
- full_text = toan bo caption final (hook + body + cta + hashtags), char_count tinh chinh xac

Tra ve JSON theo schema.`, { schema: DRAFT_SCHEMA, label: `gen-${i + 1}` })
))

const valid = drafts.filter(Boolean)
log(`Generated ${valid.length}/${N} drafts`)

phase('Judge')
const scored = await parallel(valid.map((d, i) => () =>
  agent(`${BRAND_CONTEXT}

Cham caption sau theo 4 tieu chi (0-10):
- brand_voice: dung giong noi TMUN (cam nhan/trai nghiem, am ap)
- anti_tpcn: KHONG vi pham. 10 = hoan toan safe. 0-3 = co tu cam (mat gan/giai doc/thanh nhiet/ngu ngon/chua/tri/dieu tri/cai thien benh) hoac ngu y suc khoe
- viral_hook: hook 1-2 dong dau co hap dan, scroll-stop
- ra_don: CTA + product mention manh

total = round((brand_voice + anti_tpcn + viral_hook + ra_don) / 4)
would_post = true CHI KHI anti_tpcn >= 9 VA total >= 7

Caption:
${d.full_text}

Tra ve JSON theo schema.`, { schema: SCORE_SCHEMA, label: `judge-${i + 1}` })
    .then(score => ({ ...d, score }))
))

phase('Synthesize')
const evaluated = scored.filter(Boolean)
const safe = evaluated.filter(e => e.score && e.score.would_post)
const winner = safe.sort((a, b) => (b.score.total || 0) - (a.score.total || 0))[0] || null

return {
  input: { topic, audience, image_name: imageName, n_variants: N },
  brief,
  winner: winner ? {
    full_text: winner.full_text,
    char_count: winner.char_count,
    hashtags: winner.hashtags,
    score: winner.score,
  } : null,
  all_variants: evaluated.map(e => ({
    hook: e.hook,
    char_count: e.char_count,
    preview: e.full_text.substring(0, 120),
    score: e.score,
  })),
  rejected_count: evaluated.length - safe.length,
  next_step: winner
    ? `Approve caption -> POST add_row Apps Script (anh="${imageName}", caption=winner.full_text, status=Pending). He thong publish.py se tu dang theo gio trong cot Gio.`
    : 'Khong co variant nao pass filter anti-TPCN. Refine brief (topic/audience) + chay lai workflow.',
}
