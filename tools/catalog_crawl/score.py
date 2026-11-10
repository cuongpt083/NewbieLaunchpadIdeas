from __future__ import annotations

from .models import CatalogItem

# Junior 1–2y can clone the *core job* in ~1–2 weeks. Not the full production app.
HIGH_CAT = (
    "tiện ích",
    "giáo dục",
    "học tập",
    "bàn phím",
    "nhập liệu",
    "trình duyệt",
    "ghi chú",
    "năng suất",
    "pos",
    "kho",
    "tài chính cá nhân",
    "ngân sách",
    "ngôn ngữ",
    "từ điển",
    "lịch",
    "quiz",
    "đề thi",
    "flashcard",
    "utilities",
    "education",
    "keyboard",
    "note-taking",
    "task",
    "productivity",
    "budget",
    "language",
    "file management",
    "point of sale",
    "inventory",
    "calendar",
    "focus",
    "study",
    "browser",
    "extension",
)

LOW_CAT = (
    "robot",
    "iot",
    "phần cứng",
    "hardware",
    "cad",
    "blockchain",
    "defi",
    "nft",
    "web3",
    "crypto",
    "ngân hàng",
    "neobank",
    "bảo hiểm",
    "insurance",
    "hạ tầng",
    "infrastructure",
    "devops",
    "observability",
    "compiler",
    "wearable",
    "cơ khí",
    "ai agent",
    "ai agents",
    "code editor",
)

HIGH_KW = (
    "bộ gõ",
    "telex",
    "vni",
    "todo",
    "to-do",
    "checklist",
    "flashcard",
    "quiz",
    "pomodoro",
    "habit",
    "bookmark",
    "clipboard",
    "screenshot",
    "chi tiêu",
    "expense",
    "budget",
    "từ điển",
    "dictionary",
    "converter",
    "markdown",
    "ghi chú",
    "timer",
    "kanban",
    "qr",
    "url shortener",
    "rút gọn",
    "đề thi",
    "chấm điểm",
    "điểm danh",
    "spaced repetition",
    "thẻ ghi nhớ",
    "habit tracker",
    "to do",
    "gõ tiếng việt",
)

LOW_KW = (
    "cad",
    "compiler",
    "kernel",
    "blockchain",
    "smart contract",
    "kubernetes",
    "hypervisor",
    "finite element",
    "llm train",
    "3d printing",
    "in 3d",
    "ai agent platform",
)


def _blob(item: CatalogItem) -> str:
    parts = [item.name, item.tagline or "", item.description or "", item.category or ""]
    return " ".join(parts).lower()


def _hits(text: str, needles: tuple[str, ...]) -> list[str]:
    return [n for n in needles if n in text]


def score_item(item: CatalogItem) -> CatalogItem:
    text = _blob(item)
    cat = (item.category or "").lower()
    low_c = _hits(cat, LOW_CAT) or _hits(text, LOW_CAT)
    high_c = _hits(cat, HIGH_CAT)
    high_k = _hits(text, HIGH_KW)
    low_k = _hits(text, LOW_KW)
    reasons: list[str] = []
    if low_c:
        reasons.append("low_cat:" + ",".join(low_c[:3]))
    if low_k:
        reasons.append("low_kw:" + ",".join(low_k[:3]))
    if high_c:
        reasons.append("high_cat:" + ",".join(high_c[:3]))
    if high_k:
        reasons.append("high_kw:" + ",".join(high_k[:3]))
    if low_c or low_k:
        fit = "low"
    elif high_c or high_k:
        fit = "high"
    else:
        fit = "medium"
        reasons.append("default:medium")
    item.extra["fresher_clone_fit"] = fit
    item.extra["fit_reasons"] = reasons
    job = (item.tagline or item.description or item.name or "").strip()
    if len(job) > 160:
        job = job[:157] + "…"
    item.extra["mvp_hint"] = (
        f"Clone 1–2 tính năng cốt lõi: {job} — không copy thương hiệu/UI/dữ liệu."
    )
    return item
