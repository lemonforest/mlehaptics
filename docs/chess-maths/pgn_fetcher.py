#!/usr/bin/env python3
"""
PGN Fetcher — Multi-source chess game fetcher with CLI
========================================================

Three sources for chess PGN games:

  1. HuggingFace fishtest_pgns  — Stockfish-vs-Stockfish engine test games
     Dataset: official-stockfish/fishtest_pgns (1TB, 2018-2021)

  2. chessgames.com             — Famous human games by game ID (GID)
     API: /njs/api/game/downloadPGN/{gid}

  3. The Week in Chess (TWIC)   — Elite tournament PGN bundles
     URL: theweekinchess.com/assets/files/pgn/{event}.pgn

All sources return normalized game dicts with consistent structure.

Dependencies: requests (pip install requests)
Optional: python-chess (pip install chess) — only needed for bridge export

Usage (programmatic):
    from pgn_fetcher import PGNFetcher, ChessGamesSource, TWICSource, MultiFetcher

    # HuggingFace (backward compatible)
    fetcher = PGNFetcher()
    games = fetcher.fetch_random_games(n=20)

    # chessgames.com
    cg = ChessGamesSource()
    game = cg.fetch_by_gid(1011478)  # Kasparov-Topalov 1999

    # TWIC
    twic = TWICSource()
    events = twic.list_events()
    games = twic.fetch_event('tatamast26', max_games=10)

    # All sources via facade
    multi = MultiFetcher()
    games = multi.fetch('chessgames', gids=[1011478, 1937789])
    games = multi.fetch('twic', event='tatamast26', max_games=5)

Usage (CLI):
    python pgn_fetcher.py fetch --source chessgames --gid 1011478
    python pgn_fetcher.py fetch --source twic --event tatamast26 --n 5
    python pgn_fetcher.py fetch --source hf --n 3 --seed 42
    python pgn_fetcher.py list --source twic
    python pgn_fetcher.py search --source twic --query "candidates"
    python pgn_fetcher.py cache stats
    python pgn_fetcher.py interactive
    python pgn_fetcher.py demo
"""

import os
import sys
import gzip
import json
import io
import random
import hashlib
import time
import re
import argparse
from abc import ABC, abstractmethod

import requests


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# HuggingFace fishtest
DATASET_REPO = "official-stockfish/fishtest_pgns"
HF_API_BASE = "https://huggingface.co/api/datasets"
HF_RESOLVE_BASE = "https://huggingface.co/datasets"

# chessgames.com
CHESSGAMES_BASE = "https://www.chessgames.com"
CHESSGAMES_PGN_API = CHESSGAMES_BASE + "/njs/api/game/downloadPGN/{gid}"
CHESSGAMES_RATE_DELAY_S = 1.0  # polite delay between requests

# TWIC
TWIC_BASE = "https://theweekinchess.com"
TWIC_PGN_URL = TWIC_BASE + "/assets/files/pgn/{event}.pgn"
TWIC_INDEX_URL = TWIC_BASE + "/a-year-of-pgn-game-files"

# Local cache directory (alongside this script)
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pgn_cache')

# Shared request settings
REQUEST_TIMEOUT_S = 30
DOWNLOAD_TIMEOUT_S = 120
MAX_RETRIES = 3
RETRY_DELAY_S = 2

# Browser-like UA for sites that block default requests
BROWSER_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)

# HuggingFace date range
DATE_RANGE_START = '18-05-25'
DATE_RANGE_END = '21-11-26'


# ═══════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════

class FetchError(Exception):
    """Raised when a source cannot be reached after retries."""
    pass


class ParseError(Exception):
    """Raised when PGN parsing fails completely."""
    pass


# ═══════════════════════════════════════════════════════════════
# BASE CLASS
# ═══════════════════════════════════════════════════════════════

