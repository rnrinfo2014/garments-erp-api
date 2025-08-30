# Authentication API Endpoints

## Overview
This document outlines the authentication endpoints available in the Garments ERP API system, including the newly implemented logout and password change functionality.

## Endpoints

### 1. User Login
**POST** `/api/auth/login`

Request body:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "expires_in": 30
}
```

### 2. Get Current User Info
**GET** `/api/auth/me`

Headers:
```
Authorization: Bearer {jwt_token}
```

Response:
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN",
    "status": "ACTIVE",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

### 3. Logout (NEW)
**POST** `/api/auth/logout`

Headers:
```
Authorization: Bearer {jwt_token}
```

Response:
```json
{
    "message": "Successfully logged out",
    "logged_out_at": "2024-01-30T12:00:00"
}
```

**Note**: Since JWT tokens are stateless, the client must clear the token from storage after receiving this response.

### 4. Change Password (NEW)
**POST** `/api/auth/change-password`

Headers:
```
Authorization: Bearer {jwt_token}
```

Request body:
```json
{
    "current_password": "old_password",
    "new_password": "new_password",
    "confirm_password": "new_password"
}
```

Response:
```json
{
    "message": "Password changed successfully",
    "changed_at": "2024-01-30T12:00:00"
}
```

**Validation Rules**:
- Current password must be correct
- New password must be different from current password
- New password and confirmation must match
- Password should follow security guidelines (length, complexity)

## Error Responses

### 401 Unauthorized
```json
{
    "detail": "Could not validate credentials"
}
```

### 400 Bad Request (Password Change)
```json
{
    "detail": "Current password is incorrect"
}
```

```json
{
    "detail": "New password and confirmation do not match"
}
```

```json
{
    "detail": "New password must be different from current password"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Failed to update password"
}
```

## Security Features

1. **JWT Authentication**: All protected endpoints require valid JWT tokens
2. **Password Hashing**: Passwords are securely hashed using bcrypt
3. **Current Password Verification**: Password changes require current password
4. **Password Validation**: Prevents reusing current password
5. **Token Expiration**: Access tokens expire after 30 minutes

## Usage Examples

### Login Flow
```python
import requests

# Login
response = requests.post("http://localhost:8000/api/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}
user_info = requests.get("http://localhost:8000/api/auth/me", headers=headers)
```

### Password Change Flow
```python
# Change password
response = requests.post("http://localhost:8000/api/auth/change-password", 
    headers=headers,
    json={
        "current_password": "admin123",
        "new_password": "newPassword456",
        "confirm_password": "newPassword456"
    }
)
```

### Logout Flow
```python
# Logout
response = requests.post("http://localhost:8000/api/auth/logout", headers=headers)

# Clear token from client storage
# token = None
```

## Implementation Notes

- The logout endpoint provides a clean way to end user sessions
- Clients should implement proper token storage and cleanup
- Password changes are immediately effective
- Users should be prompted to login again after password changes for security
- Consider implementing password complexity requirements in frontend validation

## Testing
All endpoints can be tested using:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Postman or similar API testing tools

Date: January 30, 2025
