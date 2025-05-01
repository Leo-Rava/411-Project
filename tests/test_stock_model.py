import pytest
from stockapp.models.stock_model import Stocks
from stockapp.db import db


@pytest.fixture
def mock_stock_price(mocker):
    return mocker.patch(
        "stockapp.models.stock_model.Stocks.get_stock_price",
        return_value={"price": 100.0}
    )


@pytest.fixture
def mock_commit(mocker):
    return mocker.patch("stockapp.models.stock_model.db.session.commit")


@pytest.fixture
def mock_add(mocker):
    return mocker.patch("stockapp.models.stock_model.db.session.add")


@pytest.fixture
def mock_rollback(mocker):
    return mocker.patch("stockapp.models.stock_model.db.session.rollback")


def test_look_up_stock_success(mocker):
    # Setup mock chain of responses
    mock_get = mocker.patch("stockapp.models.stock_model.requests.get")

    mock_get.side_effect = [
        mocker.Mock(json=lambda: {
            "Global Quote": {"05. price": "150.0"}
        }),
        mocker.Mock(json=lambda: {
            "Name": "Apple Inc.",
            "Description": "Tech company",
            "Sector": "Technology"
        }),
        mocker.Mock(json=lambda: {
            "Time Series (Daily)": {
                "2025-04-30": {
                    "1. open": "145.0",
                    "2. high": "151.0",
                    "3. low": "144.0",
                    "4. close": "150.0",
                    "6. volume": "100000"
                }
            }
        }),
    ]

    result = Stocks.look_up_stock("AAPL")

    assert result["symbol"] == "AAPL"
    assert result["name"] == "Apple Inc."
    assert result["current_price"] == 150.0
    assert "historical_prices" in result
    assert isinstance(result["historical_prices"], list)


def test_look_up_stock_invalid_symbol_raises(mocker):
    mocker.patch("stockapp.models.stock_model.requests.get", return_value=mocker.Mock(json=lambda: {"Global Quote": {}}))

    with pytest.raises(ValueError, match="No current price found for 'AAPL'"):
        Stocks.look_up_stock("AAPL")
