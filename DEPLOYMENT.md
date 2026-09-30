# GQT Student Portal — Production Deployment & Operations Manual

## 1. Executive Deployment Overview
This document outlines the standard operating procedures for deploying, maintaining, and scaling the **Global Quality Technologies (GQT) Student Portal** across Development, Staging, and Production environments.

---

## 2. Environment Architecture & Matrix

| Dimension | Development | Staging | Production |
|---|---|---|---|
| **URL** | `http://localhost:5173` | `https://staging-portal.gqt.edu` | `https://portal.gqt.edu` |
| **API URL** | `http://127.0.0.1:8000/api/v1` | `https://staging-api.portal.gqt.edu/api/v1` | `https://api.portal.gqt.edu/api/v1` |
| **Settings Module** | `config.settings.development` | `config.settings.staging` | `config.settings.production` |
| **DEBUG** | `True` | `False` | `False` |
| **HTTPS / SSL** | Optional | Enforced (`SECURE_SSL_REDIRECT=True`) | Enforced (`HSTS 31536000s + Preload`) |
| **Database** | PostgreSQL / SQLite | Managed PostgreSQL (RDS/Cloud SQL) | High-Availability PostgreSQL Cluster |
| **Cache / Queue** | Local Redis | Managed Redis (ElastiCache/MemoryStore) | Multi-node Redis Cluster |
| **Media Assets** | Local filesystem (`media/`) | S3 / R2 Bucket | S3 Bucket + CloudFront CDN |
| **Code Judge** | Mock Provider / Local Judge0 | Isolated Judge0 Container | High-Throughput Judge0 Cluster |
| **AI Mentor** | Mock Provider / Gemini API | Gemini Flash / OpenAI 4o-mini | Enterprise Gemini / GPT Cluster |
| **Email Delivery** | Console Backend | Sandboxed SMTP (Mailtrap) | SendGrid / AWS SES with SPF & DKIM |

---

## 3. Production Readiness & Security Checklist

- [x] `DEBUG = False` verified in production settings.
- [x] Unique, cryptographically secure `DJANGO_SECRET_KEY` (64+ chars) loaded from environment secret store.
- [x] `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` locked to canonical production domains.
- [x] HTTPS enforced with HSTS (`SECURE_HSTS_SECONDS = 31536000`), secure session cookies (`SESSION_COOKIE_SECURE = True`), and secure CSRF cookies (`CSRF_COOKIE_SECURE = True`).
- [x] `X_FRAME_OPTIONS = 'DENY'` and `SECURE_CONTENT_TYPE_NOSNIFF = True` enabled.
- [x] Centralized logging with JSON formatting and automated secret scrubbing (`safe_scrub_secrets`).
- [x] Zero student code executed inside the web server process; sandboxing delegated to external containerized workers.

---

## 4. Production Deployment Workflow

### Step 1: Clone Repository & Populate Environment Variables
```bash
git clone https://github.com/gqt-technologies/gqt-student-portal.git /opt/gqt-portal
cd /opt/gqt-portal

# Copy environment template and inject production secrets from Vault/AWS Secrets Manager
cp .env.example .env
chmod 600 .env
```

### Step 2: Database Migration Strategy
Run migrations with transactional safety before switching web traffic:
```bash
cd /opt/gqt-portal/backend
source .venv/bin/activate

# 1. Inspect unapplied migrations
python manage.py showmigrations --settings=config.settings.production

# 2. Apply database migrations
python manage.py migrate --no-input --settings=config.settings.production
```

### Step 3: Collect Static Assets
Compress and manifest static assets for WhiteNoise or CDN distribution:
```bash
python manage.py collectstatic --no-input --clear --settings=config.settings.production
```

### Step 4: Build Frontend Single-Page Application
Compile TypeScript assets with route-level code splitting:
```bash
cd /opt/gqt-portal/frontend
npm ci --production=false
npm run build

# Verify build outputs generated in dist/
ls -la dist/
```

