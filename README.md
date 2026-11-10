# Khảo sát nền tảng launch indie / vibe-coding

Database các website indie developer và vibe coder dùng để launch sản phẩm, cộng catalog Unikorn để lấy **ý tưởng chức năng** làm bài tập clone cho fresher.

Không copy thương hiệu, UI độc quyền hay dữ liệu độc quyền.

```
sources/            nguồn gốc (Facebook, X, URL probe)
data/platforms/     108 sàn launch
data/catalog/       sản phẩm Unikorn (JSONL + shortlist)
docs/               robots / delay / adapter
tools/catalog_crawl crawler lịch sự (stdlib)
tests/
```

## Nguồn

| Nguồn | Chi tiết |
|---|---|
| Facebook | [Bài Jack Vĩ trong group Nghiên AI](https://www.facebook.com/groups/aiartworksvn/posts/4399016940311156/) (share `1KXUjAf4bD`), 2026-05-12 |
| X gốc | [@hridoyreh, 2026-03-25](https://x.com/hridoyreh/status/2036816122096533589) — *100+ places to launch your startup* (107 mục) |
| Addendum VN | **Unikorn** (`unikorn.vn`) — Jack Vĩ thêm, founder Hải Nguyễn |

Defuddle chỉ lấy title Facebook (login wall). Nội dung đầy đủ: `web_fetch` khớp 1:1 thread X. Bản lưu: `sources/`. Từ điển file: `data/README.md`.

## Sàn launch (`data/platforms/`)

```bash
sqlite3 data/platforms/launch_platforms.sqlite \
  "SELECT list_rank, name, official_url, category
   FROM platforms
   WHERE fresher_clone_fit='high' AND url_status IN ('live','live_blocked')
   ORDER BY list_rank;"
```

Probe 2026-11-10: 108 nền tảng (107 list + Unikorn); 79 live + 16 live_blocked + 1 SSL hỏng; 29 `fresher_clone_fit=high`; 59 V / 49 H.

Ưu tiên lấy ý tưởng: Unikorn, Product Hunt, TinyLaunch, Uneed, Fazier, Indie Hackers, AlternativeTo, Startups FYI, API List / Public APIs.

## Catalog Unikorn (`data/catalog/`)

210 / 2017 URL đã parse (JSON-LD). Scorer auto: high 79 / medium 111 / low 20 (substring `tiện ích` làm **Tiện ích dev** thành high). Shortlist tay: `unikorn_fresher_hand.md` — **49 giữ / 30 loại / 28 đề độc**.

```bash
python3 -m unittest discover -s tests -t .
python3 -m tools.catalog_crawl discover --source unikorn
python3 -m tools.catalog_crawl sample --source unikorn --limit 1
python3 -m tools.catalog_crawl crawl --source unikorn --bulk   # cần ủy quyền; delay ≥10s
python3 -m tools.catalog_crawl score --source unikorn
```

Không bulk TinyLaunch / Uneed / Fazier; không gọi Unikorn `/api/*`. Chi tiết: `docs/crawl-strategy.md`.

## Gợi ý bài tập fresher

1. Unikorn trước — đề độc trong `data/catalog/unikorn_fresher_hand.md` (Yuzu Sum, Pokko, Arivo, Klass, Generate Quiz, …).
2. Launch board (PH, TinyLaunch, Uneed, Fazier): tagline + 1 job-to-be-done, MVP 1–2 tính năng.
3. AlternativeTo / OpenAlternative: bản tối giản của X.
4. API List / Chrome Web Store: biên rõ.
5. Tránh deal-site/B2B review (AppSumo, Goodfirms) khi chọn đề.

## Việc chưa làm

- TinyLaunch / Uneed / Fazier catalog (cần ủy quyền).
- ~49 dòng platform `verification=H`.
- Siết scorer (bỏ substring `tiện ích`) — chưa làm; đang dùng shortlist tay.
- Chọn license trước khi public GitHub.
