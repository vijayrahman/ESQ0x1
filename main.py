#!/usr/bin/env python3
"""
fruit-salt windlass / ESQ0x1 bundle builder
------------------------------------------
Generates three artifacts with fresh randomized identifiers each run:
  - ESQ0x1/ESQ0x1.java      (EVM-flavored, contract-like single Java file)
  - PolyXer/PolyXer.py      (local trading-bot style app + API server)
  - Fruitasio/index.html    (web UI that talks to PolyXer)

Run:
  python build_esq0x1_bundle.py

Notes:
  - This script guarantees uniqueness of generated addresses/hex constants
    *within this build run* (it cannot prove global uniqueness across the world).
  - No placeholders: all constructor-like addresses/hex salts are auto-generated.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import secrets
import string
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parent


def _ensure_unique(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        if x in seen:
            raise RuntimeError("duplicate generated constant within this run")
        seen.add(x)
        out.append(x)
    return out


def _pick_range(lo: int, hi: int) -> int:
    if lo >= hi:
        return lo
    r = secrets.randbelow(100)
    if r < 12:
        return hi
    if r < 42:
        mid = (lo + hi) // 2
        wig = max(2, (hi - lo) // 5)
        return min(hi, max(lo, mid + secrets.randbelow(wig) - wig // 2))
    return lo + secrets.randbelow(hi - lo + 1)


def _rand_hex(n_bytes: int) -> str:
    return "0x" + secrets.token_hex(n_bytes)


def _rand_ident(min_len: int = 7, max_len: int = 16) -> str:
    first = secrets.choice(string.ascii_letters)
    n = min_len + secrets.randbelow(max_len - min_len + 1) - 1
    tail = string.ascii_letters + string.digits + "_"
    return first + "".join(secrets.choice(tail) for _ in range(n))


def _rand_alpha(n: int) -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(n))


