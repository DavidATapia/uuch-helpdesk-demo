# Deployment Prep

This proof of concept is ready for production-style environment variables, but it still uses local SQLite storage. That is fine for a demo, but Cloud Run instances have ephemeral filesystems, so real production use should move tickets to Firestore, Cloud SQL, or another managed data store.

## Required Environment Variables

Set these before publishing:

- `APP_ENV=production`
- `SECRET_KEY`
- `STAFF_PASSWORD`
- `MAX_TICKETS=30`

When `APP_ENV=production` or Cloud Run is detected, the app refuses to start if `SECRET_KEY` or `STAFF_PASSWORD` are still using demo defaults.

## Generate Values

```bash
python3 - <<'PY'
import secrets

print("SECRET_KEY=" + secrets.token_urlsafe(48))
print("STAFF_PASSWORD=" + secrets.token_urlsafe(18))
PY
```

Keep the generated values somewhere private.

## Current Google Cloud State

`gcloud` is installed and authenticated. The active account is configured, but no project is currently selected.

The project created for this proof of concept is:

```text
church-helpdesk-demo-dtapia
```

Specific inventory for unrelated existing projects should stay in private notes, not in shared handoff documentation.

## Configure Google Cloud

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

For this demo project:

```bash
gcloud config set project church-helpdesk-demo-dtapia
gcloud config set run/region us-central1
```

Billing has been linked to the selected billing account named `BillingAccount`.

Deployment services have been enabled:

- Cloud Run
- Cloud Build
- Artifact Registry

The service has been deployed:

```text
https://church-helpdesk-429193551151.us-central1.run.app
```

The current public health endpoint is:

```text
https://church-helpdesk-429193551151.us-central1.run.app/health
```

## Deploy To Cloud Run

```bash
export CHURCH_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export CHURCH_STAFF_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"

gcloud run deploy church-helpdesk \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "APP_ENV=production,SECRET_KEY=${CHURCH_SECRET_KEY},STAFF_PASSWORD=${CHURCH_STAFF_PASSWORD},MAX_TICKETS=30"
```

After deployment:

```bash
gcloud run services describe church-helpdesk \
  --region us-central1 \
  --format='value(status.url)'
```

## Later Hardening

- Move secrets into Google Secret Manager.
- Replace the simple staff password gate with Google login or another identity provider.
- Move ticket storage out of local SQLite.
- Configure real email delivery instead of preview notifications.
