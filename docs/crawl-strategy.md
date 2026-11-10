# Chiến lược crawl catalog (pha 2)

Mục tiêu: lấy **ý tưởng chức năng** (tên, tagline, mô tả, category, URL sản phẩm) từ vài sàn launch ưu tiên, để chọn bài tập clone cho fresher. Không copy thương hiệu/UI/dữ liệu độc quyền.

Tool mặc định chỉ `discover` / `sample` (trần 5, cứng 20). Bulk cần `--bulk` và ủy quyền tường minh. **Unikorn bulk đã được ủy quyền** (2026-11-10): `crawl --source unikorn --bulk`, delay ≥10s, resume JSONL, halt 403/429.

## Nguồn ưu tiên

| Thứ tự | Nguồn | Catalog URL pattern | Cách lấy | Ước lượng sitemap [V] |
|---|---|---|---|---|
| 1 | Unikorn | `https://unikorn.vn/p/{slug}` | JSON-LD `SoftwareApplication` | 2017 products (`sitemap/products/1.xml`) |
| 2 | TinyLaunch | `https://www.tinylaunch.com/launch/{id}-{slug}` | JSON-LD `@graph` / og | 22215 launches (`/sitemap.xml`) |
| 3 | Uneed | `https://www.uneed.best/tool/{slug}` | og + `h1` | `__sitemap__/tools.xml` (chưa đếm đủ) |
| 4 | Fazier | `https://fazier.com/launches/{slug}` | og + `h1` | 9515 launches |

Fazier `/p/{slug}` là **profile người dùng**, không phải sản phẩm — không crawl. [V]

## Robots (mẫu 2026-11-10)

| Host | `User-agent: *` | Delay | Ghi chú |
|---|---|---|---|
| unikorn.vn | Allow `/`; Disallow `/api/*`, `/admin`, `/login`, `/register`, `/profile`, `/products/new`, `/u/*/…` | `Crawl-delay: 10` **chỉ** SemrushBot [V]. Policy crawler: **10s** [A] | Sitemap index; **chỉ** `sitemap/products/*.xml` |
| www.tinylaunch.com | Disallow `/api`, `/admin`, `/dashboard`, `/auth`, `/go/` | không ghi | Agent API (`llms.txt`, `openapi.json`) là **submit launch**, không phải list catalog. Crawler **không** gọi `/api/v1/*` |
| www.uneed.best | Disallow `/*?*sortBy=`, `/*?*orderBy=` | không ghi | Dùng `__sitemap__/tools.xml`; bỏ tags/profiles/reviews |
| fazier.com | Disallow `/admin/`, `/embeds/`, `/launch/` (số ít), `/launch-new/`, `/page/` | không ghi | Catalog = `/launches/` (số nhiều) |
| theresanaiforthat.com | Allow `/`; Disallow `/api/` | — | `Content-Signal: ai-train=no, use=reference`. Các bot train `Disallow: /`. **Không** còn `Disallow: /` cho `*` (đính chính ghi chú cũ) |
| www.producthunt.com | Allow sitemaps; Disallow `/auth`, `/search`, `/r/*` (trừ `/r/p/*`) | — | Probe HTML 403 [V] — adapter sau, cần browser |
| www.indiehackers.com | Disallow `/api/`, sign-in/up | — | HTML `*` được; bot train `Disallow: /` |
| alternativeto.net | robots.txt bị bot-wall | — | Không crawl cho đến khi có session tay |

## Policy HTTP

- Sequential, **không** parallel.
- Delay: Unikorn ≥10s; nguồn khác ≥1s; lấy `max(policy, robots crawl-delay)` nếu robots có.
- User-Agent: `NewbieLaunchpadIdeas/0.1 (+local research; sequential; honors robots.txt)`.
- Halt host khi 429 hoặc 403.
- Không vào path robots Disallow; không `/go` (redirect tracking).
- `discover` = chỉ sitemap (vài request). `sample` bắt buộc `--limit` (mặc định trần 5, cứng 20).
- Output: `data/catalog/` JSONL (`{source}.jsonl`). Schema: `source, source_url, slug, name, tagline, description, category, product_url, pricing, language, published_at`. Runtime (`*.log`, `*_crawl_state.json`, `*_scored.jsonl`) không commit.

## TinyLaunch agent API — ngoài phạm vi crawl

`GET/POST https://www.tinylaunch.com/api/v1/{categories,launch-dates,auth,maker,startups,launches}` phục vụ **đăng launch**, OTP email, Bearer ~1h. Robots Disallow `/api`. Không dùng cho catalog.

## Adapter

Package `tools/catalog_crawl`. Chạy từ root repo:

```bash
python3 -m unittest discover -s tests -t .
python3 -m tools.catalog_crawl discover --source unikorn
python3 -m tools.catalog_crawl sample --source unikorn --limit 1
python3 -m tools.catalog_crawl crawl --source unikorn --bulk
python3 -m tools.catalog_crawl score --source unikorn
```

Unikorn parse JSON-LD (đã xác nhận trên `/p/hoc-that-gioi`: name, alternateName=tagline, description, applicationCategory, installUrl, offers, datePublished, inLanguage). TinyLaunch tương tự qua `@graph`. Uneed/Fazier fallback og/`h1`.

## Chưa làm (cần ủy quyền)

- TinyLaunch/Uneed/Fazier full catalog.
- Product Hunt / AlternativeTo (403).
- TAAFT HTML (robots `*` cho phép nhưng `use=reference` — chỉ lấy excerpt ngắn nếu làm).

Unikorn: `data/catalog/unikorn.jsonl` (210/2017) + `unikorn_fresher.md` (auto) + `unikorn_fresher_hand.md` (lọc tay). Category listing chỉ SSR ~10 item; Load more đi `/api/*` (Disallow) nên phải fetch từng `/p/{slug}`.
