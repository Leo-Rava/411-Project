Description: A RESTful API for managing stock portfolios with user authentication, stock trading, and portfolio tracking capabilities.
This API provides a complete solution for:
- User account creation and authentication
- Stock lookup and trading
- Portfolio management including buying/selling stocks
- Cash deposit/withdrawal functionality
- Portfolio valuation and performance tracking

List of all routes:
- Route: ```/create-account```
  - Request Type: POST
  - Purpose: Creates a new user account with a username and password.
    - Request Body:
      - username (String): User's chosen username.
      - password (String): User's chosen password.
    - Response Format: JSON
      - Success Response Example:
      - Code: 200
      - Content: { "message": "Account created successfully" }
    - Example Request:
  ```
  {
    "username": "newuser123",
    "password": "securepassword"
  }
  ```
  
    - Example Response:
  ```
  {
  "message": "Account created successfully",
  "status": "200"
  }
  ```

- Route: `/api/login`
  - Request Type: POST
  - Purpose: Authenticates a user and creates a session
    - Request Body:
      - username (String): Registered username
      - password (String): User's password
    - Response Format: JSON
    - Success Response:
      - Code: 200
      - Content:
```
{
  "status": "success",
  "message": "User 'username' logged in successfully"
}
```
  - Example Request:
```
{
  "username": "investor1",
  "password": "SecurePass123!"
}
```
- Route: `/api/logout`
  - Request Type: POST
  - Purpose: Ends the current user session
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "User logged out successfully"
}
```
- Route: `/api/change-password`
  - Request Type: POST
  - Purpose: Changes the current user's password
  - Request Body:
    - new_password (String): New password
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Password changed successfully"
}
```
- Route: `/api/reset-users`
  - Request Type: DELETE
  - Purpose: Resets all user data
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Users table recreated successfully"
}
```

- Route: `/api/lookup-stock/<symbol>`
  - Request Type: GET
  - Authentication Required: Yes
  - Purpose: Retrieves detailed information about a stock
  - Request Body:
    - symbol (String): Stock ticker symbol (e.g., "AAPL")
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "stock": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "current_price": 175.34,
    "historical_prices": [...]
  }
}
```
- Route: `/api/reset-stocks`
  - Request Type: DELETE
  - Purpose: Resets all stock data (development only)
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Stocks table recreated successfully"
}
```

- Route: `/api/deposit-cash`
  - Request Type: POST
  - Purpose: Deposits cash into the portfolio
  - Request Body:
    - amount (Float): Deposit amount (must be positive)
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Successfully deposited $1000.00",
  "new_balance": 1500.00
}
```
- Route: `/api/withdraw-cash`
  - Request Type: POST
  - Purpose: Withdraws cash from the portfolio
  - Request Body:
    - amount (Float): Withdrawal amount (must be positive)
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Successfully withdrew $500.00",
  "new_balance": 1000.00
}
```
- Route: `/api/buy-stock`
  - Request Type: POST
  - Purpose: Purchases shares of a stock
  - Request Body:
    - symbol (String): Stock ticker symbol
    - shares (Integer): Number of shares to buy
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Successfully bought 10 shares of AAPL at $175.34 per share",
  "total_cost": 1753.40,
  "remaining_balance": 246.60
}
```
- Route: `/api/sell-stock`
  - Request Type: POST
  - Purpose: Sells shares of a stock
  - Request Body:
    - symbol (String): Stock ticker symbol
    - shares (Integer): Number of shares to sell
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "message": "Successfully sold 5 shares of AAPL at $178.50 per share",
  "total_proceeds": 892.50,
  "new_balance": 1138.50
}
```
- Route: `/api/view-portfolio`
  - Request Type: GET
  - Purpose: Retrieves the current portfolio holdings and valuation
  - Response Format: JSON
  - Success Response:
    - Code: 200
    - Content:
```
{
  "status": "success",
  "holdings": [
    {
      "symbol": "AAPL",
      "shares": 10,
      "buy_price": 175.34,
      "current_price": 178.50,
      "percent_change": 1.80,
      "total_value": 1785.00
    }
  ],
  "portfolio_value": {
    "current_total_value": 3285.00,
    "original_total_value": 3253.40,
    "percent_change": 0.97
  },
  "cash_balance": 1500.00
}
```
