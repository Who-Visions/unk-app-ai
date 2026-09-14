"""Unk pick ledger: StatSalt-style transparent capper record, graded like a sharp.

Every pick is logged before the game with the de-vigged fair price, its edge and a
Kelly stake; at the final it is graded and scored for closing line value (CLV),
the number that actually predicts long-term profit.

CLI:
  python pick_ledger.py add --capper Unk --sport nfl --event 401872925 --market spread --pick CIN --line -3.5 [--price -110] --units 1
  python pick_ledger.py grade
  python pick_ledger.py board [--sport nfl] [--period 7d|30d|ytd]
"""
import argparse
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sharp
import unk_stats as us
from unk_stats import SITE, _path, _get, _score

log = logging.getLogger("pick_ledger")
DB = Path(os.getenv("UNK_LEDGER_DB", Path(__file__).resolve().parent.parent / "data" / "unk_ledger.db"))
HOT_WINDOW = int(os.getenv("UNK_HOT_WINDOW", "10"))
UNIT_DOLLARS = float(os.getenv("UNK_UNIT_DOLLARS", "100"))
PERIODS = {"7d": 7, "30d": 30, "ytd": None, "all": None}

SCHEMA = """CREATE TABLE IF NOT EXISTS picks(
  id INTEGER PRIMARY KEY, ts TEXT, capper TEXT, sport TEXT, event_id TEXT,
  market TEXT CHECK(market IN ('ml','spread','total')), pick TEXT, line REAL,
  price INTEGER, units REAL, status TEXT DEFAULT 'pending', pnl REAL DEFAULT 0, graded_ts TEXT)"""
# added for sharp grading; migrated onto older ledgers in place
EXTRA = {"fair": "REAL", "edge": "REAL", "kelly_units": "REAL", "fair_src": "TEXT", "best_book": "TEXT",
         "best_price": "INTEGER", "close_line": "REAL", "close_price": "INTEGER", "close_fair": "REAL",
         "clv": "REAL", "line_clv": "REAL"}


def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(picks)")}
    for col, typ in EXTRA.items():
        if col not in have:
            con.execute(f"ALTER TABLE picks ADD COLUMN {col} {typ}")
    return con


def _fair_for(snap, market, pick, line):
    """De-vigged probability for my side from ESPN's two-way price, if the line still matches."""
    my_line, my_p, other_p = us.side_market(snap, market, pick)
    if my_p is None or other_p is None:
        return None, my_line, my_p
    if market != "ml" and line is not None and my_line is not None and abs(my_line - line) > 1e-9:
        return None, my_line, my_p
    return sharp.devig([my_p, other_p])[0], my_line, my_p


def price_pick(sport, event_id, market, pick, line=None, price=None):
    """Everything a sharp checks before betting: book price, best price, fair prob, edge, Kelly."""
    out = {"price": price, "fair": None, "fair_src": None, "edge": None, "kelly_units": None, "best": None}
    try:
        snap = us.event_odds(sport, event_id, fresh=True)
    except Exception as exc:
        log.warning("odds snapshot failed: %s", exc)
        snap = None
    if snap:
        fair, _, book_p = _fair_for(snap, market, pick, line)
        out["price"] = price if price is not None else (int(book_p) if book_p is not None else None)
        out["fair"], out["fair_src"] = fair, f"{snap['provider'] or 'espn'} no-vig" if fair else None
        try:
            import line_shop
            side = ("Over" if pick == "OVER" else "Under") if market == "total" else \
                (snap["home_name"] if pick == snap["home"] else snap["away_name"])
            s = line_shop.shop(sport, snap["home_name"], snap["away_name"], market, side, line)
            if s:
                out["best"] = s["best"]
                if s["sharp_fair"]:
                    out["fair"], out["fair_src"] = s["sharp_fair"], f"{s['sharp_book']} no-vig"
        except Exception as exc:
            log.warning("line shop failed: %s", exc)
    if out["price"] is None:
        out["price"] = int(os.getenv("UNK_DEFAULT_PRICE", "-110"))
        log.info("no price found, fallback %s", out["price"])
    if out["fair"]:
        out["edge"] = round(sharp.ev(out["price"], out["fair"]), 4)
        out["kelly_units"] = sharp.kelly_units(out["price"], out["fair"])
    return out


