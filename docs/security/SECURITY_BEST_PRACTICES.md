# Security Best Practices Guide

This document outlines security best practices implemented in the CoffeeStudio Platform and guidelines for maintaining security.

## Table of Contents

1. [Security Middleware](#security-middleware)
2. [Input Validation](#input-validation)
3. [Authentication & Authorization](#authentication--authorization)
4. [Database Security](#database-security)
5. [API Security](#api-security)
6. [Error Handling](#error-handling)
7. [Deployment Security](#deployment-security)

---

## Security Middleware

### SecurityHeadersMiddleware

The platform implements comprehensive HTTP security headers to protect against common web vulnerabilities:

#### Headers Implemented

1. **X-Frame-Options: DENY**
   - Prevents clickjacking attacks by disabling iframe embedding
   - Protects users from being tricked into clicking hidden elements

2. **X-Content-Type-Options: nosniff**
   - Prevents MIME type sniffing
   - Forces browsers to respect Content-Type headers

3. **X-XSS-Protection: 1; mode=block**
   - Enables browser XSS filtering
   - Blocks page loading if XSS is detected

4. **Content-Security-Policy (CSP)**
   - Restricts resources that can be loaded
   - Mitigates XSS and data injection attacks
   - Current policy:
     ```
     default-src 'self';
     script-src 'self' 'unsafe-inline' 'unsafe-eval';
     style-src 'self' 'unsafe-inline';
     img-src 'self' data: https:;
     font-src 'self' data:;
     connect-src 'self'
     ```

5. **Strict-Transport-Security (HSTS)**
   - Enforces HTTPS connections
   - Prevents man-in-the-middle attacks
   - `max-age=31536000; includeSubDomains`

6. **Referrer-Policy: strict-origin-when-cross-origin**
   - Controls referrer information sent with requests
   - Protects user privacy

7. **Permissions-Policy**
   - Disables unused browser features (geolocation, microphone, camera)
   - Reduces attack surface

### Usage

The middleware is automatically applied to all responses:

```python
# Configured in app/main.py
app.add_middleware(SecurityHeadersMiddleware)
```

---

## Input Validation

### InputValidationMiddleware

Protects against injection attacks by detecting malicious patterns in request payloads.

#### Protection Against

1. **SQL Injection**
   - Detects common SQL injection patterns
   - Blocks: UNION SELECT, DROP TABLE, INSERT INTO, etc.
   - Checks for SQL comments and OR/AND injection attempts

2. **Cross-Site Scripting (XSS)**
   - Detects script tags and javascript: URLs
   - Blocks event handlers (onclick, onerror, etc.)
   - Validates nested objects and arrays

#### Pattern Detection

**SQL Injection Patterns:**
```python
- r"(\bUNION\b.*\bSELECT\b)"
- r"(\bSELECT\b.*\bFROM\b)"
- r"(\bINSERT\b.*\bINTO\b)"
- r"(\bDELETE\b.*\bFROM\b)"
- r"(\bDROP\b.*\bTABLE\b)"
- r"(;.*(-{2}|\/\*))"  # SQL comments
- r"('\s*(OR|AND)\s*'?\d)"  # Basic OR/AND injection
```

**XSS Patterns:**
```python
- r"<script[^>]*>.*?</script>"
- r"javascript:"
- r"on\w+\s*="  # Event handlers
```

**Additional Protections:**
```python
- Request body size limit: 10MB maximum
- Logging of all malicious input attempts
- IP-based rate limiting
```

#### Response

Malicious input is rejected with:
```json
{
  "detail": "Invalid input detected. Request contains potentially malicious content."
}
```
Status Code: 400 Bad Request

For request body too large:
```json
{
  "error": {
    "code": "REQUEST_TOO_LARGE",
    "message": "Request body too large. Maximum size is 10485760 bytes."
  }
}
```
Status Code: 413 Payload Too Large

### Pydantic Field-Level Validation

#### String Fields

```python
from pydantic import BaseModel, Field, field_validator

class CooperativeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Prevent XSS in name field."""
        if any(pattern in v.lower() for pattern in ["<script", "<iframe", "javascript:"]):
            raise ValueError("Invalid characters in name")
        return v.strip()
```

#### Numeric Fields with Ranges

```python
class LotCreate(BaseModel):
    altitude_m: Optional[float] = Field(None, ge=0, le=6000)
    price_per_kg: Optional[float] = Field(None, ge=0, le=10000)
    crop_year: Optional[int] = Field(None, ge=2000, le=2100)
    expected_cupping_score: Optional[float] = Field(None, ge=0, le=100)
```

#### Enum Validation

```python
class RoasterCreate(BaseModel):
    price_position: Optional[str] = Field(None, max_length=50)
    
    @field_validator("price_position")
    @classmethod
    def validate_price_position(cls, v: Optional[str]) -> Optional[str]:
        """Validate enum values."""
        if v is None:
            return v
        valid = ["premium", "mid-range", "value", "luxury"]
        v_lower = v.lower().strip()
        if v_lower not in valid:
            raise ValueError(f"Must be one of {valid}")
        return v_lower
```

#### Currency and Incoterm Validation

```python
@field_validator("currency")
@classmethod
def validate_currency(cls, v: Optional[str]) -> Optional[str]:
    """Validate currency codes."""
    if v is None:
        return v
    valid_currencies = ["USD", "EUR", "PEN", "GBP"]
    v_upper = v.upper().strip()
    if v_upper not in valid_currencies:
        raise ValueError(f"Currency must be one of {valid_currencies}")
    return v_upper

@field_validator("incoterm")
@classmethod
def validate_incoterm(cls, v: Optional[str]) -> Optional[str]:
    """Validate incoterm values."""
    if v is None:
        return v
    valid_incoterms = ["EXW", "FOB", "CIF", "CFR", "DAP", "DDP", "FCA", "CPT", "CIP"]
    v_upper = v.upper().strip()
    if v_upper not in valid_incoterms:
        raise ValueError(f"Incoterm must be one of {valid_incoterms}")
    return v_upper
```

#### URL Validation

```python
@field_validator("website")
@classmethod
def validate_website(cls, v: Optional[str]) -> Optional[str]:
    """Validate website URL format."""
    if v and v.strip():
        v = v.strip()
        # Must be http/https
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Website must start with http:// or https://")
        # Prevent dangerous protocols
        if any(proto in v.lower() for proto in ["javascript:", "data:", "file:"]):
            raise ValueError("Invalid URL protocol")
    return v if v else None
```

#### Email Validation

```python
from pydantic import EmailStr

class CooperativeCreate(BaseModel):
    contact_email: Optional[EmailStr] = None
```

### Best Practices

1. **Always validate on the server side** - Never trust client-side validation alone
2. **Use Pydantic models** for structured validation
3. **Sanitize output** - HTML-encode data when rendering in templates
4. **Whitelist over blacklist** - Define what's allowed rather than what's forbidden

---

## Authentication & Authorization

### JWT-Based Authentication

The platform uses JSON Web Tokens (JWT) for stateless authentication.

#### Security Features

1. **Password Hashing**
   - Uses `pbkdf2_sha256` algorithm
   - Salted and hashed passwords (never stored in plain text)
   
2. **JWT Configuration**
   ```python
   # Required environment variables
   JWT_SECRET=<strong-random-secret-at-least-32-chars>
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_MINUTES=1440  # 24 hours
   ```

3. **Token Structure**
   ```json
   {
     "sub": "user_email@example.com",
     "user_id": 123,
     "role": "admin",
     "exp": 1704067200
   }
   ```

### Role-Based Access Control (RBAC)

Three roles with different permissions:

1. **Admin** - Full access (create, read, update, delete)
2. **Analyst** - Can create and modify data
3. **Viewer** - Read-only access

#### Implementation

```python
from app.api.dependencies import require_role

@router.post("/cooperatives")
def create_cooperative(
    data: CooperativeCreate,
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    # Only admin and analyst can create
    pass
```

### Best Practices

1. **Strong JWT Secret** - Use at least 32 random characters
2. **Rotate secrets** - Implement secret rotation strategy
3. **Short token expiration** - Balance security vs. user experience
4. **Secure token storage** - Use httpOnly cookies or secure storage
5. **Implement refresh tokens** - For long-lived sessions
6. **Rate limit login attempts** - Prevent brute force attacks

### CSRF Protection

Cross-Site Request Forgery (CSRF) protection prevents malicious sites from making unauthorized requests on behalf of authenticated users.

#### Token Generation

```python
from app.core.security import generate_csrf_token

# Generate token for authenticated user
token = generate_csrf_token(user.email)
```

**Token properties:**
- Cryptographically strong (32-byte random token)
- Stored as SHA-256 hash
- Session-bound (tied to user email/session ID)
- Time-limited (1 hour expiration)

#### Token Validation

```python
from app.core.security import validate_csrf_token

# Validate token on state-changing operations
is_valid = validate_csrf_token(session_id, token)

if not is_valid:
    raise HTTPException(status_code=403, detail="Invalid CSRF token")
```

#### API Usage

**Step 1: Get CSRF Token**
```bash
curl -H "Authorization: Bearer <jwt_token>" \
     https://api.example.com/auth/csrf-token

# Response:
{
  "csrf_token": "abc123..."
}
```

**Step 2: Use Token in State-Changing Requests**
```bash
curl -X POST \
     -H "Authorization: Bearer <jwt_token>" \
     -H "X-CSRF-Token: abc123..." \
     -H "Content-Type: application/json" \
     -d '{"name": "New Cooperative"}' \
     https://api.example.com/cooperatives/
```

#### Frontend Integration

```javascript
// Fetch CSRF token on login
async function login(email, password) {
  const loginRes = await fetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
  const { access_token } = await loginRes.json();
  
  // Get CSRF token
  const csrfRes = await fetch('/auth/csrf-token', {
    headers: { 'Authorization': `Bearer ${access_token}` }
  });
  const { csrf_token } = await csrfRes.json();
  
  // Store both tokens
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('csrf_token', csrf_token);
}

// Include CSRF token in all state-changing requests
async function createCooperative(data) {
  const response = await fetch('/cooperatives/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'X-CSRF-Token': localStorage.getItem('csrf_token'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  return response.json();
}
```

#### Token Cleanup

Periodically clean up expired tokens:
```python
from app.core.security import cleanup_expired_csrf_tokens

# Call periodically (e.g., in a background task)
cleanup_expired_csrf_tokens()
```

#### Best Practices

1. **Always validate CSRF tokens** for POST, PUT, PATCH, DELETE requests
2. **Don't include tokens in URLs** - Use headers or request body
3. **Regenerate tokens** after authentication state changes
4. **Set appropriate expiration** - Balance security vs. usability (default: 1 hour)
5. **Use secure storage** - In production, consider Redis for token storage

---

## Database Security

### SQLAlchemy ORM

The platform uses SQLAlchemy ORM which provides automatic protection against SQL injection.

#### Parameterized Queries

✅ **Good - Using ORM:**
```python
# Automatic parameterization
user = db.query(User).filter(User.email == email).first()
cooperatives = db.query(Cooperative).filter(Cooperative.region == region).all()
```

❌ **Bad - String concatenation:**
```python
# NEVER do this
query = f"SELECT * FROM users WHERE email = '{email}'"
db.execute(query)
```

### Database Connection Security

1. **Use environment variables** for credentials
2. **Limit database user privileges** - Grant only necessary permissions
3. **Enable SSL/TLS** for database connections in production
4. **Regular backups** - Automated with retention policy
5. **Audit logging** - Log all data modifications

### Configuration

```python
# Use environment variable, never hardcode
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Production: Use connection pooling
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=10
```

---

## API Security

### Rate Limiting

SlowAPI is configured to prevent abuse:

```python
# Global rate limit
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]
)

# Endpoint-specific limits
@limiter.limit("5/minute")
@router.post("/auth/login")
async def login(credentials: LoginRequest):
    pass
```

### CORS Configuration

Restrict origins in production:

```python
# .env
CORS_ORIGINS=https://app.coffeestudio.com,https://admin.coffeestudio.com

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Versioning

Best practice: Version your API endpoints

```
/api/v1/cooperatives
/api/v2/cooperatives
```

### Input Size Limits

Prevent DOS attacks with size limits:

```python
# FastAPI automatic protection
# Configure in main.py if needed
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=10_000_000  # 10 MB
)
```

---

## Error Handling

### Standardized Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional information
  }
}
```

### Error Types

1. **Validation Errors (422)**
   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Request validation failed",
       "details": [...]
     }
   }
   ```

2. **Authentication Errors (401)**
   ```json
   {
     "error": {
       "code": "HTTP_ERROR",
       "message": "Invalid credentials"
     }
   }
   ```

3. **Authorization Errors (403)**
   ```json
   {
     "error": {
       "code": "HTTP_ERROR",
       "message": "Insufficient permissions"
     }
   }
   ```

4. **Database Errors (409/503)**
   - 409 Conflict: Integrity constraint violation
   - 503 Service Unavailable: Operational database error

### Security Considerations

1. **Never expose stack traces** in production
2. **Don't leak sensitive information** in error messages
3. **Log detailed errors** server-side with correlation IDs
4. **Return generic messages** to clients
5. **Use structured logging** for security event monitoring

Example:
```python
# ✅ Good
return {"error": {"message": "Authentication failed"}}

# ❌ Bad - leaks information
return {"error": {"message": "User test@example.com not found"}}
```

---

## Deployment Security

### Environment Variables

Never commit secrets to version control:

```bash
# .env (never commit)
JWT_SECRET=<generate-strong-random-secret>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
PERPLEXITY_API_KEY=<if-using-discovery>
```

### Docker Security

1. **Use non-root user** in containers
   ```dockerfile
   USER appuser
   ```

2. **Scan images** for vulnerabilities
   ```bash
   docker scan coffeestudio-backend:latest
   ```

3. **Minimal base images** - Use alpine or distroless
4. **Regular updates** - Keep dependencies up to date

### HTTPS/TLS

1. **Use Let's Encrypt** for SSL certificates
2. **Configure HSTS** header (already implemented)
3. **Disable old TLS versions** (< TLS 1.2)
4. **Use strong cipher suites**

### Secrets Management

For production, use a secrets manager:

- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**
- **Google Secret Manager**

### Monitoring & Alerting

1. **Security event logging** - Log all auth attempts, access denials
2. **Anomaly detection** - Monitor for unusual patterns
3. **Alert on failures** - Multiple failed login attempts, etc.
4. **Regular security audits** - Review logs and access patterns

### Backup & Recovery

1. **Automated daily backups** of database
2. **Test restore procedures** regularly
3. **Offsite backup storage**
4. **Encryption at rest** for backups

---

## Security Checklist for Production

### Before Go-Live

- [ ] Change all default passwords and secrets
- [ ] JWT_SECRET is strong and random (≥32 chars)
- [ ] CORS origins restricted to production domains
- [ ] HTTPS enforced with valid SSL certificate
- [ ] Database credentials secured with secrets manager
- [ ] Rate limiting configured appropriately
- [ ] Security headers middleware enabled
- [ ] Input validation middleware enabled
- [ ] Error messages don't leak sensitive information
- [ ] All dependencies updated to latest secure versions
- [ ] Database backups automated and tested
- [ ] Monitoring and alerting configured
- [ ] Security audit completed
- [ ] Penetration testing performed
- [ ] Incident response plan documented

### Regular Maintenance

- [ ] Weekly dependency updates
- [ ] Monthly security audit
- [ ] Quarterly penetration testing
- [ ] Review and rotate secrets every 90 days
- [ ] Monitor security advisories
- [ ] Test backup restoration procedures

---

## Security Contacts & Resources

### Reporting Security Issues

If you discover a security vulnerability, please email:
- security@coffeestudio.com (if available)
- Create a private GitHub security advisory

**Do not** open public issues for security vulnerabilities.

### Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)

---

**Last Updated:** 2025-12-29  
**Version:** 1.0  
**Maintainer:** CoffeeStudio Security Team
