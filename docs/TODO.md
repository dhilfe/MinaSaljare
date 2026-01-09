Initialize project repo & basic documentation
Acceptance criteria:
	•	A Git repository exists with main and develop (or stage) branches.
	•	specification.md is committed in the repo root.  ￼
	•	A README.md explains how to set up the backend locally (even if minimal).
	•	Basic .gitignore for Python, Django, Node, and IDE files is in place.

⸻

	•	Set up local Python/Django backend skeleton
Acceptance criteria:
	•	A Django project (e.g. salesapp) is created with a main app (e.g. core or api).
	•	Django REST Framework is installed and added to INSTALLED_APPS.
	•	Local dev server runs with python manage.py runserver using SQLite.
	•	A test API endpoint /api/health/ returns a simple JSON { "status": "ok" }.

⸻

	•	Configure PostgreSQL for development
Acceptance criteria:
	•	A local Postgres instance is running (either native or Docker).
	•	Django DATABASES is configured to use Postgres in a .env-driven way.
	•	python manage.py migrate runs successfully against Postgres.
	•	The app can start and serve the /api/health/ endpoint reading from Postgres.

⸻

	•	Implement custom User model with roles & JWT auth
Acceptance criteria:
	•	Custom User model exists with fields: email (unique), first_name, last_name, role, is_active, timestamps.
	•	role supports at least "guardian" and "coach".
	•	JWT-based login endpoint /api/v1/auth/login returns access_token + user info (as in spec).
	•	/api/v1/me endpoint returns current user profile based on JWT.
	•	Logging in and calling /me works via Postman/curl.

⸻

	•	Add Team model and basic team API
Acceptance criteria:
	•	Team model exists per spec (name, club_name, timestamps).
	•	Relationship between User (coach) and Team is implemented (e.g. FK or M2M).
	•	/api/v1/team endpoint returns the team for the logged-in user.
	•	Guardians and coaches correctly see their associated team in /team.

⸻

	•	[x] Add Campaign model & active campaign endpoint
Acceptance criteria:
	•	Campaign model exists with fields from spec (team, name, dates, targets, buyout, currency, is_active, timestamps).
	•	A coach can create a campaign via /api/v1/campaigns (authenticated).
	•	/api/v1/campaigns/active returns the single active campaign for the user’s team.
	•	If no active campaign exists, endpoint returns a suitable empty / 404-style response.

⸻

	•	[x] Add Child & GuardianChildLink models and endpoints
Acceptance criteria:
	•	Child model is implemented (team FK, first_name, last_initial, shirt_number, active flag, timestamps).
	•	GuardianChildLink implements many-to-many between users (guardians) and children.
	•	/api/v1/children returns only children linked to the logged-in guardian.
	•	Unit tests verify that a guardian cannot see other guardians’ children.

⸻

	•	[x] Implement ChildCampaignTarget model & target logic
Acceptance criteria:
	•	ChildCampaignTarget model exists with fields: child, campaign, target_units, buyout_amount, has_paid_buyout, timestamps.
	•	Business logic to determine target_units chooses child-specific target if present, otherwise uses campaign default.
	•	A simple endpoint (or part of summary endpoints later) can show the resolved target_units for a child + campaign.
	•	Data migrations confirm model integration with existing Campaign/Child data.

⸻

	•	[x] Add Product model & CRUD endpoints (coach)
Acceptance criteria:
	•	Product model exists with fields: campaign, name, description, unit_price, profit_per_unit, is_active.
	•	/api/v1/campaigns/{campaign_id}/products (GET) returns a list of active products.
	•	/api/v1/campaigns/{campaign_id}/products (POST) allows coaches to create products.
	•	/api/v1/products/{id} (PATCH) allows coaches to update product details.
	•	Guardians can only read products; permission checks confirmed in tests.

⸻

	•	[x] Add Sale model & basic sale creation endpoint
Acceptance criteria:
	•	Sale model exists with fields from spec (campaign, child, product, quantity, total_price, buyer_name, is_paid, is_delivered, recorded_by, recorded_at, timestamps).
	•	total_price is correctly calculated on create/update as quantity * product.unit_price.
	•	/api/v1/campaigns/{campaign_id}/sales (POST) creates sales for a child with validation (quantity > 0, child in team, etc.).
	•	Guardian can only create sales for their linked children; coach can create for any team child.

