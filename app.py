from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import ProductionConfig

from stockapp.db import db
from stockapp.models.stock_model import Stocks
from stockapp.models.portfolio_model import PortfolioModel
from stockapp.models.user_model import Users
from stockapp.utils.logger import configure_logger


load_dotenv()

def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    configure_logger(app.logger)

    app.config.from_object(config_class)

    db.init_app(app)  # Initialize db with app
    with app.app_context():
        db.create_all()  # Recreate all tables

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.filter_by(username=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        return make_response(jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401)

    portfolio_model = PortfolioModel()

    ####################################################
    #
    # Healthchecks
    #
    ####################################################

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """
        Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.
        """
        app.logger.info("Health check endpoint hit")
        return make_response(jsonify({
            'status': 'success',
            'message': 'Service is running'
        }), 200)

    ##########################################################
    #
    # User Management
    #
    #########################################################

    @app.route('/api/create-user', methods=['PUT'])
    def create_user() -> Response:
        """Register a new user account.

        Expected JSON Input:
            - username (str): The desired username.
            - password (str): The desired password.

        Returns:
            JSON response indicating the success of the user creation.

        Raises:
            400 error if the username or password is missing.
            500 error if there is an issue creating the user in the database.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            Users.create_user(username, password)
            return make_response(jsonify({
                "status": "success",
                "message": f"User '{username}' created successfully"
            }), 201)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"User creation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating user",
                "details": str(e)
            }), 500)

    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """Authenticate a user and log them in.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The password of the user.

        Returns:
            JSON response indicating the success of the login attempt.

        Raises:
            401 error if the username or password is incorrect.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                return make_response(jsonify({
                    "status": "success",
                    "message": f"User '{username}' logged in successfully"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid username or password"
                }), 401)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 401)
        except Exception as e:
            app.logger.error(f"Login failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred during login",
                "details": str(e)
            }), 500)

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout() -> Response:
        """Log out the current user.

        Returns:
            JSON response indicating the success of the logout operation.
        """
        logout_user()
        return make_response(jsonify({
            "status": "success",
            "message": "User logged out successfully"
        }), 200)

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def change_password() -> Response:
        """Change the password for the current user.

        Expected JSON Input:
            - new_password (str): The new password to set.

        Returns:
            JSON response indicating the success of the password change.

        Raises:
            400 error if the new password is not provided.
            500 error if there is an issue updating the password in the database.
        """
        try:
            data = request.get_json()
            new_password = data.get("new_password")

            if not new_password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "New password is required"
                }), 400)

            username = current_user.username
            Users.update_password(username, new_password)
            return make_response(jsonify({
                "status": "success",
                "message": "Password changed successfully"
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Password change failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing password",
                "details": str(e)
            }), 500)

    @app.route('/api/reset-users', methods=['DELETE'])
    def reset_users() -> Response:
        """Recreate the users table to delete all users.

        Returns:
            JSON response indicating the success of recreating the Users table.

        Raises:
            500 error if there is an issue recreating the Users table.
        """
        try:
            app.logger.info("Received request to recreate Users table")
            with app.app_context():
                Users.__table__.drop(db.engine)
                Users.__table__.create(db.engine)
            app.logger.info("Users table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Users table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Users table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Stocks
    #
    ##########################################################

    @app.route('/api/reset-stocks', methods=['DELETE'])
    def reset_stocks() -> Response:
        """Recreate the stocks table to delete stocks.

        Returns:
            JSON response indicating the success of recreating the Stocks table.

        Raises:
            500 error if there is an issue recreating the Stocks table.
        """
        try:
            app.logger.info("Received request to recreate Stocks table")
            with app.app_context():
                Stocks.__table__.drop(db.engine)
                Stocks.__table__.create(db.engine)
            app.logger.info("Stocks table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Stocks table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Stocks table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting stocks",
                "details": str(e)
            }), 500)

    @app.route('/api/lookup-stock/<string:symbol>', methods=['GET'])
    @login_required
    def lookup_stock(symbol: str) -> Response:
        """Route to look up stock information by symbol.

        Path Parameter:
            - symbol (str): The stock symbol to look up.

        Returns:
            JSON response containing the stock details if found.

        Raises:
            400 error if the stock is not found.
            500 error if there is an issue retrieving the stock information.
        """
        try:
            app.logger.info(f"Received request to look up stock with symbol '{symbol}'")

            stock_info = Stocks.look_up_stock(symbol)

            app.logger.info(f"Successfully retrieved stock info for {symbol}")
            return make_response(jsonify({
                "status": "success",
                "stock": stock_info
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Stock lookup failed for {symbol}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Error looking up stock {symbol}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while looking up the stock",
                "details": str(e)
            }), 500)

    ############################################################
    #
    # Portfolio
    #
    ############################################################

    @app.route('/api/deposit-cash', methods=['POST'])
    @login_required
    def deposit_cash() -> Response:
        """Route to deposit cash into the portfolio.

        Expected JSON Input:
            - amount (float): The amount to deposit.

        Returns:
            JSON response indicating the success of the deposit.

        Raises:
            400 error if the amount is invalid.
            500 error if there is an issue processing the deposit.
        """
        try:
            data = request.get_json()
            amount = data.get("amount")

            if not amount or amount <= 0:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Amount must be a positive number"
                }), 400)

            portfolio_model.deposit_cash(float(amount))
            return make_response(jsonify({
                "status": "success",
                "message": f"Successfully deposited ${amount:.2f}",
                "new_balance": portfolio_model.cash_balance
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Error depositing cash: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while processing deposit",
                "details": str(e)
            }), 500)

    @app.route('/api/withdraw-cash', methods=['POST'])
    @login_required
    def withdraw_cash() -> Response:
        """Route to withdraw cash from the portfolio.

        Expected JSON Input:
            - amount (float): The amount to withdraw.

        Returns:
            JSON response indicating the success of the withdrawal.

        Raises:
            400 error if the amount is invalid or exceeds balance.
            500 error if there is an issue processing the withdrawal.
        """
        try:
            data = request.get_json()
            amount = data.get("amount")

            if not amount or amount <= 0:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Amount must be a positive number"
                }), 400)

            portfolio_model.withdraw_cash(float(amount))
            return make_response(jsonify({
                "status": "success",
                "message": f"Successfully withdrew ${amount:.2f}",
                "new_balance": portfolio_model.cash_balance
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Error withdrawing cash: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while processing withdrawal",
                "details": str(e)
            }), 500)

    @app.route('/api/buy-stock', methods=['POST'])
    @login_required
    def buy_stock() -> Response:
        """Route to buy a stock and add it to the portfolio.

        Expected JSON Input:
            - symbol (str): The stock symbol to buy.
            - shares (int): The number of shares to buy.

        Returns:
            JSON response indicating the success of the purchase.

        Raises:
            400 error if the input is invalid or insufficient funds.
            500 error if there is an issue processing the purchase.
        """
        try:
            data = request.get_json()
            symbol = data.get("symbol")
            shares = data.get("shares")

            if not symbol or not shares:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Symbol and shares are required"
                }), 400)

            if shares <= 0:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Shares must be a positive number"
                }), 400)

            # Get current price
            stock_info = Stocks.get_stock_price(symbol)
            total_cost = stock_info["price"] * shares

            # Check if user has enough cash
            if total_cost > portfolio_model.cash_balance:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Insufficient funds for this purchase"
                }), 400)

            # Process the purchase
            Stocks.buy_stock(symbol, shares)
            portfolio_model.withdraw_cash(total_cost)

            # Update holdings in portfolio model
            if symbol in portfolio_model.holdings:
                portfolio_model.holdings[symbol]["shares"] += shares
            else:
                portfolio_model.holdings[symbol] = {
                    "shares": shares,
                    "buy_price": stock_info["price"]
                }

            return make_response(jsonify({
                "status": "success",
                "message": f"Successfully bought {shares} shares of {symbol} at ${stock_info['price']:.2f} per share",
                "total_cost": total_cost,
                "remaining_balance": portfolio_model.cash_balance
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Error buying stock: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while processing purchase",
                "details": str(e)
            }), 500)

    @app.route('/api/sell-stock', methods=['POST'])
    @login_required
    def sell_stock() -> Response:
        """Route to sell a stock from the portfolio.

        Expected JSON Input:
            - symbol (str): The stock symbol to sell.
            - shares (int): The number of shares to sell.

        Returns:
            JSON response indicating the success of the sale.

        Raises:
            400 error if the input is invalid or insufficient shares.
            500 error if there is an issue processing the sale.
        """
        try:
            data = request.get_json()
            symbol = data.get("symbol")
            shares = data.get("shares")

            if not symbol or not shares:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Symbol and shares are required"
                }), 400)

            if shares <= 0:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Shares must be a positive number"
                }), 400)

            # Check if user owns enough shares
            if symbol not in portfolio_model.holdings or portfolio_model.holdings[symbol]["shares"] < shares:
                return make_response(jsonify({
                    "status": "error",
                    "message": f"You don't own enough shares of {symbol} to sell"
                }), 400)

            # Get current price
            stock_info = Stocks.get_stock_price(symbol)
            total_proceeds = stock_info["price"] * shares

            # Process the sale
            Stocks.sell_stock(symbol, shares)
            portfolio_model.deposit_cash(total_proceeds)

            # Update holdings in portfolio model
            portfolio_model.holdings[symbol]["shares"] -= shares
            if portfolio_model.holdings[symbol]["shares"] == 0:
                del portfolio_model.holdings[symbol]

            return make_response(jsonify({
                "status": "success",
                "message": f"Successfully sold {shares} shares of {symbol} at ${stock_info['price']:.2f} per share",
                "total_proceeds": total_proceeds,
                "new_balance": portfolio_model.cash_balance
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Error selling stock: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while processing sale",
                "details": str(e)
            }), 500)

    @app.route('/api/view-portfolio', methods=['GET'])
    @login_required
    def view_portfolio() -> Response:
        """Route to view the current portfolio holdings and value.

        Returns:
            JSON response containing the portfolio details and valuation.
        """
        try:
            portfolio_summary = portfolio_model.view_portfolio()
            portfolio_value = portfolio_model.calculate_portfolio_value()

            return make_response(jsonify({
                "status": "success",
                "holdings": portfolio_summary,
                "portfolio_value": portfolio_value,
                "cash_balance": portfolio_model.cash_balance
            }), 200)

        except Exception as e:
            app.logger.error(f"Error viewing portfolio: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving portfolio",
                "details": str(e)
            }), 500)

    return app

if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        app.logger.error(f"Flask app encountered an error: {e}")
    finally:
        app.logger.info("Flask app has stopped.")