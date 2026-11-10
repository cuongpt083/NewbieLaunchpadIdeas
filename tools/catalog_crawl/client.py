from __future__ import annotations

import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

USER_AGENT = "NewbieLaunchpadIdeas/0.1 (+local research; sequential; honors robots.txt)"


class HaltError(RuntimeError):
    pass


class PoliteClient:
    def __init__(self, min_delay_s: float) -> None:
        self.min_delay_s = min_delay_s
        self._last: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}

    def _host(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def robots(self, url: str) -> RobotFileParser:
        host = self._host(url)
        if host in self._robots:
            return self._robots[host]
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            self._sleep(host, 0)
            with urllib.request.urlopen(self._req(robots_url), timeout=30) as resp:
                raw = resp.read().decode("utf-8", "replace")
            rp.parse(raw.splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise HaltError(f"robots.txt {robots_url} HTTP {e.code}") from e
            rp.parse(["User-agent: *", "Allow: /"])
        except urllib.error.URLError as e:
            raise HaltError(f"robots.txt fetch failed {robots_url}: {e}") from e
        delay = rp.crawl_delay(USER_AGENT)
        if delay is not None:
            self.min_delay_s = max(self.min_delay_s, float(delay))
        self._robots[host] = rp
        return rp

    def allowed(self, url: str) -> bool:
        return self.robots(url).can_fetch(USER_AGENT, url)

    def fetch(self, url: str) -> str:
        if not self.allowed(url):
            raise HaltError(f"robots Disallow: {url}")
        self._sleep(self._host(url), self.min_delay_s)
        try:
            with urllib.request.urlopen(self._req(url), timeout=45) as resp:
                if resp.status in (403, 429):
                    raise HaltError(f"HTTP {resp.status} {url}")
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise HaltError(f"HTTP {e.code} {url}") from e
            raise

    def _sleep(self, host: str, delay: float) -> None:
        last = self._last.get(host)
        if last is not None and delay > 0:
            wait = delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last[host] = time.monotonic()

    def _req(self, url: str) -> urllib.request.Request:
        return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
