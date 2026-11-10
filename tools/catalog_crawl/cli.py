from __future__ import annotations

import argparse
import json
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from .adapters import ADAPTERS, SAMPLE_LIMIT_CAP, SAMPLE_LIMIT_DEFAULT_MAX
from .client import HaltError, PoliteClient
from .models import CatalogItem
from .score import score_item

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "catalog"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="catalog_crawl",
        description="Polite catalog discover/sample. Refuses bulk. Does not call TinyLaunch agent API.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_disc = sub.add_parser("discover", help="Fetch sitemaps only; write URL list")
    p_disc.add_argument("--source", required=True, choices=[*ADAPTERS, "all"])
    p_disc.add_argument("--out-dir", type=Path, default=OUT_DIR)

    p_sample = sub.add_parser("sample", help="Fetch N product pages (cap 5, hard 20)")
    p_sample.add_argument("--source", required=True, choices=list(ADAPTERS))
    p_sample.add_argument("--limit", type=int, required=True)
    p_sample.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p_sample.add_argument(
        "--allow-large-limit",
        action="store_true",
        help=f"Allow --limit up to {SAMPLE_LIMIT_CAP} (still not bulk)",
    )

    p_crawl = sub.add_parser(
        "crawl",
        help="Resumable sequential product crawl; requires --bulk",
    )
    p_crawl.add_argument("--source", required=True, choices=list(ADAPTERS))
    p_crawl.add_argument(
        "--bulk",
        action="store_true",
        help="Required. Confirms host-wide product crawl (honors robots, sequential delay).",
    )
    p_crawl.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max new pages this run (0 = all remaining)",
    )
    p_crawl.add_argument("--out-dir", type=Path, default=OUT_DIR)

    p_score = sub.add_parser("score", help="Rescore JSONL and write fresher shortlist")
    p_score.add_argument("--source", default="unikorn")
    p_score.add_argument("--out-dir", type=Path, default=OUT_DIR)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "discover":
            return cmd_discover(args.source, args.out_dir)
        if args.cmd == "sample":
            return cmd_sample(args.source, args.limit, args.out_dir, args.allow_large_limit)
        if args.cmd == "score":
            return cmd_score(args.source, args.out_dir)
        return cmd_crawl(args.source, args.out_dir, args.bulk, args.limit)
    except HaltError as e:
        print(f"HALT: {e}", file=sys.stderr)
        return 2


