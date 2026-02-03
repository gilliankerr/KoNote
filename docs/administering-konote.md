# Administering KoNote

This guide covers everything administrators need to configure, maintain, and secure their KoNote instance.

| I want to... | Go to... |
|--------------|----------|
| Set up my agency's instance | [Agency Configuration](#agency-configuration) |
| Create user accounts | [User Management](#user-management) |
| Back up my data | [Backup and Restore](#backup-and-restore) |
| Run security checks | [Security Operations](#security-operations) |

---

## Agency Configuration

After deployment, configure KoNote to match your organisation's needs. All setup is done through the web interface — no technical knowledge required.

**Time estimate:** 30–45 minutes for basic setup.

### First Login

**Azure AD (Office 365):**
1. Navigate to your KoNote URL
2. Click **Login with Azure AD**
3. Enter your work email and password

**Local authentication:**
1. Navigate to your KoNote URL
2. Enter username and password (provided during setup)

Your account starts as Staff. An admin must promote you to Admin to access configuration.

---

### Instance Settings

Control your organisation's branding and behaviour.

1. Click the **gear icon** (top-right) → **Instance Settings**
2. Configure:

| Field | What it does | Example |
|-------|--------------|---------|
| **Product Name** | Shown in header and titles | "Youth Housing — KoNote" |
| **Support Email** | Displayed in footer | support@agency.ca |
| **Logo URL** | Your organisation's logo | https://example.com/logo.png |
| **Date Format** | How dates appear | 2026-02-03 (ISO) |
| **Session Timeout** | Minutes before auto-logout | 30 |

3. Click **Save**

---

### Customise Terminology

Change default terms to match your organisation's vocabulary.

1. Click **gear icon** → **Terminology**
2. Edit terms as needed:
   - "Client" → "Participant", "Member", "Service User"
   - "Program" → "Service", "Initiative", "Stream"
   - "Target" → "Goal", "Objective", "Milestone"
3. Click **Save**

Changes apply immediately throughout the app.

---

### Enable/Disable Features

Toggle features based on your workflow.

1. Click **gear icon** → **Features**
2. Enable or disable:

| Feature | What it does |
|---------|--------------|
| **Programs** | Multiple service streams. Disable if single program. |
| **Custom Client Fields** | Extra data fields (funding source, referral date) |
| **Metric Alerts** | Notify staff when metrics hit thresholds |
| **Event Tracking** | Record intake, discharge, crisis, etc. |
| **Funder Report Exports** | Generate formatted reports for funders |

3. Click **Save**

Features can be toggled later without losing data.

---

### Create Programs

A program is a distinct service line your agency offers.

1. Click **gear icon** → **Programs**
2. Click **+ New Program**
3. Enter name and description
4. Click **Create**

**Assign staff to programs:**
1. Click the program name
2. Select a user from the dropdown
3. Choose role: "Coordinator" (manages) or "Staff" (delivers services)
4. Click **Add**

---

### Set Up Plan Templates

Plan templates are reusable blueprints for client outcome plans.

**Key concepts:**
- **Section** — Broad category (Housing, Employment, Health)
- **Target** — Specific goal within a section
- **Template** — Collection of sections and targets

**Create a template:**
1. Click **gear icon** → **Plan Templates**
2. Click **+ New Template**
3. Add sections and targets

**Example template:**
- **Housing**
  - Maintain stable housing for 3+ months
  - Develop independent living skills
- **Employment**
  - Enroll in or maintain employment/education
  - Achieve 80% attendance rate

Changes to templates don't affect existing client plans.

---

### Set Up Progress Note Templates

Note templates provide structure for staff documentation.

1. Click **gear icon** → **Progress Note Templates**
2. Click **+ New Template**
3. Add sections (e.g., Summary, Progress on Goals, Barriers, Next Steps)

---

### Configure Custom Fields

Capture agency-specific information not in the standard client form.

**Create a field group:**
1. Click **gear icon** → **Custom Client Fields**
2. Click **+ New Field Group**
3. Enter title (e.g., "Funding & Referral")

**Add custom fields:**
1. Click **+ New Custom Field**
2. Configure:
   - **Name:** e.g., "Funding Source"
   - **Type:** Text, Number, Date, Dropdown, Checkbox
   - **Required:** Staff must fill in
   - **Sensitive:** Contains private information
   - **Choices:** (for dropdowns) "Government, Private, Foundation"

---

## User Management

### Create User Accounts

1. Click **gear icon** → **User Management**
2. Click **+ New User**
3. Fill in:
   - **Display Name:** Full name (shown in reports)
   - **Username:** (local auth) Login name
   - **Email:** Work email
   - **Password:** (local auth) Temporary password
   - **Is Admin:** Check for configuration access
4. Click **Create**

### User Roles

| Role | Can do |
|------|--------|
| **Admin** | All settings, user management, templates |
| **Program Manager** | Program-level management |
| **Staff** | Enter data, write notes, view clients in assigned programs |
| **Receptionist** | Limited client info, basic data entry |

### Deactivate Users

When someone leaves:
1. Go to **User Management**
2. Click user → **Edit**
3. Uncheck **Is Active**
4. Click **Save**

They can no longer log in, but historical data is preserved.

---

## Backup and Restore

KoNote stores data in **two PostgreSQL databases**:
- **Main database** — clients, programs, plans, notes
- **Audit database** — immutable log of every change

### Critical: The Encryption Key

**If you lose `FIELD_ENCRYPTION_KEY`, all encrypted client data is permanently unrecoverable.**

Store it separately from database backups:
- Password manager (1Password, Bitwarden)
- Azure Key Vault
- Encrypted file with restricted access

**Never store it:**
- In the same location as database backups
- In version control (Git)
- In plain text on shared drives

---

### Manual Backup

**Docker Compose:**
```bash
# Main database
docker compose exec db pg_dump -U konote konote > backup_main_$(date +%Y-%m-%d).sql

# Audit database
docker compose exec audit_db pg_dump -U audit_writer konote_audit > backup_audit_$(date +%Y-%m-%d).sql
```

**Plain PostgreSQL:**
```bash
pg_dump -h hostname -U konote -d konote > backup_main_$(date +%Y-%m-%d).sql
pg_dump -h hostname -U audit_writer -d konote_audit > backup_audit_$(date +%Y-%m-%d).sql
```

### Automated Backups

**Windows Task Scheduler:**

Save as `C:\KoNote\backup_konote.ps1`:

```powershell
$BackupDir = "C:\Backups\KoNote"
$KoNoteDir = "C:\KoNote\konote-web"
$Date = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force }

Set-Location $KoNoteDir

# Main database
docker compose exec -T db pg_dump -U konote konote | Out-File -FilePath "$BackupDir\backup_main_$Date.sql" -Encoding utf8

# Audit database
docker compose exec -T audit_db pg_dump -U audit_writer konote_audit | Out-File -FilePath "$BackupDir\backup_audit_$Date.sql" -Encoding utf8

# Clean up backups older than 30 days
Get-ChildItem -Path $BackupDir -Filter "backup_*.sql" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force
```

Schedule via Task Scheduler to run daily at 2:00 AM.

**Linux/Mac Cron:**

Save as `/home/user/backup_konote.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/konote"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

mkdir -p "$BACKUP_DIR"

docker compose -f /path/to/konote-web/docker-compose.yml exec -T db pg_dump -U konote konote > "$BACKUP_DIR/backup_main_$DATE.sql"
docker compose -f /path/to/konote-web/docker-compose.yml exec -T audit_db pg_dump -U audit_writer konote_audit > "$BACKUP_DIR/backup_audit_$DATE.sql"

# Clean up old backups
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +30 -delete
```

Add to crontab: `0 2 * * * /home/user/backup_konote.sh`

### Cloud Provider Backups

- **Railway:** Automatic daily backups (7 days retention). Restore via dashboard.
- **Azure:** Automatic backups. Configure retention in PostgreSQL server settings.
- **Elestio:** Configure via dashboard or use managed PostgreSQL.

### Restore from Backup

**Docker Compose:**
```bash
# Stop containers
docker compose down

# Remove old volumes (WARNING: deletes current data)
docker volume rm konote-web_pgdata konote-web_audit_pgdata

# Start fresh containers
docker compose up -d

# Wait 10 seconds, then restore
docker compose exec -T db psql -U konote konote < backup_main_2026-02-03.sql
docker compose exec -T audit_db psql -U audit_writer konote_audit < backup_audit_2026-02-03.sql
```

### Backup Retention Policy

| Type | Frequency | Retention |
|------|-----------|-----------|
| Daily | Every night | 30 days |
| Weekly | Every Monday | 90 days |
| Monthly | First of month | 1 year |

---

## Security Operations

### Quick Reference

| Task | Command |
|------|---------|
| Basic check | `python manage.py check` |
| Deployment check | `python manage.py check --deploy` |
| Security audit | `python manage.py security_audit` |
| Run security tests | `pytest tests/test_security.py tests/test_rbac.py -v` |

---

### Security Checks

KoNote runs security checks automatically. You can also run them explicitly:

```bash
python manage.py check --deploy
```

**Check IDs:**

| ID | Severity | What It Checks |
|----|----------|----------------|
| `konote.E001` | Error | Encryption key exists and valid |
| `konote.E002` | Error | Security middleware loaded |
| `konote.W001` | Warning | DEBUG=True in production |
| `konote.W002` | Warning | Session cookies not secure |
| `konote.W003` | Warning | CSRF cookies not secure |

Errors prevent server start. Warnings indicate security gaps.

---

### Security Audit

For deeper analysis:

```bash
python manage.py security_audit
```

This checks encryption, access controls, audit logging, and configuration.

**Categories:**
- `ENC` — Encryption (key validity, ciphertext verification)
- `RBAC` — Role-based access control
- `AUD` — Audit logging
- `CFG` — Configuration (DEBUG, cookies, middleware)

---

### Audit Logging

Every significant action is logged to a separate audit database.

**What gets logged:**
- Login/Logout (user, timestamp, IP, success/failure)
- Client views (who viewed which client)
- Create/Update/Delete (what changed, old/new values)
- Exports (who exported what)
- Admin actions (settings changes, user management)

**View audit logs:**
1. Log in as Admin
2. Click **Admin** → **Audit Logs**
3. Filter by date, user, or action type

**Query audit database directly:**
```sql
SELECT event_timestamp, user_display, action, resource_type
FROM audit_auditlog
ORDER BY event_timestamp DESC
LIMIT 20;
```

---

### Encryption Key Management

`FIELD_ENCRYPTION_KEY` encrypts all PII:
- Client names (first, middle, last, preferred)
- Email addresses
- Phone numbers
- Dates of birth
- Sensitive custom fields

**Rotating the key:**

```bash
# 1. Generate new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Rotate (re-encrypts all data)
python manage.py rotate_encryption_key --old-key="OLD" --new-key="NEW"

# 3. Update .env with new key
# 4. Restart application
# 5. Verify it works
# 6. Securely delete old key
```

**Rotation schedule:**
- Every 90 days (baseline)
- When staff with key access leave (immediately)
- After suspected security incident (immediately)

---

### Pre-Deployment Checklist

**Required:**
- [ ] `FIELD_ENCRYPTION_KEY` set to unique generated key
- [ ] `SECRET_KEY` set to unique generated key
- [ ] `DEBUG=False`
- [ ] `python manage.py check --deploy` passes

**Strongly recommended:**
- [ ] `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] `CSRF_COOKIE_SECURE=True` (requires HTTPS)
- [ ] HTTPS configured
- [ ] Encryption key backed up separately from database
- [ ] All test users removed

---

### Incident Response

**Suspected data breach:**
1. Rotate encryption key immediately
2. Rotate SECRET_KEY (invalidates all sessions)
3. Review audit logs for unauthorized access
4. Document timeline
5. Notify affected parties per PIPEDA/GDPR (typically within 72 hours)

**Lost encryption key:**
- Encrypted PII fields are **permanently unrecoverable**
- Non-PII data (notes, metrics) remains accessible
- Consider this a data loss incident for compliance

**Suspicious login activity:**
```sql
SELECT event_timestamp, ip_address, metadata
FROM audit_auditlog
WHERE action = 'login_failed'
ORDER BY event_timestamp DESC;
```

---

## Troubleshooting

### Q: I see a login error
**A:** For Azure AD, check your email is registered. For local auth, confirm credentials with an admin.

### Q: Can I change terminology later?
**A:** Yes. Changes apply immediately to all users.

### Q: What if I delete a program?
**A:** You can't delete programs with active clients. Deactivate instead.

### Q: Do staff need to fill all custom fields?
**A:** Only if marked "Required".

### Q: Does editing a template affect existing plans?
**A:** No. Templates only apply to new plans.

---

## Support

- **Documentation:** Return to [docs/index.md](index.md)
- **Bug reports:** Contact your deployment support team
- **Security vulnerabilities:** See [SECURITY.md](../SECURITY.md)

---

**Version 1.0** — KoNote Web
Last updated: 2026-02-03
