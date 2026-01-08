# Sales Tracking App – System Specification (v2)

> Focus at launch: **single team + its guardians/children**  
> Designed to scale to **club / multi-team** later.  
> Updated to include **yearly history/statistics** so leaders (and optionally all users) can see how much everyone has sold and contributed across multiple sales during the year.

---

## 1. Goals & Scope

### 1.1 Primary Goals

- Allow a **team** (e.g., one youth sports team) to run **sales campaigns**.
- Enable **guardians** to:
  - Track each child’s progress vs. target (number of items or buy-out) per campaign.
  - Register sales quickly on mobile/web.
  - View team progress (transparent, motivating).
  - (Optionally) view history per year of how much their child has sold across campaigns.
- Enable a **coach/team leader** to:
  - Set up campaigns (targets, products, dates).
  - See how the team performs overall and who needs extra push in a campaign.
  - **See yearly history/statistics** for team and children:
    - How much each child has sold during the year.
    - How much they have contributed in different sales (campaigns).
  - Export data for ordering and finance.

### 1.2 Initial Scope (Launch)

- Single club/team deployment (no multi-tenant UI complexity).
- Core entities: **Campaign, Team, Child, Guardian, Product, Sale**.
- Roles: **Guardian**, **Coach** (admin).
- Simple email/password login.
- Multiple campaigns over the year (for yearly statistics).

---

## 2. Technical Architecture & Stack

### 2.1 High-Level Architecture

- **Backend API**  
  - RESTful JSON API.
  - Stateless (except for auth tokens).
- **Database**
  - Relational (PostgreSQL recommended).
- **Frontend**
  - Phase 1: Responsive web app (mobile-first).
  - Phase 2–3: Native-like mobile apps (sharing backend).

### 2.2 Suggested Tech Stack

**Backend**

- Language: **Python 3**
- Framework: **Django** + **Django REST Framework (DRF)**
- Database: **PostgreSQL**
- Auth: **JWT** (or DRF Token Auth) over HTTPS.

**Frontend**

- Phase 1 Web:
  - **React** + TypeScript (SPA), or simple Django templates if you want ultra-fast MVP.
- Phase 2 & 3 Mobile:
  - **Flutter** (preferred) – single codebase for **iOS** and **Android**.
  - Communicates with the same REST API.

**Infrastructure / DevOps**

- Initial hosting: **Raspberry Pi at home**
  - OS: Raspberry Pi OS (Lite) or Ubuntu Server.
  - **Docker** + **docker-compose**:
    - `backend` (Django + Gunicorn)
    - `db` (Postgres)
    - `reverse-proxy` (Caddy or Nginx)
  - HTTPS via:
    - Port forwarding + Let’s Encrypt, or
    - Cloudflare Tunnel / similar for easier secure exposure.
- Later: Optionally migrate to:
  - **VPS / cloud** (AWS EC2, DigitalOcean, etc.) with minimal changes.

---

## 3. Domain Model (Data Model)

### 3.1 Entities

#### 3.1.1 User

Represents a login/person in the system.

- `id: UUID`
- `email: string (unique)`
- `password_hash: string`
- `first_name: string`
- `last_name: string`
- `role: enum("guardian", "coach")`  
  > Future: `"club_admin"`, etc.
- `created_at: datetime`
- `updated_at: datetime`
- `is_active: boolean`

#### 3.1.2 Team

One team (e.g., “P11 Lag Blå”).

- `id: UUID`
- `name: string`
- `club_name: string` (optional, simple string)
- `created_at: datetime`
- `updated_at: datetime`

Relationships:

- A **User (coach)** may be associated as `team.coach`.
- A **Campaign** is linked to exactly one `team`.

#### 3.1.3 Campaign

A specific sales round (e.g., “Salami Spring 2026”).

- `id: UUID`
- `team: FK -> Team`
- `name: string`
- `description: string` (optional)
- `start_date: date`
- `end_date: date`
- `default_target_units_per_child: int` (e.g., 20)
- `buyout_amount_per_child: decimal` (e.g., 1000.00)
- `currency: string` (e.g., "SEK")
- `is_active: boolean`
- `created_at: datetime`
- `updated_at: datetime`

