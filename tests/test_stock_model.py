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

@pytest.fixture
def sample_stock1(session):
    stock = Stocks()
    stock.symbol = "AAPL"
    stock.number_shares = 2
    stock.purchase_price=100.0
    stock.total_cost = 200.0
    session.add(stock)
    session.commit()
    return stock

def sample_stock2(session):
    stock = Stocks()
    stock.symbol = "AAPL"
    stock.number_shares = 5
    stock.purchase_price=100.0
    stock.total_cost = 500.0
    session.add(stock)
    session.commit()

    return stock

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

def test_real_commit(app, session):
    with app.app_context():
        # Clean up previous state
        Stocks.query.delete()
        session.commit()

        stock = Stocks(symbol="AAPL", number_shares=1, purchase_price=100.0, total_cost=100.0)
        session.add(stock)
        session.commit()

        result = Stocks.query.filter_by(symbol="AAPL").first()
        print("Found stock:", result)

        assert result is not None
        assert result.symbol == "AAPL"

def test_buy_stock_updates_portfolio(app, session, mock_stock_price):
    with app.app_context():
        # Set up portfolio
        portfolio = PortfolioModel()
        portfolio.cash_balance = 1000.0
        portfolio.holdings = {}

        # Buy stock
        Stocks.buy_stock("AAPL", 5, portfolio)

        # Validate portfolio updated
        assert portfolio.cash_balance == 500.0
        assert portfolio.holdings["AAPL"] == 5

        # Validate stock persisted to DB
        stock = Stocks.query.filter_by(symbol="AAPL").first()
        assert stock is not None
        assert stock.number_shares == 5

def test_sell_stock_updates_portfolio(app, session, mock_stock_price):
    with app.app_context():
        # Setup: Buy stock first
        portfolio = PortfolioModel()
        portfolio.cash_balance = 600.0
        portfolio.holdings = {}

        Stocks.buy_stock("AAPL", 5, portfolio)
        assert portfolio.holdings["AAPL"] == 5

        # Act: Sell 2 shares
        Stocks.sell_stock("AAPL", 2, portfolio)

        # Validate portfolio and DB updated
        assert portfolio.holdings["AAPL"] == 3
        assert round(portfolio.cash_balance, 2) == 300.0  # bought for 500, sold 2x100

        stock = Stocks.query.filter_by(symbol="AAPL").first()
        assert stock is not None
        assert stock.number_shares == 3

def test_sell_more_than_owned_raises(app, session, mock_stock_price):
    with app.app_context():
        # Setup: Buy 3 shares
        portfolio = PortfolioModel()
        portfolio.cash_balance = 500.0
        portfolio.holdings = {}

        Stocks.buy_stock("AAPL", 3, portfolio)
        assert portfolio.holdings["AAPL"] == 3

        # Attempt to oversell
        with pytest.raises(ValueError, match="Cannot sell more shares than owned"):
            Stocks.sell_stock("AAPL", 5, portfolio)

def test_buy_stock_insufficient_cash_raises(app, session, mock_stock_price):
    with app.app_context():
        portfolio = PortfolioModel()
        portfolio.cash_balance = 100.0  # Not enough to buy 5 shares at $100
        portfolio.holdings = {}

        with pytest.raises(ValueError, match="Cannot buy stock with less cash than owned"):
            Stocks.buy_stock("AAPL", 5, portfolio)

def test_sell_stock_not_owned_raises(app, session, mock_stock_price):
    with app.app_context():
        portfolio = PortfolioModel()
        portfolio.cash_balance = 500.0
        portfolio.holdings = {}

        with pytest.raises(ValueError, match="Cannot sell stock you don't own"):
            Stocks.sell_stock("AAPL", 1, portfolio)



def test_buy_existing_stock_accumulates(app, session, mock_stock_price):
    with app.app_context():
        portfolio = PortfolioModel()
        portfolio.cash_balance = 1000.0
        portfolio.holdings = {}

        Stocks.buy_stock("AAPL", 3, portfolio)
        Stocks.buy_stock("AAPL", 2, portfolio)

        stock = Stocks.query.filter_by(symbol="AAPL").first()

        assert stock.number_shares == 5
        assert round(portfolio.cash_balance, 2) == 500.0
        assert portfolio.holdings["AAPL"] == 5

def test_sell_all_shares_deletes_stock(app, session, mock_stock_price):
    with app.app_context():
        portfolio = PortfolioModel()
        portfolio.cash_balance = 500.0
        portfolio.holdings = {}

        Stocks.buy_stock("AAPL", 5, portfolio)
        Stocks.sell_stock("AAPL", 5, portfolio)

        stock = Stocks.query.filter_by(symbol="AAPL").first()
        assert stock is None
        assert "AAPL" in portfolio.holdings and portfolio.holdings["AAPL"] == 0

def test_lookup_invalid_stock_symbol_raises(mocker):
    mocker.patch("stockapp.models.stock_model.requests.get", return_value=mocker.Mock(json=lambda: {}))
    
    with pytest.raises(ValueError, match="No price data found for symbol 'INVALID'"):
        Stocks.get_stock_price("INVALID")
