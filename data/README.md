# Data

Hai bộ dữ liệu độc lập. Không copy thương hiệu, UI, hay dữ liệu độc quyền — chỉ *ý tưởng chức năng*.

## `platforms/` — khảo sát sàn launch

Nguồn: bài Jack Vĩ (group Nghiên AI) khớp thread X `@hridoyreh` (107 mục) + Unikorn. Probe URL 2026-11-10.

| File | Vai trò |
|---|---|
| `launch_platforms.csv` | Bảng chính (Excel / Sheets) |
| `launch_platforms.json` | Cùng dữ liệu + `meta.counts` |
| `launch_platforms.sqlite` | Bản SQL của JSON (tiện query; không phải nguồn gốc) |
| `extra_channels.csv` | Kênh hay dùng nhưng **không** nằm trong 107 mục |

Trường chính: `official_url`, `url_status`, `category`, `idea_source_value`, `fresher_clone_fit`, `verification` (`V` / `H` / `A`).

108 nền tảng: 29 `fresher_clone_fit=high`; 59 V / 49 H.

## `catalog/` — sản phẩm Unikorn

Crawl tuần tự, robots, delay ≥10s. CLI ghi đúng các tên file này.

| File | Vai trò | Git |
|---|---|---|
| `discover_unikorn.json` | Snapshot sitemap 2017 URL | có |
| `unikorn.jsonl` | 210 sản phẩm đã parse (JSON-LD) + `extra.fresher_clone_fit` | có |
| `unikorn_fresher.md` | Shortlist **auto** (scorer heuristic) | có |
| `unikorn_fresher_hand.md` | Shortlist **tay** (49 giữ / 30 loại / 28 đề độc) | có |
| `discover_tinylaunch.json`, `discover_uneed.json` | URL sitemap (22 314 / 11 710) | có |
| `ideas_tinylaunch_recent.{md,jsonl}`, `ideas_uneed_recent.{md,jsonl}` | Mẫu sản phẩm gần đây, 115 mỗi nguồn (2 đợt) | có |
| `*_recent_batch2.jsonl` | Đợt 2 (50 mỗi nguồn), đã gộp vào `.md` | có |
| `unikorn_scored.jsonl` | Output `score` (trùng jsonl) | ignore |
| `unikorn_crawl.log`, `unikorn_crawl_state.json` | Runtime resume | ignore |

Schema JSONL: `source, source_url, slug, name, tagline, description, category, product_url, pricing, language, published_at, extra`.
