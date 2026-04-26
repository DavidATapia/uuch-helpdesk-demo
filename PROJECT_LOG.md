# UUCH Help Desk Proof of Concept

## Current State

This project is a Flask/SQLite proof-of-concept help desk for the Unitarian Universalist Church of Huntsville (UUCH). It lives in `/workspaces/church`.

The app is intended to demonstrate request intake, staff triage, ticket comments, notification previews, and basic settings. It is not ready for real production use because it still uses SQLite/local filesystem storage and a simple staff password gate.

A reusable Codex skill for lightweight interface review now exists at `~/.codex/skills/basic-ui-ux-usability`. It provides a checklist for basic UI/UX usability, accessibility, responsive layout, forms, navigation, and task-flow review.

## Local App

- Local URL: `http://127.0.0.1:5000`
- Local health endpoint: `http://127.0.0.1:5000/health`
- Run locally with: `python3 app.py`
- Reset demo data with: `python3 seed_demo.py`
- Local runtime packages were installed through apt: `python3-flask` and `gunicorn`
- Cloud Run still uses `requirements.txt`

## Tooling And Environment

Local runtime/development tools:

- `python3`
- `python3-flask`, installed through apt for local Flask runtime
- `gunicorn`, installed through apt for local/procfile-compatible serving
- SQLite through Python's standard `sqlite3` module

Deployment/GCP tools and services:

- `gcloud` is installed, authenticated, and configured for project `church-helpdesk-demo-dtapia`
- Cloud Run deploys from source using `requirements.txt`
- Enabled Google Cloud services:
  - `run.googleapis.com`
  - `cloudbuild.googleapis.com`
  - `artifactregistry.googleapis.com`

GitHub/source-control tools:

- `git` is used from `/workspaces/church`, which is now its own standalone Git repo
- `gh` is installed and authenticated as `DavidATapia`
- SSH authentication to GitHub works for `DavidATapia`

Codex/project workflow tools:

- Reusable Codex skill created at `~/.codex/skills/basic-ui-ux-usability`
- The skill is not part of this app repo; it is local Codex workflow support
- The skill was updated with source-grounded guidance from WCAG 2.2, Nielsen Norman Group usability heuristics, and GOV.UK Design System layout/form patterns

Current local-only changes not yet deployed:

- None known after the latest Cloud Run deployment.

Latest deployed UI changes include:

- Removed `Staff Sign In` from the top masthead.
- Removed service-time and Contact utility text from the masthead; footer still carries those site details.
- Kept the page-level `Staff Sign In` button on the request page.
- Normalized masthead/footer typography.
- Switched the app font stack to Helvetica/Arial to better match the UUCH website.
- Added a basic UI/UX usability pass:
  - Skip link and higher-contrast visible focus styles.
  - Required-field indicators and clearer request form helper text.
  - More user-facing attachment placeholder language.
  - Clearer public/internal comment visibility guidance for staff.
  - Dashboard filter reset action and table accessibility caption/scopes.
  - Small readability/responsive safeguards for long table and metadata values.
- Added mobile-friendly responsive behavior:
  - The same pages auto-adapt by screen width using CSS media queries rather than device/user-agent sniffing.
  - Staff dashboard table rows convert into labeled card-style rows on narrow screens.
  - Mobile masthead, sidebar, and panel spacing are more compact.
  - Requester name field uses mobile-friendly name autocomplete.
- Updated staff dashboard filters:
  - Status, category, and priority dropdown choices auto-apply on change.
  - The visible Apply button was removed.
  - Reset remains visible.
  - Search still submits when staff press Enter.
  - Filter changes and Reset now return to the dashboard summary anchor instead of the top of the page.
- Refined phone dashboard layout:
  - The Total/Open/Urgent/Resolved metric boxes stay in a compact single-row four-column grid on phone-width screens.
- Added demo guardrails:
  - Public ticket creation is capped at 30 total tickets by `MAX_TICKETS=30`.
  - The request form shows how many demo ticket slots are currently used.
  - When the cap is reached, browser submission is disabled and direct POSTs return a limit message.
  - The deployed staff password was simplified for demo sharing; the current value is stored only in `PRIVATE_NOTES.md`.
- Changed the public request form's `Ministry or Team` field to a dropdown populated from the Settings page's staff team labels, with a public-facing `Not sure` option and without exposing the staff-only `Unassigned` label.
- Staff dashboard table supports column sorting for every displayed column, with active ascending/descending arrows.
- Staff dashboard filter row uses `Assignee` instead of `Category`, while the Category column remains visible and sortable.
- Public request form Priority is no longer required; blank priority submissions are saved as `Normal` for staff triage.
- Public request form Category options are now configurable on Settings, and `Other` is kept available at the bottom automatically.
- Settings page is grouped into Ticket / Request Configuration and Admin Configuration blocks.
- Admin Configuration includes a configurable placeholder list of site admins: Staff, Shalin, Treo, Wayne, and David. This list is not wired into authentication yet.
- Settings page desktop layout places Admin Configuration directly to the right of Ticket / Request Configuration, while keeping the groups stacked on narrower screens.

