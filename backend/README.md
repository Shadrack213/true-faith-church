# TFCI backend (Django)

Django is the website's backend. The existing HTML/CSS/JavaScript site stays
the frontend (GitHub Pages) and reads its data from Django's REST API.

```
Visitor's browser ── GitHub Pages (HTML/CSS/JS, unchanged design)
        │  GET https://<your-api>/api/events/ ...  (read-only, published data only)
        ▼
Django + Django REST Framework  (Python host, e.g. Render)
        │  Django ORM, own login role "django_app"
        ▼
Supabase PostgreSQL: schema "django" (not exposed by Supabase's public Data API)
Supabase Storage: bucket "event-flyers" (public images, uploaded by Django)
```

## What's in backend/

| Path | Purpose |
| --- | --- |
| `config/settings.py` | All settings come from environment variables (`.env` locally). Safe production defaults. |
| `config/urls.py` | `/api/…` routes. `/admin/` only when `DJANGO_ADMIN_ENABLED=true` (admin phase). |
| `church/models.py` | Region, District, Event, ChurchLocation, Ministry, Leader |
| `church/migrations/` | `0001_initial` (tables, constraints, indexes) and `0002_seed_official_data` (confirmed data only) |
| `church/views.py`, `serializers.py`, `urls.py` | The REST API |
| `church/permissions.py` | Anyone may read; only signed-in staff with model permissions may write |
| `church/validators.py` | Flyer checks: real JPEG/PNG/WebP, max 5 MB, random file names |
| `church/admin.py` | Django Admin screens, ready for the admin phase |
| `church/tests.py` | 22 API tests |
| `sql/supabase_django_setup.sql` | One-time Supabase setup: `django` schema and `django_app` login |
| `sql/make_password_verifier.py` | Turns the `django_app` password into the hash that setup script needs |
| `.env.example` | Every setting name, with explanations |

## Data and rules

| Model | Visitors see | Notes |
| --- | --- | --- |
| Region | active | 20 regions seeded from the website |
| District | active | 3 named districts seeded; region left empty until verified |
| Event | `status = published` only (drafts and archived are hidden) | category national/regional/district; regional needs a region, district needs a district, national has neither; end ≥ start |
| ChurchLocation | verified **and** active **and** approved for the website | only the headquarters is seeded; the placeholder city lists were **not** imported |
| Ministry | published | the 7 ministries in the menu |
| Leader | published | only Apostle Thomas Adu Bempah, Acting General Overseer |

Writing (POST/PUT/PATCH/DELETE) needs a signed-in **staff** account with
Django's add/change/delete permission for that model. Anonymous visitors get 403.

## API routes

All `GET`, all JSON. Lists are paginated: `{"count", "next", "previous", "results"}`,
50 per page, `?page_size=` up to 200.

| Route | Filters |
| --- | --- |
| `/api/` | list of endpoints |
| `/api/health/` | `{"status":"ok","database":"ok"}` when the database is reachable |
| `/api/events/` | `?category=national\|regional\|district` `?region=<slug>` `?district=<slug>` `?when=upcoming\|past` |
| `/api/events/national/` | same filters |
| `/api/events/regional/` | `?region=<slug>` |
| `/api/events/district/` | `?district=<slug>` |
| `/api/events/<id>/` | |
| `/api/regions/`, `/api/regions/<slug>/` | |
| `/api/districts/`, `/api/districts/<slug>/` | `?region=<slug>` |
| `/api/church-locations/` | `?country=GH` or `?country=DE,NL`, `?kind=`, `?exclude_kind=headquarters` |
| `/api/ministries/`, `/api/ministries/<slug>/` | |
| `/api/leadership/` | `?scope=headquarters\|region\|district\|zone` |

Each event includes `flyer_url`: the full public address of its flyer (Supabase
Storage, or `assets/...` for flyers that are part of the website).
Invalid filters return `400` with a message; unknown routes return `404` JSON.

---

## 1. One-time Supabase setup

**a) Database login and schema for Django**
1. Choose a password for `django_app`: at least 32 characters, **letters and numbers only**. Save it in your password manager.
2. Turn it into a one-way hash on your computer (it is typed hidden, nothing is sent anywhere):
   `python backend/sql/make_password_verifier.py`
   This prints a line starting `SCRAM-SHA-256$4096:`.
3. Supabase dashboard → your project → **SQL Editor** → **New query** → paste `backend/sql/supabase_django_setup.sql`.
4. In the editor (not in the file), replace `REPLACE_WITH_SCRAM_VERIFIER` with that line, keeping the single quotes.
5. Click **Run**. The check row should show `true, true, false, false, false, {search_path=django}`.
6. Close the query tab **without saving it**.

The script only adds the empty `django` schema and the `django_app` login. It doesn't
touch existing tables, Storage, Auth users or other roles, and it is safe to run
again (an existing `django_app` keeps its password).

**b) Connection string**
1. Click **Connect** (top of the dashboard) → **Session pooler**. This works on all home networks; the "Direct connection" needs IPv6.
2. Copy the URI. It looks like `postgresql://postgres.<project-ref>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`.
3. Change the user from `postgres.<project-ref>` to **`django_app.<project-ref>`**, put the django_app password in place of `[YOUR-PASSWORD]`, and add `?sslmode=require` at the end.

