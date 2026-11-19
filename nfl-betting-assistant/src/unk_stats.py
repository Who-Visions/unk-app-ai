"""Unk stats engine: StatMuse-style multi-sport answers over ESPN's public APIs.

Covers leaders, standings, scoreboards and a computed against-the-spread record
(ESPN's own /ats endpoint returns empty, so ATS is rebuilt from final scores plus
the closing line ESPN keeps on each finished event).
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache

import requests

log = logging.getLogger("unk_stats")

SITE = os.getenv("UNK_ESPN_SITE", "https://site.api.espn.com/apis/site/v2/sports")
WEB = os.getenv("UNK_ESPN_WEB", "https://site.web.api.espn.com/apis/v2/sports")
CORE = os.getenv("UNK_ESPN_CORE", "https://sports.core.api.espn.com/v2/sports")
TIMEOUT = float(os.getenv("UNK_HTTP_TIMEOUT", "15"))
WORKERS = int(os.getenv("UNK_HTTP_WORKERS", str(min(8, (os.cpu_count() or 4)))))

# short name -> (category, league path)
SPORTS = {
    "nfl": ("football", "nfl"),
    "cfb": ("football", "college-football"),
    "nba": ("basketball", "nba"),
    "wnba": ("basketball", "wnba"),
    "ncaab": ("basketball", "mens-college-basketball"),
    "mlb": ("baseball", "mlb"),
    "nhl": ("hockey", "nhl"),
}


def _path(sport):
    try:
        return SPORTS[sport.lower()]
    except KeyError:
        raise ValueError(f"unknown sport {sport!r}; have {sorted(SPORTS)}")


@lru_cache(maxsize=512)
def _get(url):
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _score(c):
    s = c.get("score")
    if isinstance(s, dict):
        s = s.get("value")
    return float(s) if s not in (None, "") else None


def default_season(sport):
    """ESPN labels a season by the year it ends for winter sports, by the start year otherwise."""
    today = date.today()
    cat, _ = _path(sport)
    if cat in ("basketball", "hockey") and sport != "wnba":
        return today.year + 1 if today.month >= 10 else today.year
    return today.year if today.month >= 3 else today.year - 1


def teams(sport):
    cat, lg = _path(sport)
    d = _get(f"{SITE}/{cat}/{lg}/teams?limit=500")
    return [t["team"] for t in d["sports"][0]["leagues"][0]["teams"]]


def find_team(sport, q):
    q = q.lower().strip()
    for t in teams(sport):
        names = [t.get(k, "").lower() for k in ("abbreviation", "displayName", "shortDisplayName", "name", "location", "nickname")]
        if q in names or any(q and q in n for n in names[1:]):
            return t
    raise ValueError(f"no {sport} team matches {q!r}")


def scoreboard(sport, day=None):
    cat, lg = _path(sport)
    url = f"{SITE}/{cat}/{lg}/scoreboard" + (f"?dates={day}" if day else "")
    out = []
    for e in _get(url).get("events", []):
        c = e["competitions"][0]
        odds = (c.get("odds") or [{}])[0]
        out.append({
            "id": e["id"],
            "name": e["shortName"],
            "status": c["status"]["type"]["shortDetail"],
            "score": {t["team"]["abbreviation"]: _score(t) for t in c["competitors"]},
            "line": odds.get("details"),
            "total": odds.get("overUnder"),
        })
    return out


def standings(sport, season=None):
    cat, lg = _path(sport)
    season = season or default_season(sport)
    d = _get(f"{WEB}/{cat}/{lg}/standings?season={season}")
    rows = []
    for grp in d.get("children", []) or [d]:
        for e in grp.get("standings", {}).get("entries", []):
            st = {s["name"]: s.get("displayValue") for s in e["stats"]}
            rows.append({"group": grp.get("abbreviation", ""), "team": e["team"]["abbreviation"],
                         "w": st.get("wins"), "l": st.get("losses"),
                         "pct": st.get("winPercent") or (f"{st['points']} pts" if st.get("points") else None),
                         "gb": st.get("gamesBehind"), "streak": st.get("streak")})
    return rows


def leaders(sport, season=None, category=None, top=5):
    cat, lg = _path(sport)
    season = season or default_season(sport)
    d = _get(f"{CORE}/{cat}/leagues/{lg}/seasons/{season}/types/2/leaders")
    cats = d.get("categories", [])
    if category:
        c = category.lower()
        cats = [x for x in cats if c in (x["name"].lower(), x["abbreviation"].lower(), x["displayName"].lower())
                or c in x["displayName"].lower()]
    out = []
    for x in cats:
        rows = []
        for ld in x["leaders"][:top]:
            ath = _get(ld["athlete"]["$ref"]).get("displayName", "?") if "athlete" in ld else "?"
            rows.append({"name": ath, "value": ld.get("value"), "line": ld.get("displayValue")})
        out.append({"category": x["displayName"], "abbr": x["abbreviation"], "leaders": rows})
    return out


def _closing_line(cat, lg, eid):
    try:
        items = _get(f"{CORE}/{cat}/leagues/{lg}/events/{eid}/competitions/{eid}/odds").get("items", [])
    except requests.RequestException as exc:
        log.warning("odds %s: %s", eid, exc)
        return None
    items = sorted(items, key=lambda i: i.get("provider", {}).get("priority", 99))
    return items[0] if items else None


def event_odds(sport, event_id, fresh=False):
    """Both sides of every main market for one event (ESPN keeps the closing number after the final)."""
    cat, lg = _path(sport)
    if fresh:
        _get.cache_clear()
    comp = _get(f"{SITE}/{cat}/{lg}/summary?event={event_id}")["header"]["competitions"][0]
    teams = {c["homeAway"]: c["team"] for c in comp["competitors"]}
    ln = _closing_line(cat, lg, event_id)
    if not ln:
        return None
    h, a = ln.get("homeTeamOdds", {}), ln.get("awayTeamOdds", {})
    return {
        "home": teams["home"]["abbreviation"], "away": teams["away"]["abbreviation"],
        "home_name": teams["home"]["displayName"], "away_name": teams["away"]["displayName"],
        "completed": comp["status"]["type"].get("completed", False), "provider": ln.get("provider", {}).get("name"),
        "spread": ln.get("spread"),  # home team's line
        "home_spread_price": h.get("spreadOdds"), "away_spread_price": a.get("spreadOdds"),
        "total": ln.get("overUnder"), "over_price": ln.get("overOdds"), "under_price": ln.get("underOdds"),
        "home_ml": h.get("moneyLine"), "away_ml": a.get("moneyLine"),
    }


def side_market(o, market, pick):
    """-> (my_line, my_price, other_price) for one side of an event_odds() snapshot."""
    if market == "total":
        mine, other = ("over_price", "under_price") if pick == "OVER" else ("under_price", "over_price")
        return o["total"], o[mine], o[other]
    home = pick == o["home"]
    if market == "spread":
        line = o["spread"] if home else (-o["spread"] if o["spread"] is not None else None)
        return line, o["home_spread_price" if home else "away_spread_price"], o["away_spread_price" if home else "home_spread_price"]
    return None, o["home_ml" if home else "away_ml"], o["away_ml" if home else "home_ml"]


def team_ats(sport, team, season=None, seasontype=2):
    """Against-the-spread and over/under record from final scores + ESPN closing lines."""
    cat, lg = _path(sport)
    season = season or default_season(sport)
    t = find_team(sport, team)
    sched = _get(f"{SITE}/{cat}/{lg}/teams/{t['id']}/schedule?season={season}&seasontype={seasontype}")
    finals = [e for e in sched.get("events", []) if e["competitions"][0]["status"]["type"].get("completed")]
    with ThreadPoolExecutor(WORKERS) as pool:
        lines = list(pool.map(lambda e: _closing_line(cat, lg, e["id"]), finals))

    rec = {"W": 0, "L": 0, "P": 0, "O": 0, "U": 0, "OP": 0, "no_line": 0}
    games = []
    for e, ln in zip(finals, lines):
        comp = e["competitions"][0]["competitors"]
        me = next(c for c in comp if c["team"]["id"] == t["id"])
        opp = next(c for c in comp if c["team"]["id"] != t["id"])
        ms, os_ = _score(me), _score(opp)
        if ln is None or ln.get("spread") is None or ms is None:
            rec["no_line"] += 1
            continue
        my_spread = ln["spread"] if me.get("homeAway") == "home" else -ln["spread"]
        cover = ms - os_ + my_spread
        rec["W" if cover > 0 else "L" if cover < 0 else "P"] += 1
        ou = ln.get("overUnder")
        if ou is not None:
            tot = ms + os_
            rec["O" if tot > ou else "U" if tot < ou else "OP"] += 1
        games.append({"date": e["date"][:10], "opp": opp["team"]["abbreviation"], "score": f"{ms:g}-{os_:g}",
                      "spread": my_spread, "ats": "W" if cover > 0 else "L" if cover < 0 else "P", "total": ou,
                      "home": me.get("homeAway") == "home", "fav": my_spread < 0})
    decided = rec["W"] + rec["L"]
    return {"team": t["displayName"], "abbr": t["abbreviation"], "season": season, **rec,
            "ats_pct": round(rec["W"] / decided, 3) if decided else None, "games": games,
            "splits": ats_splits(games)}


def ats_splits(games):
    """Situational ATS: home/away, favorite/underdog, last 10."""
    def rec(gs):
        w, l, p = (sum(g["ats"] == x for g in gs) for x in "WLP")
        return f"{w}-{l}-{p}"
    return {"home": rec([g for g in games if g["home"]]), "away": rec([g for g in games if not g["home"]]),
            "fav": rec([g for g in games if g["fav"]]), "dog": rec([g for g in games if not g["fav"]]),
            "last10": rec(games[-10:])}


def last_result(sport, team, season=None):
    """'Did the Warriors win?' - most recent completed game."""
    cat, lg = _path(sport)
    t = find_team(sport, team)
    for st in (2, 3, 1) if season else (3, 2):
        sched = _get(f"{SITE}/{cat}/{lg}/teams/{t['id']}/schedule?season={season or default_season(sport)}&seasontype={st}")
        done = [e for e in sched.get("events", []) if e["competitions"][0]["status"]["type"].get("completed")]
        if done:
            e = done[-1]
            comp = e["competitions"][0]["competitors"]
            me = next(c for c in comp if c["team"]["id"] == t["id"])
            opp = next(c for c in comp if c["team"]["id"] != t["id"])
            return {"team": t["displayName"], "date": e["date"][:10], "won": me.get("winner"),
                    "score": f"{_score(me):g}-{_score(opp):g}", "opp": opp["team"]["displayName"], "event_id": e["id"]}
    return None


SEARCH = os.getenv("UNK_ESPN_SEARCH", "https://site.api.espn.com/apis/common/v3/search")
ATHLETE = os.getenv("UNK_ESPN_ATHLETE", "https://site.web.api.espn.com/apis/common/v3/sports")


def find_player(q, sport=None):
    items = _get(f"{SEARCH}?query={requests.utils.quote(q)}&type=player&limit=10").get("items", [])
    leagues = {lg: s for s, (_, lg) in SPORTS.items()}
    for it in items:
        if it.get("league") in leagues and (sport is None or leagues[it["league"]] == sport):
            return {"id": it["id"], "name": it["displayName"], "sport": leagues[it["league"]]}
    raise ValueError(f"no player matches {q!r}" + (f" in {sport}" if sport else ""))


def _gamelog_rows(cat, lg, athlete_id, season):
    try:
        d = _get(f"{ATHLETE}/{cat}/{lg}/athletes/{athlete_id}/gamelog?season={season}")
    except requests.RequestException as exc:
        log.warning("gamelog %s %s: %s", athlete_id, season, exc)
        return [], []
    raw, names, meta = d.get("labels", []), d.get("names", []), d.get("events", {})
    # NFL repeats labels across passing/rushing/receiving (YDS, TD); keep the first short label, disambiguate the rest
    labels, seen = [], set()
    for i, lab in enumerate(raw):
        labels.append(lab if lab not in seen else (names[i] if i < len(names) else f"{lab}_{i}"))
        seen.add(lab)
    rows = []
    for st in d.get("seasonTypes", []):
        for c in st.get("categories", []):
            for e in c.get("events", []):
                m = meta.get(e["eventId"], {})
                rows.append({"date": (m.get("gameDate") or "")[:10], "opp": (m.get("opponent") or {}).get("abbreviation"),
                             "at": m.get("atVs"), "result": m.get("gameResult"), "score": m.get("score"),
                             **dict(zip(labels, e["stats"]))})
    return rows, labels


def player_gamelog(q, sport=None, season=None, last=None):
    """Per-game lines + averages. last=1 answers 'how did X do'."""
    p = find_player(q, sport)
    cat, lg = _path(p["sport"])
    explicit = season is not None
    season = season or default_season(p["sport"])
    rows, labels = _gamelog_rows(cat, lg, p["id"], season)
    if not explicit and last and len(rows) < last:  # early season: top up from last season
        prev, _ = _gamelog_rows(cat, lg, p["id"], season - 1)
        rows = prev + rows
    rows.sort(key=lambda r: r["date"])
    rows = rows[-last:] if last else rows
    avg = {}
    for lab in labels:
        vals = []
        for r in rows:
            try:
                vals.append(float(r[lab]))
            except (TypeError, ValueError, KeyError):
                pass
        if vals and len(vals) == len(rows):
            avg[lab] = round(sum(vals) / len(vals), 1)
    return {"player": p["name"], "sport": p["sport"], "season": season, "games": len(rows), "labels": labels,
            "rows": rows, "avg": avg}
