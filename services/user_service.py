"""
services/user_service.py - accounts: register and login.

Right now these use mock_data so the UI works on its own.
BACKEND INTEGRATION POINT: replace the BODY of each function with real code
(MySQL + your logic/ files). Keep the function names, inputs and return shape
(see FRONTEND_README.md).
"""
from mock_data import data as mock
from services.responses import ok, fail


def register_user(full_name, student_id, email, password):
    # BACKEND INTEGRATION POINT
    # Real version: check the email/student ID are not already in the users table,
    # HASH the password, INSERT the new row.
    for user in mock.USERS:
        if user["email"].lower() == email.lower():
            return fail("An account with this email already exists.")
        if user["student_id"].lower() == student_id.lower():
            return fail("An account with this Student ID already exists.")

    new_user = {
        "user_id": len(mock.USERS) + 1,
        "full_name": full_name,
        "student_id": student_id,
        "email": email,
        "username": student_id.lower(),
        "password": password,
    }
    mock.USERS.append(new_user)
    return ok("Account created successfully.")


def login_user(identifier, password):
    # BACKEND INTEGRATION POINT
    # identifier can be the email OR the username.
    # Real version: look the user up, compare the hashed password.
    # On success, data = user dictionary WITHOUT the password:
    #   {"user_id", "full_name", "student_id", "email", "username"}
    identifier = identifier.strip().lower()
    for user in mock.USERS:
        if identifier in (user["email"].lower(), user["username"].lower()) \
                and user["password"] == password:
            safe_user = {key: value for key, value in user.items() if key != "password"}
            return ok("Login successful.", safe_user)
    return fail("Invalid email/username or password.")
