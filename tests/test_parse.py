from __future__ import annotations

import unittest

from tools.catalog_crawl.adapters import ADAPTERS
from tools.catalog_crawl.parse_jsonld import item_from_html, software_apps
from tools.catalog_crawl.sitemap import parse_sitemap_xml

UNIKORN_HTML = """
<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication","name":"Học Thật Giỏi","url":"https://unikorn.vn/p/hoc-that-gioi","alternateName":"Soạn đề thi bằng AI","description":"Nền tảng soạn đề.","applicationCategory":"Công cụ học tập","datePublished":"2026-11-04","installUrl":"https://hocthatgioi.vn/","offers":{"@type":"Offer","price":"0","priceCurrency":"VND","description":"Freemium"},"inLanguage":"vi"}</script>
</head><body><h1>Học Thật Giỏi</h1></body></html>
"""

TINY_HTML = """
<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"SoftwareApplication","name":"ProductLab.so","description":"AI product images.","url":"https://www.tinylaunch.com/launch/1-productlabso","sameAs":"https://www.productlab.so","applicationCategory":"AI & Machine Learning","datePublished":"2024-12-05"}]}</script>
<meta property="og:title" content="ProductLab.so: AI generated product images that sell.">
</head><body><h1>ProductLab.so</h1></body></html>
"""

UNEED_HTML = """
<html><head>
<meta property="og:title" content="Discover 1 in 8 Billion Game on Uneed">
<meta property="og:description" content="Live a whole life as one of today's babies.">
</head><body><h1>1 in 8 Billion Game</h1></body></html>
"""

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://unikorn.vn/sitemap/products/1.xml</loc></sitemap>
  <sitemap><loc>https://unikorn.vn/sitemap/users/1.xml</loc></sitemap>
</sitemapindex>
"""

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://unikorn.vn/p/hoc-that-gioi</loc><lastmod>2026-11-10</lastmod></url>
  <url><loc>https://unikorn.vn/categories/x</loc></url>
</urlset>
"""


class ParseTests(unittest.TestCase):
    def test_unikorn_jsonld(self) -> None:
        apps = software_apps(UNIKORN_HTML)
        self.assertEqual(len(apps), 1)
        item = item_from_html("unikorn", "https://unikorn.vn/p/hoc-that-gioi", "hoc-that-gioi", UNIKORN_HTML)
        self.assertEqual(item.name, "Học Thật Giỏi")
        self.assertEqual(item.tagline, "Soạn đề thi bằng AI")
        self.assertEqual(item.category, "Công cụ học tập")
        self.assertEqual(item.product_url, "https://hocthatgioi.vn/")
        self.assertEqual(item.pricing, "Freemium")
        self.assertEqual(item.language, "vi")
        self.assertEqual(item.extra["parser"], "jsonld_softwareapplication")

    def test_tinylaunch_graph(self) -> None:
        item = item_from_html(
            "tinylaunch",
            "https://www.tinylaunch.com/launch/1-productlabso",
            "1-productlabso",
            TINY_HTML,
        )
        self.assertEqual(item.name, "ProductLab.so")
        self.assertEqual(item.product_url, "https://www.productlab.so")
        self.assertEqual(item.category, "AI & Machine Learning")

    def test_uneed_og(self) -> None:
        item = item_from_html(
            "uneed",
            "https://www.uneed.best/tool/1-in-8-billion",
            "1-in-8-billion",
            UNEED_HTML,
        )
        self.assertEqual(item.name, "1 in 8 Billion Game")
        self.assertEqual(item.extra["parser"], "og_h1")

    def test_url_filters(self) -> None:
        self.assertTrue(ADAPTERS["unikorn"].is_product_url("https://unikorn.vn/p/hoc-that-gioi"))
        self.assertFalse(ADAPTERS["unikorn"].is_product_url("https://unikorn.vn/api/og/product/x"))
        self.assertFalse(ADAPTERS["unikorn"].is_product_url("https://unikorn.vn/p/x/feedback"))
        self.assertTrue(ADAPTERS["fazier"].is_product_url("https://fazier.com/launches/uptimeeye"))
        self.assertFalse(ADAPTERS["fazier"].is_product_url("https://fazier.com/p/yang"))
        self.assertFalse(ADAPTERS["fazier"].is_product_url("https://fazier.com/launch/uptimeeye"))
        self.assertTrue(ADAPTERS["tinylaunch"].is_product_url("https://www.tinylaunch.com/launch/1-productlabso"))
        self.assertFalse(ADAPTERS["uneed"]._sitemap_child_ok("https://www.uneed.best/__sitemap__/tags.xml"))
        self.assertTrue(ADAPTERS["uneed"]._sitemap_child_ok("https://www.uneed.best/__sitemap__/tools.xml"))

    def test_sitemap_index_and_urlset(self) -> None:
        kind, rows = parse_sitemap_xml(SITEMAP_INDEX)
        self.assertEqual(kind, "sitemapindex")
        self.assertEqual(len(rows), 2)
        kind, rows = parse_sitemap_xml(URLSET)
        self.assertEqual(kind, "urlset")
        self.assertEqual(rows[0][0], "https://unikorn.vn/p/hoc-that-gioi")


if __name__ == "__main__":
    unittest.main()
