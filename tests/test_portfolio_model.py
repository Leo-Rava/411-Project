import pytest
from stockapp.models.portfolio_model import PortfolioModel

# Sample portfolio fixture for reuse across tests
@pytest.fixture
def portfolio():
    model = PortfolioModel()
    model.holdings = {
        "AAPL": {"shares": 5, "buy_price": 150.0},
        "MSFT": {"shares": 2, "buy_price": 300.0}
    }
    model.cash_balance = 1000.0
    model.original_cash_balance = 1000.0
    return model

# Mock prices to avoid hitting the Alpha Vantage API
@pytest.fixture
def mock_price_cache(mocker):
    return mocker.patch(
        "stockapp.models.portfolio_model.PortfolioModel._get_stock_from_cache_or_db",
        side_effect=lambda symbol: 170.0 if symbol == "AAPL" else 320.0
    )

# Basic test to make sure view_portfolio() returns all expected fields
def test_view_portfolio_basic(portfolio, mock_price_cache):
    result = portfolio.view_portfolio()
    assert "portfolio" in result
    assert len(result["portfolio"]) == 2
    assert result["portfolio"][0]["symbol"] == "AAPL"
    assert result["portfolio"][0]["current_price"] == 170.0
    assert "percent_change" in result["portfolio"][0]

# Checks that portfolio value is calculated correctly including cash and % change
def test_calculate_portfolio_value(portfolio, mock_price_cache):
    result = portfolio.calculate_portfolio_value()

    # Verify the expected keys exist
    assert "current_total_value" in result
    assert "original_total_value" in result
    assert "percent_change" in result

    # Manually compute expected values
    expected_current_value = (5 * 170.0) + (2 * 320.0) + 1000.0
    expected_original_value = (5 * 150.0) + (2 * 300.0) + 1000.0
    expected_percent = ((expected_current_value - expected_original_value) / expected_original_value) * 100

    # Make sure the output is accurate
    assert round(result["current_total_value"], 2) == round(expected_current_value, 2)
    assert round(result["original_total_value"], 2) == round(expected_original_value, 2)
    assert round(result["percent_change"], 2) == round(expected_percent, 2)

# Test for depositing cash correctly
def test_deposit_cash_valid(portfolio):
    portfolio.deposit_cash(500)
    assert portfolio.cash_balance == 1500.0
    assert portfolio.original_cash_balance == 1500.0

# Test for valid withdrawal
def test_withdraw_cash_valid(portfolio):
    portfolio.withdraw_cash(300)
    assert portfolio.cash_balance == 700.0

# Should raise error if trying to withdraw more than available
def test_withdraw_cash_exceeds_balance_raises(portfolio):
    with pytest.raises(ValueError):
        portfolio.withdraw_cash(2000)

# Should raise error if trying to deposit a negative amount
def test_deposit_negative_cash_raises(portfolio):
    with pytest.raises(ValueError):
        portfolio.deposit_cash(-100)
