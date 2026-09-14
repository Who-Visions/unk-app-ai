"""Unk at the table: talk to Unk like a person, get tables back.

  python unk_cli.py                      # chat mode
  python unk_cli.py "knicks ats 2025"    # one question and out

In chat, just ask. A few words mean something special:
  pick bengals -3.5 2u @-115    log a pick (spread / ml / over 47.5 / under 47.5)
  my picks | board [7d|30d|ytd] grade | help | examples | quit
"""
import logging
import re
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import ask_unk as au
import pick_ledger as pl
import sharp
import unk_stats as us

con = Console()
CAPPER = "Unk"

EXAMPLES = [
    "how are the knicks against the spread in 2025",
    "did the bengals win",
    "how did jokic do",
    "ja'marr chase last 5 games",
    "mlb home run leaders 2025",
    "nhl standings",
    "what are tonight's wnba lines",
    "pick bengals -3.5 1u",
    "board 7d",
]


# ---------- Unk's voice (plain templates, so the numbers are never made up) ----------

def say(line):
    con.print(f"[bold yellow]Unk:[/] {line}")


def ats_take(pct, team):
    if pct is None:
        return f"No lines on the {team} yet. Season's too young, nephew."
    if pct >= 0.58:
        return f"The {team} have been printing money against the number. Respect it."
    if pct <= 0.42:
        return f"The {team} been burning people all year. Fade material."
    return f"The {team} are a coin flip against the spread. Don't marry 'em."


# ---------- renderers ----------

def table(title, cols, rows):
    t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold cyan", header_style="bold")
    for c in cols:
        t.add_column(c, justify="right" if c not in ("Team", "Game", "Player", "Opp", "Capper", "Status", "Group") else "left")
    for r in rows:
        t.add_row(*[("" if v is None else str(v)) for v in r])
    con.print(t)


def show_ats(it):
    r = us.team_ats(it["sport"], it.get("team") or "", it.get("season"))
    s = r["splits"]
    table(f"{r['team']} {r['season']} against the spread", ["Split", "ATS"],
          [["Overall", f"{r['W']}-{r['L']}-{r['P']}"], ["Home", s["home"]], ["Away", s["away"]],
           ["Favorite", s["fav"]], ["Underdog", s["dog"]], ["Last 10", s["last10"]],
           ["Over/Under", f"{r['O']}-{r['U']}-{r['OP']}"]])
    if r["games"]:
        table("Last 5", ["Date", "Opp", "Score", "Spread", "ATS"],
              [[g["date"], ("vs " if g["home"] else "@ ") + g["opp"], g["score"], f"{g['spread']:+g}", g["ats"]] for g in r["games"][-5:]])
    say(ats_take(r["ats_pct"], r["team"].split()[-1]))


def show_result(it):
    r = us.last_result(it["sport"], it.get("team") or "", it.get("season"))
    if not r:
        return say("They ain't finished a game yet this season.")
    word = "Yeah, they got it" if r["won"] else "Nah, they took an L"
    say(f"{word}. {r['team']} {r['score']} against the {r['opp']} on {r['date']}.")


def show_player(it, q):
    n = it.get("last") or (1 if re.search(r"\bdo\b|\bdid\b|last (game|night)", q.lower()) else 5)
    sport = it.get("sport") if it.get("player") else None
    try:
        r = us.player_gamelog(it.get("player") or q, sport, it.get("season"), last=n)
    except ValueError:
        r = us.player_gamelog(it.get("player") or q, None, it.get("season"), last=n)
    keys = [k for k in ("PTS", "REB", "AST", "3PT", "CMP", "YDS", "REC", "CAR", "TD", "H", "HR", "RBI", "G", "A")
            if k in r["labels"] and any(str(g.get(k)) not in ("0", "0-0", "None") for g in r["rows"])][:7]
    table(f"{r['player']}: last {r['games']}", ["Date", "Opp", "Result", *keys],
          [[g["date"], f"{g['at'] or ''} {g['opp'] or ''}", f"{g['result'] or ''} {g['score'] or ''}", *[g.get(k) for k in keys]]
           for g in r["rows"]])
    if r["games"] > 1:
        say(f"{r['player']} averaging " + ", ".join(f"{r['avg'][k]} {k}" for k in keys if k in r["avg"]) + f" over those {r['games']}.")


