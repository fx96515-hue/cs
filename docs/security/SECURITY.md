# Security Measures

This document outlines the security measures implemented in the CoffeeStudio platform.

## Table of Contents

- [Authentication & Authorization](#authentication--authorization)
- [Input Validation](#input-validation)
- [SQL Injection Prevention](#sql-injection-prevention)
- [Rate Limiting](#rate-limiting)
- [CORS Configuration](#cors-configuration)
- [Secrets Management](#secrets-management)
- [Dependency Security](#dependency-security)
- [Security Scanning](#security-scanning)
- [Best Practices](#best-practices)

## Authentication & Authorization

### JWT Tokens

- **Token-based authentication** using JSON Web Tokens (JWT)
- **Token expiry**: 24 hours (configurable)
- **Algorithm**: HS256 with secure secret key
- **Claims include**: 
  - `sub` (subject/email)
  - `role` (user role)
  - `iat` (issued at)
  - `exp` (expiration)
  - `iss` (issuer)
  - `aud` (audience)

### Password Security

- **Password hashing**: PBKDF2-SHA256 with 300,000 rounds
- **Why PBKDF2 over bcrypt**: Stability across Docker/Windows environments
- **No plaintext passwords** stored anywhere
- Passwords **never logged** or exposed in error messages

### Role-Based Access Control (RBAC)

Three role levels:
- **admin** - Full access to all operations
- **analyst** - Read and write access, cannot delete
- **viewer** - Read-only access

Role enforcement at API level using dependency injection.

### Inactive User Handling

- Inactive user accounts cannot log in
- Login attempts by inactive users return generic "Invalid credentials" error
- Prevents user enumeration attacks

## Input Validation

### Pydantic Schemas

All API inputs validated using Pydantic schemas with:

**Cooperative validation:**
```python
- name: 2-255 characters, XSS prevention checks
- email: EmailStr validation
- website: URL protocol validation (http/https only)
- altitude_m: 0-6000 meters range
- region: Validated against known Peruvian coffee regions
```

**Lot validation:**
```python
- name: 2-255 characters, XSS prevention
- cooperative_id: Must be positive integer
- crop_year: 2000-2100 range
- incoterm: Validated against standard incoterms (FOB, CIF, etc.)
- currency: Validated currency codes (USD, EUR, PEN, GBP)
- price_per_kg: 0-10,000 range
- weight_kg: Positive, up to 100,000 kg
- cupping_score: 0-100 range
```

**Roaster validation:**
```python
- name: 2-255 characters, XSS prevention
- email: EmailStr validation
- website: URL protocol validation
- price_position: Enum validation (premium, mid-range, value, luxury)
- status: Enum validation (active, inactive, prospect, archived)
```

**Cupping validation:**
```python
- sca_score: 0-100 range
- component scores (aroma, flavor, etc.): 0-10 range
- taster: XSS prevention
```

**Logistics validation:**
```python
- weight_kg: Positive, up to 50,000 kg
- price: 0-100 USD/kg range
- incoterm: Validated against standard incoterms
- percentages: 0-1 (0-100%) range
```

**Margin calculation validation:**
```python
- currencies: Validated currency codes
- yield_factor: 0-1 range (must be positive)
- prices: 0-10,000 range
```

**General validation patterns:**
- String length limits to prevent buffer overflow
- Type checking for all fields
- Pattern matching for emails, URLs, phone numbers
- XSS prevention (blocks `<script>`, `<iframe>`, `javascript:`)
- Enum validation for restricted values

### Input Validation Middleware

Enhanced middleware with:
- **Request body size limits**: Maximum 10MB per request
- **SQL injection detection**: Pattern-based detection with multiple signatures
- **XSS detection**: Script tags, javascript: URLs, event handlers
- **Security event logging**: All malicious input attempts logged

### Validation Errors

- Return HTTP 422 for validation errors
- Return HTTP 400 for malicious input detected by middleware
- Return HTTP 413 for request body too large
- Error messages are informative but don't leak sensitive data
- Field-level validation errors help developers debug

## SQL Injection Prevention

### SQLAlchemy ORM

- **All database queries use SQLAlchemy ORM**
- Parameterized queries prevent SQL injection
- **No raw SQL execution** in application code
- Type-safe query construction

### Example of Safe Queries

```python
# Safe - parameterized
coop = db.query(Cooperative).filter(Cooperative.id == coop_id).first()

# Never done - raw SQL
# db.execute(f"SELECT * FROM cooperatives WHERE id = {coop_id}")
```

## Rate Limiting

### SlowAPI Rate Limiter

- **Global rate limit**: 200 requests per minute per IP
- **Login endpoint**: 5 attempts per minute per IP
- **Bootstrap endpoint**: 10 attempts per hour per IP

### Configuration

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

### Headers

Rate limit information included in response headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

### Endpoint-Specific Limits

Custom rate limits applied to sensitive endpoints:
```python
@router.post("/login")
@limiter.limit("5/minute")  # Stricter limit for auth
def login(...)

@router.post("/dev/bootstrap")
@limiter.limit("10/hour")  # Prevent abuse
def bootstrap(...)
```

## CSRF Protection

### CSRF Token Generation

CSRF tokens protect against cross-site request forgery attacks:

```python
from app.core.security import generate_csrf_token, validate_csrf_token

# Generate token for authenticated user
token = generate_csrf_token(user.email)

# Validate token on state-changing operations
is_valid = validate_csrf_token(user.email, token)
```

### Token Properties

- **Cryptographically strong**: Generated using `secrets.token_urlsafe(32)`
- **Hashed storage**: Tokens stored as SHA-256 hashes
- **Time-limited**: Tokens expire after 1 hour
- **Session-bound**: Each token tied to specific user session

### Usage in API

```bash
# Get CSRF token
curl -H "Authorization: Bearer <token>" /auth/csrf-token

# Use token in state-changing requests
curl -X POST -H "Authorization: Bearer <token>" \
     -H "X-CSRF-Token: <csrf-token>" \
     /cooperatives
```

### Token Cleanup

Expired tokens automatically cleaned up:
```python
from app.core.security import cleanup_expired_csrf_tokens
cleanup_expired_csrf_tokens()
```

## CORS Configuration

### Allowed Origins

Configured via environment variable `CORS_ORIGINS`:

```
CORS_ORIGINS=http://localhost:3000,https://coffeestudio.example.com
```

### Settings

- **Credentials**: Allowed for authenticated requests
- **Methods**: All HTTP methods allowed for API flexibility
- **Headers**: All headers allowed (can be restricted if needed)

### Production Recommendation

Restrict to specific domains in production:
```
CORS_ORIGINS=https://coffeestudio.example.com
```

## Secrets Management

### Environment Variables

All secrets stored in environment variables:

```bash
# Required secrets
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=<strong-random-secret>
BOOTSTRAP_ADMIN_PASSWORD=<strong-password>

# Optional API keys
PERPLEXITY_API_KEY=<api-key>
```

### Secret Generation

Generate secure secrets:

```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Never Commit Secrets

- `.env` files in `.gitignore`
- Use `.env.example` for documentation
- GitHub Secrets for CI/CD

## Dependency Security

### Automated Scanning

**GitHub Dependabot:**
- Automatically checks for vulnerable dependencies
- Creates PRs to update vulnerable packages

**Trivy (CI):**
- Scans for vulnerabilities in dependencies
- Runs on every push/PR
- Focuses on CRITICAL and HIGH severity issues

**npm audit (Frontend):**
- Runs in CI pipeline
- Alerts on production dependencies only

### Manual Checks

```bash
# Backend
pip install safety
safety check

# Frontend
npm audit
```

## Security Scanning

### Semgrep (SAST)

- Static Application Security Testing
- Scans code for security patterns
- Runs on every push/PR
- Non-blocking (warnings only)

### Trivy (Vulnerability Scanner)

- Scans for:
  - Known CVEs in dependencies
  - Misconfigurations
  - Exposed secrets
- Outputs SARIF format for GitHub integration

### Manual Security Testing

```bash
# Run Semgrep locally
pip install semgrep
semgrep --config auto apps/api/

# Run Trivy locally
trivy fs --severity CRITICAL,HIGH .
```

## Best Practices

### Development

1. **Never hardcode secrets** - Use environment variables
2. **Validate all inputs** - Use Pydantic schemas
3. **Use ORM** - Avoid raw SQL queries
4. **Log security events** - Login attempts, access denials
5. **Generic error messages** - Don't leak information to attackers
6. **Keep dependencies updated** - Review Dependabot PRs promptly

### Production Deployment

1. **Use strong JWT secret** - At least 32 random bytes
2. **HTTPS only** - No unencrypted connections
3. **Restrict CORS** - Only allow your domain
4. **Monitor logs** - Watch for unusual patterns
5. **Regular security audits** - Review code and dependencies
6. **Backup encryption** - Encrypt database backups
7. **Least privilege** - Database users should have minimal permissions

### Incident Response

If a security issue is discovered:

1. **Assess severity** - Determine impact and scope
2. **Contain** - Disable affected features if needed
3. **Patch** - Fix the vulnerability
4. **Test** - Verify the fix
5. **Deploy** - Roll out the patch
6. **Document** - Record what happened and how it was fixed
7. **Review** - Update security practices to prevent recurrence

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email the maintainers directly at: [your-security-email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Checklist

Before production deployment:

- [ ] Strong, unique JWT_SECRET configured
- [ ] BOOTSTRAP_ADMIN_PASSWORD set to strong password
- [ ] CORS_ORIGINS restricted to production domain(s)
- [ ] HTTPS/TLS configured
- [ ] Database credentials are strong and unique
- [ ] All dependencies updated to latest secure versions
- [ ] Security scans passing (Semgrep, Trivy)
- [ ] Rate limiting enabled
- [ ] Logging configured for security events
- [ ] Backup strategy in place
- [ ] Incident response plan documented

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)
