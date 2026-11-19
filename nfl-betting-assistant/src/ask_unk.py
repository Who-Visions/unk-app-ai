"""Ask Unk: natural-language sports questions -> unk_stats / pick_ledger answers.

The question is parsed into an intent by the loopback gemma lane (coach.local,
never leaves the box); a keyword parser is the fallback when that lane is down.

  python ask_unk.py "knicks against the spread this season"
  python ask_unk.py "nba standings"
  python ask_unk.py "mlb home run leaders"
"""
import json
import logging
import os
import re
import sys

import unk_stats as us
import pick_ledger as pl

log = logging.getLogger("ask_unk")
INTENTS = ["ats", "standings", "leaders", "scoreboard", "board", "player", "result"]
SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": INTENTS},
        "sport": {"type": "string", "enum": sorted(us.SPORTS)},
        "team": {"type": "string"},
        "player": {"type": "string"},
        "last": {"type": "integer"},
        "period": {"type": "string"},
        "category": {"type": "string"},
        "season": {"type": "integer"},
    },
    "required": ["intent", "sport"],
}


def _coach():
    tools = os.getenv("COACH_TOOLS_DIR") or os.path.expanduser(r"~\Outpost\NouGen\tools")
    if not os.getenv("COACH_TOOLS_DIR"):
        log.info("COACH_TOOLS_DIR unset, fallback %s", tools)
    sys.path.insert(0, tools)
    import coach
    return coach


def parse_llm(q):
    prompt = (f"Turn this sports question into JSON. intents: ats=against the spread/cover record, standings, "
              f"leaders=stat leaders (category like points, home runs), scoreboard=today's games/lines, "
              f"board=capper pick leaderboard, player=a named player's games/stats, result=did a team win its last game. "
              f"sports: {sorted(us.SPORTS)}. team = the team named, if any. player = full player name, if any. "
              f"last = N when 'last N games'. period = 7d/30d/ytd for the board. "
              f"season only if a year is stated.\nQuestion: {q}")
    return json.loads(_coach().local(prompt, schema=SCHEMA, max_tokens=200))


def parse_keywords(q):
    ql = q.lower()
    sport = next((s for s in us.SPORTS if re.search(rf"\b{s}\b", ql)), None)
    intent = ("ats" if re.search(r"spread|\bats\b|cover", ql) else "standings" if "standing" in ql
              else "leaders" if "leader" in ql or "most" in ql else "board" if re.search(r"capper|leaderboard|record of picks", ql)
              else "scoreboard")
    team = None
    for s in ([sport] if sport else list(us.SPORTS)):
        for t in us.teams(s):
            if t["nickname"].lower() in ql or t["abbreviation"].lower() in ql.split():
                team, sport = t["nickname"], s
                break
        if team:
            break
    year = re.search(r"\b(20\d\d)\b", ql)
    cat = re.sub(r"\b(" + "|".join(us.SPORTS) + r"|leaders?|most|top|in|the|this|season|year|\d{4})\b", "", ql).strip() or None
    return {"intent": intent, "sport": sport or "nfl", "team": team, "category": cat if intent == "leaders" else None,
            "season": int(year.group(1)) if year else None}


def _explicit_intent(q):
    """Unambiguous keywords win over the model (gemma once filed 'home run leaders' as ats)."""
    ql = q.lower()
    for intent, pat in (("ats", r"spread|\bats\b|cover"), ("standings", r"standing|who leads the"), ("leaders", r"leader"),
                        ("board", r"capper|leaderboard"), ("result", r"\bdid (the )?\w+( \w+)? (win|lose)\b")):
        if re.search(pat, ql):
            return intent
    return None


def parse(q):
    try:
        it = parse_llm(q) | {"parser": "gemma"}
        forced = _explicit_intent(q)
        if forced and forced != it["intent"]:
            log.info("intent %s -> %s (explicit keyword)", it["intent"], forced)
            it |= {"intent": forced, "parser": "gemma+kw"}
        # numbers stated in the question beat the model's reading of them
        year = re.search(r"\b(20\d\d)\b", q)
        it["season"] = int(year.group(1)) if year else None
        n = re.search(r"\blast (\d+)\b", q.lower())
        if n:
            it["last"] = int(n.group(1))
        return it
    except Exception as exc:
        log.warning("gemma parse failed (%s), keyword fallback", exc)
        return parse_keywords(q) | {"parser": "keywords"}


def answer(q):
    it = parse(q)
    sp, season = it["sport"], it.get("season")
    head = f"[{it['parser']}] {it['intent']} / {sp}"
    if it["intent"] == "ats":
        r = us.team_ats(sp, it.get("team") or "", season)
        tail = " ".join(g["ats"] for g in r["games"][-10:])
        s = r["splits"]
        return (f"{head}\n{r['team']} {r['season']}: {r['W']}-{r['L']}-{r['P']} ATS ({r['ats_pct']}), "
                f"O/U {r['O']}-{r['U']}-{r['OP']}. Last 10 ATS: {tail}" + (f"  ({r['no_line']} games without a line)" if r["no_line"] else "")
                + f"\nhome {s['home']} | away {s['away']} | fav {s['fav']} | dog {s['dog']}")
    if it["intent"] == "standings":
        return head + "\n" + "\n".join(f"{r['group']:<6} {r['team']:<5} {r['w']}-{r['l']}  {r['pct']}  {r['streak'] or ''}"
                                       for r in us.standings(sp, season))
    if it["intent"] == "leaders":
        cats = us.leaders(sp, season, it.get("category"), top=5)[:3]
        return head + "\n" + "\n".join(f"{c['category']}: " + ", ".join(f"{l['name']} {l['value']:g}" for l in c["leaders"]) for c in cats)
    if it["intent"] == "player":
        n = it.get("last") or (1 if re.search(r"\bdo\b|\bdid\b|last (game|night)", q.lower()) else 5)
        r = us.player_gamelog(it.get("player") or q, it.get("sport") if it.get("sport") != "nfl" or it.get("player") else None,
                              season, last=n)
        keys = [k for k in ("PTS", "REB", "AST", "3PT", "CMP", "REC", "CAR", "YDS", "TD", "H", "HR", "RBI", "G", "A") if k in r["avg"] or k in r["labels"]]
        lines = [f"{g['date']} {g['at'] or ''} {g['opp'] or ''} {g['result'] or ''} {g['score'] or ''}  "
                 + " ".join(f"{k} {g.get(k)}" for k in keys) for g in r["rows"]]
        avg = " ".join(f"{k} {r['avg'][k]}" for k in keys if k in r["avg"])
        return f"{head}\n{r['player']} last {r['games']}: {avg}\n" + "\n".join(lines)
    if it["intent"] == "result":
        r = us.last_result(sp, it.get("team") or "", season)
        return f"{head}\n{r['team']} {'W' if r['won'] else 'L'} {r['score']} vs {r['opp']} ({r['date']})" if r else f"{head}\nno completed game"
    if it["intent"] == "board":
        return head + "\n" + "\n".join(f"{b['capper']} {b['W']}-{b['L']}-{b['P']} units {b['units']:+} last {b['last']}"
                                       for b in pl.leaderboard(sp, it.get("period"))) or "no graded picks yet"
    return head + "\n" + "\n".join(f"{g['name']:<12} {g['status']:<18} {g['line'] or ''}" for g in us.scoreboard(sp))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print(answer(" ".join(sys.argv[1:]) or "nfl scoreboard"))
