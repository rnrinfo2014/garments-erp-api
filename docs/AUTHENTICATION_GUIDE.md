# FastAPI Authentication Guide

Your FastAPI application now supports **two authentication methods**:

## 1. JWT Token Authentication (Existing)

### How it works:
1. Send username/password to `/api/auth/login`
2. Get a JWT token back
3. Use the token in `Authorization: Bearer <token>` header for subsequent requests

### Example:
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Response: {"access_token": "eyJ0eXAiOi...", "token_type": "bearer"}

# Use token
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJ0eXAiOi..."
```

### Token-based endpoints:
- `GET /api/auth/me` - Get current user info
- `GET /api/users` - Get all users (Admin only)
- `POST /api/users` - Create user (Admin only)
- `PUT /api/users/{id}` - Update user (Admin only)
- `DELETE /api/users/{id}` - Delete user (Superadmin only)

## 2. HTTP Basic Authentication (New)

### How it works:
Send username/password directly in the `Authorization: Basic <credentials>` header with every request.

### Example:
```bash
# Encode credentials: echo -n "admin:admin" | base64
# Result: YWRtaW46YWRtaW4=

curl -X GET "http://localhost:8000/api/auth/me-basic" \
  -H "Authorization: Basic YWRtaW46YWRtaW4="
```

### PowerShell example:
```powershell
$credentials = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes("admin:admin"))
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me-basic" -Headers @{"Authorization" = "Basic $credentials"}
```

### Basic Auth endpoints:
- `GET /api/auth/me-basic` - Get current user info
- `GET /api/users-basic` - Get all users (Admin only)
- `GET /api/users-basic/{id}` - Get user by ID (Admin only)

## 3. Testing Your Authentication

Run the test script:
```bash
python test_auth.py
```

Or test manually:
1. Open http://localhost:8000/docs
2. Try both authentication methods in Swagger UI
3. For Basic Auth: Click "Authorize" and use HTTPBasic
4. For Token Auth: Use the login endpoint first, then use HTTPBearer

## 4. API Documentation

Visit http://localhost:8000/docs to see interactive API documentation with both authentication methods.

## 5. When to Use Each Method

### Use JWT Token Authentication when:
- Building web applications
- Need session management
- Want better security (tokens expire)
- Building mobile apps

### Use Basic Authentication when:
- Building simple scripts or tools
- Need quick testing
- Integrating with systems that only support Basic Auth
- Prototyping

## 6. Security Notes

- **Basic Auth**: Username/password sent with every request (less secure)
- **Token Auth**: Credentials sent only once, token expires (more secure)
- Always use HTTPS in production
- Change default credentials in production