## Deployed App

- Cloud Run URL: `https://church-helpdesk-429193551151.us-central1.run.app`
- Health endpoint: `https://church-helpdesk-429193551151.us-central1.run.app/health`
- GitHub repo target: `https://github.com/DavidATapia/uuch-helpdesk-demo`
- Google Cloud project: `church-helpdesk-demo-dtapia`
- Cloud Run service: `church-helpdesk`
- Region: `us-central1`
- Latest deployed revision recorded here: `church-helpdesk-00019-fmr`
- Billing is linked to the selected billing account named `BillingAccount`
- Enabled services:
  - `run.googleapis.com`
  - `cloudbuild.googleapis.com`
  - `artifactregistry.googleapis.com`
- The deployed app includes the latest masthead typography/link refinements, the request team dropdown, sortable dashboard columns, and the basic UI/UX usability pass.
- The deployed app includes the mobile-friendly responsive refinements.

Deployment notes:

- `.gcloudignore` excludes private notes, local SQLite data, logs, and local runtime artifacts from source upload.
- Fresh Cloud Run source deploy required adding `roles/run.builder` to the default build service account.
- Use `DEPLOYMENT.md` for deploy commands and production environment variable guidance.

## Core Features

- Public request form: `/` and `/request`
- Request confirmation: `/request/confirmation/<id>`
- Staff login: `/staff/login`
- Staff logout: `/staff/logout`
- Staff dashboard: `/tickets`
- Ticket triage/detail/comments: `/tickets/<id>`
- Staff-only notification preview log: `/notifications`
- Staff-only demo settings page: `/settings`
- Health endpoint: `/health`

Request capture includes:

- Requester name
- Contact info
- Category
- Priority
- Ministry/team
- Location
- Title
- Description
- Attachment placeholder for a future phase

Staff workflow includes:

- Filter/search ticket dashboard
- Sort ticket dashboard by any displayed table column
- Status, priority, and assignee updates
- Public/internal comments
- Activity history
- Preview notifications for new requests, ticket updates, and comments

## Current Branding And Content

- App name: `UUCH Help Desk`
- Public pages use a UUCH masthead with:
  - UUCH logo
  - UUCH tagline
- Footer includes:
  - UUCH address
  - Sunday service time
  - Phone
  - Email
  - UUCH.org link
  - Contact link
  - Donate link
  - Accessibility link
  - Privacy link
- The visual pass is intentionally minimal for now.

Current request categories:

- Care / Pastoral Care
- Care Committee
- Property / Safety
- Technology
- Worship / Music
- Children and Youth RE
- Adult RE
- Hospitality
- Membership
- Social Justice
- Stewardship / Finance
- Events / Calendar
- General
- Other

Current staff team labels:

- Unassigned
- Technology Team
- Safety Team
- Media Team
- Care Team
- Office Admin
- Events Team

## Configuration

Main settings live in `demo_settings.json`.

Settings currently include:

- Church/demo name
- Staff notification recipient placeholder
- Requester reply-from placeholder
- Notification mode label
- Public contact instructions
- Request category labels, which drive the public request form's `Category` dropdown
- Staff team labels, which also drive the public request form's `Ministry or Team` dropdown
- Site admin placeholder names for a future individual-login phase; this list is not wired into authentication yet

Production-style environment examples live in `.env.example`.

Important production env vars:

- `APP_ENV=production`
- `SECRET_KEY`
- `STAFF_PASSWORD`
- `MAX_TICKETS=30` for the current demo ticket cap

The app refuses to start in production/Cloud Run if `SECRET_KEY` or `STAFF_PASSWORD` are still using demo defaults.

## Private Details

Real deployed `SECRET_KEY` and `STAFF_PASSWORD` values are stored only in `PRIVATE_NOTES.md`.

`PRIVATE_NOTES.md` is gitignored and should not be included in public handoff docs.

Unrelated older Google Cloud project inventory was intentionally moved out of this public log and into `PRIVATE_NOTES.md`.

## Important Product Question

Ask stakeholders who the intended audience should be:

- Internal only for staff/volunteers?
- Fully public-facing for members, visitors, and community requesters?
- Mixed, with public intake plus staff-only triage and internal notes?

This decision should guide authentication, privacy language, request categories, and whether some request types should be hidden or internal-only.

## Current Verification

Latest local verification:

