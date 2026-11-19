import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

import sharp
import pick_ledger as pl


@pytest.mark.parametrize("method", ["multiplicative", "additive", "power", "shin"])
def test_devig_sums_to_one(method):
    assert sum(sharp.devig([-198, 164], method)) == pytest.approx(1, abs=1e-6)


def test_devig_even_market_is_fifty_fifty():
    for m in ("multiplicative", "power", "shin"):
        assert sharp.devig([-110, -110], m) == pytest.approx([0.5, 0.5], abs=1e-6)


def test_power_gives_longshot_less_than_multiplicative():
    # favorite-longshot bias: power shades the dog down vs a proportional split
    assert sharp.devig([-400, 300], "power")[1] < sharp.devig([-400, 300], "multiplicative")[1]


def test_american_round_trip():
    for a in (-250, -110, 100, 150, 400):
        assert sharp.to_american(sharp.implied(a)) == pytest.approx(a, abs=1) or a == 100


def test_kelly_zero_without_edge_and_capped():
    assert sharp.kelly(-110, 0.50) == 0
    assert sharp.kelly(+300, 0.90) == sharp.KELLY_CAP


def test_ev_and_clv():
    assert sharp.ev(+100, 0.55) == pytest.approx(0.10)
    assert sharp.clv(-105, 0.5) == pytest.approx(0.5 * (1 + 100 / 105) - 1)


def test_settle_markets():
    s = {"CIN": 33, "TB": 27}
    assert pl.settle("spread", "CIN", -3.5, s) == "win"
    assert pl.settle("spread", "CIN", -6, s) == "push"
    assert pl.settle("spread", "TB", 3.5, s) == "loss"
    assert pl.settle("total", "OVER", 50.5, s) == "win"
    assert pl.settle("ml", "TB", None, s) == "loss"


def test_closing_value_line_and_price():
    snap = {"home": "CIN", "away": "TB", "spread": -3.5, "home_spread_price": -112, "away_spread_price": -108,
            "total": 50.5, "over_price": -110, "under_price": -110, "home_ml": -198, "away_ml": 164}
    got_better = pl.closing_value({"market": "spread", "pick": "CIN", "line": -3.0, "price": -110}, snap)
    assert got_better["line_clv"] == pytest.approx(0.5) and got_better["clv"] is None
    # +180 vs a +164/-198 close is still -EV once the vig is out; +200 clears it
    assert pl.closing_value({"market": "ml", "pick": "TB", "line": None, "price": 180}, snap)["clv"] < 0
    assert pl.closing_value({"market": "ml", "pick": "TB", "line": None, "price": 200}, snap)["clv"] > 0
    over = pl.closing_value({"market": "total", "pick": "OVER", "line": 48.5, "price": -110}, snap)
    assert over["line_clv"] == pytest.approx(2.0)
