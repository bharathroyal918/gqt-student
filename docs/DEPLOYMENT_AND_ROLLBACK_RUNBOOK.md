# GQT Student Portal — Deployment & Rollback Runbook

## 1. Overview & Service Mapping

| Component | Target Provider | Configuration File | Production URL |
| :--- | :--- | :--- | :--- |
| **Backend Web Service** | Render | `render.yaml`, `backend/build.sh` | `https://gqt-student.onrender.com` |
| **Frontend Single Page App** | Vercel | `frontend/package.json`, `frontend/vite.config.ts` | `https://gqt-student-uz53.vercel.app/` |
| **Database** | Supabase Cloud | Managed PostgreSQL with PgBouncer | Direct connection via `DATABASE_URL` |

---

## 2. Pre-Deployment Release Verification (Local Release Gates)

Before pushing any commit to `master` for production deployment, execute the local release verification workflow:

### Step 1: Backend System & Migration Checks
```bash
cd backend
.\venv\Scripts\python manage.py check
.\venv\Scripts\python manage.py makemigrations --check --dry-run
```
*Expected Result:* `System check identified no issues (0 silenced).` and `No changes detected`.

### Step 2: Backend Regression Test Suite
```bash
cd backend
.\venv\Scripts\pytest -q
```
*Expected Result:* All 323 tests passed.

### Step 3: Frontend Type Check & Tests
```bash
cd frontend
npx tsc --noEmit
npm test -- --run
```
*Expected Result:* 0 TypeScript errors and all Vitest suites passed.

### Step 4: Frontend Production Build
```bash
cd frontend
npm run build
```
*Expected Result:* Successful bundle compilation in `dist/`.

---

## 3. Render Backend Deployment Procedure

### 3.1 Automated Deployment via Git Push
1. Ensure `render.yaml` specifies:
   - `healthCheckPath: /health/live/`
   - `startCommand: "gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2 --timeout 60 --graceful-timeout 30 --keep-alive 5"`
2. Push clean commit to `origin/master`.
3. Render automatically triggers `backend/build.sh`:
   - Installs `requirements.txt`
   - Runs `python manage.py collectstatic --no-input`
   - Runs `python manage.py migrate --no-input`
4. Render monitors `GET /health/live/`. Once it receives HTTP 200, traffic routes to the new container.

### 3.2 Manual Render Dashboard Checks
If modifying configuration in the Render UI:
1. Navigate to: **Dashboard** > **gqt-student-portal-backend** > **Settings**.
2. Verify **Health Check Path** is set to: `/health/live/`.
3. Verify Environment Variables:
   - `DJANGO_SETTINGS_MODULE`: `config.settings.production`
   - `DEBUG`: `False`
   - `DATABASE_URL`: Valid Supabase pooled connection string
   - `ALLOWED_HOSTS`: `localhost,127.0.0.1,backend,.onrender.com,gqt-student.onrender.com`

---

## 4. Vercel Frontend Deployment Procedure

1. Navigate to: **Dashboard** > **gqt-student-portal-frontend** (or active project).
2. Verify Environment Variables:
   - `VITE_API_BASE_URL`: `https://gqt-student.onrender.com/api/v1`
3. Deploying via Git:
   - Pushing to `master` automatically compiles Vite and deploys static assets with edge caching.

---

## 5. Rollback Runbook

### 5.1 Render Backend Rollback
If an unexpected runtime regression occurs post-deployment:
1. **Via Render Dashboard:**
   - Go to **gqt-student-portal-backend** > **Deploys**.
   - Select the last known good deploy commit (e.g. `dbed397`).
   - Click **Rollback to this deploy**.
   - Render immediately points traffic back to the previous healthy container.
2. **Via Git Revert:**
   ```bash
   git revert HEAD --no-edit
   git push origin master
   ```

### 5.2 Vercel Frontend Rollback
1. Go to **Vercel Dashboard** > Project > **Deployments**.
2. Locate the previous working production deployment.
3. Click the three dots `...` and choose **Instant Rollback**.
4. Traffic instantly switches back within seconds without rebuilding.
