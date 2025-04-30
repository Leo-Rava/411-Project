import pytest
from stockapp.models.stock_model import Stocks
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def sample_stock():
    return Stocks(symbol="AAPL", number_shares=10, purchase_price=150.00, total_cost=1500.00)


@pytest.fixture
def mock_quote_response(mocker):
    return mocker.patch("stockapp.models.stock_model.Stocks.get_stock_price", return_value={
        "symbol": "AAPL",
        "price": 150.00,
        "volume": 1000000,
        "latest_trading_day": "2025-04-25"
    })


@pytest.fixture
def mock_lookup_response(mocker):
    return mocker.patch("stockapp.models.stock_model.Stocks.look_up_stock", return_value={
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "description": "Apple designs, manufactures, and sells consumer electronics.",
        "sector": "Technology",
        "current_price": 150.00,
        "historical_prices": [
            {"date": "2025-04-26", "open": 148.0, "high": 151.0, "low": 147.0, "close": 150.0, "volume": 100000}
        ]
    })


##########################################################
# Buy Stock
##########################################################

def test_buy_stock_adds_new_entry(session, mock_quote_response):
    Stocks.buy_stock("AAPL", 5)
    stock = session.query(Stocks).filter_by(symbol="AAPL").first()

    assert stock is not None, "Stock entry should be created"
    assert stock.number_shares == 5
    assert stock.purchase_price == 150.00
    assert stock.total_cost == 750.00


def test_buy_stock_updates_existing_entry(session, mock_quote_response):
    # Create existing stock first
    stock = Stocks(symbol="AAPL", number_shares=5, purchase_price=150.00, total_cost=750.00)
    session.add(stock)
    session.commit()

    Stocks.buy_stock("AAPL", 5)

    updated_stock = session.query(Stocks).filter_by(symbol="AAPL").first()
    assert updated_stock.number_shares == 10
    assert round(updated_stock.purchase_price, 2) == 150.00
    assert updated_stock.total_cost == 1500.00


def test_buy_stock_invalid_shares_raises():
    with pytest.raises(ValueError):
        Stocks.buy_stock("AAPL", 0)


##########################################################
# Sell Stock
##########################################################

def test_sell_stock_reduces_shares(session, mock_quote_response):
    stock = Stocks(symbol="AAPL", number_shares=10, purchase_price=150.00, total_cost=1500.00)
    session.add(stock)
    session.commit()

    Stocks.sell_stock("AAPL", 5)

    updated_stock = session.query(Stocks).filter_by(symbol="AAPL").first()
    assert updated_stock.number_shares == 5
    assert updated_stock.total_cost == 750.00


def test_sell_stock_deletes_entry(session, mock_quote_response):
    stock = Stocks(symbol="AAPL", number_shares=5, purchase_price=150.00, total_cost=750.00)
    session.add(stock)
    session.commit()

    Stocks.sell_stock("AAPL", 5)

    deleted_stock = session.query(Stocks).filter_by(symbol="AAPL").first()
    assert deleted_stock is None, "Stock should be deleted when shares go to zero"


def test_sell_more_than_owned_raises(session, mock_quote_response):
    stock = Stocks(symbol="AAPL", number_shares=2, purchase_price=150.00, total_cost=300.00)
    session.add(stock)
    session.commit()

    with pytest.raises(ValueError):
        Stocks.sell_stock("AAPL", 3)


##########################################################
# Look Up Stock
##########################################################

def test_lookup_returns_full_data(mock_lookup_response):
    result = Stocks.look_up_stock("AAPL")

    assert result["symbol"] == "AAPL"
    assert "description" in result
    assert "current_price" in result
    assert "historical_prices" in result
    assert isinstance(result["historical_prices"], list)