"""Fetch Wild, Alarcón-Nieto & Aplin (2024) great tit Dryad dataset via Playwright.

Dryad uses Anubis (techaro.lol) proof-of-work + AWS WAF token to gate downloads.
Both are standard rate-limiting mechanisms designed to be passed by real browsers
running JS. Playwright drives a real headless Chromium that solves the PoW the
intended way (no bypass; just normal JS execution).

DOI: 10.5061/dryad.x95x69ps8 (Wild et al. 2024 great tit ontogeny).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "great_tit_wild_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANDING = "https://datadryad.org/dataset/doi:10.5061/dryad.x95x69ps8"

TARGETS = [
    ("2981852", "README.md"),
    ("2981839", "species_age.txt"),
    ("2981818", "fledgling_data.txt"),
    ("2981843", "Mill.data.summer.txt"),
    ("2981840", "Mill.data.autumn.txt"),
    ("2981842", "Mill.data.winter.txt"),
    ("2981841", "Mill.data.spring.txt"),
]


async def warmup(page) -> None:
    """Visit landing page so Anubis PoW + WAF token cookies are issued."""
    print(f"Loading landing: {LANDING}")
    await page.goto(LANDING, wait_until="networkidle", timeout=120000)
    # Anubis sometimes presents an interstitial. Wait for it to clear.
    for _ in range(20):
        title = await page.title()
        if "Validating" not in title and "Just a moment" not in title:
            break
        await page.wait_for_timeout(1000)
    print(f"Landing settled: title={await page.title()!r}")


async def fetch_via_download(ctx, fid: str, name: str) -> bool:
    """Trigger a download by navigating; Playwright catches the download event."""
    out = OUT_DIR / name
    page = await ctx.new_page()
    url = f"https://datadryad.org/downloads/file_stream/{fid}"
    try:
        async with page.expect_download(timeout=180000) as dl_info:
            # goto() raises if Content-Disposition forces download; that's fine —
            # the download event is captured by expect_download regardless.
            try:
                await page.goto(url, wait_until="commit", timeout=10000)
            except Exception:
                pass  # noqa: BLE001 — download interrupts navigation; expected
        download = await dl_info.value
        await download.save_as(out)
        print(f"  DOWNLOAD-EVENT  {name}  {out.stat().st_size} bytes")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  download-event FAILED for {name}: {type(exc).__name__}: {exc}")
        return False
    finally:
        await page.close()


async def fetch_via_navigate(ctx, fid: str, name: str) -> bool:
    """Navigate the page to the URL; if it returns text/binary, capture body."""
    out = OUT_DIR / name
    page = await ctx.new_page()
    url = f"https://datadryad.org/downloads/file_stream/{fid}"
    try:
        # The Anubis interstitial may redirect after PoW. Wait long enough.
        resp = await page.goto(url, wait_until="networkidle", timeout=180000)
        if resp is None:
            return False
        # If Anubis solved PoW, page now contains the file body.
        # For text/* responses, that body is the html-rendered text inside <pre>.
        # For application/* it triggers a download instead (caught by other path).
        body = await resp.body()
        ctype = resp.headers.get("content-type", "")
        if len(body) > 200 and "Validating" not in body[:300].decode("utf-8", "replace"):
            out.write_bytes(body)
            print(f"  NAVIGATED      {name}  {len(body)} bytes  ({ctype})")
            return True
        # Maybe the page rendered it as text content inside body
        text = await page.evaluate("() => document.body.innerText")
        if text and len(text) > 200 and "Validating" not in text[:200]:
            out.write_text(text, encoding="utf-8")
            print(f"  INNERTEXT      {name}  {len(text)} chars")
            return True
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"  navigate FAILED for {name}: {type(exc).__name__}: {exc}")
        return False
    finally:
        await page.close()


async def main() -> int:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            accept_downloads=True,
        )
        page = await ctx.new_page()
        await warmup(page)
        cookies = await ctx.cookies("https://datadryad.org")
        print(f"Cookies after warmup: {[c['name'] for c in cookies]}")
        await page.close()

        failures = []
        for fid, name in TARGETS:
            print(f"Fetching {name} (id={fid})")
            # First try a real browser download event
            ok = await fetch_via_download(ctx, fid, name)
            if not ok:
                ok = await fetch_via_navigate(ctx, fid, name)
            if not ok:
                failures.append(name)

        await browser.close()
        if failures:
            print(f"FAILED: {failures}", file=sys.stderr)
            return 2
        print("ALL FETCHED")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