def add_pick(capper, sport, event_id, market, pick, line=None, price=None, units=1.0):
    _path(sport)
    pick = pick.upper()
    q = price_pick(sport, event_id, market, pick, line, price)
    best = q["best"] or {}
    with db() as con:
        cur = con.execute(
            "INSERT INTO picks(ts,capper,sport,event_id,market,pick,line,price,units,fair,edge,kelly_units,fair_src,best_book,best_price)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), capper, sport.lower(), str(event_id), market, pick, line, q["price"],
             units, q["fair"], q["edge"], q["kelly_units"], q["fair_src"], best.get("book"), best.get("price")))
        return {"id": cur.lastrowid, **q}


def payout(units, price):
    return units * (price / 100 if price > 0 else 100 / abs(price))


def settle(market, pick, line, scores):
    """scores: {ABBR: points}. Returns win/loss/push."""
    if market == "total":
        tot = sum(scores.values())
        edge = (tot - line) if pick == "OVER" else (line - tot)
    else:
        mine = scores[pick]
        opp = next(v for k, v in scores.items() if k != pick)
        edge = mine - opp + ((line or 0) if market == "spread" else 0)
    return "win" if edge > 0 else "loss" if edge < 0 else "push"


def final_scores(sport, event_id):
    cat, lg = _path(sport)
    comp = _get(f"{SITE}/{cat}/{lg}/summary?event={event_id}")["header"]["competitions"][0]
    if not comp["status"]["type"].get("completed"):
        return None
    return {c["team"]["abbreviation"]: _score(c) for c in comp["competitors"]}


def closing_value(p, snap):
    """CLV against the de-vigged close. Price CLV only when the number didn't move; line CLV in points always."""
    close_line, close_price, other = us.side_market(snap, p["market"], p["pick"])
    close_fair = sharp.devig([close_price, other])[0] if close_price is not None and other is not None else None
    line_clv = None
    if p["market"] == "spread" and close_line is not None and p["line"] is not None:
        line_clv = p["line"] - close_line
    elif p["market"] == "total" and close_line is not None and p["line"] is not None:
        line_clv = (close_line - p["line"]) if p["pick"] == "OVER" else (p["line"] - close_line)
    same_number = p["market"] == "ml" or (line_clv is not None and abs(line_clv) < 1e-9)
    clv = round(sharp.clv(p["price"], close_fair), 4) if close_fair and same_number else None
    return {"close_line": close_line, "close_price": close_price, "close_fair": close_fair, "clv": clv, "line_clv": line_clv}


def grade():
    _get.cache_clear()
    n = 0
    with db() as con:
        for p in con.execute("SELECT * FROM picks WHERE status='pending'").fetchall():
            scores = final_scores(p["sport"], p["event_id"])
            if not scores:
                continue
            res = settle(p["market"], p["pick"], p["line"], scores)
            pnl = payout(p["units"], p["price"]) if res == "win" else -p["units"] if res == "loss" else 0.0
            cv = {}
            try:
                snap = us.event_odds(p["sport"], p["event_id"])
                cv = closing_value(dict(p), snap) if snap else {}
            except Exception as exc:
                log.warning("clv for pick %s failed: %s", p["id"], exc)
            con.execute("UPDATE picks SET status=?, pnl=?, graded_ts=?, close_line=?, close_price=?, close_fair=?, clv=?, line_clv=?"
                        " WHERE id=?", (res, round(pnl, 3), datetime.now(timezone.utc).isoformat(), cv.get("close_line"),
                                        cv.get("close_price"), cv.get("close_fair"), cv.get("clv"), cv.get("line_clv"), p["id"]))
            n += 1
    return n


