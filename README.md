Description:

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