⸻

	•	[x] Implement sale listing endpoints for guardians
Acceptance criteria:
	•	/api/v1/campaigns/{campaign_id}/sales/my-children (GET) returns all sales for children linked to the authenticated guardian.
	•	Responses include product name, quantity, total_price, is_paid, is_delivered.
	•	Pagination and basic filtering (e.g. by child) is implemented or at least designed.
	•	Unit tests verify access control (guardian cannot see other children’s sales).

⸻

	•	[x] Implement sale update & delete endpoints
Acceptance criteria:
	•	/api/v1/sales/{id} (PATCH) allows updating quantity, payment status, delivery status.
	•	Optional /api/v1/sales/{id} (DELETE) removes a sale (or marks as deleted) with correct permission checks.
	•	Only the creating guardian or a coach can modify/delete a sale.
	•	Business rules validated (e.g. cannot update to negative quantity).

⸻

	•	[x] Implement child campaign summary endpoint
Acceptance criteria:
	•	/api/v1/children/{child_id}/campaigns/{campaign_id}/summary returns fields as per spec: target_units, total_units_sold, total_sales_amount, remaining_units_to_target, progress_percent.
	•	Derived metrics are calculated using sales and targets correctly.
	•	Guardian can only view summaries for their children; coach can view all in the team.
	•	Results match manual calculations in test data.

⸻

	•	[x] Implement team campaign summary & team-status endpoint
Acceptance criteria:
	•	/api/v1/team/campaigns/{campaign_id}/summary returns a list of children with target_units, total_units_sold, progress_percent plus team totals.
	•	Aggregate fields: team_total_units_sold, team_target_units, team_progress_percent are correctly computed.
	•	Guardian sees only per-child aggregates (no buyer details).
	•	Coach can optionally access more detailed breakdown via another endpoint or query param if needed later.

⸻

	•	[x] Implement CSV export endpoint for coach
Acceptance criteria:
	•	/api/v1/campaigns/{campaign_id}/export/csv returns a CSV file with all sales required for ordering & bookkeeping (child, product, quantity, buyer_name, paid, delivered, totals).
	•	Only coaches can access this endpoint.
	•	CSV opens correctly in Excel/Sheets and matches database content.
	•	At least one automated test validates CSV headers and basic row structure.

⸻

	•	[x] Configure Django Admin for quick coach management (Phase 1 admin)
Acceptance criteria:
	•	User, Team, Campaign, Child, GuardianChildLink, ChildCampaignTarget, Product, Sale are all visible in Django Admin.
	•	Admin lists are filtered by team/campaign where relevant.
	•	Coach role can be used to administrate initial data via admin (for internal use).
	•	You can configure one real campaign end-to-end via Django Admin.

⸻

	•	[x] Set up basic security: password hashing, HTTPS assumption, permissions
Acceptance criteria:
	•	Password hashing uses a strong algorithm (e.g. Argon2 or bcrypt).
	•	DRF permissions enforce role-based rules for all endpoints (guardian vs coach).
	•	Sensitive data (passwords, secrets) is managed via environment variables, not in code.
	•	A short security checklist is documented in README.md (e.g. “Use HTTPS in production, secure JWT secret”).

⸻

	•	[x] Create React + TypeScript web app scaffold (Phase 1 Web)
Acceptance criteria:
	•	React + TypeScript project is created (e.g. Vite or CRA).
	•	API base URL and JWT handling are centralised (e.g. Axios instance with interceptor).
	•	Basic routing is set up (e.g. /login, /home, /team).
	•	The app can be started with npm run dev and shows a placeholder page.

⸻

	•	[x] Implement login UI & JWT storage
Acceptance criteria:
	•	/login screen has email/password fields and a “Log in” button.
	•	On successful login, JWT is stored securely (e.g. HTTP-only cookie or local storage with clear plan).
	•	User is redirected to /home after login.
	•	Invalid credentials show a friendly error message.

