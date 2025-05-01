import pytest
from stockapp.models.stock_model import Stocks
from stockapp.models.portfolio_model import PortfolioModel
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

def test_buy_stock_updates_portfolio(mock_stock_price, mock_commit, mock_add):
    portfolio = PortfolioModel()
    portfolio.cash_balance=1000.0
    portfolio.holdings = {}

    Stocks.buy_stock("AAPL", 5, portfolio)

    assert portfolio.cash_balance == 500.0
    assert portfolio.holdings["AAPL"] == 5

def test_sell_stock_updates_portfolio(mock_stock_price, mock_commit, mock_add):
    stock = Stocks(symbol="AAPL", number_shares=5, purchase_price=100.0, total_cost=500.0)

    portfolio = PortfolioModel()
    portfolio.cash_balance = 100.0
    portfolio.holdings = {"AAPL": 5}

    Stocks.sell_stock("AAPL", 2, portfolio)

    assert portfolio.cash_balance == 300.0  # +200 from selling 2 shares at $100 each
    assert portfolio.holdings["AAPL"] == 3

def test_sell_more_than_owned_raises(mock_stock_price, mock_rollback):
    stock = Stocks(symbol="AAPL", number_shares=3, purchase_price=100.0, total_cost=300.0)

    portfolio = PortfolioModel()
    portfolio.cash_balance=100.0
    portfolio.holdings = {"AAPL": 3}

    with pytest.raises(ValueError, match="Cannot sell more shares than owned"):
        Stocks.sell_stock("AAPL", 5, portfolio)