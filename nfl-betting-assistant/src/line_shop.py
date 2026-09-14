"""Line shopping across books via The Odds API, with Pinnacle as the sharp reference.

Needs ODDS_API_KEY (nfl-betting-assistant/.env). Each call costs markets x regions credits,
so results are cached per process and the region list is env-tunable.
"""
import logging
import os
import time

import requests
from dotenv import load_dotenv

import sharp

load_dotenv()
log = logging.getLogger("line_shop")

BASE = os.getenv("UNK_ODDS_API_BASE", "https://api.the-odds-api.com/v4")
REGIONS = os.getenv("UNK_ODDS_REGIONS", "us,eu")  # eu carries Pinnacle
# sharpest first; Pinnacle skips some markets (e.g. WNBA), the Betfair exchange usually has them
SHARP_BOOKS = [b.strip() for b in os.getenv("UNK_SHARP_BOOKS", "pinnacle,betfair_ex_eu,circasports").split(",") if b.strip()]
CACHE_SECS = int(os.getenv("UNK_ODDS_CACHE_SECS", "300"))
KEYS = {"nfl": "americanfootball_nfl", "cfb": "americanfootball_ncaaf", "nba": "basketball_nba",
        "wnba": "basketball_wnba", "ncaab": "basketball_ncaab", "mlb": "baseball_mlb", "nhl": "icehockey_nhl"}
MARKET = {"ml": "h2h", "spread": "spreads", "total": "totals"}
_cache = {}


def available():
    return bool(os.getenv("ODDS_API_KEY"))


def _odds(sport):
    hit = _cache.get(sport)
    if hit and time.time() - hit[0] < CACHE_SECS:
        return hit[1]
    r = requests.get(f"{BASE}/sports/{KEYS[sport]}/odds", timeout=15, params={
        "apiKey": os.getenv("ODDS_API_KEY"), "regions": REGIONS, "markets": "h2h,spreads,totals", "oddsFormat": "american"})
    r.raise_for_status()
    log.info("odds api %s: remaining %s", sport, r.headers.get("x-requests-remaining"))
    _cache[sport] = (time.time(), r.json())
    return _cache[sport][1]


def _game(sport, home_name, away_name):
    for g in _odds(sport):
        if g["home_team"] == home_name and g["away_team"] == away_name:
            return g
    for g in _odds(sport):  # loose match on nickname
        if home_name.split()[-1] in g["home_team"] and away_name.split()[-1] in g["away_team"]:
            return g
    return None


def shop(sport, home_name, away_name, market, side_name, line=None):
    """Best available price for one side, plus Pinnacle's no-vig fair probability when it's posted.

    side_name: full team name for ml/spread, 'Over'/'Under' for totals.
    """
    if not available() or sport not in KEYS:
        return None
    g = _game(sport, home_name, away_name)
    if not g:
        return None
    best, fairs = None, {}
    for bk in g.get("bookmakers", []):
        for m in bk.get("markets", []):
            if m["key"] != MARKET[market]:
                continue
            outs = m["outcomes"]
            mine = next((o for o in outs if o["name"] == side_name and (line is None or o.get("point") == line)), None)
            if not mine:
                continue
            if best is None or sharp.to_decimal(mine["price"]) > sharp.to_decimal(best["price"]):
                best = {"book": bk["title"], "price": mine["price"], "point": mine.get("point")}
            if bk["key"] in SHARP_BOOKS and len(outs) == 2:
                fairs[bk["key"]] = sharp.devig([o["price"] for o in outs])[outs.index(mine)]
    # sharpest book that actually posted this number wins
    src = next((b for b in SHARP_BOOKS if b in fairs), None)
    return {"best": best, "sharp_fair": fairs.get(src), "sharp_book": src}