⸻

	•	[x] Implement Guardian “My Sales” home view
Acceptance criteria:
	•	/home displays:
	•	Child selector (dropdown or tabs) for guardians with multiple children.
	•	Child progress card with sold, target, remaining, sales_amount, and a progress bar.
	•	Data is fetched from /children and child summary endpoint.
	•	Loading and error states are handled gracefully.
	•	Switching child updates the progress card without page reload.

⸻

	•	[x] Implement “Add Sale” flow in web UI
Acceptance criteria:
	•	A prominent “Add Sale” button from the home view opens the add-sale screen/modal.
	•	Product selection uses /campaigns/{campaign_id}/products.
	•	Quantity stepper/input, optional buyer name, and checkboxes for Paid / Delivered are present.
	•	On submit, a request to /campaigns/{campaign_id}/sales is sent, and success updates the child summary.
	•	User gets confirmation (toast/snackbar) after a successful save.

⸻

	•	[x] Implement Guardian Team Status view (web)
Acceptance criteria:
	•	/team (or similar route) shows:
	•	Campaign name & end date.
	•	List of children with short names (e.g. “Lisa A”) and progress bars + X / Y units.
	•	Data comes from /team/campaigns/{campaign_id}/summary.
	•	No detailed sale/buyer info is exposed in this view.
	•	View is mobile-friendly and readable on a phone.

⸻

	•	[x] Implement basic coach dashboard web view (optional, beyond Django Admin)
Acceptance criteria:
	•	A coach-only route (e.g. /coach/dashboard) is accessible based on role.
	•	Dashboard shows team totals and per-child stats using team summary endpoint.
	•	Simple UI to navigate to campaign/product settings (can link to Django Admin for v1).
	•	Access is blocked for guardians (redirect or error).

⸻

	•	Dockerize backend & database for production-like deployment
Acceptance criteria:
	•	Dockerfile exists for Django backend (Gunicorn-based).
	•	docker-compose.yml includes db (Postgres) and backend services as per spec.
	•	Environment variables for DB connection, JWT secret, etc. are wired via .env.
	•	docker-compose up starts backend + DB and allows access to API locally.

⸻

	•	Add reverse proxy (Caddy or Nginx) and serve frontend
Acceptance criteria:
	•	A proxy service (Caddy or Nginx) is added to docker-compose.yml.
	•	Proxy terminates HTTP/HTTPS and forwards /api/ to backend container.
	•	React build (or Django static) is served via proxy on /.
	•	Local request to https://localhost (or http:// if using self-signed) shows the web app and functional API.

⸻

	•	Deploy full stack on Raspberry Pi
Acceptance criteria:
	•	Project repo is cloned onto the Raspberry Pi.
	•	docker-compose up -d runs all services (db, backend, proxy, frontend).
	•	Pi is reachable from your LAN via hostname/IP and displays the app.
	•	You can run a small “real” test campaign with your team using the Pi-hosted instance.

⸻

	•	Expose Raspberry Pi app securely to the internet
Acceptance criteria:
	•	Either port forwarding + Let’s Encrypt or a tunneling solution (e.g. Cloudflare Tunnel) provides HTTPS public access.
	•	Domain/subdomain points to the Pi-hosted app.
	•	TLS certificates are valid and auto-renewing.
	•	Basic rate limiting / firewall rules are in place on the router/tunnel service.

⸻

	•	Implement automated backups & simple monitoring
Acceptance criteria:
	•	Nightly Postgres backups are configured (e.g. cron + pg_dump) to an encrypted location.
	•	There is a documented restore procedure tested at least once.
	•	Basic uptime/health monitoring (e.g. simple script or external service) pings /api/health/.
	•	You receive an alert (email/notification) if the service goes down.



⸻

	•	Implement yearly statistics endpoints (team & children)
Acceptance criteria:
	•	Backend exposes /api/v1/stats/team/year, /api/v1/stats/child/{child_id}/year and /api/v1/stats/me/children/year as described in specification_v2.md.
	•	Given test data spanning multiple campaigns within the same calendar year, all three endpoints return correct totals for units and sales amounts, and correct per-campaign breakdowns according to the spec.
	•	Yearly stats are computed based on Sale.recorded_at together with Campaign, Team and Child relations (no hard-coded years).
	•	Access control ensures guardians only see stats for their own children, while coaches see stats for the whole team.

