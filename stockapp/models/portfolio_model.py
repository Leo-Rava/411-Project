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
    A class to manage a user's stock portfolio.

    What this file should do:
    - Display the user's current stock holdings, including quantity, current price of each stock,
      and the total value of each holding, culminating in an overall portfolio value.
    - Calculate the total portfolio value based on the latest market prices.

    Reference:
    - PlaylistModel structure used as template.
    """

    def __init__(self):
        """Initializes the Portfolio with an empty dictionary of stock holdings.

        The portfolio starts empty.
        A TTL (time-to-live) cache system is set up to avoid hitting the stock API too frequently.
        TTL is set to 60 seconds by default, but can be overridden using the TTL_SECONDS environment variable.

        Attributes:
            holdings (Dict[str, int]): Maps stock symbols to number of shares held.
            _stock_cache (Dict[str, Stocks]): Caches stock data objects for quick access.
            _ttl (Dict[str, float]): Tracks expiration times for cached stock data.
            ttl_seconds (int): Time-to-live for each stock data entry in seconds.
        """
        self.holdings = {}
        self._stock_cache = {}
        self._ttl = {}
        self.ttl_seconds = int(os.environ.get("TTL_SECONDS", 60))

    ##################################################
    # Portfolio Management Functions
    ##################################################

    def view_portfolio(self) -> Dict:
        """
        Displays the user's current portfolio holdings.

        This will later:
        - Show each stock's symbol, quantity, latest price
        - Calculate and show the total value for each stock
        - Summarize the overall portfolio value

        Returns:
            Dict: A structured summary of the user's holdings.
        """
        pass

    def calculate_portfolio_value(self) -> float:
        """
        Calculates the current total value of the portfolio.

        This will later:
        - Fetch current stock prices from the Alpha Vantage API
        - Multiply shares * current price for each stock
        - Return the total value

        Returns:
            float: Total portfolio value.
        """
        pass