> Note: Multiple campaigns per year per team enable yearly statistics across all sales.

#### 3.1.4 Child (Participant)

A child in the team.

- `id: UUID`
- `team: FK -> Team`
- `first_name: string`
- `last_initial: string` (optional)
- `shirt_number: string` (optional)
- `created_at: datetime`
- `updated_at: datetime`
- `is_active: boolean`

#### 3.1.5 GuardianChildLink

Connects guardians to children (many-to-many).

- `id: UUID`
- `guardian: FK -> User (role="guardian")`
- `child: FK -> Child`
- `relationship: string` (optional, e.g., "mother", "father")

#### 3.1.6 ChildCampaignTarget

Target per child per campaign.

- `id: UUID`
- `child: FK -> Child`
- `campaign: FK -> Campaign`
- `target_units: int` (override default if needed)
- `buyout_amount: decimal` (optional override)
- `has_paid_buyout: boolean`
- `created_at: datetime`
- `updated_at: datetime`

#### 3.1.7 Product

Products sold in a campaign.

- `id: UUID`
- `campaign: FK -> Campaign`
- `name: string`
- `description: string` (optional)
- `unit_price: decimal`
- `profit_per_unit: decimal` (optional, for club profit)
- `is_active: boolean`

#### 3.1.8 Sale

A single sale event (e.g., 3 units to Grandma).

- `id: UUID`
- `campaign: FK -> Campaign`
- `child: FK -> Child`
- `product: FK -> Product`
- `quantity: int`
- `total_price: decimal` (denormalized = `quantity * product.unit_price`)
- `buyer_name: string` (optional)
- `is_paid: boolean`
- `is_delivered: boolean`
- `recorded_by: FK -> User` (guardian or coach)
- `recorded_at: datetime`  // used for yearly statistics
- `updated_at: datetime`

---

### 3.2 Derived Metrics (Logic)

For each child & campaign:

- `total_units_sold` = `sum(quantity for sales)`
- `total_sales_amount` = `sum(total_price)`
- `target_units` = from `ChildCampaignTarget` or `Campaign.default_target_units_per_child`
- `progress_percent` = `min(100, total_units_sold / target_units * 100)`
- `remaining_units_to_target` = `max(0, target_units - total_units_sold)`

For team & campaign:

- `team_total_units_sold` = `sum(child.total_units_sold)`
- `team_target_units` = `sum(child.target_units)`
- `team_progress_percent` = `team_total_units_sold / team_target_units * 100`

#### 3.2.1 Yearly Statistics

Using `Sale.recorded_at` and `Campaign` relations:

For a given year `Y` and team:

- `year_total_units_sold` (team)  
  = sum of all `Sale.quantity` where `Sale.recorded_at.year == Y` and `Sale.campaign.team == team`.
- `year_total_sales_amount` (team)  
  = sum of all `Sale.total_price` for that year and team.

Per child, per year:

- `child_year_total_units_sold`
- `child_year_total_sales_amount`
- Breakdown per campaign:
  - List of `{campaign, total_units, total_amount}`.

Optional “contribution” metric:

- Total **profit** using `Product.profit_per_unit` where defined.

> Yearly stats can initially be computed on demand via queries; later you can add a cached table/materialized view if needed.

---

## 4. API Design (REST)

Base URL: `/api/v1`

All endpoints return JSON.  
Auth: Bearer JWT in `Authorization` header.

---

### 4.1 Auth

#### POST `/auth/register`

- For initial MVP, only coach can create guardian accounts via admin UI / CLI.  
  (Public registration is optional later.)

#### POST `/auth/login`

**Request:**

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

**Response:**

```json
{
  "access_token": "jwt-token",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "guardian",
    "first_name": "Anna",
    "last_name": "Andersson"
  }
}
```

#### POST `/auth/logout`

- Optional server-side token blacklist/logout.

---

### 4.2 Current User

