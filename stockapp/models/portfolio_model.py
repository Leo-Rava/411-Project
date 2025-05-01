import logging
import os
import time
from typing import Dict

from models.stock_model import Stocks
from utils.logger import configure_logger
from utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class PortfolioModel:
    """
    A class to manage a user's stock portfolio

    Responsibilities:
    - Display the user's current stock holdings, including quantity, current price of each stock,
      and the total value of each holding, culminating in an overall portfolio value
    - Calculate the total portfolio value based on the latest market prices
    """

    def __init__(self):
        """Initializes the Portfolio with an empty dictionary of stock holdings

        Attributes:
            holdings (Dict[str, int]): Maps stock symbols to number of shares held
            _stock_cache (Dict[str, Stocks]): Caches stock data objects for quick access
            _ttl (Dict[str, float]): Tracks expiration times for cached stock data
            ttl_seconds (int): Time-to-live for each stock data entry in seconds
            cash_balance (float): Current available cash in the brokerage account
            original_cash_balance (float): Original deposited cash amount
        """
        self.holdings = {}
        self._stock_cache = {}
        self._ttl = {}
        self.ttl_seconds = int(os.environ.get("TTL_SECONDS", 60))
        self.cash_balance = 0.0 
        self.original_cash_balance = 0.0

    ##################################################
    ## Portfolio Retrieval Functions
    ##################################################

    def view_portfolio(self) -> Dict:
        """
        Displays the user's current portfolio holdings.

        Logic:
        - For each stock in holdings:
            - Fetch current price (from cache or DB)
            - Retrieve number of shares held
            - Calculate percentage change from original purchase price
        - Build and return a structured summary showing:
            - Stock symbol (ticker)
            - Shares held
            - Current stock price
            - Percentage change compared to buy price

        Returns:
            Dict: A structured summary of the user's portfolio, including
                  ticker, shares, current price, and percent change for each holding
        """
        summary = []

        for symbol, info in self.holdings.items():
            shares = info["shares"]
            buy_price = info["buy_price"]

            try:
                current_price = self._get_stock_from_cache_or_db(symbol)
                percent_change = ((current_price - buy_price) / buy_price) * 100
            except Exception:
                current_price = None
                percent_change = None

            summary.append({
                "symbol": symbol,
                "shares": shares,
                "buy_price": round(buy_price, 2),
                "current_price": round(current_price, 2) if current_price else "N/A",
                "percent_change": round(percent_change, 2) if percent_change else "N/A",
                "total_value": round(self._calculate_stock_value(symbol, shares), 2)
            })

        return {"portfolio": summary}


    def calculate_portfolio_value(self) -> Dict:
        """
        Calculates the total current value of the portfolio.

        Logic:
        - For each stock in holdings:
            - Fetch current price (from cache or DB)
            - Multiply shares by current price
            - Sum total value of all stock holdings
        - Add available cash balance from brokerage account
        - Calculate percentage change relative to original invested amount

        Returns:
        Dict - A summary including:
            - current_total_value (float): Portfolio value + cash
            - original_total_value (float): Original invested amount + cash
            - percent_change (float): Percentage change from original value
        """
        total_current_value = 0.0
        total_original_value = self.original_cash_balance

        for symbol, info in self.holdings.items():
            shares = info["shares"]
            buy_price = info["buy_price"]
            total_original_value += shares * buy_price

            try:
                stock_value = self._calculate_stock_value(symbol, shares)
                total_current_value += stock_value
            except Exception as e:
                logger.warning(f"Skipping {symbol} due to price fetch error: {e}")

        total_current_value += self.cash_balance

        try:
            percent_change = ((total_current_value - total_original_value) / total_original_value) * 100 if total_original_value > 0 else 0.0
        except ZeroDivisionError:
            percent_change = 0.0

        return {
            "current_total_value": round(total_current_value, 2),
            "original_total_value": round(total_original_value, 2),
            "percent_change": round(percent_change, 2)
        }

    ##################################################
    # Internal Helper Functions
    ##################################################

    def _get_stock_from_cache_or_db(self, symbol: str) -> float:
        """
        Retrieves a stock either from the internal cache or from the database.

        Args:
            symbol (str): The stock symbol to retrieve.

        Returns:
            Stocks: The stock object with current price information.
        """
        now = time.time()

        # Uses cached price if still valid
        if symbol in self._stock_cache and self._ttl.get(symbol, 0) > now:
            logger.debug(f"{symbol} price fetched from cache")
            return self._stock_cache[symbol]

        try:
            stock_data = Stocks.get_stock_price(symbol)
            current_price = stock_data["price"]

            # Cache it
            self._stock_cache[symbol] = current_price
            self._ttl[symbol] = now + self.ttl_seconds

            logger.info(f"{symbol} price fetched from API: ${current_price}")
            return current_price

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            raise

    def _calculate_stock_value(self, symbol: str, shares: int) -> float:
        """
        Calculates the total value of a given stock holding.

        Args:
            symbol (str): The stock symbol.
            shares (int): Number of shares held.

        Returns:
            float: The total value of the holding.
        """
        current_price = self._get_stock_from_cache_or_db(symbol)
        return shares * current_price


    def deposit_cash(self, amount: float) -> None:
        """
        Deposits cash into the brokerage account

        This increases both the current cash balance and the original cash balance
        Useful for simulating initial funding or manual deposits into the account

        Args:
            amount (float): The amount of cash to deposit (must be a positive number)

        Raises:
            ValueError: If the amount is not a positive number
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be a positive number.")
    
        self.cash_balance += amount
        self.original_cash_balance += amount
        logger.info(f"Deposited ${amount:.2f}. New balance: ${self.cash_balance:.2f}")

    def withdraw_cash(self, amount: float) -> None:
        """
        Withdraws cash from the brokerage account

        This decreases the current cash balance but does not affect the original cash balance
        Useful for simulating cash withdrawals after selling stocks or manual transfers

        Args:
            amount (float): The amount of cash to withdraw (must be positive and not exceed current balance)

        Raises:
            ValueError: If the amount is not positive or exceeds the current cash balance
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be a positive number.")
    
        if amount > self.cash_balance:
            raise ValueError("Withdrawal exceeds current cash balance.")
    
        self.cash_balance -= amount
        logger.info(f"Withdrew ${amount:.2f}. Remaining balance: ${self.cash_balance:.2f}")
