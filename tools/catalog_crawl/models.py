from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CatalogItem:
    source: str
    source_url: str
    slug: str
    name: str
    tagline: str | None = None
    description: str | None = None
    category: str | None = None
    product_url: str | None = None
    pricing: str | None = None
    language: str | None = None
    published_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
