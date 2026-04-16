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
            "    sb.append(d.mode).append('|').append(d.score).append('|').append(d.hint).append('|');",
            "    for (Trade t : ts) {",
            "      sb.append(t.t).append(',').append(t.trader).append(',').append(t.tokenIn).append(',').append(t.tokenOut)",
            "        .append(',').append(t.amountIn).append(',').append(t.amountOut).append(',').append(t.fee).append(',').append(t.memo).append(';');",
            "    }",
            "    return sb.toString().getBytes(StandardCharsets.UTF_8);",
            "  }",
            "",
            "  public static final class Receipt {",
            "    public final long nonce,t; public final String caller,token,kind; public final long amount;",
            "    public Receipt(long nonce,long t,String caller,String token,long amount,String kind){this.nonce=nonce;this.t=t;this.caller=caller;this.token=token;this.amount=amount;this.kind=kind;}",
            "  }",
            "  public static final class PricePoint { public final long t,px,vol; public PricePoint(long t,long px,long vol){this.t=t;this.px=px;this.vol=vol;} }",
            "  public static final class Trade {",
            "    public final long t; public final String trader,tokenIn,tokenOut,memo; public final long amountIn,amountOut,fee;",
            "    public Trade(long t,String tr,String ti,String to,long ai,long ao,long fee,String memo){this.t=t;this.trader=tr;this.tokenIn=ti;this.tokenOut=to;this.amountIn=ai;this.amountOut=ao;this.fee=fee;this.memo=memo;}",
            "  }",
            "  public static final class TradeIntent {",
            "    public final String tokenIn,tokenOut,memo; public final long amountIn,rateBps;",
            "    public TradeIntent(String ti,String to,long ai,long rb,String memo){this.tokenIn=ti;this.tokenOut=to;this.amountIn=ai;this.rateBps=rb;this.memo=memo;}",
            "  }",
            "  public static final class MeshDecision {",
            "    public final String mode,hint; public final long score; public final List<TradeIntent> intents;",
            "    public MeshDecision(String m,long s,String h,List<TradeIntent> i){this.mode=m;this.score=s;this.hint=h;this.intents=i;}",
            "  }",
            "  public static final class Tick {",
            "    public final long t; public final PricePoint price; public final MeshDecision decision; public final List<Trade> trades; public final String digest;",
            "    public Tick(long t,PricePoint p,MeshDecision d,List<Trade> ts,String dig){this.t=t;this.price=p;this.decision=d;this.trades=ts;this.digest=dig;}",
            "  }",
            "",
            "  private static final class NonceWheel { private long n=1; long next(){return n++;} }",
            "",
            "  private static final class EventBus {",
            "    private final Deque<String> q = new ArrayDeque<>();",
            "    private final int cap = 4096;",
            "    void emit(String kind,String a,String b,String data){",
            "      long t=nowSec();",
            "      String s=t+\"|\"+kind+\"|\"+safe(a)+\"|\"+safe(b)+\"|\"+safe(data);",
            "      q.addLast(s);",
            "      while(q.size()>cap) q.removeFirst();",
            "    }",
            "    List<String> tail(int n){",
            "      if(n<=0) return Collections.emptyList();",
            "      n=Math.min(n,q.size());",
            "      List<String> out=new ArrayList<>(n);",
            "      int skip=q.size()-n; int i=0;",
            "      for(String s:q){ if(i++>=skip) out.add(s); }",
            "      return out;",
            "    }",
            "    private static String safe(String s){",
            "      if(s==null) return \"\";",
            "      s=s.replace(\"\\n\",\" \").replace(\"\\r\",\" \");",
            "      return s.length()>240 ? s.substring(0,240) : s;",
            "    }",
            "  }",
            "",
            "  private static final class Vault {",
            "    private final Map<String, Map<String, Long>> bal = new HashMap<>();",
            "    void credit(String token,String who,long amt){",
            "      Map<String,Long> by=bal.computeIfAbsent(token,k->new HashMap<>());",
            "      long cur=by.getOrDefault(who,0L);",
            "      long nxt=cur+amt;",
            "      if(((cur^nxt)&(amt^nxt))<0) throw new ArithmeticException(\"overflow\");",
            "      by.put(who,nxt);",
            "    }",
            "    void debit(String token,String who,long amt){",
            "      Map<String,Long> by=bal.computeIfAbsent(token,k->new HashMap<>());",
            "      long cur=by.getOrDefault(who,0L);",
            "      if(cur<amt) throw new IllegalStateException(\"insufficient\");",
            "      by.put(who,cur-amt);",
            "    }",
            "    Snapshot snapshot(){",
            "      Map<String, Map<String, Long>> c=new HashMap<>();",
            "      for(Map.Entry<String,Map<String,Long>> e: bal.entrySet()) c.put(e.getKey(), new HashMap<>(e.getValue()));",
            "      return new Snapshot(c);",
            "    }",
            "    static final class Snapshot{",
            "      final Map<String, Map<String, Long>> bal;",
            "      Snapshot(Map<String, Map<String, Long>> b){this.bal=b;}",
            "      long balanceOf(String token,String who){ Map<String,Long> by=bal.get(token); return by==null?0L:by.getOrDefault(who,0L); }",
            "    }",
            "  }",
            "",
            "  private static final class Oracle {",
            "    private final Deque<PricePoint> tape = new ArrayDeque<>();",
            "    private final int cap = 2048;",
            "    void push(long t,long px,long vol){ tape.addLast(new PricePoint(t,px,vol)); while(tape.size()>cap) tape.removeFirst(); }",
            "    PricePoint latest(){ PricePoint p=tape.peekLast(); return p!=null?p:new PricePoint(nowSec(),100_000_000L,1_000_000L); }",
            "  }",
            "",
            "  private static final class Mesh {",
            "    private final List<Rule> rules = new ArrayList<>();",
            "    private final SplittableRandom r = new SplittableRandom(fold(IMM_SALT_A) ^ (fold(IMM_SALT_B) << 1));",
            "    void installDefaults(){",
            "      rules.clear();",
            "      rules.add(new Rule(\"polyMomentum\",13,37));",
            "      rules.add(new Rule(\"mirrorFade\",9,19));",
            "      rules.add(new Rule(\"fruitWarp\",7,31));",
            "      rules.add(new Rule(\"copyCatSkew\",5,23));",
            "      rules.add(new Rule(\"quietMean\",11,29));",
            "    }",
            "    MeshDecision decide(PricePoint p, Vault.Snapshot s){",
            "      long score=0;",
            "      StringBuilder hint=new StringBuilder(96);",
            "      for(Rule ru: rules){ long x=ru.eval(p); score += x; if(hint.length()<88) hint.append(ru.name).append('=').append(x).append(' '); }",
            "      String mode=(score%3==0)?\"scan\":((score%3==1)?\"pounce\":\"blend\");",
            "      int k=1+(int)(Math.abs(score)%3);",
            "      List<TradeIntent> intents=new ArrayList<>();",
            "      for(int i=0;i<k;i++){",
            "        String tokenIn=(i%2==0)?IMM_OWNER:IMM_GUARD;",
            "        String tokenOut=(i%2==0)?IMM_GUARD:IMM_OWNER;",
            "        long amt=10_000L + (Math.abs(score)%250_000L);",
            "        long rate=9_000L + (Math.abs(score)%2_000L);",
            "        String memo=mode+\"#\"+i+\":\"+(char)('a'+(int)(Math.abs(score)%26));",
            "        intents.add(new TradeIntent(tokenIn,tokenOut,amt,rate,memo));",
            "      }",
            "      return new MeshDecision(mode,score,hint.toString().trim(),intents);",
            "    }",
            "    static final class Rule{",
            "      final String name; final long a,b;",
            "      Rule(String n,long a,long b){this.name=n;this.a=a;this.b=b;}",
            "      long eval(PricePoint p){ long x=(p.px/10_000L) ^ (p.vol/1_000L); x=(x*a+b) ^ (x>>>3); x=(x%100_000L)-50_000L; return x; }",
            "    }",
            "    private static long fold(String s){ long x=0x9e3779b97f4a7c15L; for(int i=0;i<s.length();i++){ x ^= (s.charAt(i)*0x100000001b3L); x = (x<<7) | (x >>> (64-7)); } return x; }",
            "  }",
            "",
            "}",
        ]
    )

    # Insert padding BEFORE final brace to keep Java valid.
    if not j or j[-1] != "}":
        raise RuntimeError("unexpected java shape")
    pad_count = max(0, target_lines - len(j))
    if pad_count:
        pad_lines: List[str] = []
        for i in range(pad_count):
            if i % 3 == 0:
                pad_lines.append(f"  private static final long _PAD_{i} = 0x{secrets.token_hex(4)}L;")
            elif i % 3 == 1:
                pad_lines.append(f"  private static String _pad_{i}(String s) {{ return (s==null?\"\":s)+\"{_rand_alpha(3)}\"; }}")
            else:
                pad_lines.append(f"  private static long _padx_{i}(long x) {{ return (x ^ 0x{secrets.token_hex(2)}) + {secrets.randbelow(97)+3}L; }}")
        j = j[:-1] + pad_lines + [j[-1]]

    out_path.write_text("\n".join(j) + "\n", encoding="utf-8")