- `python3 -m py_compile app.py seed_demo.py`
- Local `/settings` rendered separate Ticket / Request Configuration and Admin Configuration blocks
- Local CSS check confirmed Settings uses a two-column desktop form grid, stacked narrow-screen rules, and a lower current-demo-values summary
- Local `/settings` rendered the Site Admins editor with Staff, Shalin, Treo, Wayne, and David
- Local settings normalization confirmed blank and duplicate admin entries are cleaned, with the default admin placeholder list restored if the field is emptied
- Local request POST check confirmed a blank Priority submission succeeds and saves as `Normal`
- Local settings normalization confirmed duplicate/early `Other` category entries are cleaned and `Other` stays at the bottom
- Local `/request` rendered Category as required, included `Other`, and rendered Priority without the required marker or required attribute
- Local `/settings` rendered the request category labels editor and help text
- Local dashboard render showed the second filter as `Assignee`, removed the Category dropdown filter, preserved assignee state in sort links, and kept the Category sort column available
- Local backend filter check confirmed filtering to `Care Team` returns only Care Team tickets
- Local dashboard render showed sortable header links, `aria-sort`, active direction arrows, and preserved sort state in the filter form
- Local route checks confirmed all 14 sort combinations load: 7 columns times ascending and descending
- Local data check confirmed request-title ascending and priority descending sort orders behave as expected
- Local `/request` rendered the `Ministry or Team` dropdown with `Not sure`, `Technology Team`, and `Safety Team`, and did not expose the staff-only `Unassigned` label
- Local POST sanity check confirmed configured team labels are accepted and unconfigured team labels are saved as blank
- Local server started at `http://127.0.0.1:5000`
- Local `/health` returned HTTP 200 after restart
- Local `/` shows `UUCH Help Desk` and the UUCH tagline in the masthead without service-time or Contact utility text
- Local `/` still shows the page-level `Staff Sign In` button
- Local `/` renders required-field indicators, request helper text, updated attachment language, and the routing examples panel
- Local staff login using the demo password redirected to `/tickets`
- Local `/tickets` renders the dashboard reset action and accessible table caption
- Local `/tickets/1` renders staff comment visibility guidance and required comment text

Latest deployed verification:

- Online `/health` returned HTTP 200 after deployment of revision `church-helpdesk-00015-ch5`
- Online `/` rendered `UUCH Help Desk`, UUCH logo, simplified masthead without service-time or Contact utility text, footer contact details, updated categories, required-field indicators, request helper text, updated attachment language, and the routing examples panel
- Online `/request` rendered the `Ministry or Team` dropdown with `Not sure`, `Technology Team`, and `Safety Team`, and did not expose the staff-only `Unassigned` label
- Online `/tickets?sort=request&direction=asc` rendered sortable dashboard headers with `aria-sort`, active ascending arrows, neutral arrows on inactive columns, and a descending toggle link
- Online request-title ascending and descending sort checks returned different first rows, confirming live sort order changes
- Online `/tickets?assignee=Care+Team&sort=request&direction=asc` rendered the Assignee dropdown, removed the Category dropdown filter, preserved the assignee filter in sort links, and returned only Care Team rows
- Online `/request` rendered Category as required with `Other` as the last option and rendered Priority without the required marker or required attribute
- Online `/settings` rendered the request category labels editor and help text
- Online `/settings` rendered separate Ticket / Request Configuration and Admin Configuration blocks, with the Site Admins editor containing Staff, Shalin, Treo, Wayne, and David
- Online `/settings` and `styles.css` confirmed the desktop two-column Settings form layout and narrow-screen stacked fallback
- Online `/` rendered the mobile-friendly requester name autocomplete
- Online `/` rendered the demo ticket limit display: 5 of 30 ticket slots used
- Online staff login succeeded with the current private staff password and redirected to `/tickets`
- Online `/tickets` rendered the dashboard summary anchor, reset action linked to that anchor, auto-apply dropdown filter script, accessible table caption, mobile card labels for ticket rows, updated categories, and seeded demo tickets
- Online `styles.css` included the phone-width four-column metric grid, compact metric styling, and higher-contrast focus outline
- Online `/tickets/1` rendered staff comment visibility guidance and required comment text
- Online `/settings` showed the current staff team labels, including `Technology Team` and `Safety Team`

## Recommended Next Steps

### Best Immediate Next Step

Do a short stakeholder review before adding more features. Ask:

- Is this for members/visitors, internal staff, or both?
- What kinds of requests should be public?
- What requests should never go through this system?
- Who triages tickets?
- What response-time expectation should requesters see?

This decision affects almost everything else.

### Good GitHub Next Steps

- Add GitHub issues for the next major items.
- Add a simple GitHub Actions check that runs `python3 -m py_compile app.py seed_demo.py`.
- Add a `v0.1-demo` tag so we can always get back to this working demo state.

### Best Product Improvements

- Replace preview notifications with real email.
- Add a simple "request received" email to the submitter.
- Add spam/rate protection before wider sharing.
- Add clearer privacy language once audience is decided.
- Decide whether requesters should ever be able to check ticket status.

### Best Technical Improvements

- Move tickets out of local SQLite before real use. Cloud Run storage is ephemeral.
- Replace the shared staff password with Google login or another identity provider.
- Move secrets into Google Secret Manager.
- Map a friendly URL under `davidtapia.org`.

### Recommended Order

1. Create GitHub issues for the roadmap.
2. Add a tiny CI check.
3. Decide the intended audience before building more deeply.
