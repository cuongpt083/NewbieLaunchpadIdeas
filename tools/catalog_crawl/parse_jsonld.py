from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlparse

from .models import CatalogItem

_JSONLD = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_OG = re.compile(
    r'<meta[^>]+property=["\']og:([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
    re.I,
)
_OG_SWAP = re.compile(
    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:([^"\']+)["\']',
    re.I,
)
_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")


def jsonld_blocks(html: str) -> list[Any]:
    out: list[Any] = []
    for raw in _JSONLD.findall(html):
        text = unescape(raw.strip())
        try:
            out.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return out


def flatten_jsonld(obj: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        if "@graph" in node:
            walk(node["@graph"])
            return
        found.append(node)

    walk(obj)
    return found


def software_apps(html: str) -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    for block in jsonld_blocks(html):
        for node in flatten_jsonld(block):
            types = node.get("@type")
            if types == "SoftwareApplication":
                apps.append(node)
            elif isinstance(types, list) and "SoftwareApplication" in types:
                apps.append(node)
    return apps


def og_tags(html: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for key, val in _OG.findall(html):
        tags.setdefault(key, unescape(val))
    for val, key in _OG_SWAP.findall(html):
        tags.setdefault(key, unescape(val))
    return tags


def first_h1(html: str) -> str | None:
    m = _H1.search(html)
    if not m:
        return None
    text = unescape(_TAG.sub("", m.group(1)))
    text = " ".join(text.split())
    return text or None


def _str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, dict):
        for key in ("name", "url", "description"):
            if key in value:
                return _str(value[key])
        return None
    if isinstance(value, list) and value:
        return _str(value[0])
    return str(value)


def item_from_app(source: str, source_url: str, slug: str, app: dict[str, Any]) -> CatalogItem:
    offers = app.get("offers") if isinstance(app.get("offers"), dict) else {}
    pricing = _str(offers.get("description")) if offers else None
    if not pricing and offers:
        price = _str(offers.get("price"))
        currency = _str(offers.get("priceCurrency"))
        if price:
            pricing = f"{price} {currency or ''}".strip()
    return CatalogItem(
        source=source,
        source_url=source_url,
        slug=slug,
        name=_str(app.get("name")) or slug,
        tagline=_str(app.get("alternateName")),
        description=_str(app.get("description")),
        category=_str(app.get("applicationCategory")),
        product_url=_str(app.get("installUrl") or app.get("sameAs")),
        pricing=pricing,
        language=_str(app.get("inLanguage")),
        published_at=_str(app.get("datePublished")),
        extra={"parser": "jsonld_softwareapplication"},
    )


def item_from_html(source: str, source_url: str, slug: str, html: str) -> CatalogItem:
    apps = software_apps(html)
    if apps:
        return item_from_app(source, source_url, slug, apps[0])
    og = og_tags(html)
    name = first_h1(html) or og.get("title") or slug
    tagline = og.get("description")
    title = og.get("title") or ""
    if " | " in title:
        name = title.split(" | ", 1)[0].strip() or name
    if title.startswith("Discover ") and " on Uneed" in title:
        name = title[len("Discover ") :].split(" on Uneed", 1)[0].strip() or name
    product_url = None
    host = urlparse(source_url).netloc
    same = og.get("url")
    if same and urlparse(same).netloc and urlparse(same).netloc != host:
        product_url = same
    return CatalogItem(
        source=source,
        source_url=source_url,
        slug=slug,
        name=name,
        tagline=tagline,
        description=tagline,
        product_url=product_url,
        extra={"parser": "og_h1"},
    )