def cmd_discover(source: str, out_dir: Path) -> int:
    names = list(ADAPTERS) if source == "all" else [source]
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, int] = {}
    for name in names:
        adapter = ADAPTERS[name]
        client = PoliteClient(adapter.min_delay_s)
        urls = adapter.collect_product_urls(client)
        path = out_dir / f"discover_{name}.json"
        path.write_text(
            json.dumps(
                {
                    "source": name,
                    "sitemap_entry": adapter.sitemap_entry,
                    "min_delay_s": adapter.min_delay_s,
                    "count": len(urls),
                    "urls": urls,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        summary[name] = len(urls)
        print(f"{name}: {len(urls)} product URLs -> {path}")
    print(json.dumps({"discover": summary}, ensure_ascii=False))
    return 0


def cmd_sample(source: str, limit: int, out_dir: Path, allow_large: bool) -> int:
    cap = SAMPLE_LIMIT_CAP if allow_large else SAMPLE_LIMIT_DEFAULT_MAX
    if limit < 1 or limit > cap:
        print(
            f"--limit must be 1..{cap} (use --allow-large-limit for up to {SAMPLE_LIMIT_CAP}; bulk requires explicit user auth)",
            file=sys.stderr,
        )
        return 2
    adapter = ADAPTERS[source]
    client = PoliteClient(adapter.min_delay_s)
    urls = adapter.collect_product_urls(client)[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"sample_{source}.jsonl"
    n = 0
    with dest.open("w", encoding="utf-8") as fh:
        for url in urls:
            html = client.fetch(url)
            item = adapter.parse(url, html)
            fh.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
            n += 1
            print(f"{n}/{limit} {item.name} {url}")
    print(f"wrote {n} items -> {dest}")
    return 0


def done_urls(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = row.get("source_url")
        if url:
            done.add(url)
    return done


def _write_state(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def cmd_crawl(source: str, out_dir: Path, bulk: bool, limit: int) -> int:
    if not bulk:
        print("crawl requires --bulk (explicit authorization)", file=sys.stderr)
        return 2
    if limit < 0:
        print("--limit must be >= 0", file=sys.stderr)
        return 2
    adapter = ADAPTERS[source]
    client = PoliteClient(adapter.min_delay_s)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{source}.jsonl"
    err_path = out_dir / f"{source}_errors.jsonl"
    state_path = out_dir / f"{source}_crawl_state.json"
    urls = adapter.collect_product_urls(client)
    (out_dir / f"discover_{source}.json").write_text(
        json.dumps(
            {
                "source": source,
                "sitemap_entry": adapter.sitemap_entry,
                "min_delay_s": adapter.min_delay_s,
                "count": len(urls),
                "urls": urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    skip = done_urls(dest) | done_urls(err_path)
    pending = [u for u in urls if u not in skip]
    if limit:
        pending = pending[:limit]
    fits = {"high": 0, "medium": 0, "low": 0}
    n = 0
    total = len(urls)
    started = datetime.now(timezone.utc).isoformat()
    with dest.open("a", encoding="utf-8") as fh:
        for url in pending:
            try:
                html = client.fetch(url)
            except HaltError:
                _write_state(
                    state_path,
                    {
                        "source": source,
                        "status": "halted",
                        "last_url": url,
                        "done": len(done_urls(dest)),
                        "total": total,
                        "started_utc": started,
                        "updated_utc": datetime.now(timezone.utc).isoformat(),
                    },
                )
                if dest.exists() and dest.stat().st_size:
                    cmd_score(source, out_dir)
                raise
            except urllib.error.HTTPError as e:
                # HTTPError is a URLError subclass — must be caught first.
                # 404/410: permanent skip. 5xx/other: skip this pass, retry on resume.
                if e.code in (404, 410):
                    with err_path.open("a", encoding="utf-8") as eh:
                        eh.write(
                            json.dumps(
                                {
                                    "source_url": url,
                                    "http_status": e.code,
                                    "at": datetime.now(timezone.utc).isoformat(),
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                print(f"skip HTTP {e.code} {url}", file=sys.stderr)
                continue
            except urllib.error.URLError as e:
                print(f"skip URLError {url}: {e}", file=sys.stderr)
                continue
            item = score_item(adapter.parse(url, html))
            fh.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
            fh.flush()
            n += 1
            fit = item.extra.get("fresher_clone_fit", "medium")
            fits[fit] = fits.get(fit, 0) + 1
            print(f"{n}/{len(pending)} {fit} {item.name} {url}")
            _write_state(
                state_path,
                {
                    "source": source,
                    "status": "running",
                    "last_url": url,
                    "last_name": item.name,
                    "written_this_run": n,
                    "done": len(done_urls(dest)),
                    "total": total,
                    "fits_this_run": fits,
                    "started_utc": started,
                    "updated_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
    _write_state(
        state_path,
        {
            "source": source,
            "status": "done" if not pending or n == len(pending) else "partial",
            "written_this_run": n,
            "done": len(done_urls(dest)),
            "total": total,
            "fits_this_run": fits,
            "started_utc": started,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    cmd_score(source, out_dir)
    print(json.dumps({"wrote": n, "fits": fits, "dest": str(dest)}, ensure_ascii=False))
    return 0


def cmd_score(source: str, out_dir: Path) -> int:
    src = out_dir / f"{source}.jsonl"
    if not src.exists():
        print(f"missing {src}", file=sys.stderr)
        return 2
    items: list[dict] = []
    counts = {"high": 0, "medium": 0, "low": 0}
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = CatalogItem(
            source=row.get("source") or source,
            source_url=row.get("source_url") or "",
            slug=row.get("slug") or "",
            name=row.get("name") or "",
            tagline=row.get("tagline"),
            description=row.get("description"),
            category=row.get("category"),
            product_url=row.get("product_url"),
            pricing=row.get("pricing"),
            language=row.get("language"),
            published_at=row.get("published_at"),
            extra=dict(row.get("extra") or {}),
        )
        score_item(item)
        d = item.to_dict()
        items.append(d)
        fit = d["extra"].get("fresher_clone_fit", "medium")
        counts[fit] = counts.get(fit, 0) + 1
    scored = out_dir / f"{source}_scored.jsonl"
    with scored.open("w", encoding="utf-8") as fh:
        for row in items:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    high = [r for r in items if r["extra"].get("fresher_clone_fit") == "high"]
    md = out_dir / f"{source}_fresher.md"
    lines = [
        f"# {source} — ý tưởng clone fresher/junior",
        "",
        f"generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"scored: {len(items)}  high: {counts.get('high', 0)}  "
        f"medium: {counts.get('medium', 0)}  low: {counts.get('low', 0)}",
        "",
        "Chỉ lấy *ý tưởng chức năng*. Không copy thương hiệu, UI, hay dữ liệu độc quyền.",
        "",
        "| Tên | Tagline | Category | Unikorn | Gợi ý MVP |",
        "|---|---|---|---|---|",
    ]
    for r in high:
        tag = (r.get("tagline") or "").replace("|", "/")
        cat = (r.get("category") or "").replace("|", "/")
        hint = (r["extra"].get("mvp_hint") or "").replace("|", "/")
        lines.append(
            f"| {r.get('name','')} | {tag} | {cat} | {r.get('source_url','')} | {hint} |"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"scored {len(items)} -> {scored}; high {counts.get('high', 0)} -> {md}")
    return 0
