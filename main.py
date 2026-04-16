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


def _rand_evm_addr_mixed_case() -> str:
    h = secrets.token_hex(20)
    out = []
    for ch in h:
        if ch in "abcdef" and secrets.randbelow(2) == 0:
            out.append(ch.upper())
        else:
            out.append(ch)
    return "0x" + "".join(out)


def generate_constants() -> Dict[str, str]:
    addrs = _ensure_unique([_rand_evm_addr_mixed_case() for _ in range(10)])
    consts = {
        "ADDR_OWNER": addrs[0],
        "ADDR_GUARD": addrs[1],
        "ADDR_SINK": addrs[2],
        "ADDR_TOKEN0": addrs[3],
        "ADDR_TOKEN1": addrs[4],
        "ADDR_TOKEN2": addrs[5],
        "ADDR_TOKEN3": addrs[6],
        "ADDR_TOKEN4": addrs[7],
        "ADDR_TOKEN5": addrs[8],
        "ADDR_TOKEN6": addrs[9],
        "SALT_A": _rand_hex(16),
        "SALT_B": _rand_hex(20),
        "SALT_UI": _rand_hex(12),
        "HEX_TAG": _rand_hex(9),
    }
    _ensure_unique(list(consts.values()))
    return consts


def _pad_to(target_lines: int, lines: List[str], mk_line) -> List[str]:
    if len(lines) >= target_lines:
        return lines
    need = target_lines - len(lines)
    for i in range(need):
        lines.append(mk_line(i))
    return lines


def build_java_esq0x1(out_path: Path, target_lines: int, c: Dict[str, str]) -> None:
    # Single-file Java, intentionally "contract-like" (roles, immutable params, events, bounded math).
    errs = _ensure_unique([_rand_ident(9, 14) for _ in range(13)])
    evs = _ensure_unique([_rand_ident(8, 16) for _ in range(17)])

    j: List[str] = []
    j.extend(
        [
            "/*",
            f"  {secrets.choice(['Fruitasio relay', 'Poly-copy mesh', 'Citrus vault weave'])}",
            "  A contract-shaped Java artifact: roles, immutable parameters, event log, and bounded settlement.",
            "*/",
            "",
            "import java.nio.charset.StandardCharsets;",
            "import java.security.MessageDigest;",
            "import java.security.NoSuchAlgorithmException;",
            "import java.util.ArrayDeque;",
            "import java.util.ArrayList;",
            "import java.util.Collections;",
            "import java.util.Deque;",
            "import java.util.HashMap;",
            "import java.util.List;",
            "import java.util.Map;",
            "import java.util.SplittableRandom;",
            "",
            "public final class ESQ0x1 {",
            f"  public static final String IMM_OWNER = \"{c['ADDR_OWNER']}\";",
            f"  public static final String IMM_GUARD = \"{c['ADDR_GUARD']}\";",
            f"  public static final String IMM_SINK  = \"{c['ADDR_SINK']}\";",