⸻

	•	Implement Guardian yearly history view (web)
Acceptance criteria:
	•	A History/Year view exists in the web app where a guardian can select a year (default: current year) and see yearly statistics for their children using /api/v1/stats/me/children/year or per-child yearly endpoints.
	•	For each child, the view shows total units sold, total sales amount, and a simple breakdown per campaign (campaign name + units + amount) for that year.
	•	Loading and error states are handled; guardians cannot access yearly stats for children they are not linked to.
	•	Basic layout is mobile-friendly and readable on a phone.

⸻

	•	Implement coach yearly statistics dashboard (web)
Acceptance criteria:
	•	A coach-only yearly statistics view exists in the web app that uses /api/v1/stats/team/year for the logged-in coach’s team.
	•	The view shows team totals for the selected year (units and sales amount) plus a sortable table of children with their yearly totals and number of campaigns.
	•	Clicking a child opens a detail view (drawer/modal/page) showing per-campaign breakdown for that year (campaign name, units sold, sales amount) per the spec.
	•	Permissions ensure guardians cannot access the coach yearly statistics dashboard (they are redirected or get a clear error).

⸻

Phase 2 – Flutter iOS App
	•	Initialize Flutter project and integrate with REST API
Acceptance criteria:
	•	Flutter project is created with a clean folder structure.
	•	Base HTTP client for talking to the REST API is implemented.
	•	Environment configuration (API base URL, etc.) exists for dev vs production.
	•	A simple test screen can call /api/health/ and display the result.

⸻

	•	Implement iOS login & token handling in Flutter
Acceptance criteria:
	•	Login screen exists mirroring the web login (email/password).
	•	On successful login, JWT is stored securely (e.g. flutter_secure_storage).
	•	The app navigates to the home screen after login.
	•	Invalid credentials show an error UI.

⸻

	•	Implement iOS Guardian home & Add Sale flows in Flutter
Acceptance criteria:
	•	Home screen shows child selector and progress card pulling from /children + summary endpoint.
	•	Add Sale screen uses products endpoint + sale creation endpoint.
	•	After creating a sale, child summary is refreshed and success feedback is shown.
	•	UI is tested on at least one physical iOS device or simulator.

⸻

	•	Implement iOS Team Status screen & basic settings
Acceptance criteria:
	•	Team status screen shows aggregated data (like web /team).
	•	Settings screen allows logout and basic preferences (e.g. notifications toggle placeholder).
	•	Navigation between screens uses a bottom nav or similar tab system.
	•	Role-based access is respected (guardian flows only).

⸻

	•	Add push notifications for campaign reminders (iOS)
Acceptance criteria:
	•	Firebase Cloud Messaging (or alternative) is integrated with the Flutter app.
	•	Device tokens can be saved on backend (simple endpoint).
	•	Test push notifications can be sent (e.g. “N days left in campaign”).
	•	At least one real device receives and displays notification while app is backgrounded.

⸻

	•	Distribute iOS app via TestFlight / App Store
Acceptance criteria:
	•	Apple Developer account is set up and app identifiers/profiles are configured.
	•	App builds successfully in Xcode and is uploaded to App Store Connect.
	•	TestFlight is enabled and at least one external tester (e.g. yourself + a coach) installs the app.
	•	(Optional) App is submitted and approved for App Store release.

⸻

Phase 3 – Flutter Android App
	•	Configure Android build & test on devices
Acceptance criteria:
	•	Android build config (Gradle, app ID, icons) is completed.
	•	App builds and runs on at least one Android emulator and one physical device (if available).
	•	Network calls work correctly to the same backend.
	•	Login, home, add sale, and team status flows function as on iOS.

⸻

	•	Publish Android app to Google Play (optional)
Acceptance criteria:
	•	Google Play Developer account is set up.
	•	App bundle is uploaded and passes Play Console checks.
	•	Internal testing track is used for initial testers (team/guardians).
	•	(Optional) App is published to production or closed testing track for wider use.
