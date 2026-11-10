from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.catalog_crawl.cli import done_urls
from tools.catalog_crawl.models import CatalogItem
from tools.catalog_crawl.score import score_item


class ScoreTests(unittest.TestCase):
    def test_high_ime_and_education(self) -> None:
        ime = score_item(
            CatalogItem(
                source="unikorn",
                source_url="https://unikorn.vn/p/rustype",
                slug="rustype",
                name="Rustype",
                tagline="Bộ gõ tiếng Việt Telex & VNI",
                category="Bàn phím & Nhập liệu",
            )
        )
        self.assertEqual(ime.extra["fresher_clone_fit"], "high")
        edu = score_item(
            CatalogItem(
                source="unikorn",
                source_url="https://unikorn.vn/p/hoc-that-gioi",
                slug="hoc-that-gioi",
                name="Học Thật Giỏi",
                tagline="Soạn đề thi bằng AI",
                category="Công cụ học tập",
            )
        )
        self.assertEqual(edu.extra["fresher_clone_fit"], "high")

    def test_video_not_low_via_ide_substring(self) -> None:
        item = score_item(
            CatalogItem(
                source="unikorn",
                source_url="https://unikorn.vn/p/clip",
                slug="clip",
                name="Clip",
                tagline="Tải video YouTube",
                category="Giải trí",
            )
        )
        self.assertNotEqual(item.extra["fresher_clone_fit"], "low")

    def test_low_beats_high(self) -> None:
        cad = score_item(
            CatalogItem(
                source="unikorn",
                source_url="https://unikorn.vn/p/3bcad",
                slug="3bcad",
                name="3BCAD",
                tagline="Thiết kế chi tiết cơ khí 3D",
                category="Tiện ích",
                description="CAD tham số và in 3D",
            )
        )
        self.assertEqual(cad.extra["fresher_clone_fit"], "low")

    def test_httperror_is_urlerror_subclass(self) -> None:
        import urllib.error

        self.assertTrue(issubclass(urllib.error.HTTPError, urllib.error.URLError))

    def test_resume_skips_done(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.jsonl"
            path.write_text(
                json.dumps({"source_url": "https://unikorn.vn/p/a"}) + "\n"
                + "{bad\n"
                + json.dumps({"source_url": "https://unikorn.vn/p/b"})
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                done_urls(path),
                {"https://unikorn.vn/p/a", "https://unikorn.vn/p/b"},
            )


if __name__ == "__main__":
    unittest.main()