#### GET `/me`

Returns profile info and basic team/campaign context.

**Response:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "guardian",
  "first_name": "Anna",
  "last_name": "Andersson",
  "children": [
    {
      "id": "child-uuid",
      "first_name": "Lisa",
      "team": { "id": "team-uuid", "name": "P11 Blue" }
    }
  ]
}
```

---

### 4.3 Team & Campaign (Coach only for write)

#### GET `/team`

- For MVP: returns single team for the logged-in user (coach or guardian).

#### GET `/campaigns/active`

- Returns the active campaign for the logged-in user’s team.

#### POST `/campaigns` (coach)

- Create new campaign.

**Example request:**

```json
{
  "team_id": "team-uuid",
  "name": "Salami Spring 2026",
  "description": "Fundraiser for Gothenburg Cup",
  "start_date": "2026-03-01",
  "end_date": "2026-03-31",
  "default_target_units_per_child": 20,
  "buyout_amount_per_child": 1000.0,
  "currency": "SEK"
}
```

#### PATCH `/campaigns/{id}` (coach)

- Update campaign fields (e.g., `end_date`, `is_active`).

---

### 4.4 Child & Targets

#### GET `/children` (guardian)

- Returns children linked to logged-in guardian.

**Response:**

```json
[
  {
    "id": "child-uuid-1",
    "first_name": "Lisa",
    "last_initial": "A",
    "team": { "id": "team-uuid", "name": "P11 Blue" }
  }
]
```

#### GET `/children/{id}/campaigns/{campaign_id}/summary`

- Returns child’s progress in a specific campaign.

**Response:**

```json
{
  "child": { "id": "child-uuid", "first_name": "Lisa" },
  "campaign": { "id": "camp-uuid", "name": "Salami Spring 2026" },
  "target_units": 20,
  "total_units_sold": 12,
  "total_sales_amount": 1800.0,
  "remaining_units_to_target": 8,
  "progress_percent": 60.0
}
```

#### GET `/team/campaigns/{campaign_id}/summary` (guardian or coach)

- Returns team-level stats for a campaign.
- Guardian sees only aggregate numbers per child (no buyer details).
- Coach may optionally see more detail (configurable later).

---

### 4.5 Products

#### GET `/campaigns/{campaign_id}/products`

- List products for a campaign.

**Response:**

```json
[
  {
    "id": "product-uuid-1",
    "name": "Salami",
    "description": "500 g",
    "unit_price": 150.0
  }
]
```

#### POST `/campaigns/{campaign_id}/products` (coach)

- Create product.

**Example request:**

```json
{
  "name": "Salami",
  "description": "500 g premium salami",
  "unit_price": 150.0,
  "profit_per_unit": 50.0
}
```

#### PATCH `/products/{id}` (coach)

- Update product fields.

---

### 4.6 Sales

#### GET `/campaigns/{campaign_id}/sales/my-children` (guardian)

- Returns sales for children linked to the guardian in that campaign.

#### POST `/campaigns/{campaign_id}/sales` (guardian/coach)

**Request:**

```json
{
  "child_id": "child-uuid",
  "product_id": "product-uuid",
  "quantity": 3,
  "buyer_name": "Grandma",
  "is_paid": true,
  "is_delivered": false
}
```

**Response:**

```json
{
  "id": "sale-uuid",
  "child_id": "child-uuid",
  "product_id": "product-uuid",
  "quantity": 3,
  "total_price": 450.0,
  "buyer_name": "Grandma",
  "is_paid": true,
  "is_delivered": false,
  "recorded_at": "2026-01-07T19:00:00Z"
}
```

#### PATCH `/sales/{id}`

- Allow correcting quantity, payment, delivery status.

**Example request:**

```json
{
  "quantity": 4,
  "is_paid": true,
  "is_delivered": true
}
```

#### DELETE `/sales/{id}` (optional)

- Only coach or the guardian who created it can delete.

---

### 4.7 Team Summary & Export (Coach)

#### GET `/campaigns/{campaign_id}/team-summary`

- Returns list of children and their stats for a specific campaign.

**Response:**

```json
{
  "campaign": { "id": "camp-uuid", "name": "Salami Spring 2026" },
  "team": { "id": "team-uuid", "name": "P11 Blue" },
  "children": [
    {
      "id": "child-uuid-1",
      "name": "Lisa A",
      "target_units": 20,
      "total_units_sold": 18,
      "progress_percent": 90.0
    },
    {
      "id": "child-uuid-2",
      "name": "Erik B",
      "target_units": 20,
      "total_units_sold": 5,
      "progress_percent": 25.0
    }
  ],
  "team_total_units_sold": 23,
  "team_target_units": 40,
  "team_progress_percent": 57.5
}
```

#### GET `/campaigns/{campaign_id}/export/csv`

- Returns CSV for offline processing, ordering, and bookkeeping.

---

### 4.8 Yearly Statistics (New)

These endpoints provide history/statistics over a year across multiple campaigns.

#### GET `/stats/team/year`

Query parameters:

- `year` (required, e.g. `2026`)

Returns yearly statistics for the team of the logged-in coach. For guardians, it can return a limited version if you choose to expose it.

**Example response (coach):**

```json
{
  "team": { "id": "team-uuid", "name": "P11 Blue" },
  "year": 2026,
  "total_units_sold": 350,
  "total_sales_amount": 52500.0,
  "children": [
    {
      "child_id": "child-uuid-1",
      "name": "Lisa A",
      "total_units_sold": 120,
      "total_sales_amount": 18000.0,
      "campaigns": [
        {
          "campaign_id": "camp-uuid-1",
          "campaign_name": "Salami Spring 2026",
          "units_sold": 80,
          "sales_amount": 12000.0
        },
        {
          "campaign_id": "camp-uuid-2",
          "campaign_name": "Christmas Cookies 2026",
          "units_sold": 40,
          "sales_amount": 6000.0
        }
      ]
    },
    {
      "child_id": "child-uuid-2",
      "name": "Erik B",
      "total_units_sold": 80,
      "total_sales_amount": 12000.0,
      "campaigns": [
        {
          "campaign_id": "camp-uuid-1",
          "campaign_name": "Salami Spring 2026",
          "units_sold": 50,
          "sales_amount": 7500.0
        }
      ]
    }
  ]
}
```

#### GET `/stats/child/{child_id}/year`

- Returns yearly statistics for a specific child (coach can see any; guardian can see only their own children).

#### GET `/stats/me/children/year`

- For a guardian, returns yearly stats across all their children combined (optionally broken down by child and campaign).

---

## 5. UI – Views & Components

### 5.1 Guardian – Web & Mobile

#### 5.1.1 Home / “My Sales”

**Components:**

- `ChildSelector`
  - If guardian has multiple children, simple dropdown or swipeable tabs.
- `ChildProgressCard`
  - Child name.
  - Progress bar (units sold vs target).
  - Stats:
    - `sold`
    - `target`
    - `remaining`
    - `sales_amount`
- `QuickActions`
  - “Add Sale”
  - “View Team Status”
  - (Later) “View History”

**UX notes:**

- One primary CTA button visible at the bottom: **“Add Sale”**.
- Secondary actions in top-right or additional menu.

#### 5.1.2 Add Sale Flow

**Components:**

- `ProductSelect`
  - Dropdown or grid with product cards (name + price).
- `QuantityStepper`
  - Buttons `-` and `+`, or numeric input.
- `BuyerInfoSection`
  - `buyer_name` (optional text field).
  - Checkboxes: `Paid`, `Delivered`.
- `PrimaryButton`
  - “Save Sale”.
- `SuccessToast`
  - “Great! 3 units added – now you’re at 12 / 20!”

**UX notes:**

- Keep steps minimal (ideally in a single screen).
- Use good defaults: quantity starts at 1, buyer name optional.

#### 5.1.3 Team Status (Guardian)

**Components:**

- `TeamSummaryList`
  - For each child: short name (e.g., “Lisa A”), small progress bar, “X / Y”.
- `CampaignInfoCard`
  - Campaign name.
  - End date.
  - Short message from coach (optional).

**Privacy:**

- No detailed buyer info visible in this view.
- Only aggregated per-child data.

#### 5.1.4 Yearly History (Guardian – optional in later phase)

**Components:**

- `YearSelector`
  - Dropdown for year (default = current year).
- `ChildYearSummaryCard`
  - For each child:
    - Total units sold this year.
    - Total sales amount this year.
    - List of campaigns with totals.
- Simple charts (optional later):
  - Bar chart per campaign or per month.

---

### 5.2 Coach – Web & Mobile

#### 5.2.1 Campaign Setup

**Components:**

- `CampaignForm`
  - Fields:
    - Name, description.
    - Start date, end date.
    - Default target units per child.
    - Buyout amount.
    - Currency.
- `ProductListEditor`
  - Table or list with:
    - Product name, unit price, profit per unit.
  - Actions:
    - Add product.
    - Edit product.
    - Disable product (instead of delete if already used).

#### 5.2.2 Team Dashboard (Campaign View)

**Components:**

- `TeamProgressOverview`
  - Overall progress bar.
  - Total units sold.
  - Total sales amount.
- `ChildPerformanceTable`
  - Columns: name, target, sold, %, remaining.
  - Sorting options (by sold units, %, remaining, etc.).
- `ExportButton`
  - CSV download for the campaign.

#### 5.2.3 Yearly Statistics (Coach)

**Components:**

- `YearSelector`
  - Choose year (default current).
- `YearTeamOverview`
  - Card with:
    - Total units sold in year.
    - Total sales amount in year.
    - (Optionally) total profit.
- `ChildYearlyTable`
  - For each child:
    - Total units sold in year.
    - Total sales amount in year.
    - Number of campaigns participated in.
  - Sortable by units, amount, name.
- `ChildYearDetailDrawer` / modal
  - When clicking a child:
    - Show breakdown per campaign:
      - Campaign name.
      - Units sold.
      - Sales amount.
- Optional simple charts:
  - Bar chart: children vs units.
  - Bar chart: campaigns vs total units.

---

### 5.3 Common UI Components

- `AppBar/NavBar`
  - Shows current view name, access to profile/logout.
- `BottomNav` (in mobile apps)
  - Tabs like: Home, Team, History, Settings.
- `ProgressBar`
  - Used for child and team progress.
- `Card`
  - To group key information clearly.
- `Dialog/Modal`
  - For destructive actions (delete sale, etc.).
- `Toast/Snackbar`
  - For quick feedback on actions.

---

## 6. Phases (Web → iOS → Android)

### 6.1 Phase 1 – Web MVP

**Backend:**

- Implement models:
  - User, Team, Campaign, Child, GuardianChildLink, ChildCampaignTarget, Product, Sale.
- Implement auth:
  - `/auth/login`, `/me`.
- Implement core endpoints:
  - Campaign-level:
    - Get active campaign.
    - Get child campaign summary.
    - Get team campaign summary.
  - Sales:
    - Create sale.
    - List sales for guardian’s children.
  - Coach/admin:
    - Manage campaign and products.
- (Optional for MVP) Implement yearly stats endpoints:
  - At least `/stats/team/year` for coach.

**Frontend (web):**

- Tech:
  - React + TypeScript (or Django templates if you want speed over SPA).
- Guardian flows:
  - Login.
  - View “My Sales” (child progress).
  - Add sale.
  - View team campaign summary.
- Coach flows:
  - Simple “admin” area (could even be Django admin initially).
  - Manage campaign.
  - Manage products.
  - View team campaign summary / export.
  - View basic yearly statistics (table only).

**Goal:**

- Run a full real-life campaign for one team to validate:
  - Data model.
  - Core flows.
  - Usability for non-technical guardians.
- Optionally run multiple campaigns in a year to validate yearly stats outputs.

---

### 6.2 Phase 2 – iOS App (Flutter)

**Scope:**

- Create a **Flutter** app focusing on iOS first.
- Use the existing REST API.

**Screens:**

- `LoginScreen`
- `HomeScreen`
  - Shows child progress + quick action to add sale.
- `AddSaleScreen`
  - Product select, quantity, buyer info.
- `TeamStatusScreen`
  - Aggregated team view for current campaign.
- `HistoryScreen` (can be added in this phase or later)
  - Year selector, yearly stats view.
- `SettingsScreen`
  - Logout, notification preferences (basic).

**Extra:**

- Push notifications (using Firebase Cloud Messaging + APNs):
  - “X days left in campaign.”
  - “You are only N units from your target.”
- Optional:
  - Notify coach when campaign ends with quick link to yearly statistics.

**Distribution:**

- Apple Developer account.
- Use TestFlight for pilot with your team.

---

### 6.3 Phase 3 – Android App (Flutter)

**Scope:**

- Reuse Flutter codebase.
- Configure Android build (Gradle, app ID, icons).
- Test on several Android devices/emulators.

**Publish:**

- Google Play Store.
- Alternatively, private distribution (APK) for smaller groups if preferred.

---

## 7. Security, Privacy & Permissions

### 7.1 Roles & Access

- **Guardian**
  - Can view / edit sales for their linked children.
  - Can view team campaign summary (per-child aggregates, no buyer-level data for others).
  - Can (optionally) view yearly stats for their own children only.
- **Coach**
  - Can manage campaign and products.
  - Can view team stats including per-child breakdown (campaign and yearly).
  - Can export all sales data for the team’s campaigns.

### 7.2 Personal Data

- Children:
  - Store minimal info: first name + optional last initial or shirt number.
- Buyers:
  - Only optional `buyer_name` string.
  - Avoid storing sensitive contact info unless absolutely required.
- Guardians:
  - Email + hashed password.
  - Names for personalization.

### 7.3 Transport & Storage

- All API endpoints served over **HTTPS** (even on Raspberry Pi, via reverse proxy).
- Passwords:
  - Use strong password hashing (Argon2 or bcrypt).
- Backups:
  - Regular database backups to encrypted storage.
  - Consider off-device backup (e.g., encrypted dump to cloud storage).

---

## 8. Raspberry Pi Deployment Sketch

### 8.1 Conceptual `docker-compose.yml`

Services:

- `db` – PostgreSQL.
- `backend` – Django + Gunicorn.
- `reverse-proxy` – Caddy or Nginx:
  - Terminates TLS.
  - Serves static files and forwards `/api/` to backend.

**High-level structure (pseudo):**

```yaml
version: "3.9"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: salesapp
      POSTGRES_USER: salesuser
      POSTGRES_PASSWORD: changeme
    volumes:
      - db_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgres://salesuser:changeme@db:5432/salesapp
    depends_on:
      - db

  proxy:
    image: caddy:latest
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend

volumes:
  db_data:
```

- Frontend build:
  - Either served as static files from the proxy (React build) or from Django.

### 8.2 Local Development

- Develop backend locally on your Mac:
  - Use Django + SQLite for speed initially.
- Once models & API stabilize:
  - Switch to Postgres locally or in Docker.
- Deploy to Pi:
  - Copy repo, build Docker images, run `docker-compose up -d`.

---

## 9. Extensibility Ideas (Future)

- Invite links for guardians per child (instead of manually linking).
- Public “support page” per child:
  - A simple, shareable link where friends/family can place orders directly tied to that child.
- In-app coach messages:
  - Simple announcements visible for all guardians in a campaign.
- Simple gamification:
  - Badges for milestones (“First sale”, “50% of target”, “Target reached”).
- Widgets on mobile:
  - Show current campaign progress and yearly stats on device home screen (iOS/Android widgets).
- More advanced reporting:
  - Export yearly stats by year, by campaign type, etc.

---

This file is intended to be saved as `specification.md` in your project repo and used as a living system specification as you build the web MVP, then the iOS app, and later the Android app, now including yearly history/statistics for leaders (and optionally all users).
