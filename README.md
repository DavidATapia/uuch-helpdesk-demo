# UUCH Help Desk Proof of Concept

A local proof-of-concept help desk for UUCH requests. It includes a request form, staff dashboard, ticket detail pages, comments, activity history, and SQLite-backed demo data.

## Local Setup

```bash
cd /workspaces/church
sudo apt-get install -y python3-flask gunicorn
python app.py
```

Open `http://127.0.0.1:5000`.

The staff dashboard uses a simple demo password gate. The default password is:

```text
church-demo
```

To set a different local password:

```bash
STAFF_PASSWORD="replace-this" python app.py
```

Demo display and notification settings live in:

```text
demo_settings.json
```

A production-style environment template is available at:

```text
.env.example
```

## Reset Demo Data

```bash
python seed_demo.py
```

or:

```bash
flask --app app seed-demo
```

## Main Screens

- `/` or `/request` - public request submission form.
- `/request/confirmation/<id>` - public request confirmation page.
- `/staff/login` - staff sign in.
- `/tickets` - staff dashboard.
- `/tickets/<id>` - ticket detail, triage, comments, and activity.
- `/notifications` - staff-only preview log for notification emails/messages.
- `/settings` - staff-only demo configuration page.
- `/health` - simple health check.
- `/healthz` - local fallback health check.

## Notification Preview Log

This proof of concept does not send real email. Instead, it records preview notifications when:

- A new request is submitted.
- Staff changes status, priority, or assignee.
- Staff adds a public or internal comment.

Use `/notifications` after signing in to review the mock messages.

## Demo Settings

Use `/settings` after signing in to adjust:

- Church/demo name.
- Staff notification recipient placeholder.
- Requester reply-from placeholder.
- Notification mode label.
- Public contact instructions.
- Request category labels used in the public request form.
- Staff team labels used in the assignee dropdown.
- Site admin placeholder names for a future individual-login phase.

## Deployment Notes

The app includes `requirements.txt` and a `Procfile` so it can be deployed to Google Cloud Run from source once `gcloud` is configured. Cloud Run will use `requirements.txt`; the local container can use Ubuntu packages.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the current deployment prep checklist, secret generation commands, and Cloud Run commands.

Likely deployment flow:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy church-helpdesk --source . --region us-central1 --allow-unauthenticated
```

For a public demo, use placeholder data only until authentication, data retention, privacy, and notification rules are designed.

Before publishing, set production values for `SECRET_KEY` and `STAFF_PASSWORD`. When `APP_ENV=production` or Cloud Run is detected, the app refuses to start if those values are still using demo defaults.

Current demo Cloud Run URL:

```text
https://church-helpdesk-429193551151.us-central1.run.app
```