**c) Flyer storage**
1. **Storage** → check there is a bucket called **`event-flyers`** marked **Public**. If not: **New bucket** → name `event-flyers`, **Public** on → set the file size limit to 5 MB and the allowed types to `image/jpeg, image/png, image/webp` → **Create**.
2. **Storage → S3 Configuration** (Settings): make sure **S3 connection** is enabled, then **New access key** → copy the **Access key ID** and **Secret access key** (shown once). Also note the **Region** on that page.

Keep the S3 secret, the django_app password and the Django secret key **only** in `backend/.env` and in your hosting provider's secret settings.

## 2. Run it on Windows

Open **PowerShell** in the project folder (`C:\Users\Shady\Desktop\true-faith-church`).

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell says scripts are disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

```powershell
pip install -r requirements.txt
copy .env.example .env
notepad .env
```
In `.env`, set:
- `DJANGO_SECRET_KEY`: generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DATABASE_URL`: from step 1b
- the `SUPABASE_…` storage values: from step 1c

Leave the storage values empty to keep test uploads on your computer.

```powershell
python manage.py check              # settings OK?
python manage.py showmigrations     # connects to the database; lists migrations
python manage.py migrate            # creates the tables in schema "django" + official data
python manage.py runserver 127.0.0.1:8000
```

Open these in the browser:
- http://127.0.0.1:8000/api/health/ should show `{"status": "ok", "database": "ok"}`
- http://127.0.0.1:8000/api/events/national/
- http://127.0.0.1:8000/api/events/regional/?region=ashanti-east
- http://127.0.0.1:8000/api/events/district/?district=kumasi-district
- http://127.0.0.1:8000/api/church-locations/?country=GH
- http://127.0.0.1:8000/api/regions/

**Frontend (second PowerShell window):** this repository has no Vite set-up (there is no `package.json`), so serve the static site on port 5173 with Python:
```powershell
cd C:\Users\Shady\Desktop\true-faith-church
python -m http.server 5173
```
Then open http://localhost:5173/events-national.html. On localhost the site
uses the Django API at http://127.0.0.1:8000 automatically
(`assets/js/api-config.js`). If Django isn't running, pages show their
built-in content and the browser console says `[TFCI] Events could not be loaded`.

**When you are ready for Django Admin (later phase):**
```powershell
python manage.py createsuperuser
```
Then set `DJANGO_ADMIN_ENABLED=true` in `.env`, restart, and open http://127.0.0.1:8000/admin/.
There is no public sign-up: accounts are created with `createsuperuser` or by a superuser in Admin.

## 3. Event flyers

In the admin phase: **Admin → Events → (event) → Flyer → choose file → Save**.
- Django checks that the file really is a JPEG, PNG or WebP of at most 5 MB.
- It uploads the file to the `event-flyers` bucket with a random name, so a replaced flyer always gets a fresh URL.
- It stores the file's path in PostgreSQL.
- The API returns its public URL as `flyer_url`.

The website shows it in the existing square flyer frame with a **View Flyer**
button (National Events hero card), or as the past-event card picture.

Staff can also upload through the API (`multipart/form-data`, field `flyer`)
when signed in. Anonymous uploads are refused.

## 4. Tests

```powershell
python manage.py test church
```
The tests need a PostgreSQL where the user may create a temporary test
database, i.e. a **local** PostgreSQL. Don't run them against the live Supabase
database. They cover filtering, hidden drafts and archived events, blocked
anonymous and non-staff writes, input validation, flyer upload, replace and
rejection, and CORS.

## 5. Deploying to Render

GitHub Pages only serves static files, so Django runs on Render while the website
stays on GitHub Pages. `render.yaml` (in the repository root) describes the service;
it contains **no secrets**.

- Region: Frankfurt (closest to the Supabase project in Paris). Free plan.
- Build: install requirements, `collectstatic` (Django Admin's styles), `migrate`.
- Start: `gunicorn config.wsgi:application`. Health check: `/api/health/`.
- Set automatically: `DJANGO_DEBUG=false`, a Render-generated `DJANGO_SECRET_KEY`,
  `DJANGO_ADMIN_ENABLED=true`, `CORS_ALLOWED_ORIGINS=https://shadrack213.github.io`,
  the Supabase project ref, bucket and region. Render's own address is added to
  `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` automatically (`RENDER_EXTERNAL_HOSTNAME`).
- Entered by you in Render's dashboard (never in the repository): `DATABASE_URL`,
  `SUPABASE_S3_ACCESS_KEY_ID`, `SUPABASE_S3_SECRET_ACCESS_KEY`. Copy each one from your
  private `backend/.env` without showing it:
  `backend\.venv\Scripts\python backend\sql\copy_env_value.py DATABASE_URL`
  (paste in the browser with Ctrl+V; `--clear` empties the clipboard afterwards).

Once `https://<service>.onrender.com/api/health/` shows `ok`, put that address in
`productionUrl` in `assets/js/api-config.js` and push. Only then does the live website
start using Django.

Free Render services "sleep" after about 15 minutes without visitors. The first visit
afterwards can take up to a minute; the page shows its built-in content until the data
arrives.

## About the earlier Supabase JavaScript setup

Django replaces it as the backend. The website no longer loads
`assets/js/supabase-config.js`; that file and `supabase/` are kept for
reference only and can be removed later. The `event-flyers` bucket is reused by
Django. If you already ran the old `supabase/migrations/*.sql` files, those
tables sit unused in the `public` schema and can be dropped later; ask before
removing anything.