### Step 5: Start Application Services (Systemd / Docker)
#### A. Web Service (Gunicorn / Uvicorn ASGI)
```bash
gunicorn config.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --threads 2 \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile -
```

#### B. Celery Background Worker
```bash
celery -A config worker \
  --loglevel=INFO \
  --concurrency=4 \
  --queues=code_execution,ai,notifications,reports,default \
  -n worker1@%h
```

#### C. Celery Beat Scheduler (Periodic Tasks & Deadline Notifications)
```bash
celery -A config beat \
  --loglevel=INFO \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 5. Health Probes & Monitoring

The platform exposes standardized endpoints for load balancers and orchestrators:

- **Liveness Probe** (`GET /api/v1/health/live/`):
  - Returns HTTP 200 `{ "status": "alive" }`.
  - Use in Kubernetes `livenessProbe` (interval: 10s, timeout: 2s).
- **Readiness Probe** (`GET /api/v1/health/ready/`):
  - Verifies database query execution (`SELECT 1`) and Redis cache read/write ping.
  - Returns HTTP 200 `{ "status": "ready" }` or HTTP 503 if dependencies are degraded.
  - Use in Kubernetes `readinessProbe` (interval: 15s, timeout: 5s).
- **Full Health Telemetry** (`GET /api/v1/health/`):
  - Provides diagnostic status of database, cache, and versions.

---

## 6. Backup & Disaster Recovery

### Automated Database Backups
- **Schedule**: Full database snapshots daily at 02:00 UTC; continuous WAL archiving for Point-in-Time Recovery (PITR).
- **Manual Backup Command**:
```bash
pg_dump -Fc --no-acl --no-owner -h postgres-cluster.internal -U gqt_db_user gqt_portal_prod > /backup/gqt_db_$(date +%Y%m%d_%H%M%S).dump
```

### Database Restore Procedure
1. Stop web and worker processes to avoid partial state changes:
   ```bash
   systemctl stop gqt-backend gqt-celery-worker gqt-celery-beat
   ```
2. Restore database schema and data:
   ```bash
   pg_restore --clean --if-exists --no-acl --no-owner -h postgres-cluster.internal -U gqt_db_user -d gqt_portal_prod /backup/gqt_db_YYYYMMDD_HHMMSS.dump
   ```
3. Run migrations and restart services:
   ```bash
   python manage.py migrate --settings=config.settings.production
   systemctl start gqt-backend gqt-celery-worker gqt-celery-beat
   ```

---

## 7. Rollback Strategy

### A. Zero-Downtime Blue-Green Switch
In containerized environments (Kubernetes / ECS / Nginx upstream):
1. Keep the previous production version (**Blue**) running.
2. Deploy new version (**Green**) and verify `/api/v1/health/ready/` passes.
3. Switch routing proxy to **Green**.
4. If anomalies occur within the 15-minute monitoring window, immediately revert routing proxy back to **Blue**.

### B. Database Migration Rollback
If a schema migration must be reversed:
```bash
# Roll back to the specific previous migration target
python manage.py migrate <app_name> <migration_number> --settings=config.settings.production
```

---

## 8. Incident Handling & Emergency Runbook

### High Error Rate / Sentry Alerts
1. Inspect live structured application logs:
   ```bash
   journalctl -u gqt-backend -n 100 --no-pager
   ```
2. Verify dependency health:
   ```bash
   curl -i https://api.portal.gqt.edu/api/v1/health/
   ```
3. Check Redis memory and connection pool status:
   ```bash
   redis-cli -u $REDIS_URL info memory
   ```

### Celery Worker Queue Congestion
1. Inspect active task queues:
   ```bash
   celery -A config inspect active
   ```
2. Scale worker instances or purge non-critical pending tasks if required:
   ```bash
   celery -A config purge -Q notifications
   ```