def show_standings(it):
    rows = us.standings(it["sport"], it.get("season"))
    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    for g, rs in groups.items():
        table(f"{it['sport'].upper()} {g}", ["Team", "W", "L", "Pct", "GB", "Streak"],
              [[r["team"], r["w"], r["l"], r["pct"], r["gb"], r["streak"]] for r in rs])


def show_leaders(it):
    for c in us.leaders(it["sport"], it.get("season"), it.get("category"), top=5)[:3]:
        table(c["category"], ["#", "Player", "Value"],
              [[i + 1, l["name"], f"{l['value']:g}"] for i, l in enumerate(c["leaders"])])


def show_scoreboard(it):
    games = us.scoreboard(it["sport"])
    if not games:
        return say(f"Nothing on the {it['sport'].upper()} board right now.")
    table(f"{it['sport'].upper()} board", ["Game", "Status", "Line", "Total"],
          [[g["name"], g["status"], g["line"], g["total"]] for g in games])


def show_board(period=None, sport=None):
    b = pl.leaderboard(sport, period)
    if not b:
        return say("No graded picks yet. Log one: pick bengals -3.5 1u")
    table(f"Cappers ({period or 'all time'})",
          ["Capper", "Record", "Win %", "Units", "Profit", "ROI", "Avg CLV", "Beat close", "Last 10", ""],
          [[x["capper"], f"{x['W']}-{x['L']}-{x['P']}", x["win_pct"], f"{x['units']:+}", f"${x['profit']:+,.0f}", x["roi"],
            f"{x['avg_clv']:+.1%}" if x["avg_clv"] is not None else "", f"{x['beat_close']:.0%}" if x["beat_close"] is not None else "",
            x["last"], "🔥" if x["hot"] else ""] for x in b])
    say("Win % lies in small samples. Beat the close and the money follows.")


def show_my_picks():
    with pl.db() as c:
        rows = c.execute("SELECT * FROM picks ORDER BY id DESC LIMIT 15").fetchall()
    if not rows:
        return say("You ain't logged nothing yet.")
    table("Recent picks", ["#", "Capper", "Sport", "Pick", "Line", "Price", "Units", "Edge", "Close", "CLV", "Status", "P/L"],
          [[r["id"], r["capper"], r["sport"], f"{r['pick']} {r['market']}", r["line"], r["price"], r["units"],
            f"{r['edge']:+.1%}" if r["edge"] is not None else "",
            (f"{r['close_line']:g} " if r["close_line"] is not None else "") + (f"{r['close_price']:+d}" if r["close_price"] is not None else ""),
            f"{r['clv']:+.1%}" if r["clv"] is not None else (f"{r['line_clv']:+g} pts" if r["line_clv"] is not None else ""),
            r["status"], f"{r['pnl']:+}" if r["status"] != "pending" else ""] for r in rows])


# ---------- logging picks in plain words ----------

PICK_RE = re.compile(
    r"^pick\s+(?P<team>.+?)\s+(?:(?P<ml>ml|moneyline)|(?P<ou>over|under|o|u)\s*(?P<total>\d+(?:\.\d+)?)|(?P<line>[+-]\d+(?:\.\d+)?))"
    r"(?:\s+(?P<units>\d+(?:\.\d+)?)u)?(?:\s*@\s*(?P<price>[+-]?\d+))?\s*$", re.I)


def find_game(team_words):
    """Find the next unfinished game for a team, across every sport we cover."""
    for sport in us.SPORTS:
        try:
            t = us.find_team(sport, team_words)
        except ValueError:
            continue
        for g in us.scoreboard(sport):
            if t["abbreviation"] in g["score"] and not g["status"].startswith("Final"):
                return sport, t, g
    return None, None, None


