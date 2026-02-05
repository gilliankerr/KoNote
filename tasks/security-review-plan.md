# Security Review Plan: PII & Access Control

**Version:** 2.0
**Last Updated:** 2026-02-03
**Review Type:** Periodic security assessment for major code changes

---

## When to Run This Review

Run this security review when any of the following change:

- [ ] Models with encrypted fields (`_*_encrypted` BinaryFields)
- [ ] Authentication views or middleware
- [ ] RBAC middleware or access control logic
- [ ] Audit logging infrastructure
- [ ] Session or cookie configuration
- [ ] Any new endpoint that accesses client data
- [ ] Dependencies related to cryptography or authentication

**Minimum frequency:** Quarterly, even without code changes.

---

## Review Objectives

1. Verify all PII is encrypted at rest AND in transit
2. Confirm RBAC enforces program-scoped data isolation
3. Validate audit logging captures all sensitive operations
4. Test for common vulnerabilities (OWASP Top 10)
5. Verify privacy compliance (PIPEDA, data minimization, consent)
6. Assess encryption key management lifecycle
7. Test actual attack scenarios, not just code patterns

---

## Two-Tier Assessment Model

### Tier 1: Gate Checks (Pass/Fail)

**Any failure blocks deployment.** No exceptions.

| Gate | Requirement |
|------|-------------|
| G1 | No Critical vulnerabilities found |
| G2 | All PII fields use encryption (no plaintext storage) |
| G3 | RBAC middleware enabled and enforced |
| G4 | Audit logging functional and writing to separate database |
| G5 | Session cookies have HttpOnly, Secure, SameSite flags |
| G6 | DEBUG=False in production settings |
| G7 | Encryption key loaded from environment (not hardcoded) |

### Tier 2: Maturity Score (Continuous Improvement)

| Category | Weight | Max Points |
|----------|--------|------------|
| Encryption & PII Protection | 25 | 25 |
| Access Control & RBAC | 25 | 25 |
| Authentication & Sessions | 15 | 15 |
| Audit & Logging | 15 | 15 |
| OWASP & General Security | 20 | 20 |
| **Total** | 100% | 100 |

**Passing threshold:** 85/100 (with all Gate Checks passed)

---

## Section 1: Encryption & PII Protection (25 points)

### Files to Review

| File | What to Check |
|------|---------------|
| `konote/encryption.py` | Algorithm strength, error handling, key loading |
| `apps/clients/models.py` | All PII uses `_*_encrypted` pattern |
| `apps/auth_app/models.py` | User email encryption |
| `apps/clients/forms.py` | No raw PII leakage in validation errors |
| `konote/settings/*.py` | TLS/HSTS configuration |

### Checklist

**Encryption at Rest (10 points)**
- [ ] All PII fields use `_field_encrypted` BinaryField + property accessor
- [ ] Custom fields with `is_sensitive=True` are encrypted
- [ ] No PII stored in plaintext anywhere (including logs, cache, temp files)
- [ ] Fernet key loaded from `FIELD_ENCRYPTION_KEY` environment variable
- [ ] No hardcoded keys in code, settings, or version control

**Encryption in Transit (5 points)**
- [ ] HTTPS enforced (SECURE_SSL_REDIRECT=True or load balancer handles)
- [ ] HSTS header enabled (SECURE_HSTS_SECONDS > 0)
- [ ] Minimum TLS 1.2 (check deployment configuration)
- [ ] Any outbound API calls use certificate validation

**Key Management (5 points)**
- [ ] Key rotation command (`rotate_encryption_key`) tested and documented
- [ ] Key rotation doesn't cause data loss (test with real data)
- [ ] Key backup/recovery procedure documented
- [ ] Key not exposed in error messages, logs, or stack traces

**Error Handling (5 points)**
- [ ] Decryption errors return safe marker (not exception with key details)
- [ ] The `[decryption error]` marker doesn't appear in user-facing UI
- [ ] Form validation errors don't echo back submitted PII
- [ ] DEBUG=False in production (no stack traces exposed)
- [ ] Custom 500 error page doesn't expose sensitive details

---

## Section 2: Access Control & RBAC (25 points)

### Files to Review

| File | What to Check |
|------|---------------|
| `konote/middleware/program_access.py` | All client routes protected |
| `apps/clients/views.py` | Program scoping enforced |
| `apps/notes/views.py` | Client access validation |
| `apps/programs/models.py` | Role definitions |

### Checklist

**Program-Scoped Access (10 points)**
- [ ] Every client data route checks program overlap
- [ ] Middleware covers all URL patterns that access client data
- [ ] Admins without program roles cannot access client records
- [ ] Client list views filter by user's accessible programs
- [ ] No direct object access (e.g., `/clients/<id>`) without permission check

