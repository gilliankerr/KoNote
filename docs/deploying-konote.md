# Deploying KoNote

This guide covers everything you need to get KoNote running — from local development to cloud production. Choose your path:

| I want to... | Go to... |
|--------------|----------|
| Try KoNote locally | [Local Development (Docker)](#local-development-docker) |
| Deploy to Railway | [Deploy to Railway](#deploy-to-railway) |
| Deploy to Azure | [Deploy to Azure](#deploy-to-azure) |
| Deploy to Elestio | [Deploy to Elestio](#deploy-to-elestio) |
| Set up PDF reports | [PDF Report Setup](#pdf-report-setup) |
| Go live with real data | [Before You Enter Real Data](#before-you-enter-real-data) |

---

## Is This Guide For Me?

**Yes.** This guide is written for nonprofit staff who aren't developers.

If you've ever:
- Installed WordPress or another web application
- Used Excel competently (formulas, sorting, multiple sheets)
- Followed step-by-step software instructions

...you have the skills to set up KoNote. Every step shows you exactly what to type and what to expect.

---

## Understanding Your Responsibility

KoNote stores sensitive client information. By running your own instance, you're taking on responsibility for protecting that data.

### What KoNote Does Automatically

When configured correctly, KoNote:

- **Encrypts client names, emails, birth dates, and phone numbers** — Even if someone accessed your database directly, they'd see scrambled text
- **Blocks common security mistakes** — The server won't start if critical security settings are missing
- **Logs who accesses what** — Every client view or change is recorded in a separate audit database
- **Restricts access by role** — Staff only see clients in their assigned programs

### What You Need to Do

| Your Responsibility | Why It Matters |
|---------------------|----------------|
| **Keep the encryption key safe** | If you lose it, all client data becomes unreadable — permanently |
| **Use HTTPS in production** | Without it, data travels unprotected over the internet |
| **Remove departed staff promptly** | Former employees shouldn't access client data |
| **Back up your data regularly** | Hardware fails; mistakes happen |

### When to Get Help

Consider engaging IT support if:
- Your organisation serves **vulnerable populations** (children, mental health clients, survivors of violence)
- You're subject to **specific regulatory requirements** (healthcare privacy laws, government contracts)
- You're **not comfortable** with the responsibility after reading this section

---

## Automatic Platform Detection

KoNote automatically detects which platform it's running on and configures itself appropriately:

| Platform | How It's Detected | What's Auto-Configured |
|----------|-------------------|------------------------|
| **Railway** | `RAILWAY_ENVIRONMENT` variable | Production settings, `.railway.app` domains allowed |
| **Azure App Service** | `WEBSITE_SITE_NAME` variable | Production settings, `.azurewebsites.net` domains allowed |
| **Elestio** | `ELESTIO_VM_NAME` variable | Production settings, `.elest.io` domains allowed |
| **Docker/Self-hosted** | `DATABASE_URL` is set | Production settings, localhost allowed by default |

This means you only need to set the **essential** variables for each platform — KoNote handles the rest.

### Essential Variables (All Platforms)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `AUDIT_DATABASE_URL` | PostgreSQL connection for audit logs |
| `SECRET_KEY` | Random string for session signing |
| `FIELD_ENCRYPTION_KEY` | Fernet key for PII encryption |

If something is missing, the startup check will tell you exactly what's wrong and give platform-specific hints on how to fix it.

---

## Prerequisites

### All Platforms

| Software | What It Does | Where to Get It |
|----------|--------------|-----------------|
| **Git** | Downloads the KoNote code | [git-scm.com](https://git-scm.com/download/win) |
| **Python 3.12+** | Runs the application | [python.org](https://www.python.org/downloads/) |

### For Local Development

| Software | What It Does | Where to Get It |
|----------|--------------|-----------------|
| **Docker Desktop** | Runs databases automatically | [docker.com](https://www.docker.com/products/docker-desktop/) |

---

## Generating Security Keys

You'll need two unique keys for any deployment. Generate them on your computer:

```bash
# Generate SECRET_KEY (Django sessions)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate FIELD_ENCRYPTION_KEY (PII encryption)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Save both keys securely.** The `FIELD_ENCRYPTION_KEY` is especially critical — if you lose it, all encrypted client data is unrecoverable.

---

## Local Development (Docker)

Docker handles PostgreSQL, the web server, and all dependencies automatically. This is the recommended path for trying KoNote.

**Time estimate:** 30–45 minutes

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/konote-web.git
cd konote-web
```

### Step 2: Create Environment File

```bash
copy .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` and add your generated keys:

```ini
SECRET_KEY=your-generated-secret-key-here
FIELD_ENCRYPTION_KEY=your-generated-encryption-key-here

POSTGRES_USER=konote
POSTGRES_PASSWORD=MySecurePassword123
POSTGRES_DB=konote

AUDIT_POSTGRES_USER=audit_writer
AUDIT_POSTGRES_PASSWORD=AnotherPassword456
AUDIT_POSTGRES_DB=konote_audit
```

### Step 4: Start the Containers

```bash
docker-compose up -d
```

Wait about 30 seconds for health checks to pass.

### Step 5: Run Migrations

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py migrate --database=audit
```

### Step 6: Create Admin User

```bash
docker-compose exec web python manage.py createsuperuser
```

### Step 7: Access KoNote

Open **http://localhost:8000** and log in.

### Docker Commands Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all containers |
| `docker-compose down` | Stop all containers |
| `docker-compose logs web` | View application logs |
| `docker-compose down -v` | Stop and delete all data |

---

## Deploy to Railway

Railway automatically builds and deploys from GitHub. Best for small organisations wanting simple cloud hosting.

**Estimated cost:** ~$45–50/month (app + two databases)

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select **konote-web**
4. Click **Deploy**

### Step 2: Add PostgreSQL Databases

KoNote needs **two** PostgreSQL databases (main + audit).

1. Click **+ Add** → **Add from Marketplace** → **PostgreSQL**
2. Wait for it to initialise
3. Repeat to add a second PostgreSQL database

### Step 3: Configure Environment Variables

In your Railway project, click **Variables** on your app service and add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Your generated key |
| `FIELD_ENCRYPTION_KEY` | Your generated key |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (use your first database's name) |
| `AUDIT_DATABASE_URL` | `${{Postgres-XXXX.DATABASE_URL}}` (use your second database's name) |

**Note:** The `${{ServiceName.DATABASE_URL}}` syntax tells Railway to pull the URL from your Postgres service. Check your database service names in the Railway dashboard.

Optional variables (auto-detected, only set if needed):
- `ALLOWED_HOSTS` — Auto-includes `.railway.app` domains
- `AUTH_MODE` — Defaults to `local`, set to `azure` for SSO

### Step 4: Redeploy

Click **Redeploy** and wait for the build to complete.

### Step 5: Verify

Click the generated domain (e.g., `konote-web-production-xxxx.up.railway.app`). You should see the login page.

### Adding a Custom Domain

1. In Railway, find **Domain** section
2. Click **Add Custom Domain**
3. Enter your domain (e.g., `outcomes.myorg.ca`)
4. Follow DNS instructions from Railway
5. Update `ALLOWED_HOSTS` to include your domain

### Azure AD SSO (Optional)

To let users log in with Microsoft credentials:

1. Register an app in [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Set redirect URI to `https://your-domain/auth/callback/`
3. Create a client secret
4. Add to Railway variables:
   - `AUTH_MODE=azure`
   - `AZURE_CLIENT_ID=...`
   - `AZURE_CLIENT_SECRET=...`
   - `AZURE_TENANT_ID=...`
   - `AZURE_REDIRECT_URI=https://your-domain/auth/callback/`

---

## Deploy to Azure

Azure Container Apps provides enterprise-grade hosting with Azure AD integration.

**Time estimate:** 1–2 hours

### Step 1: Create Resource Group

```bash
az group create --name konote-prod --location canadacentral
```

### Step 2: Create PostgreSQL Databases

```bash
# Main database
az postgres flexible-server create \
  --resource-group konote-prod \
  --name konote-db \
  --location canadacentral \
  --admin-user konote \
  --admin-password <YOUR_PASSWORD> \
  --version 16

# Audit database
az postgres flexible-server create \
  --resource-group konote-prod \
  --name konote-audit-db \
  --location canadacentral \
  --admin-user audit_writer \
  --admin-password <YOUR_AUDIT_PASSWORD> \
  --version 16
```

Create the databases:

```bash
az postgres flexible-server db create \
  --resource-group konote-prod \
  --server-name konote-db \
  --database-name konote

az postgres flexible-server db create \
  --resource-group konote-prod \
  --server-name konote-audit-db \
  --database-name konote_audit
```

### Step 3: Create Container Registry

```bash
az acr create \
  --resource-group konote-prod \
  --name konoteregistry \
  --sku Basic
```

### Step 4: Build and Push Docker Image

```bash
docker build -t konote:latest .
az acr login --name konoteregistry
docker tag konote:latest konoteregistry.azurecr.io/konote:latest
docker push konoteregistry.azurecr.io/konote:latest
```

### Step 5: Create Container App

```bash
az containerapp create \
  --name konote-web \
  --resource-group konote-prod \
  --environment konote-env \
  --image konoteregistry.azurecr.io/konote:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server konoteregistry.azurecr.io \
  --cpu 0.5 \
  --memory 1Gi
```

### Step 6: Configure Environment Variables

In Azure Portal, go to your Container App → Containers → Environment variables. Add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Your generated key |
| `FIELD_ENCRYPTION_KEY` | Your generated key |
| `DATABASE_URL` | `postgresql://konote:PASSWORD@konote-db.postgres.database.azure.com:5432/konote` |
| `AUDIT_DATABASE_URL` | `postgresql://audit_writer:PASSWORD@konote-audit-db.postgres.database.azure.com:5432/konote_audit` |

Optional (auto-detected):
- `ALLOWED_HOSTS` — Auto-includes `.azurewebsites.net` domains; add custom domains if needed
- `AUTH_MODE` — Defaults to `local`, set to `azure` for Azure AD SSO

### Step 7: Run Migrations

Create a temporary Azure Container Instance to run migrations:

```bash
az container create \
  --resource-group konote-prod \
  --name konote-migrate \
  --image konoteregistry.azurecr.io/konote:latest \
  --environment-variables DATABASE_URL="..." AUDIT_DATABASE_URL="..." SECRET_KEY="..." FIELD_ENCRYPTION_KEY="..." \
  --command-line "/bin/bash -c 'python manage.py migrate && python manage.py migrate --database=audit'"
```

Delete the container after it completes.

### Step 8: Configure Custom Domain

1. Go to Container App → Custom domains
2. Add your domain
3. Follow Azure's DNS validation instructions
4. Azure automatically provisions an SSL certificate

---

## Deploy to Elestio

Elestio runs Docker Compose applications with managed services.

### Step 1: Create Service

1. Log in to [elest.io](https://elest.io)
2. Create a new **Docker Compose** service
3. Paste your `docker-compose.yml` content

### Step 2: Configure Environment Variables

Add these in the Elestio dashboard:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Your generated key |
| `FIELD_ENCRYPTION_KEY` | Your generated key |
| `DATABASE_URL` | `postgresql://konote:konote@db:5432/konote` |
| `AUDIT_DATABASE_URL` | `postgresql://audit_writer:audit_pass@audit_db:5432/konote_audit` |

Optional (auto-detected):
- `ALLOWED_HOSTS` — Auto-includes `.elest.io` domains; add custom domains if needed
- `AUTH_MODE` — Defaults to `local`, set to `azure` for Azure AD SSO

### Step 3: Connect GitHub Repository

1. Go to Repository settings in Elestio
2. Connect to your GitHub account
3. Select the `konote-web` repository
4. Choose the `main` branch

### Step 4: Run Initial Setup

In the Elestio console, run:

```bash
python manage.py migrate
python manage.py migrate --database=audit
python manage.py lockdown_audit_db
```

KoNote auto-detects Elestio and uses production settings automatically.

### Step 5: Configure Domain and TLS

1. Point your domain's DNS to Elestio's IP
2. In Elestio, add your custom domain
3. Enable HTTPS enforcement

---

## PDF Report Setup

KoNote can generate PDF reports using WeasyPrint. This is optional — the app works fully without it.

### Quick Check

```bash
python manage.py shell -c "from apps.reports.pdf_utils import is_pdf_available; print('PDF available:', is_pdf_available())"
```

### Installation by Platform

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**macOS:**
```bash
brew install pango gdk-pixbuf libffi
```

**Windows:** Requires GTK3 runtime. Install [MSYS2](https://www.msys2.org/), then:
```bash
pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-gdk-pixbuf2
```
Add `C:\msys64\mingw64\bin` to your PATH.

**Docker:** The Dockerfile should include:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

### Working Without PDF

If you skip PDF setup:
- All features except PDF export work normally
- Users can still view reports in-browser
- CSV export is available
- Browser "Print to PDF" works as an alternative

---

## Before You Enter Real Data

Complete this checklist before entering any real client information.

### 1. Encryption Key Backup

- [ ] I have copied my `FIELD_ENCRYPTION_KEY` to a secure location (password manager, encrypted file)
- [ ] The backup is stored **separately** from my database backups
- [ ] I can retrieve the key without logging into KoNote

**Test yourself:** Close this document. Can you retrieve your encryption key from your backup? If not, fix that now.

### 2. Database Backups Configured

- [ ] I know how backups happen (manual, scheduled, or hosting provider automatic)
- [ ] I have tested restoring from a backup at least once
- [ ] Backups are stored in a different location than the database

### 3. User Accounts Set Up

- [ ] All staff accounts created with correct roles
- [ ] Test users and demo accounts removed or disabled

### 4. Security Settings Verified

Run the deployment check:

```bash
# Docker:
docker-compose exec web python manage.py check --deploy

# Direct:
python manage.py check --deploy
```

You should see no errors about `FIELD_ENCRYPTION_KEY`, `SECRET_KEY`, or `CSRF`.

### 5. Final Sign-Off

- [ ] I have verified my encryption key is backed up and retrievable
- [ ] I understand that losing my encryption key means losing client PII
- [ ] My team has been trained on data entry procedures
- [ ] I know who to contact if something goes wrong

---

## Troubleshooting

### "FIELD_ENCRYPTION_KEY not configured"

Generate and add a key to your `.env`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Database connection refused

1. Check PostgreSQL is running
2. Verify credentials in `DATABASE_URL` match your database setup
3. For Docker: ensure containers are up (`docker-compose ps`)

### Port 8000 already in use

Run on a different port:
```bash
python manage.py runserver 8080
```

### Container keeps restarting

Check logs for the error:
```bash
docker-compose logs web
```

Usually caused by missing environment variables.

---

## Glossary

| Term | What It Means |
|------|---------------|
| **Terminal** | A text-based window where you type commands |
| **Repository** | A folder containing all the code, stored on GitHub |
| **Clone** | Download a copy of code from GitHub to your computer |
| **Migration** | A script that creates database tables |
| **Container** | A self-contained package that runs the application |
| **Environment variables** | Settings stored in a `.env` file |
| **Encryption key** | A password used to scramble sensitive data |

---

## Next Steps

Once your deployment is running:

1. **[Administering KoNote](administering-konote.md)** — Configure your agency's settings
2. **[Using KoNote](using-konote.md)** — Train your staff
