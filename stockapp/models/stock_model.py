import logging
import requests

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from stockapp.db import db
from stockapp.utils.logger import configure_logger
from stockapp.utils.api_utils import get_random

import os


api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

logger = logging.getLogger(__name__)
configure_logger(logger)

#   Note: I think looking at the playlist model would be best. It is most similar to what we
#   are trying to do. 


class Stocks(db.Model):
    """Represents a stock in the catalog.

    Provides detailed information about a specific stock, including its current market
    price, historical price data, and a brief description of the company.

    Used in a Flask-SQLAlchemy application for playlist management,
    user interaction, and data-driven song operations.
    """

    __tablename__ = "Stocks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String, nullable=False)
    number_shares = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)  # Price per share
    total_cost = db.Column(db.Float, nullable=False)      # Total cost at purchase


    def validate(self) -> None:
        """Validates the song instance before committing to the database.

        Raises:
            ValueError: If any required fields are invalid.
        """
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("Stock must be a non-empty string.")
        if not isinstance(self.number_shares, int) or self.number_shares <= 0:
            raise ValueError("number_shares must be an integer > 0")
    
    ##################################################
    ## Stocks Retrieval Functions
    ##################################################

    @classmethod
    def buy_stock(cls, symbol: str, number_shares: int) -> None:
        """
        Buys a new stock in the stocks table using SQLAlchemy.

        Args:
            symbol (str): The stocks symbol.
            number_shares (int): number of shares the user wishes to buy.

        Raises:
            ValueError: If any field is invalid or if a song with the same compound key already exists.
            SQLAlchemyError: For any other database-related issues.
        """
        try:
            symbol = symbol.upper()
            if number_shares <= 0:
                raise ValueError("Number of shares must be greater than 0")

            # Lookup price using Alpha Vantage
            stock_info = cls.get_stock_price(symbol)
            price = stock_info["price"]
            total_cost = price * number_shares

            # Check if stock already exists
            stock = cls.query.filter_by(symbol=symbol).first()
            if stock:
                # Average cost update (optional: keep it simple here)
                total_shares = stock.number_shares + number_shares
                new_total_cost = stock.total_cost + total_cost
                new_avg_price = new_total_cost / total_shares

                stock.number_shares = total_shares
                stock.total_cost = new_total_cost
                stock.purchase_price = new_avg_price
            else:
                new_stock = cls(
                    symbol=symbol,
                    number_shares=number_shares,
                    purchase_price=price,
                    total_cost=total_cost
                )
                new_stock.validate()
                db.session.add(new_stock)

            db.session.commit()
            logger.info(f"Bought {number_shares} shares of {symbol} at ${price:.2f} per share (Total: ${total_cost:.2f})")

        except (ValueError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Error buying stock {symbol}: {str(e)}")
            raise

    @classmethod
    def sell_stock(cls, symbol: str, number_shares: int) -> None:
        """
        Permanently sells stock from the portfolio its symbol.

        Args:
            symbol (str): The symbol of the stock to sell
            number_shares (int): Number of shares of specified stock to sell

        Raises:
            ValueError: If the stock with the given symbol does not exist.
            SQLAlchemyError: For any database-related issues.
        """
        try:
            symbol = symbol.upper()
            if number_shares <= 0:
                raise ValueError("Number of shares must be greater than 0")

            stock = cls.query.filter_by(symbol=symbol).first()
            if not stock:
                raise ValueError(f"No stock with symbol {symbol} found in portfolio")
            
            if stock.number_shares < number_shares:
                raise ValueError(f"Cannot sell more shares than owned")
            
            # Lookup price using Alpha Vantage
            stock_info = cls.get_stock_price(symbol)
            price = stock_info["price"]
            total_cost = price * number_shares

            # Check if stock already exists
            # Average cost update (optional: keep it simple here)
            total_shares = stock.number_shares - number_shares
            new_total_cost = stock.total_cost - total_cost
            new_avg_price = new_total_cost / total_shares

            stock.number_shares -= number_shares
            stock.total_cost = new_total_cost
            stock.purchase_price = new_avg_price
            if stock.number_shares == 0:
                db.session.delete(stock)

            db.session.commit()
            logger.info(f"Sold {number_shares} shares of {symbol} at ${price:.2f} per share (Total: ${total_cost:.2f})")

        except (ValueError, SQLAlchemyError) as e:
            db.session.rollback()
            logger.error(f"Error selling stock {symbol}: {str(e)}")
            raise


    @classmethod
    def look_up_stock(cls, symbol: str) -> dict:
        try:
            symbol = symbol.upper()

            # Current price
            quote_url = (
                f"https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            )
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json().get("Global Quote", {})

            if "05. price" not in quote_data:
                raise ValueError(f"No current price found for '{symbol}'.")

            current_price = float(quote_data["05. price"])

            # Company info
            overview_url = (
                f"https://www.alphavantage.co/query"
                f"?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
            )
            overview_response = requests.get(overview_url)
            overview_data = overview_response.json()

            if "Name" not in overview_data:
                raise ValueError(f"No company info found for '{symbol}'.")

            # Historical price data (last 7 days)
            history_url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}"
            )
            history_response = requests.get(history_url)
            history_data = history_response.json().get("Time Series (Daily)", {})

            # Convert history to recent 7-day list of prices
            recent_history = []
            for date, daily_data in list(history_data.items())[:7]:
                recent_history.append({
                    "date": date,
                    "open": float(daily_data["1. open"]),
                    "high": float(daily_data["2. high"]),
                    "low": float(daily_data["3. low"]),
                    "close": float(daily_data["4. close"]),
                    "volume": int(daily_data["6. volume"]),
                })

            return {
                "symbol": symbol,
                "name": overview_data.get("Name"),
                "description": overview_data.get("Description"),
                "sector": overview_data.get("Sector"),
                "current_price": current_price,
                "historical_prices": recent_history
            }
        except Exception as e:
            logger.error(f"Error looking up stock {symbol}: {str(e)}")
            raise

    ##################################################
    ## Stocks Helper Functions
    ##################################################

    @classmethod
    def get_stock_price(cls, symbol: str) -> dict:
        """
        Provides details about specific stock from its symbol

        Args:
            symbol (str): Symbol of stock user wishes to look up

        Raises: 
            ValueError: If the stock with given symbol does not exist
            SQLAlchemyError: For any database-related issues.
        """
        try:
            symbol = symbol.upper()
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            )
            response = requests.get(url)
            data = response.json()

            quote = data.get("Global Quote")
            if not quote or "05. price" not in quote:
                raise ValueError(f"No price data found for symbol '{symbol}'.")

            return {
                "symbol": symbol,
                "price": float(quote["05. price"]),
                "volume": int(quote["06. volume"]),
                "latest_trading_day": quote["07. latest trading day"],
            }

        except Exception as e:
            logger.error(f"Error looking up stock {symbol}: {str(e)}")
            raise
