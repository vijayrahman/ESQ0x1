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
            f"  public static final String IMM_SALT_A = \"{c['SALT_A']}\";",
            f"  public static final String IMM_SALT_B = \"{c['SALT_B']}\";",
            f"  public static final String IMM_TAG = \"{c['HEX_TAG']}\";",
            f"  public static final long IMM_GENESIS_EPOCH = {int(_dt.datetime.now().timestamp())}L;",
            "",
            "  // custom errors",
        ]
    )

    for e in errs:
        j.extend([f"  public static final class {e} extends RuntimeException {{", f"    public {e}(String m) {{ super(m); }}", "  }", ""])

    j.append("  // events")
    for ev in evs:
        j.extend(
            [
                f"  public static final class {ev} {{",
                "    public final long t; public final String a; public final String b; public final String data;",
                f"    public {ev}(long t, String a, String b, String data) {{ this.t=t; this.a=a; this.b=b; this.data=data; }}",
                "  }",
                "",
            ]
        )

    j.extend(
        [
            "  private final EventBus bus = new EventBus();",
            "  private final Vault vault = new Vault();",
            "  private final Oracle oracle = new Oracle();",
            "  private final Mesh mesh = new Mesh();",
            "  private final NonceWheel nonces = new NonceWheel();",
            "  private volatile boolean paused = false;",
            "  private volatile long lastTickMs = System.currentTimeMillis();",
            "",
            "  public ESQ0x1() {",
            "    // seeded defaults so there is nothing you must fill in",
            "    oracle.push(nowSec(), 100_000_000L, 1_000_000L);",
            "    oracle.push(nowSec(), 100_160_000L, 1_000_800L);",
            "    mesh.installDefaults();",
            "    bus.emit(\"Init\", IMM_OWNER, IMM_GUARD, IMM_TAG);",
            "  }",
            "",
            "  public synchronized void pause(String caller) {",
            f"    if (!eqAddr(caller, IMM_GUARD) && !eqAddr(caller, IMM_OWNER)) throw new {errs[0]}(\"auth\");",
            "    paused = true;",
            "    bus.emit(\"Paused\", caller, \"\", \"1\");",
            "  }",
            "",
            "  public synchronized void unpause(String caller) {",
            f"    if (!eqAddr(caller, IMM_OWNER)) throw new {errs[1]}(\"owner\");",
            "    paused = false;",
            "    bus.emit(\"Unpaused\", caller, \"\", \"0\");",
            "  }",
            "",
            "  public synchronized Receipt deposit(String caller, String token, long amount) {",
            "    live(); requireAddr(caller); requireAddr(token);",
            f"    if (amount <= 0) throw new {errs[2]}(\"amount\");",
            "    vault.credit(token, caller, amount);",
            "    bus.emit(\"Deposit\", caller, token, Long.toString(amount));",
            "    return new Receipt(nonces.next(), nowSec(), caller, token, amount, \"deposit\");",
            "  }",
            "",
            "  public synchronized Receipt withdraw(String caller, String token, long amount) {",
            "    live(); requireAddr(caller); requireAddr(token);",
            f"    if (amount <= 0) throw new {errs[3]}(\"amount\");",
            "    vault.debit(token, caller, amount);",
            "    bus.emit(\"Withdraw\", caller, token, Long.toString(amount));",
            "    return new Receipt(nonces.next(), nowSec(), caller, token, amount, \"withdraw\");",
            "  }",
            "",
            "  public synchronized Tick tick(String caller) {",
            "    live(); requireAddr(caller);",
            "    long now = System.currentTimeMillis();",
            f"    if (now - lastTickMs < 150) throw new {errs[4]}(\"throttle\");",
            "    lastTickMs = now;",
            "    PricePoint p = oracle.latest();",
            "    MeshDecision d = mesh.decide(p, vault.snapshot());",
            "    List<Trade> ts = new ArrayList<>();",
            "    for (TradeIntent ti : d.intents) ts.add(settle(caller, ti));",
            "    String digest = digestBase64(encodeTick(p, d, ts));",
            "    bus.emit(\"Tick\", caller, \"\", digest);",
            "    return new Tick(nowSec(), p, d, ts, digest);",
            "  }",
            "",
            "  public synchronized void pushOracle(String caller, long px, long vol) {",
            "    live();",
            f"    if (!eqAddr(caller, IMM_GUARD) && !eqAddr(caller, IMM_OWNER)) throw new {errs[5]}(\"oracle\");",
            f"    if (px <= 0 || vol <= 0) throw new {errs[6]}(\"oracle\");",
            "    oracle.push(nowSec(), px, vol);",
            "    bus.emit(\"OraclePush\", caller, \"\", px + \":\" + vol);",
            "  }",
            "",
            "  public synchronized List<String> tailEvents(int n) { return bus.tail(n); }",
            "",
            "  private Trade settle(String caller, TradeIntent ti) {",
            "    long inAmt = clamp(ti.amountIn, 1L, 1_000_000_000L);",
            "    long fee = Math.max(1L, inAmt / 777L);",
            "    long outAmt = Math.max(1L, (inAmt - fee) * ti.rateBps / 10_000L);",
            "    vault.debit(ti.tokenIn, caller, inAmt);",
            "    vault.credit(ti.tokenOut, caller, outAmt);",
            "    vault.credit(ti.tokenIn, IMM_SINK, fee);",
            "    Trade t = new Trade(nowSec(), caller, ti.tokenIn, ti.tokenOut, inAmt, outAmt, fee, ti.memo);",
            "    bus.emit(\"Trade\", caller, ti.tokenIn, ti.tokenOut + \":\" + inAmt + \":\" + outAmt);",
            "    return t;",
            "  }",
            "",
            "  private void live() {",
            f"    if (paused) throw new {errs[7]}(\"paused\");",
            "  }",
            "",
            "  private static long nowSec() { return System.currentTimeMillis() / 1000L; }",
            "",
            "  private static boolean eqAddr(String x, String y) { return x != null && y != null && x.equalsIgnoreCase(y); }",
            "",
            "  private static void requireAddr(String a) {",
            "    if (a == null || !a.startsWith(\"0x\") || a.length() != 42) throw new IllegalArgumentException(\"addr\");",
            "    for (int i = 2; i < a.length(); i++) {",
            "      char c = a.charAt(i);",
            "      boolean ok = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');",
            "      if (!ok) throw new IllegalArgumentException(\"addr\");",
            "    }",
            "  }",
            "",
            "  private static long clamp(long x, long lo, long hi) { return x < lo ? lo : (x > hi ? hi : x); }",
            "",
            "  private static byte[] sha256(byte[] in) {",
            "    try {",
            "      MessageDigest md = MessageDigest.getInstance(\"SHA-256\");",
            "      md.update(\"ESQ0x1|\".getBytes(StandardCharsets.UTF_8));",
            "      return md.digest(in);",
            "    } catch (NoSuchAlgorithmException e) {",
            "      throw new RuntimeException(e);",
            "    }",
            "  }",
            "",
            "  private static String digestBase64(byte[] blob) {",
            "    return java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(sha256(blob));",
            "  }",
            "",
            "  private static byte[] encodeTick(PricePoint p, MeshDecision d, List<Trade> ts) {",
            "    StringBuilder sb = new StringBuilder(512);",
            "    sb.append(p.t).append('|').append(p.px).append('|').append(p.vol).append('|');",
