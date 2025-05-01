import requests


def run_smoketest():
    base_url = "http://localhost:5001/api" # Changed port to 5001
    username = "test_user"
    password = "test_password"

    test_stock_aapl = {
        "symbol": "AAPL",
        "shares": 10
    }

    test_stock_msft = {
        "symbol": "MSFT",
        "shares": 5
    }

    # Health check
    health_response = requests.get(f"{base_url}/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "success"
    print("Health check successful")

    # Reset users and stocks
    delete_user_response = requests.delete(f"{base_url}/reset-users")
    assert delete_user_response.status_code == 200
    assert delete_user_response.json()["status"] == "success"
    print("Reset users successful")

    delete_stocks_response = requests.delete(f"{base_url}/reset-stocks")
    assert delete_stocks_response.status_code == 200
    assert delete_stocks_response.json()["status"] == "success"
    print("Reset stocks successful")

    # Create user
    create_user_response = requests.put(f"{base_url}/create-user", json={
        "username": username,
        "password": password
    })
    assert create_user_response.status_code == 201
    assert create_user_response.json()["status"] == "success"
    print("User creation successful")

    session = requests.Session()

    # Log in
    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": password
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login successful")

    # Deposit cash
    deposit_resp = session.post(f"{base_url}/deposit-cash", json={
        "amount": 10000.00
    })
    assert deposit_resp.status_code == 200
    assert deposit_resp.json()["status"] == "success"
    print("Cash deposit successful")

    # Lookup stock (requires authentication)
    lookup_resp = session.get(f"{base_url}/lookup-stock/AAPL")
    assert lookup_resp.status_code == 200
    assert lookup_resp.json()["status"] == "success"
    print("Stock lookup successful")

    # Buy stock
    buy_stock_resp = session.post(f"{base_url}/buy-stock", json=test_stock_aapl)
    assert buy_stock_resp.status_code == 200
    assert buy_stock_resp.json()["status"] == "success"
    print("Stock purchase successful")

    # View portfolio
    portfolio_resp = session.get(f"{base_url}/view-portfolio")
    assert portfolio_resp.status_code == 200
    assert portfolio_resp.json()["status"] == "success"
    print("Portfolio view successful")

    # Change password
    change_password_resp = session.post(f"{base_url}/change-password", json={
        "new_password": "new_password"
    })
    assert change_password_resp.status_code == 200
    assert change_password_resp.json()["status"] == "success"
    print("Password change successful")

    # Log in with new password
    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": "new_password"
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login with new password successful")

    # Buy another stock
    buy_stock_resp = session.post(f"{base_url}/buy-stock", json=test_stock_msft)
    assert buy_stock_resp.status_code == 200
    assert buy_stock_resp.json()["status"] == "success"
    print("Second stock purchase successful")

    # Sell stock
    sell_stock_resp = session.post(f"{base_url}/sell-stock", json={
        "symbol": "AAPL",
        "shares": 5
    })
    assert sell_stock_resp.status_code == 200
    assert sell_stock_resp.json()["status"] == "success"
    print("Stock sale successful")

    # Withdraw cash
    withdraw_resp = session.post(f"{base_url}/withdraw-cash", json={
        "amount": 1000.00
    })
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.json()["status"] == "success"
    print("Cash withdrawal successful")

    # Log out
    logout_resp = session.post(f"{base_url}/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("Logout successful")

    # Attempt to buy stock while logged out (should fail)
    buy_stock_logged_out_resp = requests.post(f"{base_url}/buy-stock", json=test_stock_aapl)
    assert buy_stock_logged_out_resp.status_code == 401
    assert buy_stock_logged_out_resp.json()["status"] == "error"
    print("Stock purchase failed as expected when logged out")


if __name__ == "__main__":
    run_smoketest()