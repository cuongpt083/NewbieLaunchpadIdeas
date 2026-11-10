from __future__ import annotations

import re
from xml.etree import ElementTree as ET


def parse_sitemap_xml(xml_text: str) -> tuple[str, list[tuple[str, str | None]]]:
    """Return ('urlset'|'sitemapindex', [(loc, lastmod), ...])."""
    cleaned = re.sub(r'\sxmlns="[^"]+"', "", xml_text, count=1)
    root = ET.fromstring(cleaned)
    kind = root.tag.split("}")[-1]
    rows: list[tuple[str, str | None]] = []
    if kind == "sitemapindex":
        for sm in root.findall("sitemap"):
            loc = (sm.findtext("loc") or "").strip()
            lastmod = (sm.findtext("lastmod") or "").strip() or None
            if loc:
                rows.append((loc, lastmod))
        return "sitemapindex", rows
    for url in root.findall("url"):
        loc = (url.findtext("loc") or "").strip()
        lastmod = (url.findtext("lastmod") or "").strip() or None
        if loc:
            rows.append((loc, lastmod))
    if not rows:
        for el in root.iter():
            if el.tag.split("}")[-1] == "loc" and el.text:
                rows.append((el.text.strip(), None))
        if kind != "sitemapindex" and rows and all(
            r[0].endswith(".xml") or "/sitemap" in r[0] for r in rows[:5]
        ):
            return "sitemapindex", rows
    return "urlset", rows
