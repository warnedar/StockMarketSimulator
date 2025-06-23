import pytest

from stock_market_simulator.utils.config_parser import parse_config_file
from stock_market_simulator.strategies.base_strategies import STRATEGY_MAP


def test_parse_config_file_basic(tmp_path):
    config_text = """\
    years=3
    stepsize=2
    approach=demo
        ticker=TEST, strategy=buy_hold, spread=0.5, expense_ratio=0.1
    """
    cfg = tmp_path / "cfg.txt"
    cfg.write_text(config_text)

    years, stepsize, approaches = parse_config_file(str(cfg))

    assert years == 3
    assert stepsize == 2
    assert len(approaches) == 1
    name, mapping = approaches[0]
    assert name == "demo"
    assert "TEST" in mapping
    entry = mapping["TEST"]
    assert entry["strategy"] is STRATEGY_MAP["buy_hold"]
    assert entry["spread"] == 0.5
    assert entry["expense_ratio"] == 0.1


def test_missing_years_or_stepsize(tmp_path):
    cfg1 = tmp_path / "cfg1.txt"
    cfg1.write_text(
        """\
        stepsize=1
        approach=demo
            ticker=TEST, strategy=buy_hold
        """
    )
    with pytest.raises(ValueError):
        parse_config_file(str(cfg1))

    cfg2 = tmp_path / "cfg2.txt"
    cfg2.write_text(
        """\
        years=5
        approach=demo
            ticker=TEST, strategy=buy_hold
        """
    )
    with pytest.raises(ValueError):
        parse_config_file(str(cfg2))