**Role Hierarchy (5 points)**
- [ ] Role hierarchy enforced: front_desk < staff < program_manager
- [ ] Front Desk role has appropriately limited data access
- [ ] Staff cannot access program_manager-only functions
- [ ] Role stored in request context for view-level checks

**Edge Cases (5 points)**
- [ ] Client enrolled in multiple programs: user needs overlap with at least one
- [ ] User with multiple roles: highest role applies
- [ ] Removed program role: access revoked immediately
- [ ] New client enrolment: existing users gain access correctly

**Attack Scenario Testing (5 points)**
- [ ] **IDOR test**: User A cannot access `/clients/X` where X is in User B's program only
- [ ] **Vertical escalation test**: Front Desk cannot access staff-only features
- [ ] **Direct URL test**: Knowing a client ID doesn't grant access
- [ ] **API endpoint test**: All endpoints (not just UI) enforce RBAC

---

## Section 3: Authentication & Sessions (15 points)

### Files to Review

| File | What to Check |
|------|---------------|
| `apps/auth_app/views.py` | Login logic, rate limiting, error messages |
| `konote/settings/base.py` | Session and password configuration |
| Azure AD configuration | Token validation (if using SSO) |

### Checklist

**Login Security (5 points)**
- [ ] Rate limiting on login endpoints (currently 5 POST/min)
- [ ] Generic error messages (no username enumeration)
- [ ] Failed login attempts logged in audit trail
- [ ] Account lockout after repeated failures (or CAPTCHA)

**Session Security (5 points)**
- [ ] Session cookies: HttpOnly=True, Secure=True, SameSite=Lax
- [ ] Session timeout configured (currently 30 min)
- [ ] Session invalidated on logout
- [ ] Session ID regenerated on login (prevents fixation)

**Password Security (5 points)**
- [ ] Argon2 password hasher (primary)
- [ ] Minimum 10 characters enforced
- [ ] Common password list checked
- [ ] Password not similar to username/email

**If using Azure AD SSO:**
- [ ] Token signature validated
- [ ] Token audience matches application
- [ ] Token issuer validated
- [ ] Token expiry checked
- [ ] Callback URL validated

---

## Section 4: Audit & Logging (15 points)

### Files to Review

| File | What to Check |
|------|---------------|
| `apps/audit/models.py` | Fields captured, immutability |
| `konote/middleware/audit.py` | Coverage of operations |
| `apps/audit/management/commands/lockdown_audit_db.py` | DB permissions |
| `konote/db_router.py` | Database routing |

### Checklist

**Audit Coverage (5 points)**
- [ ] All state-changing operations logged (POST/PUT/PATCH/DELETE)
- [ ] Login and logout events logged
- [ ] Failed authentication attempts logged
- [ ] Client record views logged (for compliance)
- [ ] Data exports logged

**Audit Integrity (5 points)**
- [ ] Audit database has INSERT-only permissions (no UPDATE/DELETE)
- [ ] `lockdown_audit_db` command has been run
- [ ] Audit logs stored in separate database
- [ ] Database router prevents accidental writes to wrong database

**Audit Content (5 points)**
- [ ] Logs capture: user ID, display name, IP address
- [ ] Logs capture: action, resource type, resource ID
- [ ] Logs capture: timestamp, HTTP status
- [ ] Old/new values captured for changes (without PII in plaintext)
- [ ] Audit failures don't break main operations (graceful degradation)

**Attack Scenario Testing:**
- [ ] Verify actions that bypass UI are still logged
- [ ] Verify audit logs cannot be modified via any endpoint
- [ ] Verify failed/denied actions are logged

---

## Section 5: OWASP & General Security (20 points)

### Checklist

**A01: Broken Access Control (covered in Section 2)**

**A02: Cryptographic Failures (4 points)**
- [ ] No weak algorithms (MD5, SHA1 for security purposes)
- [ ] Random values use `secrets` module, not `random`
- [ ] No sensitive data in URLs (query strings logged by servers)

**A03: Injection (4 points)**
- [ ] All database queries use ORM (no raw SQL with user input)
- [ ] If raw SQL exists, it uses parameterized queries
- [ ] No `eval()`, `exec()`, or similar with user input
- [ ] Template rendering uses auto-escaping (no `|safe` with user data)

