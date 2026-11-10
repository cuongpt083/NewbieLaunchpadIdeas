from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .client import PoliteClient
from .models import CatalogItem
from .parse_jsonld import item_from_html
from .sitemap import parse_sitemap_xml

SAMPLE_LIMIT_CAP = 20
SAMPLE_LIMIT_DEFAULT_MAX = 5


@dataclass(frozen=True)
class Adapter:
    name: str
    min_delay_s: float
    sitemap_entry: str
    product_hosts: tuple[str, ...]

    def is_product_url(self, url: str) -> bool:
        raise NotImplementedError

    def slug(self, url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        return path.rsplit("/", 1)[-1]

    def collect_product_urls(self, client: PoliteClient) -> list[str]:
        urls: list[str] = []
        queue = [self.sitemap_entry]
        seen: set[str] = set()
        while queue:
            sm = queue.pop(0)
            if sm in seen:
                continue
            seen.add(sm)
            kind, rows = parse_sitemap_xml(client.fetch(sm))
            if kind == "sitemapindex":
                for loc, _ in rows:
                    if self._sitemap_child_ok(loc):
                        queue.append(loc)
                continue
            for loc, _ in rows:
                if self.is_product_url(loc):
                    urls.append(loc)
        return urls

    def _sitemap_child_ok(self, loc: str) -> bool:
        return True

    def parse(self, url: str, html: str) -> CatalogItem:
        return item_from_html(self.name, url, self.slug(url), html)


class Unikorn(Adapter):
    def __init__(self) -> None:
        super().__init__(
            name="unikorn",
            min_delay_s=10.0,
            sitemap_entry="https://unikorn.vn/sitemap.xml",
            product_hosts=("unikorn.vn",),
        )

    def _sitemap_child_ok(self, loc: str) -> bool:
        return "/sitemap/products/" in loc

    def is_product_url(self, url: str) -> bool:
        p = urlparse(url)
        return p.netloc.endswith("unikorn.vn") and p.path.startswith("/p/") and p.path.count("/") == 2


class TinyLaunch(Adapter):
    def __init__(self) -> None:
        super().__init__(
            name="tinylaunch",
            min_delay_s=1.0,
            sitemap_entry="https://www.tinylaunch.com/sitemap.xml",
            product_hosts=("www.tinylaunch.com", "tinylaunch.com"),
        )

    def is_product_url(self, url: str) -> bool:
        p = urlparse(url)
        return p.netloc.endswith("tinylaunch.com") and p.path.startswith("/launch/")


class Uneed(Adapter):
    def __init__(self) -> None:
        super().__init__(
            name="uneed",
            min_delay_s=1.0,
            sitemap_entry="https://www.uneed.best/sitemap_index.xml",
            product_hosts=("www.uneed.best", "uneed.best"),
        )

    def _sitemap_child_ok(self, loc: str) -> bool:
        return loc.rstrip("/").endswith("/__sitemap__/tools.xml")

    def is_product_url(self, url: str) -> bool:
        p = urlparse(url)
        return p.netloc.endswith("uneed.best") and p.path.startswith("/tool/")


class Fazier(Adapter):
    def __init__(self) -> None:
        super().__init__(
            name="fazier",
            min_delay_s=1.0,
            sitemap_entry="https://fazier.com/launches/sitemap.xml",
            product_hosts=("fazier.com", "www.fazier.com"),
        )

    def is_product_url(self, url: str) -> bool:
        p = urlparse(url)
        path = p.path
        if path.startswith("/p/"):
            return False
        return p.netloc.endswith("fazier.com") and path.startswith("/launches/") and "/sitemap" not in path


ADAPTERS: dict[str, Adapter] = {
    "unikorn": Unikorn(),
    "tinylaunch": TinyLaunch(),
    "uneed": Uneed(),
    "fazier": Fazier(),
}