def _since(period):
    now = datetime.now(timezone.utc)
    if period in (None, "all"):
        return None
    if period == "ytd":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    days = PERIODS.get(period) or int(str(period).rstrip("d"))
    return (now - timedelta(days=days)).isoformat()


def leaderboard(sport=None, period=None):
    """period: 7d / 30d / ytd / all / '<n>d'. Ranked by units; CLV shown as the skill check."""
    where, args = ["status!='pending'"], []
    if sport:
        where.append("sport=?"); args.append(sport.lower())
    since = _since(period)
    if since:
        where.append("graded_ts>=?"); args.append(since)
    with db() as con:
        rows = con.execute(f"SELECT * FROM picks WHERE {' AND '.join(where)} ORDER BY graded_ts", args).fetchall()
    board = {}
    for r in rows:
        b = board.setdefault(r["capper"], {"capper": r["capper"], "W": 0, "L": 0, "P": 0, "units": 0.0, "risked": 0.0,
                                           "seq": [], "by_sport": {}, "clvs": [], "beat": []})
        k = {"win": "W", "loss": "L", "push": "P"}[r["status"]]
        b[k] += 1
        b["units"] += r["pnl"]
        b["risked"] += r["units"]
        b["seq"].append(r["status"])
        s = b["by_sport"].setdefault(r["sport"], {"W": 0, "L": 0, "P": 0, "units": 0.0})
        s[k] += 1
        s["units"] = round(s["units"] + r["pnl"], 2)
        if r["clv"] is not None:
            b["clvs"].append(r["clv"])
        if r["clv"] is not None or r["line_clv"] is not None:
            b["beat"].append((r["clv"] or 0) > 0 or (r["line_clv"] or 0) > 0)
    out = []
    for b in board.values():
        dec = b["W"] + b["L"]
        last = [s for s in b.pop("seq") if s != "push"][-HOT_WINDOW:]
        clvs, beat = b.pop("clvs"), b.pop("beat")
        b.update(win_pct=round(b["W"] / dec, 3) if dec else None, units=round(b["units"], 2),
                 roi=round(b["units"] / b["risked"], 3) if b["risked"] else None,
                 last=f"{last.count('win')}-{last.count('loss')}", profit=round(b["units"] * UNIT_DOLLARS, 2),
                 avg_clv=round(sum(clvs) / len(clvs), 4) if clvs else None,
                 beat_close=round(sum(beat) / len(beat), 3) if beat else None)
        b["hot"] = len(last) >= HOT_WINDOW // 2 and last.count("win") / len(last) >= 0.7
        out.append(b)
    return sorted(out, key=lambda b: b["units"], reverse=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    for f in ("capper", "sport", "event", "market", "pick"):
        a.add_argument(f"--{f}", required=True)
    a.add_argument("--line", type=float)
    a.add_argument("--price", type=int)
    a.add_argument("--units", type=float, default=1.0)
    sub.add_parser("grade")
    bd = sub.add_parser("board")
    bd.add_argument("--sport")
    bd.add_argument("--period", help="7d | 30d | ytd | all | <n>d")
    args = ap.parse_args()
    if args.cmd == "add":
        print(add_pick(args.capper, args.sport, args.event, args.market, args.pick, args.line, args.price, args.units))
    elif args.cmd == "grade":
        print("graded", grade())
    else:
        for b in leaderboard(args.sport, args.period):
            print(f"{'🔥' if b['hot'] else '  '} {b['capper']:<14} {b['W']}-{b['L']}-{b['P']}  win {b['win_pct']}  "
                  f"units {b['units']:+}  ${b['profit']:+,.0f}  roi {b['roi']}  clv {b['avg_clv']}  beat close {b['beat_close']}")
            for s, r in b["by_sport"].items():
                print(f"     {s:<6} {r['W']}-{r['L']}-{r['P']}  {r['units']:+}u")