class PGNSource(ABC):
    """Base class for PGN game sources.

    Provides shared infrastructure: HTTP session with retries, logging,
    cache directory management, and the common parse_games() static method.
    """

    name = 'base'

    def __init__(self, cache_dir=None, verbose=True):
        self.cache_dir = cache_dir or CACHE_DIR
        self.verbose = verbose
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'pgn-fetcher/2.0 (chess-spectral-research)'
        })
        os.makedirs(self.cache_dir, exist_ok=True)

    def _log(self, msg):
        if self.verbose:
            # stderr so stdout stays reserved for content (piping into pgn_bridge.py)
            print(f"  [pgn_fetcher:{self.name}] {msg}", flush=True, file=sys.stderr)

    def _api_get(self, url, timeout=None):
        """GET with retry logic and exponential backoff.

        Retries on transient errors (timeout, 5xx, 429).
        Does NOT retry on definitive errors (404, 403).
        """
        timeout = timeout or REQUEST_TIMEOUT_S
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.get(url, timeout=timeout)
                if resp.status_code == 429:
                    wait = RETRY_DELAY_S * (2 ** attempt)
                    self._log(f"Rate limited (429), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                if resp.status_code in (404, 403):
                    # Definitive errors — don't retry
                    resp.raise_for_status()
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    # Only retry on transient errors
                    if hasattr(e, 'response') and e.response is not None:
                        if e.response.status_code in (404, 403):
                            raise FetchError(
                                f"HTTP {e.response.status_code}: {url}"
                            ) from e
                    wait = RETRY_DELAY_S * (attempt + 1)
                    self._log(f"Retry {attempt + 1}/{MAX_RETRIES}: {e}")
                    time.sleep(wait)
                else:
                    raise FetchError(
                        f"Failed after {MAX_RETRIES} attempts: {url}"
                    ) from e

    @staticmethod
    def _parse_single_game(game_text, min_moves=None, max_moves=None,
                           result_filter=None):
        """Parse a single game's PGN text. Returns dict or None if filtered."""
        headers = {}
        header_end = 0
        for m in re.finditer(r'^\[(\w+)\s+"(.*)"\]', game_text, re.MULTILINE):
            headers[m.group(1)] = m.group(2)
            header_end = m.end()

        moves_text = game_text[header_end:].strip()

        ply_count = headers.get('PlyCount')
        if ply_count and ply_count.isdigit():
            n_moves = int(ply_count) // 2
        else:
            # Match move numbers like "1." "23." but NOT decimals like "0.14"
            move_numbers = re.findall(r'(?:^|\s)(\d+)\.', moves_text)
            n_moves = int(move_numbers[-1]) if move_numbers else 0

        if min_moves is not None and n_moves < min_moves:
            return None
        if max_moves is not None and n_moves > max_moves:
            return None
        if result_filter is not None and headers.get('Result') != result_filter:
            return None

        return {
            'headers': headers,
            'moves': moves_text,
            'pgn': game_text,
            'n_moves': n_moves,
        }

    @staticmethod
    def parse_games(pgn_text, max_games=None, min_moves=None, max_moves=None,
                    result_filter=None):
        """Parse individual games from a PGN text blob.

        Args:
            pgn_text: Raw PGN string (may contain thousands of games)
            max_games: Stop after extracting this many games (None = all)
            min_moves: Skip games shorter than this (full moves, not plies)
            max_moves: Skip games longer than this
            result_filter: If set, only keep games with this result
                           ('1-0', '0-1', '1/2-1/2', or '*')

        Returns list of dicts:
            {
                'headers': dict of PGN header key-value pairs,
                'moves': str of the move text (SAN notation),
                'pgn': str full PGN text for this game,
                'n_moves': int estimated full-move count
            }
        """
        games = []
        game_starts = [m.start() for m in
                       re.finditer(r'^\[Event ', pgn_text, re.MULTILINE)]

        if not game_starts:
            return games

        for i, start in enumerate(game_starts):
            if max_games is not None and len(games) >= max_games:
                break

            end = game_starts[i + 1] if i + 1 < len(game_starts) else len(pgn_text)
            game_text = pgn_text[start:end].strip()

            if not game_text:
                continue

            parsed = PGNSource._parse_single_game(
                game_text, min_moves, max_moves, result_filter
            )
            if parsed is not None:
                games.append(parsed)

        return games

    @staticmethod
    def _normalize_game(game_dict, source_name, source_id):
        """Add source metadata to a game dict."""
        game_dict['source'] = source_name
        game_dict['source_id'] = str(source_id)
        return game_dict

    def cache_stats(self):
        """Report cache usage."""
        if not os.path.exists(self.cache_dir):
            return {'files': 0, 'size_mb': 0.0}

        total_size = 0
        file_count = 0
        for f in os.listdir(self.cache_dir):
            fp = os.path.join(self.cache_dir, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
                file_count += 1

        return {
            'files': file_count,
            'size_mb': total_size / 1e6,
            'path': self.cache_dir,
        }

    def clear_cache(self):
        """Remove all cached files."""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            self._log("Cache cleared")


# ═══════════════════════════════════════════════════════════════
# SOURCE 1: HUGGINGFACE FISHTEST (existing PGNFetcher, preserved)
# ═══════════════════════════════════════════════════════════════

class PGNFetcher(PGNSource):
    """Fetch PGN games from the HuggingFace fishtest_pgns dataset.

    Caches downloaded files locally to avoid redundant downloads.
    All network calls use the public HuggingFace REST API (no auth required).

    This is the original class — backward compatible with all existing imports.
    """

    name = 'huggingface'

    def __init__(self, cache_dir=None, verbose=True):
        super().__init__(cache_dir=cache_dir, verbose=verbose)
        self._dates_cache = None

    # ── Directory listing ──────────────────────────────────────

    def list_dates(self, force_refresh=False):
        """List all available date directories (YY-MM-DD format).

        Returns sorted list of date strings. Cached after first call.
        """
        if self._dates_cache is not None and not force_refresh:
            return self._dates_cache

        # Check local cache file first
        dates_cache_file = os.path.join(self.cache_dir, '_dates.json')
        cache_age_limit = 86400 * 7  # refresh weekly

        if (not force_refresh
                and os.path.exists(dates_cache_file)
                and time.time() - os.path.getmtime(dates_cache_file) < cache_age_limit):
            with open(dates_cache_file, 'r') as f:
                self._dates_cache = json.load(f)
            self._log(f"Loaded {len(self._dates_cache)} dates from cache")
            return self._dates_cache

        self._log("Fetching date listing from HuggingFace API...")
        url = f"{HF_API_BASE}/{DATASET_REPO}/tree/main"
        resp = self._api_get(url)
        entries = resp.json()

        dates = sorted([
            e['path'] for e in entries
            if e['type'] == 'directory' and re.match(r'^\d{2}-\d{2}-\d{2}$', e['path'])
        ])

        # Save to local cache
        with open(dates_cache_file, 'w') as f:
            json.dump(dates, f)

        self._dates_cache = dates
        self._log(f"Found {len(dates)} dates ({dates[0]} to {dates[-1]})")
        return dates

    def list_tests(self, date):
        """List test IDs available on a given date.

        Returns list of test_id strings (MongoDB ObjectIds).
        """
        # Check local cache
        tests_cache_file = os.path.join(self.cache_dir, f'_tests_{date}.json')
        if os.path.exists(tests_cache_file):
            with open(tests_cache_file, 'r') as f:
                return json.load(f)

        url = f"{HF_API_BASE}/{DATASET_REPO}/tree/main/{date}"
        resp = self._api_get(url)
        entries = resp.json()

        test_ids = sorted([
            e['path'].split('/')[-1] for e in entries
            if e['type'] == 'directory'
        ])

        with open(tests_cache_file, 'w') as f:
            json.dump(test_ids, f)

        self._log(f"Date {date}: {len(test_ids)} tests")
        return test_ids

    # ── Metadata ───────────────────────────────────────────────

    def fetch_metadata(self, date, test_id):
        """Fetch the JSON metadata for a specific test run.

        Returns dict with test configuration, results, SPRT data, etc.
        """
        cache_file = os.path.join(self.cache_dir, f'{test_id}.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)

        url = (f"{HF_RESOLVE_BASE}/{DATASET_REPO}/resolve/main/"
               f"{date}/{test_id}/{test_id}.json")
        resp = self._api_get(url)
        meta = resp.json()

        with open(cache_file, 'w') as f:
            json.dump(meta, f, indent=2)

        return meta

    def get_tc_base(self, meta):
        """Extract base time control in seconds from metadata."""
        if 'tc_base' in meta:
            return float(meta['tc_base'])
        tc_str = meta.get('args', {}).get('tc', '')
        match = re.match(r'^(\d+(?:\.\d+)?)', tc_str)
        return float(match.group(1)) if match else 0.0

    def get_total_games(self, meta):
        """Extract total games played from results."""
        r = meta.get('results', {})
        return r.get('wins', 0) + r.get('losses', 0) + r.get('draws', 0)

    # ── PGN download ──────────────────────────────────────────

    def fetch_pgn(self, date, test_id):
        """Download and decompress the PGN file for a test run.

        Returns the full PGN text as a string. Cached locally as .pgn.gz.
        """
        gz_cache = os.path.join(self.cache_dir, f'{test_id}.pgn.gz')
        txt_cache = os.path.join(self.cache_dir, f'{test_id}.pgn')

        # Check for decompressed cache first
        if os.path.exists(txt_cache):
            self._log(f"Cache hit: {test_id}.pgn")
            with open(txt_cache, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()

        # Check for compressed cache
        if os.path.exists(gz_cache):
            self._log(f"Decompressing cached {test_id}.pgn.gz")
            with gzip.open(gz_cache, 'rt', encoding='utf-8', errors='replace') as f:
                text = f.read()
            with open(txt_cache, 'w', encoding='utf-8') as f:
                f.write(text)
            return text

        # Download from HuggingFace
        url = (f"{HF_RESOLVE_BASE}/{DATASET_REPO}/resolve/main/"
               f"{date}/{test_id}/{test_id}.pgn.gz")
        self._log(f"Downloading {test_id}.pgn.gz ...")
        resp = self._api_get(url, timeout=DOWNLOAD_TIMEOUT_S)

        # Save compressed
        with open(gz_cache, 'wb') as f:
            f.write(resp.content)
        self._log(f"Downloaded {len(resp.content) / 1e6:.1f} MB")

        # Decompress
        text = gzip.decompress(resp.content).decode('utf-8', errors='replace')
        with open(txt_cache, 'w', encoding='utf-8') as f:
            f.write(text)

        return text

    def fetch_pgn_games(self, date, test_id, max_games=100,
                        min_moves=None, max_moves=None, result_filter=None):
        """Download PGN and return parsed games directly.

        Streams from gzip — only decompresses enough to get max_games.
        More memory-efficient than fetch_pgn() for large PGN files.
        """
        gz_cache = os.path.join(self.cache_dir, f'{test_id}.pgn.gz')

        # Download if not cached
        if not os.path.exists(gz_cache):
            url = (f"{HF_RESOLVE_BASE}/{DATASET_REPO}/resolve/main/"
                   f"{date}/{test_id}/{test_id}.pgn.gz")
            self._log(f"Downloading {test_id}.pgn.gz ...")
            resp = self._api_get(url, timeout=DOWNLOAD_TIMEOUT_S)
            with open(gz_cache, 'wb') as f:
                f.write(resp.content)
            self._log(f"Downloaded {len(resp.content) / 1e6:.1f} MB")
        else:
            self._log(f"Cache hit: {test_id}.pgn.gz")

        # Stream-parse from gzip: read games one at a time
        games = []
        candidates_needed = (max_games or 100) * 5
        current_game_lines = []
        games_seen = 0

        with gzip.open(gz_cache, 'rt', encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('[Event ') and current_game_lines:
                    game_text = ''.join(current_game_lines).strip()
                    if game_text:
                        parsed = self._parse_single_game(game_text,
                                                         min_moves, max_moves,
                                                         result_filter)
                        if parsed is not None:
                            games.append(parsed)
                            if len(games) >= (max_games or candidates_needed):
                                break
                    games_seen += 1
                    if games_seen >= candidates_needed:
                        break
                    current_game_lines = [line]
                else:
                    current_game_lines.append(line)

            # Don't forget the last game
            if current_game_lines and len(games) < (max_games or candidates_needed):
                game_text = ''.join(current_game_lines).strip()
                if game_text:
                    parsed = self._parse_single_game(game_text,
                                                     min_moves, max_moves,
                                                     result_filter)
                    if parsed is not None:
                        games.append(parsed)

        return games

    # ── High-level convenience methods ─────────────────────────

    def fetch_random_games(self, n=20, min_moves=30, max_moves=100,
                           tc_base_min=10.0, date=None, seed=None):
        """Fetch N random games from the dataset.

        Picks a random date, picks a random test with suitable time control,
        downloads the PGN, and extracts N games matching move-count filters.
        """
        if seed is not None:
            random.seed(seed)

        dates = self.list_dates()
        collected = []
        attempts = 0
        max_attempts = 10

        while len(collected) < n and attempts < max_attempts:
            attempts += 1

            chosen_date = date or random.choice(dates)
            self._log(f"Attempt {attempts}: trying date {chosen_date}")

            try:
                test_ids = self.list_tests(chosen_date)
            except (requests.RequestException, FetchError):
                self._log(f"  Failed to list tests for {chosen_date}, skipping")
                continue

            if not test_ids:
                continue

            random.shuffle(test_ids)
            for test_id in test_ids[:3]:
                try:
                    meta = self.fetch_metadata(chosen_date, test_id)
                except (requests.RequestException, FetchError):
                    continue

                tc = self.get_tc_base(meta)
                total = self.get_total_games(meta)

                if tc < tc_base_min:
                    continue
                if total < 100:
                    continue

                self._log(f"  Test {test_id}: TC={tc}s, {total} games")

                remaining = n - len(collected)
                try:
                    games = self.fetch_pgn_games(
                        chosen_date, test_id,
                        max_games=remaining * 3,
                        min_moves=min_moves,
                        max_moves=max_moves,
                    )
                except (requests.RequestException, FetchError, Exception) as e:
                    self._log(f"  Failed: {e}")
                    continue

                if games:
                    random.shuffle(games)
                    take = min(remaining, len(games))
                    for g in games[:take]:
                        g['source_date'] = chosen_date
                        g['source_test'] = test_id
                        g['source_tc'] = tc
                    collected.extend(games[:take])
                    self._log(f"  Collected {take} games "
                              f"(total: {len(collected)}/{n})")
                break

        if len(collected) < n:
            self._log(f"Warning: only collected {len(collected)}/{n} games")

        return collected[:n]

    def fetch_games_by_criteria(self, n=50, min_moves=30, max_moves=80,
                                tc_base_min=10.0, tc_base_max=None,
                                result_filter=None, decisive_only=False,
                                dates=None, seed=None):
        """Fetch games matching specific criteria, sampling across dates."""
        if seed is not None:
            random.seed(seed)

        all_dates = self.list_dates()
        search_dates = dates or random.sample(all_dates, min(15, len(all_dates)))
        collected = []

        for chosen_date in search_dates:
            if len(collected) >= n:
                break

            try:
                test_ids = self.list_tests(chosen_date)
            except (requests.RequestException, FetchError):
                continue

            for test_id in test_ids:
                if len(collected) >= n:
                    break

                try:
                    meta = self.fetch_metadata(chosen_date, test_id)
                except (requests.RequestException, FetchError):
                    continue

                tc = self.get_tc_base(meta)
                if tc < tc_base_min:
                    continue
                if tc_base_max is not None and tc > tc_base_max:
                    continue

                total = self.get_total_games(meta)
                if total < 100:
                    continue

                remaining = n - len(collected)
                effective_filter = result_filter

                try:
                    games = self.fetch_pgn_games(
                        chosen_date, test_id,
                        max_games=remaining * 3,
                        min_moves=min_moves,
                        max_moves=max_moves,
                        result_filter=effective_filter,
                    )
                except (requests.RequestException, FetchError, Exception):
                    continue

                if decisive_only:
                    games = [g for g in games
                             if g['headers'].get('Result') in ('1-0', '0-1')]

                if games:
                    random.shuffle(games)
                    take = min(remaining, len(games))
                    for g in games[:take]:
                        g['source_date'] = chosen_date
                        g['source_test'] = test_id
                        g['source_tc'] = tc
                    collected.extend(games[:take])
                    self._log(f"  {chosen_date}/{test_id}: +{take} games "
                              f"(total: {len(collected)}/{n})")

        if len(collected) < n:
            self._log(f"Warning: only collected {len(collected)}/{n} games")

        return collected[:n]


# ═══════════════════════════════════════════════════════════════
# SOURCE 2: CHESSGAMES.COM
# ═══════════════════════════════════════════════════════════════

class ChessGamesSource(PGNSource):
    """Fetch individual games from chessgames.com by game ID (GID).

    Uses the public PGN download API. Requires browser-like User-Agent
    (403 otherwise). Polite rate limiting between requests.

    Usage:
        cg = ChessGamesSource()
        game = cg.fetch_by_gid(1011478)       # Kasparov-Topalov 1999
        games = cg.fetch_by_gids([1011478, 1937789])

    Famous GIDs:
        1011478  Kasparov-Topalov 1999 (Rxd4!! sacrifice)
        1937789  Carlsen-Caruana WCC 2018 G6
        1060802  Fischer-Spassky 1972 G6
        1032455  Kasparov-Deep Blue 1997 G6
    """

    name = 'chessgames'

    def __init__(self, cache_dir=None, verbose=True):
        super().__init__(cache_dir=cache_dir, verbose=verbose)
        # chessgames.com requires browser-like UA
        self._session.headers['User-Agent'] = BROWSER_UA

    def fetch_by_gid(self, gid):
        """Fetch a single game by numeric game ID.

        Returns normalized game dict, or None if the game doesn't exist.
        """
        gid = int(gid)
        cache_file = os.path.join(self.cache_dir, f'chessgames_{gid}.pgn')

        # Check cache
        if os.path.exists(cache_file):
            self._log(f"Cache hit: chessgames_{gid}.pgn")
            with open(cache_file, 'r', encoding='utf-8') as f:
                pgn_text = f.read()
        else:
            url = CHESSGAMES_PGN_API.format(gid=gid)
            try:
                resp = self._api_get(url)
            except FetchError:
                self._log(f"Failed to fetch GID {gid}")
                return None

            if resp.status_code == 403:
                self._log(f"chessgames.com blocked request for GID {gid}. "
                          f"Try again later or download manually.")
                return None

            pgn_text = resp.text
            if not pgn_text.strip() or '[Event' not in pgn_text:
                self._log(f"GID {gid}: empty or invalid PGN response")
                return None

            # Cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(pgn_text)

        # Parse
        parsed = self._parse_single_game(pgn_text.strip())
        if parsed is None:
            return None

        self._normalize_game(parsed, 'chessgames', gid)
        h = parsed['headers']
        self._log(f"GID {gid}: {h.get('White', '?')} vs {h.get('Black', '?')} "
                  f"({h.get('Result', '?')})")
        return parsed

    def fetch_by_gids(self, gids, delay=None):
        """Fetch multiple games by GID with polite rate limiting.

        Args:
            gids: List of integer game IDs
            delay: Seconds between requests (default: CHESSGAMES_RATE_DELAY_S)

        Returns list of game dicts (skips failures).
        """
        delay = delay if delay is not None else CHESSGAMES_RATE_DELAY_S
        games = []
        for i, gid in enumerate(gids):
            game = self.fetch_by_gid(gid)
            if game is not None:
                games.append(game)
            if i < len(gids) - 1 and delay > 0:
                # Only delay between requests, not after cache hits
                cache_file = os.path.join(self.cache_dir,
                                          f'chessgames_{int(gids[i + 1])}.pgn')
                if not os.path.exists(cache_file):
                    time.sleep(delay)
        return games


# ═══════════════════════════════════════════════════════════════
# SOURCE 3: THE WEEK IN CHESS (TWIC)
# ═══════════════════════════════════════════════════════════════

class TWICSource(PGNSource):
    """Fetch tournament PGN bundles from The Week in Chess (TWIC).

    TWIC publishes PGN files for elite chess tournaments at
    theweekinchess.com/assets/files/pgn/{event}.pgn

    Usage:
        twic = TWICSource()
        events = twic.list_events()              # ~211 tournaments
        games = twic.fetch_event('tatamast26')    # Tata Steel Masters 2026
        matches = twic.search_events('candidates')
    """

    name = 'twic'

    def __init__(self, cache_dir=None, verbose=True):
        super().__init__(cache_dir=cache_dir, verbose=verbose)
        self._events_cache = None

    def list_events(self, force_refresh=False):
        """List available tournament event names from the TWIC index page.

        Returns list of event name strings (the filename without .pgn).
        Cached locally as _twic_events.json.
        """
        if self._events_cache is not None and not force_refresh:
            return self._events_cache

        events_cache_file = os.path.join(self.cache_dir, '_twic_events.json')
        cache_age_limit = 86400 * 7  # refresh weekly

        if (not force_refresh
                and os.path.exists(events_cache_file)
                and time.time() - os.path.getmtime(events_cache_file) < cache_age_limit):
            with open(events_cache_file, 'r') as f:
                self._events_cache = json.load(f)
            self._log(f"Loaded {len(self._events_cache)} events from cache")
            return self._events_cache

        # Scrape the TWIC index page for PGN links
        self._log("Fetching TWIC event listing...")
        try:
            resp = self._api_get(TWIC_INDEX_URL)
        except FetchError:
            # Fall back to cached list if available
            if os.path.exists(events_cache_file):
                self._log("TWIC index unreachable, using stale cache")
                with open(events_cache_file, 'r') as f:
                    self._events_cache = json.load(f)
                return self._events_cache
            raise

        # Extract event names from PGN links in the HTML
        # Pattern: assets/files/pgn/{event}.pgn or href=".../{event}.pgn"
        events = re.findall(
            r'assets/files/pgn/([a-zA-Z0-9_-]+)\.pgn',
            resp.text
        )
        # Deduplicate while preserving order
        seen = set()
        unique_events = []
        for e in events:
            if e not in seen:
                seen.add(e)
                unique_events.append(e)

        # Cache
        with open(events_cache_file, 'w') as f:
            json.dump(unique_events, f)

        self._events_cache = unique_events
        self._log(f"Found {len(unique_events)} events")
        return unique_events

    def search_events(self, query):
        """Search event names by substring (case-insensitive).

        Returns list of matching event name strings.
        """
        events = self.list_events()
        query_lower = query.lower()
        return [e for e in events if query_lower in e.lower()]

    def fetch_event(self, event, max_games=None, min_moves=None,
                    max_moves=None, result_filter=None):
        """Download and parse games from a TWIC tournament PGN.

        Args:
            event: Event name (e.g., 'tatamast26') — no .pgn extension
            max_games: Limit number of games returned
            min_moves, max_moves: Filter by move count
            result_filter: Filter by result string

        Returns list of normalized game dicts.
        """
        event = event.replace('.pgn', '')  # strip extension if provided
        cache_file = os.path.join(self.cache_dir, f'twic_{event}.pgn')

        # Check cache
        if os.path.exists(cache_file):
            self._log(f"Cache hit: twic_{event}.pgn")
            with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                pgn_text = f.read()
        else:
            url = TWIC_PGN_URL.format(event=event)
            try:
                resp = self._api_get(url, timeout=DOWNLOAD_TIMEOUT_S)
            except FetchError:
                self._log(f"Failed to download TWIC event '{event}'")
                return []

            if resp.status_code == 404:
                self._log(f"TWIC event '{event}' not found (404)")
                return []

            pgn_text = resp.text
            if not pgn_text.strip():
                self._log(f"TWIC event '{event}': empty PGN")
                return []

            # Cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(pgn_text)
            self._log(f"Downloaded {len(pgn_text) / 1e3:.1f} KB")

        # Parse games
        games = self.parse_games(pgn_text, max_games=max_games,
                                 min_moves=min_moves, max_moves=max_moves,
                                 result_filter=result_filter)

        # Normalize
        for g in games:
            self._normalize_game(g, 'twic', event)

        self._log(f"Event '{event}': {len(games)} games")
        return games

    def fetch_random_from_event(self, event, n=10, seed=None, **filters):
        """Fetch N random games from a TWIC event.

        Downloads the full event PGN, then randomly samples N games.
        """
        if seed is not None:
            random.seed(seed)

        all_games = self.fetch_event(event, **filters)
        if not all_games:
            return []

        random.shuffle(all_games)
        return all_games[:n]


# ═══════════════════════════════════════════════════════════════
# MULTI-SOURCE FACADE
# ═══════════════════════════════════════════════════════════════

class MultiFetcher:
    """Facade that holds all PGN sources and dispatches requests.

    Usage:
        multi = MultiFetcher()
        games = multi.fetch('chessgames', gids=[1011478])
        games = multi.fetch('twic', event='tatamast26', max_games=5)
        games = multi.fetch('hf', n=10, seed=42)
    """

    SOURCE_ALIASES = {
        'hf': 'huggingface',
        'fishtest': 'huggingface',
        'cg': 'chessgames',
        'chess': 'chessgames',
    }

    def __init__(self, cache_dir=None, verbose=True):
        self.cache_dir = cache_dir or CACHE_DIR
        self.verbose = verbose
        self._sources = {}

    def _get_source(self, name):
        """Lazy-init source by name."""
        name = self.SOURCE_ALIASES.get(name, name)
        if name not in self._sources:
            if name == 'huggingface':
                self._sources[name] = PGNFetcher(
                    cache_dir=self.cache_dir, verbose=self.verbose
                )
            elif name == 'chessgames':
                self._sources[name] = ChessGamesSource(
                    cache_dir=self.cache_dir, verbose=self.verbose
                )
            elif name == 'twic':
                self._sources[name] = TWICSource(
                    cache_dir=self.cache_dir, verbose=self.verbose
                )
            else:
                raise ValueError(f"Unknown source: {name!r}. "
                                 f"Available: huggingface, chessgames, twic")
        return self._sources[name]

    def fetch(self, source_name, **kwargs):
        """Dispatch fetch to the appropriate source.

        Args for 'huggingface': n, min_moves, max_moves, seed, tc_base_min, date
        Args for 'chessgames': gids (list of int), gid (single int)
        Args for 'twic': event (str), max_games, min_moves, max_moves
        """
        source = self._get_source(source_name)

        if isinstance(source, PGNFetcher):
            return source.fetch_random_games(
                n=kwargs.get('n', 20),
                min_moves=kwargs.get('min_moves', 30),
                max_moves=kwargs.get('max_moves', 100),
                tc_base_min=kwargs.get('tc_base_min', 10.0),
                date=kwargs.get('date'),
                seed=kwargs.get('seed'),
            )

        elif isinstance(source, ChessGamesSource):
            gids = kwargs.get('gids') or []
            gid = kwargs.get('gid')
            if gid is not None:
                gids = [gid] + [g for g in gids if g != gid]
            if not gids:
                raise ValueError("chessgames source requires --gid or gids=[]")
            return source.fetch_by_gids(gids, delay=kwargs.get('delay'))

        elif isinstance(source, TWICSource):
            event = kwargs.get('event')
            if not event:
                raise ValueError("twic source requires --event")
            return source.fetch_event(
                event,
                max_games=kwargs.get('max_games') or kwargs.get('n'),
                min_moves=kwargs.get('min_moves'),
                max_moves=kwargs.get('max_moves'),
                result_filter=kwargs.get('result_filter'),
            )

    def list_available(self, source_name):
        """List available items for a source."""
        source = self._get_source(source_name)
        if isinstance(source, PGNFetcher):
            return source.list_dates()
        elif isinstance(source, TWICSource):
            return source.list_events()
        else:
            return []

    def search(self, source_name, query):
        """Search within a source."""
        source = self._get_source(source_name)
        if isinstance(source, TWICSource):
            return source.search_events(query)
        elif isinstance(source, PGNFetcher):
            # Search dates by prefix
            dates = source.list_dates()
            return [d for d in dates if query in d]
        else:
            return []

    def cache_stats(self):
        """Cache stats from whichever source has been initialized."""
        # All sources share the same cache dir
        for s in self._sources.values():
            return s.cache_stats()
        # No source initialized yet — create a temporary one
        tmp = PGNSource.__new__(PGNSource)
        tmp.cache_dir = self.cache_dir
        return tmp.cache_stats()


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def _format_game_summary(game, index=None):
    """Format a single game as a one-line summary."""
    h = game.get('headers', {})
    prefix = f"  {index}. " if index is not None else "  "
    white = h.get('White', '?')
    black = h.get('Black', '?')
    result = h.get('Result', '?')
    event = h.get('Event', '')
    date = h.get('Date', '')
    n = game.get('n_moves', '?')
    elo_w = h.get('WhiteElo', '')
    elo_b = h.get('BlackElo', '')
    elo = f" ({elo_w}/{elo_b})" if elo_w and elo_b and elo_w != '?' else ""
    return f"{prefix}{white} vs {black} {result}{elo} — {n} moves [{event} {date}]"


def _output_games(games, args):
    """Output games in the requested format."""
    fmt = getattr(args, 'format', 'summary')
    output_file = getattr(args, 'output', None)

    if fmt == 'pgn':
        text = '\n\n'.join(g['pgn'] for g in games)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  Wrote {len(games)} games to {output_file}", file=sys.stderr)
        else:
            print(text)

    elif fmt == 'json':
        # Serialize as JSON array
        data = []
        for g in games:
            data.append({
                'headers': g['headers'],
                'moves': g['moves'],
                'n_moves': g['n_moves'],
                'source': g.get('source', ''),
                'source_id': g.get('source_id', ''),
            })
        text = json.dumps(data, indent=2)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  Wrote {len(games)} games to {output_file}", file=sys.stderr)
        else:
            print(text)

    elif fmt == 'ndjson':
        lines = []
        for g in games:
            lines.append(json.dumps({
                'headers': g['headers'],
                'moves': g['moves'],
                'n_moves': g['n_moves'],
                'source': g.get('source', ''),
                'source_id': g.get('source_id', ''),
            }))
        text = '\n'.join(lines) + '\n'
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  Wrote {len(games)} games to {output_file}", file=sys.stderr)
        else:
            print(text)

    else:
        # Default: human-readable summary
        for i, g in enumerate(games, 1):
            print(_format_game_summary(g, i))


def cmd_fetch(args, multi):
    """Handle the 'fetch' subcommand."""
    source = args.source

    if source in ('chessgames', 'cg', 'chess'):
        if not args.gid:
            print("Error: --gid required for chessgames source", file=sys.stderr)
            return
        games = multi.fetch('chessgames', gids=args.gid)

    elif source in ('twic',):
        if not args.event:
            print("Error: --event required for twic source", file=sys.stderr)
            return
        games = multi.fetch('twic', event=args.event,
                            n=args.n, max_games=args.n,
                            min_moves=args.min_moves,
                            max_moves=args.max_moves,
                            result_filter=args.result)

    elif source in ('hf', 'huggingface', 'fishtest'):
        games = multi.fetch('huggingface',
                            n=args.n,
                            min_moves=args.min_moves,
                            max_moves=args.max_moves,
                            seed=args.seed,
                            tc_base_min=args.tc_min or 10.0,
                            date=args.date)
    else:
        print(f"Error: unknown source '{source}'", file=sys.stderr)
        return

    if not games:
        print("  0 games matched. Try relaxing filters or a different source.",
              file=sys.stderr)
        return

    # Status to stderr so stdout can pipe cleanly (`--format pgn | pgn_bridge.py`).
    print(f"\n  Fetched {len(games)} games:", file=sys.stderr)
    _output_games(games, args)


def cmd_list(args, multi):
    """Handle the 'list' subcommand."""
    source = args.source
    items = multi.list_available(source)

    if not items:
        print(f"  No items found for source '{source}'")
        return

    print(f"\n  {len(items)} items from '{source}':\n")
    for item in items:
        print(f"    {item}")


def cmd_search(args, multi):
    """Handle the 'search' subcommand."""
    results = multi.search(args.source, args.query)

    if not results:
        print(f"  No results for '{args.query}' in '{args.source}'")
        return

    print(f"\n  {len(results)} matches for '{args.query}':\n")
    for item in results:
        print(f"    {item}")


def cmd_cache(args, multi):
    """Handle the 'cache' subcommand."""
    if args.cache_action == 'stats':
        stats = multi.cache_stats()
        print(f"\n  Cache: {stats.get('files', 0)} files, "
              f"{stats.get('size_mb', 0):.1f} MB")
        print(f"  Path: {stats.get('path', CACHE_DIR)}")
    elif args.cache_action == 'clear':
        # Initialize one source to get access to clear_cache
        source = multi._get_source('huggingface')
        source.clear_cache()
        print("  Cache cleared.")


def cmd_demo(args, multi):
    """Run the original HuggingFace demo."""
    print("=" * 70)
    print("  PGN Fetcher — HuggingFace fishtest_pgns Demo")
    print("=" * 70)

    fetcher = multi._get_source('huggingface')

    dates = fetcher.list_dates()
    print(f"\n  Dataset spans {dates[0]} to {dates[-1]} ({len(dates)} dates)")

    demo_date = '18-06-15'
    print(f"\n  Exploring date: {demo_date}")
    tests = fetcher.list_tests(demo_date)
    print(f"  Tests on {demo_date}: {len(tests)}")

    if tests:
        test_id = tests[0]
        print(f"\n  Fetching metadata for test {test_id}...")
        meta = fetcher.fetch_metadata(demo_date, test_id)
        tc = fetcher.get_tc_base(meta)
        total = fetcher.get_total_games(meta)
        is_green = meta.get('is_green', False)
        info = meta.get('args', {}).get('info', 'N/A')
        print(f"  TC: {tc}s | Games: {total} | Passed: {is_green}")
        print(f"  Info: {info}")

    print("\n  Fetching 5 random games (seed=42, TC>=10s, 30-80 moves)...")
    games = fetcher.fetch_random_games(n=5, seed=42, min_moves=30, max_moves=80)
    print(f"  Got {len(games)} games:\n")

    for i, g in enumerate(games):
        h = g['headers']
        print(f"  Game {i + 1}: {h.get('White', '?')} vs {h.get('Black', '?')}")
        print(f"    Result: {h.get('Result', '?')} | Moves: ~{g['n_moves']}"
              f" | TC: {g.get('source_tc', '?')}s")
        print(f"    Source: {g.get('source_date')}/{g.get('source_test')}")
        print(f"    Moves: {g['moves'][:80]}...")
        print()

    stats = fetcher.cache_stats()
    print(f"  Cache: {stats['files']} files, {stats['size_mb']:.1f} MB")
    print(f"  Path: {stats['path']}")

    print("\n" + "=" * 70)
    print("  Demo complete.")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ═══════════════════════════════════════════════════════════════

def interactive_mode():
    """Simple text-menu interactive mode for browsing PGN sources."""
    multi = MultiFetcher(verbose=True)

    print("=" * 60)
    print("  PGN Fetcher — Interactive Mode")
    print("  Three sources: HuggingFace, chessgames.com, TWIC")
    print("=" * 60)

    while True:
        print("\n  1. Browse HuggingFace fishtest")
        print("  2. Fetch from chessgames.com (by GID)")
        print("  3. Browse TWIC tournaments")
        print("  4. Search TWIC events")
        print("  5. Cache stats")
        print("  6. Exit")

        try:
            choice = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        if choice == '1':
            _interactive_hf(multi)
        elif choice == '2':
            _interactive_chessgames(multi)
        elif choice == '3':
            _interactive_twic_browse(multi)
        elif choice == '4':
            _interactive_twic_search(multi)
        elif choice == '5':
            stats = multi.cache_stats()
            print(f"\n  Cache: {stats.get('files', 0)} files, "
                  f"{stats.get('size_mb', 0):.1f} MB")
            print(f"  Path: {stats.get('path', CACHE_DIR)}")
        elif choice == '6':
            print("  Goodbye.")
            break
        else:
            print("  Invalid choice. Enter 1-6.")


def _interactive_hf(multi):
    """Interactive HuggingFace fishtest browser."""
    try:
        n = input("  How many games? [10]: ").strip() or '10'
        seed = input("  Random seed? [none]: ").strip() or None
        n = int(n)
        seed = int(seed) if seed else None
    except (ValueError, EOFError, KeyboardInterrupt):
        print("  Cancelled.")
        return

    print(f"\n  Fetching {n} random fishtest games...")
    try:
        games = multi.fetch('huggingface', n=n, seed=seed)
    except Exception as e:
        print(f"  Error: {e}")
        return

    print(f"  Got {len(games)} games:\n")
    for i, g in enumerate(games, 1):
        print(_format_game_summary(g, i))


def _interactive_chessgames(multi):
    """Interactive chessgames.com fetcher."""
    try:
        gid_str = input("  Enter GID(s) (comma-separated): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("  Cancelled.")
        return

    if not gid_str:
        print("  No GIDs entered.")
        return

    try:
        gids = [int(g.strip()) for g in gid_str.split(',')]
    except ValueError:
        print("  Invalid GID format. Use integers separated by commas.")
        return

    print(f"\n  Fetching {len(gids)} games from chessgames.com...")
    try:
        games = multi.fetch('chessgames', gids=gids)
    except Exception as e:
        print(f"  Error: {e}")
        return

    print(f"  Got {len(games)} games:\n")
    for i, g in enumerate(games, 1):
        print(_format_game_summary(g, i))
        # Show first 100 chars of moves
        print(f"      {g['moves'][:100]}...")


def _interactive_twic_browse(multi):
    """Interactive TWIC event browser."""
    print("\n  Loading TWIC events...")
    try:
        events = multi.list_available('twic')
    except Exception as e:
        print(f"  Error: {e}")
        return

    print(f"  {len(events)} events available. Showing first 20:\n")
    for i, ev in enumerate(events[:20], 1):
        print(f"    {i:3d}. {ev}")

    if len(events) > 20:
        print(f"    ... and {len(events) - 20} more (use 'search' to filter)")

    try:
        event = input("\n  Enter event name to fetch (or press Enter to cancel): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("  Cancelled.")
        return

    if not event:
        return

    try:
        n = input("  Max games? [all]: ").strip()
        max_games = int(n) if n else None
    except (ValueError, EOFError, KeyboardInterrupt):
        max_games = None

    print(f"\n  Fetching from TWIC event '{event}'...")
    try:
        games = multi.fetch('twic', event=event, max_games=max_games)
    except Exception as e:
        print(f"  Error: {e}")
        return

    print(f"  Got {len(games)} games:\n")
    for i, g in enumerate(games[:20], 1):
        print(_format_game_summary(g, i))
    if len(games) > 20:
        print(f"    ... and {len(games) - 20} more")


def _interactive_twic_search(multi):
    """Interactive TWIC event search."""
    try:
        query = input("  Search query: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("  Cancelled.")
        return

    if not query:
        return

    results = multi.search('twic', query)
    if not results:
        print(f"  No events matching '{query}'")
        return

    print(f"\n  {len(results)} matches:\n")
    for ev in results:
        print(f"    {ev}")


# ═══════════════════════════════════════════════════════════════
# MAIN / CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def build_parser():
    """Build the argparse parser."""
    parser = argparse.ArgumentParser(
        prog='pgn_fetcher',
        description='Multi-source chess PGN fetcher (HuggingFace, chessgames.com, TWIC)',
    )
    sub = parser.add_subparsers(dest='command')

    # ── fetch ──
    p_fetch = sub.add_parser('fetch', help='Fetch games from a source')
    p_fetch.add_argument('--source', '-s', default='hf',
                         choices=['hf', 'huggingface', 'fishtest',
                                  'chessgames', 'cg', 'chess', 'twic'],
                         help='Source (default: hf)')
    p_fetch.add_argument('--n', '-n', type=int, default=20,
                         help='Number of games (default: 20)')
    p_fetch.add_argument('--min-moves', type=int, default=None,
                         help='Minimum full moves')
    p_fetch.add_argument('--max-moves', type=int, default=None,
                         help='Maximum full moves')
    p_fetch.add_argument('--result', choices=['1-0', '0-1', '1/2-1/2'],
                         help='Filter by result')
    p_fetch.add_argument('--seed', type=int, help='Random seed')
    p_fetch.add_argument('--output', '-o', help='Output file path')
    p_fetch.add_argument('--format', '-f', default='summary',
                         choices=['summary', 'pgn', 'json', 'ndjson'],
                         help='Output format (default: summary)')
    # HuggingFace-specific
    p_fetch.add_argument('--date', help='HuggingFace date (YY-MM-DD)')
    p_fetch.add_argument('--tc-min', type=float,
                         help='Min time control in seconds (HF)')
    # chessgames.com-specific
    p_fetch.add_argument('--gid', type=int, nargs='+',
                         help='chessgames.com game ID(s)')
    # TWIC-specific
    p_fetch.add_argument('--event', help='TWIC event name')

    # ── list ──
    p_list = sub.add_parser('list', help='List available dates/events')
    p_list.add_argument('--source', '-s', default='twic',
                        choices=['hf', 'huggingface', 'twic'],
                        help='Source (default: twic)')

    # ── search ──
    p_search = sub.add_parser('search', help='Search for events/dates')
    p_search.add_argument('--source', '-s', default='twic',
                          choices=['hf', 'huggingface', 'twic'],
                          help='Source (default: twic)')
    p_search.add_argument('--query', '-q', required=True,
                          help='Search query')

    # ── cache ──
    p_cache = sub.add_parser('cache', help='Cache management')
    p_cache.add_argument('cache_action', choices=['stats', 'clear'],
                         help='Cache action')

    # ── demo ──
    sub.add_parser('demo', help='Run the original HuggingFace demo')

    # ── interactive ──
    sub.add_parser('interactive', help='Interactive browsing mode')

    return parser


def main():
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # No command → interactive mode
    if args.command is None:
        interactive_mode()
        return

    multi = MultiFetcher(verbose=True)

    if args.command == 'fetch':
        cmd_fetch(args, multi)
    elif args.command == 'list':
        cmd_list(args, multi)
    elif args.command == 'search':
        cmd_search(args, multi)
    elif args.command == 'cache':
        cmd_cache(args, multi)
    elif args.command == 'demo':
        cmd_demo(args, multi)
    elif args.command == 'interactive':
        interactive_mode()


if __name__ == '__main__':
    main()