**A04: Insecure Design (4 points)**
- [ ] Principle of least privilege applied
- [ ] Defence in depth (multiple layers of protection)
- [ ] Fail securely (errors don't grant access)

**A05: Security Misconfiguration (4 points)**
- [ ] DEBUG=False in production
- [ ] SECRET_KEY from environment variable
- [ ] ALLOWED_HOSTS configured properly
- [ ] Security headers set (CSP, X-Frame-Options, X-Content-Type-Options)

**A06: Vulnerable Components (2 points)**
- [ ] Run `pip-audit` or `safety check` for known vulnerabilities
- [ ] Django and cryptography packages up to date

**A07: Auth Failures (covered in Section 3)**

**A08: Software and Data Integrity (2 points)**
- [ ] CSRF protection enabled and tokens in all forms
- [ ] Subresource integrity for CDN scripts (if any)

**HTMX-Specific Checks:**
- [ ] HTMX requests respect CSRF protection
- [ ] No `hx-*` attributes accept user-controlled URLs
- [ ] HX-Request header validated where needed

---

## Section 6: Privacy Compliance (Bonus — Not Scored)

These checks support PIPEDA and similar privacy regulations but don't affect the security score.

### Data Minimization
- [ ] All collected PII fields have documented purpose
- [ ] No unnecessary PII collected
- [ ] Review: Could any encrypted fields be removed or anonymized?

### Consent Management
- [ ] Consent captured before PII is stored
- [ ] Consent type matches processing purpose
- [ ] Consent withdrawal triggers appropriate data handling
- [ ] Consent changes logged in audit trail

### Data Retention
- [ ] `retention_expires` field populated appropriately
- [ ] Expired data actually purged (verify with test data)
- [ ] Purging logged in audit trail
- [ ] Retention periods configurable per agency

### Data Subject Rights
- [ ] Client can request data export (right of access)
- [ ] `erasure_requested` triggers actual erasure
- [ ] Erasure is complete (no orphaned data in related tables)
- [ ] Erasure logged in audit trail

### Breach Readiness
- [ ] System can detect suspicious access patterns
- [ ] Alerting configured for security events
- [ ] Incident response procedure documented
- [ ] Can identify affected records within 72 hours

---

## Testing Tools & Procedures

### Automated Scanning
```bash
# Dependency vulnerabilities
pip-audit

# Django security check
python manage.py check --deploy

# If OWASP ZAP available
# zap-cli quick-scan --self-contained http://localhost:8000
```

### Manual Testing Setup
1. Create test users with each role (admin, program_manager, staff, front_desk)
2. Create test clients enrolled in specific programs
3. Test access from users NOT in those programs

### Test Data Strategy
- Use obviously fake data (e.g., "Test Client AAA", "test@example.com")
- Clear test data after review
- Never use production data for testing

---

## Output Format

### Executive Summary
- **Gate Check Status:** PASS / FAIL
- **Maturity Score:** XX/100
- **Production Ready:** Yes / No / With Fixes
- **Critical Issues:** Count
- **Important Issues:** Count

### Findings by Severity

#### Critical (Must Fix Before Deployment)
Issues that allow unauthorized data access, data exposure, or security bypass.

#### Important (Should Fix Soon)
Gaps in protection, missing controls, or weak configurations.

#### Minor (Continuous Improvement)
Defence-in-depth improvements, hardening opportunities.

**For each finding:**
- **Location:** file:line or endpoint
- **Issue:** What's wrong
- **Impact:** Security/privacy consequence
- **Fix:** How to remediate
- **Test:** How to verify the fix

### Recommendations
Improvements for future development cycles.

### Metrics (for Trend Tracking)
- Total findings by severity
- Findings by category
- Comparison to previous review
- Time to remediate previous Critical issues

---

## Regression Test Library

After each review, add test cases for Critical and Important findings:

| Finding ID | Date | Description | Test Added | File |
|------------|------|-------------|------------|------|
| (Example) | 2026-02-03 | IDOR on /clients/<id> | Yes | tests/test_rbac.py |

These tests should run in CI/CD to prevent regression.

---

## Review Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Reviewer | | | |
| Developer | | | |
| (Optional) Security Lead | | | |

---

## Appendix: Architecture Notes

1. **Encrypted fields can't be searched in SQL** — client search loads accessible clients into Python memory. Documented ceiling: ~2,000 clients.

2. **Two databases** — app data in `default`, audit logs in `audit` with restricted permissions.

3. **Property accessors** — use `client.first_name`, never `client._first_name_encrypted` directly.

4. **Decryption errors** — return `"[decryption error]"` string instead of raising exception. This marker should never appear in production UI.

5. **Session storage** — server-side database sessions, not cookies.

6. **HTMX** — Used for partial page updates. Inherits Django's CSRF protection via middleware.