def log_pick(text):
    m = PICK_RE.match(text.strip())
    if not m:
        return say("Say it like: pick bengals -3.5 2u @-115  |  pick lakers ml  |  pick chiefs over 47.5")
    sport, t, g = find_game(m["team"])
    if not g:
        return say(f"I don't see an upcoming game for '{m['team']}' on any board right now.")
    if m["ml"]:
        market, sel, line = "ml", t["abbreviation"], None
    elif m["ou"]:
        market, sel, line = "total", "OVER" if m["ou"].lower().startswith("o") else "UNDER", float(m["total"])
    else:
        market, sel, line = "spread", t["abbreviation"], float(m["line"])
    price = int(m["price"]) if m["price"] else None  # None = take the live book price
    units = float(m["units"]) if m["units"] else 1.0
    with con.status("[yellow]Pricing it like a sharp...[/]"):
        r = pl.add_pick(CAPPER, sport, g["id"], market, sel, line, price, units)
    what = (f"{sel} on the moneyline" if market == "ml" else
            f"{sel} {line:+g}" if market == "spread" else f"{sel.lower()} {line:g}")
    rows = [["Your price", f"{r['price']:+d}"]]
    if r["best"]:
        rows.append(["Best price", f"{r['best']['price']:+d} at {r['best']['book']}"])
    if r["fair"]:
        rows += [["Fair price", f"{sharp.to_american(r['fair']):+d}  ({r['fair']:.1%}, {r['fair_src']})"],
                 ["Edge", f"{r['edge']:+.1%}"], ["Kelly says", f"{r['kelly_units']:g}u (¼ Kelly, {sharp.BANKROLL_UNITS:g}u roll)"]]
    table(f"#{r['id']} {what} ({g['name']})", ["", "Value"], rows)
    if r["edge"] is None:
        say(f"Locked in, {units:g}u. Couldn't get a clean fair price on that number, so no edge read.")
    elif r["edge"] > 0:
        say(f"Locked in, {units:g}u. You're getting a better number than fair. That's how we eat.")
    elif r["best"] and sharp.ev(r["best"]["price"], r["fair"]) > 0:
        e = sharp.ev(r["best"]["price"], r["fair"])
        say(f"Locked in, {units:g}u, but hold up: {r['best']['book']} at {r['best']['price']:+d} is BETTER than fair "
            f"({e:+.1%}). Bet it there, nephew.")
    elif r["best"] and sharp.to_decimal(r["best"]["price"]) > sharp.to_decimal(r["price"]):
        say(f"Locked in, {units:g}u, but you're paying juice. {r['best']['book']} has it at {r['best']['price']:+d}. Shop, nephew.")
    else:
        say(f"Locked in, {units:g}u. No edge against fair though. We'll see what the close says.")


# ---------- the loop ----------

SHOW = {"ats": show_ats, "result": show_result, "standings": show_standings, "leaders": show_leaders,
        "scoreboard": show_scoreboard}


def handle(q):
    ql = q.lower().strip()
    if ql in ("help", "?"):
        return con.print(Panel(__doc__.split("\n\n", 1)[1].strip(), title="How to talk to Unk", border_style="yellow"))
    if ql == "examples":
        return [con.print(f"  [cyan]›[/] {e}") for e in EXAMPLES]
    if ql.startswith("pick "):
        return log_pick(q)
    if ql in ("my picks", "picks"):
        return show_my_picks()
    if ql == "grade":
        n = pl.grade()
        return say(f"Graded {n} pick{'s' if n != 1 else ''}." if n else "Nothing's final yet. Patience, nephew.")
    if ql.startswith("board") or "leaderboard" in ql or "capper" in ql:
        period = next((p for p in ("7d", "30d", "ytd") if p in ql), None)
        sport = next((s for s in us.SPORTS if re.search(rf"\b{s}\b", ql)), None)
        return show_board(period, sport)
    with con.status("[yellow]Unk's looking it up...[/]"):
        it = au.parse(q)
    if it["intent"] == "player":
        with con.status("[yellow]Pulling the game log...[/]"):
            return show_player(it, q)
    if it["intent"] == "board":
        return show_board(it.get("period"), it.get("sport"))
    with con.status("[yellow]Crunching...[/]"):
        return SHOW[it["intent"]](it)


def safe(q):
    try:
        handle(q)
    except ValueError as exc:
        say(f"Couldn't place that one: {exc}. Try the city or the nickname.")
    except Exception as exc:  # network hiccups, ESPN shape changes
        logging.getLogger("unk").debug("error", exc_info=True)
        say(f"Something went sideways ({type(exc).__name__}). ESPN might be slow. Run it back.")


def main():
    logging.basicConfig(level=logging.ERROR)
    if len(sys.argv) > 1:
        return safe(" ".join(sys.argv[1:]))
    con.print(Panel.fit("[bold yellow]UNK[/] at the table\n[dim]ask anything, 'examples' for ideas, 'quit' to dip[/]",
                        border_style="yellow"))
    say("Yo, nephew! What we looking at?")
    while True:
        try:
            q = con.input("[bold green]you ›[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in ("quit", "exit", "q", "bye"):
            break
        if q:
            safe(q)
    say("Aight, stay up.")


if __name__ == "__main__":
    main()