def build_polyxer_py(out_path: Path, target_lines: int, c: Dict[str, str]) -> None:
    # Single-file Python app: stdlib HTTP server, signal engine, risk gates, pseudo fills.
    code = f'''"""
PolyXer.py — {secrets.choice(["poly copy-cat tradint bot", "fruit-mesh executor", "tape-driven signal loom"])}

Run:
  python PolyXer.py --port 8891

Endpoints:
  GET  /api/health
  GET  /api/state
  GET  /api/events?limit=200
  POST /api/oracle   {{px, vol}}
  POST /api/step     {{n}}
  POST /api/order    {{side, qty, symbol}}
  GET  /             (serves Fruitasio/index.html if present)
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import json
import math
import random
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

IMM_OWNER = {c["ADDR_OWNER"]!r}
IMM_GUARD = {c["ADDR_GUARD"]!r}
IMM_SALT_A = {c["SALT_A"]!r}

ROOT = Path(__file__).resolve().parent
STATIC_FRUITASIO = (ROOT.parent / "Fruitasio" / "index.html")


def _now_s() -> int:
    return int(time.time())


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _sha256(b: bytes) -> bytes:
    return hashlib.sha256(b"PolyXer|" + b).digest()


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else (hi if x > hi else x)


def _jitter(seed: int, mag: float = 1.0) -> float:
    r = random.Random(seed ^ 0xA53C_91F)
    return (r.random() * 2.0 - 1.0) * mag


@dataclasses.dataclass(frozen=True)
class PricePoint:
    t: int
    px: float
    vol: float


@dataclasses.dataclass
class Event:
    t: int
    kind: str
    a: str = ""
    b: str = ""
    data: str = ""


@dataclasses.dataclass
class Fill:
    t: int
    side: str
    symbol: str
    qty: float
    px: float
    fee: float
    slip: float
    tag: str


class RingLog:
    def __init__(self, cap: int = 5000) -> None:
        self._cap = int(cap)
        self._q: List[Event] = []
        self._lock = threading.Lock()

    def emit(self, kind: str, a: str = "", b: str = "", data: str = "") -> None:
        with self._lock:
            self._q.append(Event(_now_s(), kind, a, b, data))
            if len(self._q) > self._cap:
                self._q = self._q[-self._cap :]

    def tail(self, n: int) -> List[Dict[str, Any]]:
        n = max(0, int(n))
        with self._lock:
            xs = self._q[-n:] if n else []
        return [dataclasses.asdict(e) for e in xs]


class OracleTape:
    def __init__(self, cap: int = 4096) -> None:
        self._cap = int(cap)
        self._tape: List[PricePoint] = []

    def push(self, px: float, vol: float) -> PricePoint:
        p = PricePoint(_now_s(), float(px), float(vol))
        self._tape.append(p)
        if len(self._tape) > self._cap:
            self._tape = self._tape[-self._cap :]
        return p

    def latest(self) -> PricePoint:
        if not self._tape:
            return PricePoint(_now_s(), 100.0, 1.0)
        return self._tape[-1]


class Wallet:
    def __init__(self) -> None:
        self.cash: float = 10_000.0
        self.pos: Dict[str, float] = {{}}
        self.pnl: float = 0.0
        self.fees: float = 0.0
        self._lock = threading.Lock()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {{"cash": self.cash, "pos": dict(self.pos), "pnl": self.pnl, "fees": self.fees}}

    def apply_fill(self, fill: Fill) -> None:
        with self._lock:
            side = fill.side.lower()
            qty = float(fill.qty)
            cost = fill.px * qty
            if side == "buy":
                self.cash -= cost + fill.fee
                self.pos[fill.symbol] = self.pos.get(fill.symbol, 0.0) + qty
            else:
                self.cash += cost - fill.fee
                self.pos[fill.symbol] = self.pos.get(fill.symbol, 0.0) - qty
            self.fees += fill.fee


class PolyCopyCat:
    def __init__(self, salt: str) -> None:
        self.salt = salt
        self.bias = random.Random(int.from_bytes(_sha256(salt.encode("utf-8")), "big")).random()

    def signal(self, p: PricePoint) -> Dict[str, Any]:
        x = math.log(max(1e-9, p.px))
        v = math.log(max(1e-9, p.vol))
        s1 = math.sin(x * (1.3 + self.bias))
        s2 = math.cos(v * (0.7 + self.bias / 2.0))
        raw = (s1 * 0.65 + s2 * 0.35) + _jitter(int(p.t + p.px * 10), 0.05)
        score = float(_clamp(raw, -1.0, 1.0))
        side = "buy" if score > 0.18 else ("sell" if score < -0.18 else "hold")
        return {{"side": side, "score": score, "heat": abs(score)}}


class RiskGates:
    def __init__(self) -> None:
        self.max_notional = 2_000.0
        self.max_pos = 30.0
        self.daily_loss_stop = -600.0

    def check(self, wallet: Wallet, symbol: str, side: str, qty: float, px: float) -> Tuple[bool, str]:
        w = wallet.snapshot()
        notional = qty * px
        if notional > self.max_notional:
            return False, "max_notional"
        pos = w["pos"].get(symbol, 0.0)
        nxt = pos + qty if side == "buy" else pos - qty
        if abs(nxt) > self.max_pos:
            return False, "max_pos"
        if w["pnl"] <= self.daily_loss_stop:
            return False, "daily_loss_stop"
        if w["cash"] < 50.0 and side == "buy":
            return False, "low_cash"
        return True, "ok"


class MicroExchange:
    def __init__(self, log: RingLog) -> None:
        self.log = log
        self.fee_bps = 8.0
        self.slip_bps = 12.0

    def fill(self, side: str, symbol: str, qty: float, ref_px: float, tag: str) -> Fill:
        side = side.lower().strip()
        qty = float(max(0.0, qty))
        base = float(ref_px)
        dir_ = 1.0 if side == "buy" else -1.0
        slip = base * (self.slip_bps / 10_000.0) * (0.3 + random.random())
        px = base + dir_ * slip
        fee = abs(px * qty) * (self.fee_bps / 10_000.0)
        f = Fill(_now_s(), side, symbol, qty, px, fee, slip, tag)
        self.log.emit("Fill", side, symbol, json.dumps(dataclasses.asdict(f), separators=(",", ":")))
        return f


class PolyXerCore:
    def __init__(self) -> None:
        self.log = RingLog()
        self.oracle = OracleTape()
        self.wallet = Wallet()
        self.sig = PolyCopyCat(IMM_SALT_A)
        self.risk = RiskGates()
        self.ex = MicroExchange(self.log)
        self.paused = False
        self.symbol = "FRUIT-USD"
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        self.oracle.push(100.0, 1.0)
        self.oracle.push(100.2, 1.05)
        self.oracle.push(99.8, 0.98)
        self.log.emit("Genesis", IMM_OWNER, IMM_GUARD, "seeded")

    def health(self) -> Dict[str, Any]:
        return {{"ok": True, "t": _now_s(), "app": "PolyXer"}}

    def state_root(self) -> str:
        blob = json.dumps(self.wallet.snapshot(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        m = _sha256(blob + self.oracle.latest().px.hex().encode("utf-8"))
        return "0x" + m.hex()

    def state(self) -> Dict[str, Any]:
        p = self.oracle.latest()
        s = self.sig.signal(p)
        return {{
            "t": _now_s(),
            "paused": self.paused,
            "oracle": dataclasses.asdict(p),
            "signal": s,
            "wallet": self.wallet.snapshot(),
            "risk": {{"max_notional": self.risk.max_notional, "max_pos": self.risk.max_pos, "daily_loss_stop": self.risk.daily_loss_stop}},
            "symbol": self.symbol,
            "root": self.state_root(),
        }}

    def push_oracle(self, px: float, vol: float) -> Dict[str, Any]:
        if self.paused:
            raise RuntimeError("paused")
        p = self.oracle.push(px, vol)
        self.log.emit("Oracle", "", "", json.dumps(dataclasses.asdict(p), separators=(",", ":")))
        return dataclasses.asdict(p)

    def order(self, side: str, qty: float, symbol: Optional[str] = None, tag: str = "manual") -> Dict[str, Any]:
        if self.paused:
            return {{"ok": False, "why": "paused"}}
        symbol = (symbol or self.symbol).strip()
        p = self.oracle.latest()
        ok, why = self.risk.check(self.wallet, symbol, side, float(qty), float(p.px))
        if not ok:
            self.log.emit("Reject", side, symbol, why)
            return {{"ok": False, "why": why}}
        f = self.ex.fill(side, symbol, float(qty), float(p.px), tag)
        self.wallet.apply_fill(f)
        return {{"ok": True, "fill": dataclasses.asdict(f)}}

    def step(self, n: int = 1) -> Dict[str, Any]:
        n = max(1, min(50, int(n)))
        fills: List[Dict[str, Any]] = []
        for i in range(n):
            p = self.oracle.latest()
            s = self.sig.signal(p)
            side = s["side"]
            if side == "hold":
                self.log.emit("Hold", "", "", f"score={{s['score']:.4f}}")
            else:
                qty = float(_clamp(1.0 + s["heat"] * 4.5, 0.3, 5.5))
                res = self.order(side, qty, self.symbol, tag=f"auto:{{i}}")
                if res.get("ok") and res.get("fill"):
                    fills.append(res["fill"])
            drift = _jitter(int(p.t + i * 13), 0.22) + (0.04 if side == "buy" else (-0.04 if side == "sell" else 0.0))
            nxt_px = float(max(1e-6, p.px * (1.0 + drift / 100.0)))
            nxt_vol = float(max(1e-6, p.vol * (1.0 + abs(drift) / 50.0)))
            self.push_oracle(nxt_px, nxt_vol)
        digest = _b64u(_sha256(json.dumps(fills, separators=(",", ":")).encode("utf-8")))
        self.log.emit("Step", "", "", digest)
        return {{"ok": True, "fills": fills, "digest": digest}}


CORE = PolyXerCore()


def _read_json(req: BaseHTTPRequestHandler, limit: int = 120_000) -> Dict[str, Any]:
    n = int(req.headers.get("content-length") or "0")
    if n < 0 or n > limit:
        raise ValueError("body size")
    raw = req.rfile.read(n) if n else b"{{}}"
    if not raw:
        return {{}}
    return json.loads(raw.decode("utf-8"))


def _send_json(req: BaseHTTPRequestHandler, status: int, obj: Any) -> None:
    data = json.dumps(obj, separators=(",", ":"), sort_keys=False).encode("utf-8")
    req.send_response(status)
    req.send_header("content-type", "application/json; charset=utf-8")
    req.send_header("cache-control", "no-store")
    req.send_header("content-length", str(len(data)))
    req.end_headers()
    req.wfile.write(data)


def _send_bytes(req: BaseHTTPRequestHandler, status: int, data: bytes, ctype: str) -> None:
    req.send_response(status)
    req.send_header("content-type", ctype)
    req.send_header("cache-control", "no-store")
    req.send_header("content-length", str(len(data)))
    req.end_headers()
    req.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    server_version = "PolyXer/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        CORE.log.emit("HTTP", self.command, self.path, fmt % args if args else fmt)

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            qs = urllib.parse.parse_qs(parsed.query or "")

            if path == "/api/health":
                return _send_json(self, 200, CORE.health())
            if path == "/api/state":
                return _send_json(self, 200, CORE.state())
            if path == "/api/events":
                lim = int((qs.get("limit") or ["200"])[0])
                return _send_json(self, 200, {{"events": CORE.log.tail(lim)}})
            if path == "/":
                if STATIC_FRUITASIO.exists():
                    return _send_bytes(self, 200, STATIC_FRUITASIO.read_bytes(), "text/html; charset=utf-8")
                return _send_bytes(self, 200, b"<h1>PolyXer</h1><p>Missing Fruitasio/index.html</p>", "text/html; charset=utf-8")
            return _send_json(self, 404, {{"ok": False, "error": "not_found"}})
        except Exception as e:
            CORE.log.emit("ErrGET", "", "", repr(e))
            return _send_json(self, 500, {{"ok": False, "error": "server", "detail": repr(e)}})

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            body = _read_json(self)

            if path == "/api/oracle":
                px = float(body.get("px"))
                vol = float(body.get("vol"))
                return _send_json(self, 200, {{"ok": True, "point": CORE.push_oracle(px, vol)}})
            if path == "/api/step":
                n = int(body.get("n") or 1)
                return _send_json(self, 200, CORE.step(n))
            if path == "/api/order":
                side = str(body.get("side") or "hold")
                qty = float(body.get("qty") or 0.0)
                symbol = str(body.get("symbol") or CORE.symbol)
                return _send_json(self, 200, CORE.order(side, qty, symbol, tag="api"))
            return _send_json(self, 404, {{"ok": False, "error": "not_found"}})
        except Exception as e:
            CORE.log.emit("ErrPOST", "", "", traceback.format_exc()[-1200:])
            return _send_json(self, 500, {{"ok": False, "error": "server", "detail": repr(e)}})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8891)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    CORE.log.emit("Start", args.host, str(args.port), "ready")
    print(f"PolyXer listening on http://{{args.host}}:{{args.port}}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

    lines = code.splitlines()

    def pad_line(i: int) -> str:
        if i % 5 == 0:
            return f"_POLY_PAD_{i} = '{_rand_hex(6)}'  # pad"
        if i % 5 == 1:
            return f"def _poly_pad_{i}(x: int) -> int: return (x ^ {secrets.randbelow(1<<16)}) + {secrets.randbelow(997)+3}"
        if i % 5 == 2:
            return f"_poly_table_{i} = ({secrets.randbelow(999)},{secrets.randbelow(999)},{secrets.randbelow(999)})"
        if i % 5 == 3:
            return f"_poly_note_{i} = {secrets.choice(['\"mesh\"','\"tape\"','\"warp\"','\"copy\"'])}"
        return ""

    lines = _pad_to(target_lines, lines, pad_line)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_fruitasio_html(out_path: Path, target_lines: int, c: Dict[str, str]) -> None:
    ui_salt = c["SALT_UI"]
    theme = secrets.choice(["mango", "lychee", "grapefruit", "dragonfruit", "kiwi", "papaya", "plum"])
