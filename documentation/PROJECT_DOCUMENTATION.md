# 📚 PROJECT_DOCUMENTATION.md - Finance Forecast Project - Complete Documentation

**Project:** Finance Forecast - Intelligent Banking Transaction Analysis System  
**Status:** ✅ PRODUCTION READY  
**Last Updated:** January 14, 2026  
**Document Version:** 3.0 (Complete Project Coverage)

**Location:** `documentation/PROJECT_DOCUMENTATION.md`

---

## ⚡ Executive Summary

### **What This Project Is**
A full-stack web application that helps users analyze their bank transactions, detect subscriptions, manage budgets, and gain financial insights. It includes intelligent pattern recognition, user-configurable preferences, multi-language support, and a modern responsive UI.

### **Technology Stack**
- **Backend:** Python 3.13 + Django 6.0
- **Frontend:** React 18 + Tailwind CSS
- **Database:** PostgreSQL
- **Cache/Message Queue:** Redis + Celery
- **AI/LLM:** Ollama (GEMMA2 model)
- **Auth:** Google OAuth2 via django-allauth
- **Deployment:** Docker Compose

### **Key Features**
✅ Bank account management  
✅ Transaction import (CSV + JSON)  
✅ Recurring transaction detection  
✅ Budget rules & auto-categorization  
✅ AI-powered financial insights  
✅ Multi-language support (EN + DE)  
✅ Configurable number/date/currency formats  
✅ Sensitive mode (blur financial data)  
✅ Dark mode  
✅ Mobile-responsive UI  

### **Quick Deploy**
```bash
cd /Users/matthiasschmid/Projects/finance
./dc.sh build web celery-worker celery-beat
./dc.sh up -d web celery-worker celery-beat
```

---

## 📑 Complete Table of Contents

### Architecture & Technology
1. [Technology Stack](#-technology-stack)
2. [Project Structure](#-project-structure)
3. [Database Design](#-database-design)
4. [API Architecture](#-api-architecture)

### Core Features
5. [Authentication & Users](#-authentication--users)
6. [Bank Accounts & Transactions](#-bank-accounts--transactions)
7. [Categories & Rules](#-categories--rules)
8. [Recurring Transactions](#-recurring-transactions)
9. [AI Insights](#-ai-insights)
10. [Analytics](#-analytics)

### User Experience
11. [Frontend Architecture](#-frontend-architecture)
12. [UI Components & Features](#-ui-components--features)
13. [Sensitive Mode](#-sensitive-mode)
14. [Dark Mode](#-dark-mode)
15. [Format Preferences](#-format-preferences)
16. [Internationalization](#-internationalization)

### Deployment & Operations
17. [Docker Compose Setup](#-docker-compose-setup)
18. [Environment Configuration](#-environment-configuration)
19. [Background Tasks (Celery)](#-background-tasks-celery)
20. [Database Migrations](#-database-migrations)

### Development
20. [Design Decisions](#-design-decisions)
21. [Critical Bugs Fixed](#-critical-bugs-fixed)
22. [Error Handling](#-error-handling)
23. [Security Measures](#-security-measures)
24. [Performance Optimization](#-performance-optimization)

### Future & Reference
25. [Future Enhancements](#-future-enhancements)
26. [Development Guide](#-development-guide)
27. [Support & Troubleshooting](#-support--troubleshooting)

---

## 🏗️ Technology Stack

### **Backend** (Python/Django)
```
Django              6.0.1       - Web framework
Django REST         3.15.2      - API framework
Python              3.13        - Language
PostgreSQL          16-alpine   - Database
Redis               7-alpine    - Cache/message broker
Celery              5.3.6       - Task queue
```

### **Frontend** (JavaScript/React)
```
React               18.2.0      - UI library
Tailwind CSS        3.4.1       - Styling
esbuild             0.19.11     - Bundler
Chart.js            4.4.1       - Charts
axios               1.6.8       - HTTP client
```

### **Authentication**
```
django-allauth      0.63.3      - Auth framework
google-auth         -           - Google OAuth
PyJWT               2.10.1      - JWT tokens
```

### **Infrastructure & Services**
```
Gunicorn            21.2.0      - WSGI server
WhiteNoise          6.6.0       - Static files
Ollama              latest      - LLM service
Docker Compose      -           - Orchestration
```

### **Development Tools**
```
pytest              8.2.1       - Testing
black               24.1.1      - Code formatter
flake8              6.1.0       - Linter
isort               13.2        - Import sorter
```

---

## 📁 Project Structure

```
finance/
├─ backend/                      # Django application
│  ├─ finance_project/           # Main Django project
│  │  ├─ settings_base.py        # Base settings (all environments)
│  │  ├─ settings_local.py       # Override settings (gitignored)
│  │  ├─ settings.py             # Loads base + local
│  │  ├─ celery.py               # Celery configuration
│  │  ├─ middleware.py           # Custom Django middleware
│  │  ├─ urls.py                 # URL routing
│  │  ├─ templates/              # Django templates
│  │  ├─ static/                 # CSS, JS, built frontend
│  │  └─ apps/                   # Django applications
│  │     ├─ accounts/            # User management & OAuth
│  │     ├─ banking/             # Bank accounts & transactions
│  │     ├─ analytics/           # Statistics & analytics
│  │     └─ ai/                  # AI insights & category generation
│  ├─ requirements.txt           # Python dependencies
│  ├─ docker/                    # Docker configuration
│  │  └─ Dockerfile              # Container definition
│  ├─ manage.py                  # Django CLI
│  └─ pytest.ini                 # Test configuration
│
├─ frontend/                     # React application
│  ├─ src/
│  │  ├─ index.jsx               # Main app (496 lines - complex state mgmt)
│  │  ├─ index.css               # Global styles (Tailwind imports)
│  │  ├─ components/             # React components
│  │  │  ├─ Dashboard.jsx        # Main dashboard
│  │  │  ├─ TransactionsTable.jsx # Transaction list with edit
│  │  │  ├─ AccountDetailsView.jsx # Account detail modal
│  │  │  ├─ ImportCsvModal.jsx   # CSV/JSON import
│  │  │  ├─ CreateAccountModal.jsx # Create bank account
│  │  │  ├─ CategoriesManager.jsx # Category CRUD
│  │  │  ├─ RulesManager.jsx     # Rule CRUD
│  │  │  ├─ RecurringTransactionsView.jsx # Subscriptions
│  │  │  ├─ InsightsPanel.jsx    # AI insights
│  │  │  ├─ LoginPage.jsx        # Login/signup
│  │  │  ├─ LandingPage.jsx      # Public landing page
│  │  │  ├─ CookieConsent.jsx    # GDPR cookie consent
│  │  │  └─ ... more components
│  │  ├─ utils/                  # Helper functions
│  │  │  ├─ format.js            # Date/currency/number formatting
│  │  │  ├─ i18n.js              # Internationalization
│  │  │  ├─ sensitive.js         # Sensitive mode blur
│  │  │  ├─ csrf.js              # CSRF token handling
│  │  │  └─ ...
│  │  ├─ hooks/                  # React hooks
│  │  │  └─ useLanguage.jsx      # Translation hook
│  │  └─ locales/                # Translation files
│  │     ├─ en.json              # English translations (1000+ keys)
│  │     └─ de.json              # German translations (1000+ keys)
│  ├─ package.json               # Dependencies & scripts
│  ├─ tailwind.config.js         # Tailwind configuration
│  └─ postcss.config.js          # PostCSS configuration
│
├─ deploy/                       # Deployment files
│  ├─ docker-compose.yml         # Service orchestration
│  ├─ .env.example               # Environment template
│  └─ .env.local                 # Actual secrets (gitignored)
│
├─ dc.sh                         # Docker Compose shorthand script
├─ README.md                     # Project documentation
└─ CLAUDE.md                     # This file

```

---

## 💾 Database Design

### **Data Models Overview**

```
User (Django auth)
├─ UserProfile              # Per-user settings
├─ AllowedGoogleUser        # OAuth whitelist
├─ BankAccount (many)       # User's bank accounts
│  └─ Transaction (many)    # Individual transactions
│     └─ Category           # Transaction category
├─ Category (many)          # User's custom categories
├─ Rule (many)              # Auto-categorization rules
└─ RecurringTransaction (many) # Detected subscriptions
```

### **Key Tables**

**UserProfile** (Per-user configuration)
```python
- user (OneToOne to Django User)
- currency_preference: "USD", "EUR", etc.
- preferences: JSON (stores all format prefs)
  {
    "dateFormat": "MM/DD/YYYY",
    "numberFormat": "1,000.00",
    "language": "en",
    "sensitiveMode": false,
    "darkMode": false
  }
```

**BankAccount** (User's accounts)
```python
- user: FK
- name: String (e.g., "Checking", "Savings")
- institution: String (e.g., "Chase")
- iban: String (optional, max 34 chars)
- currency: String (default "EUR")
- opening_balance: Decimal
- opening_balance_date: Date (optional, for calculating real balance)
- created_at: DateTime
```

**Transaction** (Bank transactions)
```python
- account: FK (BankAccount)
- date: Date
- amount: Decimal (max_digits=12, decimal_places=2)
- reference: String (512 chars max - transaction reference/ID from bank)
- description: String (1024 chars max - transaction description)
- category: FK (Category, nullable)
- type: Choice (income/expense/transfer)
  # Automatically set to "transfer" if partner_iban matches user's account (see below)

# Extended fields for rich data (from bank imports)
- partner_name, partner_iban, partner_account_number
- owner_account, owner_name
- reference_number, booking_date, valuation_date
- virtual_card_number, virtual_card_device
- payment_app, payment_method, merchant_name
- exchange_rate, transaction_fee
- booking_type, sepa_scheme
- meta: JSON (any additional data)

# Metadata
- created_at, updated_at
```

**Transaction Type Classification:**
- **income:** Money coming into the account (salary, refunds, transfers from others)
- **expense:** Money going out to merchants or external parties (purchases, bills, payments)
- **transfer:** Money moving between accounts owned by the same user (auto-detected if partner_iban matches user's account IBAN)

**Automatic Transfer Detection (NEW):**
During CSV/JSON import, transactions are automatically labeled as "transfer" when:
- The `partner_iban` field matches an IBAN of any bank account owned by the user
- Detection is case-insensitive and whitespace-tolerant
- If detected, overrides any explicit type in the CSV
- Example: Transferring $1000 to your savings account automatically gets labeled "transfer", not "expense"
- Logged for monitoring: Info log when internal transfer detected, debug log when no match found

---

## **Category** (User-defined)
```python
- user: FK
- name: String (max 100, unique per user)
- color: String (hex color, e.g., "#3b82f6")
```

**Rule** (Auto-categorization)
```python
- user: FK
- name: String
- conditions: JSON
  {
    "description_contains": ["netflix"],
    "amount_range": [0, 100],
    "date_from": "2024-01-01"
  }
- category: FK
- priority: Int (lower = higher priority)
- active: Boolean
```

**RecurringTransaction** (Detected subscriptions)
```python
- account: FK
- user: FK
- description, merchant_name: String
- amount: Decimal
- frequency: Choice (weekly/bi-weekly/monthly/quarterly/yearly)
- next_expected_date, last_occurrence_date: Date
- occurrence_count: Int
- confidence_score: Float (0-1)
- is_active, is_ignored: Boolean
- user_notes: Text
- similar_descriptions: JSON (list of variants)
- transaction_ids: JSON (list of matching transaction IDs)
```

**ExchangeRate** (Global currency exchange rates - singleton)
```python
# SINGLETON MODEL: Only one record (pk=1) exists system-wide
# Caches USD-based exchange rates from OpenExchangeRates API

- rates: JSON
  {
    "EUR": 0.9200,
    "GBP": 0.7920,
    "JPY": 145.50,
    ...
  }
- last_updated: DateTime (timestamp of last successful API fetch)
- api_url: URL (endpoint used, stored for reference)
- error_message: Text (blank if OK, contains error if fetch failed)

# Usage:
# - Fetched hourly via Celery beat task: fetch_exchange_rates_task
# - Base currency: USD (1.0 is implicit for USD)
# - If fetch fails: keeps cached rates, doesn't crash (graceful degradation)
# - Used for displaying account balances in user's preferred currency
```

---

## 🚀 API Architecture

### **All Endpoints Overview**

**Accounts/Auth:**
```
POST   /api/accounts/auth/login/           - Google OAuth
POST   /api/accounts/auth/logout/          - Logout
GET    /api/accounts/auth/check/           - Check authentication
GET    /api/accounts/profile/              - Get user profile
PATCH  /api/accounts/profile/              - Update profile (currency, prefs)
GET    /api/accounts/preferences/          - Get all preferences
PATCH  /api/accounts/preferences/          - Update preferences
GET    /api/currencies/                    - List available currencies
```

**Bank Accounts:**
```
GET    /api/banking/accounts/              - List user's accounts (includes converted_balance, conversion_rate_age)
POST   /api/banking/accounts/              - Create account
GET    /api/banking/accounts/{id}/         - Get account details
PATCH  /api/banking/accounts/{id}/         - Update account
DELETE /api/banking/accounts/{id}/         - Delete account
GET    /api/banking/accounts/{id}/balance-timeline/ - Chart data
```

**Transactions:**
```
GET    /api/banking/transactions/          - List transactions (paginated, filterable)
POST   /api/banking/transactions/          - Create transaction (manual)
GET    /api/banking/transactions/{id}/     - Get transaction
PATCH  /api/banking/transactions/{id}/     - Update transaction
DELETE /api/banking/transactions/{id}/     - Delete transaction
POST   /api/banking/transactions/import/   - Import CSV/JSON
```

**Categories:**
```
GET    /api/banking/categories/            - List categories
POST   /api/banking/categories/            - Create category
PATCH  /api/banking/categories/{id}/       - Update category
DELETE /api/banking/categories/{id}/       - Delete category
```

**Rules:**
```
GET    /api/banking/rules/                 - List rules
POST   /api/banking/rules/                 - Create rule
PATCH  /api/banking/rules/{id}/            - Update rule
DELETE /api/banking/rules/{id}/            - Delete rule
POST   /api/banking/rules/apply/           - Apply rules to transactions
```

**Recurring Transactions:**
```
GET    /api/banking/recurring/             - List recurring patterns
GET    /api/banking/recurring/summary/     - Summary stats (total, costs, breakdown)
GET    /api/banking/recurring/overdue/     - Get overdue items
GET    /api/banking/recurring/upcoming/    - Get upcoming items
POST   /api/banking/recurring/detect/      - Trigger detection
POST   /api/banking/recurring/{id}/ignore/ - Mark as ignored
POST   /api/banking/recurring/{id}/unignore/ - Unignore
PATCH  /api/banking/recurring/{id}/add_note/ - Add notes
GET    /api/banking/recurring/{id}/linked_transactions/ - Get linked transactions (NEW)
```

**Analytics:**
```
GET    /api/analytics/overview/            - Total balance, income vs expenses, trends
GET    /api/analytics/accounts/{id}/balance-timeseries/ - Balance history for chart
GET    /api/analytics/category-expense/    - Category breakdown (NEW: supports ?period=)

Query Parameters for category-expense:
  - period: one of [current_month, last_month, current_year, last_year, 
                     current_week, last_week, all_time]
  - default: current_month
  - example: /api/analytics/category-expense/?period=last_month
```

**AI Insights:**
```
POST   /api/ai/insights/                   - Get AI insights
POST   /api/ai/generate-categories/        - Generate categories from transactions
```

---

## 👤 Authentication & Users

### **Google OAuth2 Flow**

1. User clicks "Sign in with Google" on login page
2. Redirect to Google auth endpoint (via django-allauth)
3. User confirms with Google
4. Google redirects back with auth code
5. Django exchanges code for user info
6. User created/updated in database
7. Django session/JWT token created
8. User redirected to dashboard

### **Configuration**

**In settings_base.py:**
```python
INSTALLED_APPS += [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

**Environment variables (.env.local):**
```
SOCIALACCOUNT_PROVIDERS={
    'google': {
        'APP': {...},
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': False,
    }
}
```

### **Allowlist Feature**

Optional feature to restrict login to specific email addresses:

```python
# In settings_base.py
ALLOWLIST_ENABLED = env.bool('ALLOWLIST_ENABLED', default=False)

# In OAuth callback handler
if ALLOWLIST_ENABLED:
    AllowedGoogleUser.objects.get(email=user.email, active=True)
    # Raises DoesNotExist if not in allowlist
```

---

## 🏦 Bank Accounts & Transactions

### **Account Management**
- Users create multiple bank accounts
- Each account has currency (EUR, USD, etc.)
- Opening balance + opening balance date for reference calculations
- IBAN support for real-world banking

### **Transaction Import**

**CSV Format Support:**
```csv
date,amount,description,type,category,partner_name,iban
2026-01-14,350.00,Netflix subscription,expense,Entertainment,Netflix,DE89370400440532013000
```

**JSON Format Support:**
```json
{
  "booking": "2026-01-14T00:00:00Z",
  "amount": {"value": -350, "precision": 2},
  "partnerName": "NETFLIX",
  "reference": "Monthly subscription",
  "cardNumber": "516879XXXXXX7877"
}
```

**Decimal Handling:**
- All amounts stored as Decimal (not float)
- JSON "precision" field handled: value=5070, precision=2 → 50.70
- No floating-point rounding errors

---

## 🎯 Categories & Rules

### **Categories**
- User-defined categories with custom colors
- Each transaction can have a category
- Used for reporting and filtering
- AI can auto-generate categories from transaction patterns
- **Search functionality**: Search categories by name (case-insensitive partial match)
- **Ordering/Sorting**: Sort by name or color (ascending/descending)
- **Duplicate prevention**: Backend validates to prevent duplicate category names for the same user
- **Validation**: User-friendly translated error messages for validation failures

#### **Category Management Features**
| Feature | Details |
|---------|---------|
| **Search** | Query parameter: `?search=category_name` |
| **Ordering** | Query parameter: `?ordering=name` or `?ordering=-name` |
| **Sortable Fields** | `name`, `color` |
| **Default Sort** | By name (ascending) |
| **Search Fields** | `name` (case-insensitive contains) |
| **Duplicate Check** | Prevents same user from creating categories with identical names |
| **Validation** | Django REST Framework serializer validation with translated error messages |
| **Error Handling** | Returns proper REST API response with field-specific validation errors |

#### **API Examples**

**Get all categories:**
```
GET /api/banking/categories/
```

**Search for categories containing "Entertainment":**
```
GET /api/banking/categories/?search=Entertainment
```

**Sort by name ascending:**
```
GET /api/banking/categories/?ordering=name
```

**Sort by name descending:**
```
GET /api/banking/categories/?ordering=-name
```

**Combine search and sort:**
```
GET /api/banking/categories/?search=Ent&ordering=-name
```

**Sort by color:**
```
GET /api/banking/categories/?ordering=color
GET /api/banking/categories/?ordering=-color
```

#### **Error Handling**

**Duplicate Category Error** (Translated)
- English: "A category with this name already exists."
- German: "Eine Kategorie mit diesem Namen existiert bereits."
- Backend validates **before** database constraint violation
- Returns HTTP 400 with proper error response

**Required Field Errors** (Translated)
- English: "Category name is required."
- German: "Der Kategoriename ist erforderlich."

#### **Frontend Implementation**

**CategoriesManager Component:**
- Search input with real-time filtering
- Sortable column headers (Name, Color)
- Click to toggle sort direction
- Pagination support
- Error modal with translated messages
- Create/Edit modals with validation

**Backend ViewSet Configuration:**
```python
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'color']
    ordering = ['name']  # Default ordering
```

### **Rules** (Auto-categorization)
- Conditions: description contains, amount range, date range
- Match transactions and auto-assign category
- Editable priority (lower = higher priority)
- Can be toggled active/inactive

**Example Rule:**
```python
{
    "name": "Netflix",
    "conditions": {
        "description_contains": ["netflix", "NETFLIX.COM"],
        "amount_range": [9, 20]
    },
    "category_id": 5,
    "priority": 10,
    "active": true
}
```

---

## 🔄 Recurring Transactions

### **Detection Algorithm - Improved Three-Pass Strategy**

The detection system uses an **advanced multi-field matching strategy** with intelligent priority-based frequency selection:

**Pass 1: Partner Information Matching (Primary - 95%+ Confidence)**
- Matches by: `partner_iban` + `partner_name` + `payment_method`
- Why this is best: Bank account uniquely identifies source/destination
- Example: Netflix from DE89XXXXX + "NETFLIX Inc" + "CARD" always matches
- Confidence potential: 95%+ (nearly unique identification)
- **Most reliable method - uses bank-provided data**

**Pass 2: Merchant Information Matching (Secondary - 75-85% Confidence)**
- Matches by: `merchant_name` + `payment_method` + `card_brand`
- Why this works: Merchant + payment type = reliable identification
- Example: Amazon VISA is grouped separately from Amazon MASTERCARD
- Distinguishes payment sources (different cards = different patterns)
- Confidence potential: 75-85% (good reliability, handles variations)
- **Good method - uses standardized merchant data**

**Pass 3: Description Text Matching (Tertiary - 50-70% Confidence)**
- Matches by: `reference` + `description` (fuzzy matching)
- Why this works: Last resort for transactions with minimal data
- Example: "Netflix" ≈ "NETFLIX.COM" ≈ "Netflix GmbH"
- Confidence potential: 50-70% (moderate, used as fallback)
- **Fallback method - uses text-based pattern matching**

### **Best-Match Frequency Selection (NEW)**

Unlike traditional approaches that might detect a single transaction as "monthly AND quarterly AND yearly", this system now returns **only the best-matching frequency** per transaction group:

**Frequency Priority System:**
- **Weekly (Priority 5):** Most specific, easiest to verify, highest priority
- **Bi-weekly (Priority 4):** Specific, common (every 2 weeks)
- **Monthly (Priority 3):** Most common, less specific than weekly
- **Quarterly (Priority 2):** Less common, more ambiguous
- **Yearly (Priority 1):** Least specific, easiest to accidentally match

**How Best Match Is Selected:**
```
Score = Confidence×0.5 + Priority×0.2 + Occurrences×0.2 + Accuracy×0.1
```
- Confidence (50%): How consistent the pattern is
- Priority (20%): Frequency specificity (weekly > yearly)
- Occurrences (20%): More transactions = better
- Accuracy (10%): How close to expected interval

**Example: Netflix (30-day intervals)**
```
Weekly:    0.15×0.5 + 1.0×0.2 + 1.0×0.2 + 0.1×0.1 = 0.485 ❌
Monthly:   0.95×0.5 + 0.6×0.2 + 1.0×0.2 + 0.95×0.1 = 0.890 ✅ BEST
Quarterly: 0.35×0.5 + 0.4×0.2 + 1.0×0.2 + 0.2×0.1 = 0.475 ❌
Yearly:    0.25×0.5 + 0.2×0.2 + 1.0×0.2 + 0.1×0.1 = 0.355 ❌

Result: Netflix detected as MONTHLY only (no duplicates)
```

### **Detection Parameters**

**Lookback Period:** 1825 days (365 × 5 years)
- Extended from 365 days to capture yearly subscriptions and annual fees
- Enables detection of:
  - Annual insurance policies
  - Yearly membership renewals
  - Birthday reminders
  - Tax returns
  - Holiday spending patterns

**Minimum Occurrences:**
- Weekly: 3 occurrences (3 weeks)
- Bi-weekly: 3 occurrences (6 weeks)
- Monthly: 2 occurrences (2 months)
- Quarterly: 2 occurrences (6 months)
- **Yearly: 2 occurrences (2 years)** ← Updated from 1


**Tolerances:**
- Amount tolerance: 5% (for small price variations)
- Interval tolerance: 30% of expected days (e.g., ±9 days for monthly)

**Confidence Scoring (0-1 scale):**
- Pass 1 (Partner Info) multiplier: 1.0 → 95%+ potential
- Pass 2 (Merchant Info) multiplier: 0.85 → 75-85% potential
- Pass 3 (Description) multiplier: 0.65 → 50-70% potential
- Components (weighted):
  - Interval consistency: 50% weight
  - Amount consistency: 30% weight
  - Occurrence ratio: 20% weight
- Minimum threshold: 60% (transactions below this are filtered out)

### **Why This Is Improved**

1. **Bank Account Matching (NEW - Pass 1):** Uses `partner_iban` + `partner_name` + `payment_method`
   - Bank account uniquely identifies the source/destination
   - Nearly impossible to accidentally match wrong transactions
   - **95%+ confidence potential**

2. **Multi-Field Merchant Matching (Enhanced - Pass 2):** Uses `merchant_name` + `payment_method` + `card_brand`
   - Includes card brand to distinguish payment sources
   - Amazon VISA ≠ Amazon MASTERCARD (separate patterns)
   - Handles merchant name variations
   - **75-85% confidence potential**

3. **Single Best-Match Frequency Selection (NEW):**
   - Returns only best-matching frequency per transaction group
   - Prevents duplicates (no more "monthly AND quarterly AND yearly")
   - Prioritizes specific frequencies (weekly=5) over vague ones (yearly=1)
   - **Eliminates user confusion**

4. **Pass-Based Confidence Multipliers:**
   - Reflects quality of the matching method used
   - Most reliable method gets highest multiplier (1.0)
   - Least reliable method gets lowest multiplier (0.65)
   - Provides meaningful, calibrated confidence scores

5. **Longer Historical Period:** 5 years instead of 1 year
   - Captures annual subscriptions (insurance, memberships, etc.)
   - Detects seasonal patterns (holidays, tax time, etc.)
   - Increases confidence for infrequent but regular payments

6. **Higher Bar for Yearly:** Requires 2 occurrences instead of 1
   - Prevents false positives from one-time yearly events
   - Ensures pattern recurrence before flagging as recurring

7. **Progressive Priority:** Most reliable methods first
   - Bank data checked before merchant data
   - Merchant data checked before text matching
   - Results in higher overall detection accuracy

### **User Management**
- Can ignore false positives
- Can add personal notes
- See next expected date and days until
- Get alerts for overdue subscriptions
- View monthly/yearly cost equivalents
- **View linked transactions** - Click the 🔗 button to see all actual transactions that match this recurring pattern

### **Linked Transactions Feature (NEW)**
Users can now click the 🔗 button next to any recurring transaction to view all the actual bank transactions that form the pattern. This provides deep insights into:
- All individual transaction dates and amounts
- Payment descriptions and references
- Categories assigned to each transaction
- Confirms the pattern detection was correct

**Backend Implementation:**
- New endpoint: `GET /api/banking/recurring/{id}/linked_transactions/`
- Returns the list of Transaction objects stored in `RecurringTransaction.transaction_ids`
- Includes full transaction details via TransactionSerializer
- Respects user permissions (only shows user's own transactions)

**Frontend Implementation:**
- New LinkedTransactionsModal component displays transactions in a scrollable table
- Shows date, description, reference, amount (color-coded), and category
- Modal header displays recurring pattern summary (description, frequency)
- Footer shows total transaction count
- Responsive design works on mobile devices

### **Admin Dashboard** (Django Admin)
- Full CRUD interface for reviewing detected patterns
- Display name, merchant, frequency, amount, confidence score
- Visual confidence indicators (green/blue/yellow/red)
- Filter by frequency, status (active/ignored), account
- Search by description, merchant name, account
- View matching transaction IDs and similar descriptions
- Readonly confidence calculation details
- Superuser-only delete permission
- Manual creation disabled (only via detection)

### **API - 8 Endpoints**
✅ List (with pagination/filtering), summary, overdue, upcoming, detect, ignore/unignore, add notes, linked_transactions (NEW)

### **Frontend Components**
- **RecurringTransactionsView:** Complete dashboard with pagination
  - Account selection
  - Summary cards (total, active, monthly/yearly costs)
  - Frequency breakdown
  - Searchable, filterable list (25 items per page)
  - Pagination controls
  - Ignore/unignore transactions
  - Add user notes
  - **View linked transactions** - Click 🔗 to see all transactions in the pattern
- **LinkedTransactionsModal:** (NEW) Modal showing all linked transactions
  - Displays full transaction details (date, description, reference, amount, category)
  - Scrollable table for large transaction sets
  - Header shows recurring pattern details
  - Footer shows total transaction count
  - Close button to dismiss modal
- **Overdue alerts:** Visual warnings for missed recurring transactions
- **Confidence scores:** Color-coded percentages (90%+ green, 75%+ blue, 60%+ yellow, <60% red)

---

## 🤖 AI Insights

### **Implementation**
- Uses Ollama LLM locally (GEMMA2 model)
- HTTP-based communication to Ollama service
- Fallback to mock provider in development
- Configurable host (localhost:11434 or docker service)

### **Capabilities**
1. **Financial Insights** - Budgeting suggestions, spending analysis
2. **Category Generation** - Auto-create categories from transactions
3. **Expense Analysis** - Identify unusual patterns

### **Configuration**
```python
# In settings_base.py
OLLAMA_HOST = env('OLLAMA_HOST', default='http://ollama:11434')
ACTIVE_AI_PROVIDER = env('ACTIVE_AI_PROVIDER', default='ollama')

# Services using it
- InsightsPanel (generate insights from transactions)
- CategoryGeneratorService (auto-create categories)
```

---

## 📊 Analytics

### **Available Metrics**
- **Total Balance** - Sum of all accounts
- **Income vs Expenses** - Monthly breakdown
- **Monthly Trends** - Balance over time
- **Category Breakdown** - Spending by category
- **Recurring Costs** - Monthly/yearly subscriptions

### **Timeline Data**
- Daily balance calculation
- Filters by date range, account, category
- Used for charting (Chart.js)

---

## 🎨 Frontend Architecture

### **State Management (React)**
Main app state in `index.jsx` (496 lines):
```javascript
- activeTab              // current view (dashboard, transactions, etc.)
- showImportModal       // import dialog visibility
- sidebarCollapsed      // sidebar state
- isAuthenticated       // user auth status
- loading               // loading state
- showSettingsMenu      // settings dropdown
- sensitiveMode         // blur financial data
- darkMode              // dark theme
- compactView           // compact layout
- formatPrefs           // date/currency/number formats
```

### **Component Hierarchy**
```
AppContent (main)
├─ Header (logo, menu, settings)
├─ Sidebar (navigation)
├─ MainContent (tab routing)
│  ├─ Dashboard
│  │  ├─ SummaryCards
│  │  ├─ CategoryPieChart
│  │  ├─ IncomeExpenseChart
│  │  └─ TopTransactions
│  ├─ TransactionsTable
│  │  ├─ Filters (date, category, amount)
│  │  ├─ Search
│  │  ├─ EditTransactionModal
│  │  └─ Pagination
│  ├─ AccountDetailsView (modal)
│  │  ├─ BalanceChart
│  │  ├─ AccountFilters
│  │  └─ TransactionsList
│  ├─ CategoriesManager (CRUD)
│  ├─ RulesManager (CRUD)
│  ├─ RecurringTransactionsView
│  ├─ InsightsPanel (AI)
│  └─ ...
├─ SettingsMenu
│  ├─ Sensitive Mode toggle
│  ├─ Dark Mode toggle
│  ├─ Compact View toggle
│  ├─ Format Preferences (date, currency, numbers)
│  ├─ Language selector
│  └─ Logout
└─ Footer
```

---

## 🎯 UI Components & Features

### **DateInput Component** (Reusable Date Input with Picker)

### **CustomDatePicker Component** (Professional Custom Calendar)

A fully custom, professional date picker with calendar UI, multilingual support, and configurable date formats.

#### **Features**
- ✅ Beautiful custom calendar UI with month/year navigation
- ✅ Text input for manual date entry in user's preferred format
- ✅ Multilingual support (English, German, extensible)
- ✅ Respects user's configured date format
- ✅ Click outside to close
- ✅ "Today" button in footer
- ✅ Professional Tailwind styling
- ✅ Works reliably everywhere (modals, flexible layouts)
- ✅ Keyboard accessible

#### **Supported Languages**
| Language | Month Names | Day Names | Button Text |
|----------|------------|-----------|-------------|
| English | January, February, ... | Sun, Mon, ... | Today |
| German | Januar, Februar, ... | So, Mo, ... | Heute |

New languages can be added easily by extending monthNames and dayNames objects.

#### **Supported Date Formats**
- MM/DD/YYYY (US)
- DD/MM/YYYY (Europe)
- YYYY-MM-DD (ISO/Nordic)
- DD.MM.YYYY (German)

Respects user's format preference configured in Settings.

#### **Props**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | string | undefined | ISO format date (YYYY-MM-DD) |
| `onChange` | function | required | Callback receiving ISO format date |
| `placeholder` | string | auto | Input placeholder (auto-generated if not provided) |
| `title` | string | "Enter date in your preferred format" | Tooltip text |
| `showPickerButton` | boolean | true | Show/hide 📅 button |
| `className` | string | "" | Additional CSS classes |

#### **Usage Example**
```javascript
import CustomDatePicker from './CustomDatePicker'

<CustomDatePicker
  value={dateFrom}  // ISO format: "2026-01-14"
  onChange={(isoDate) => setDateFrom(isoDate)}
  title="Start date for filter"
  showPickerButton={true}
/>
```

#### **How It Works**

**Calendar Modal:**
- Shows current month with clickable dates
- Month/year header with navigation arrows (←/→)
- Previous month and next month navigation
- Selected date highlighted in blue
- Today's date shown with blue border
- "Today" button in footer for quick selection
- Click outside to close calendar

**Manual Text Entry:**
- Type date in user's preferred format
- Real-time format validation
- Press Enter or click away to confirm
- Placeholder shows expected format

**Data Flow:**
```
User Action
    ↓
Type date OR click calendar
    ↓
Format validation/conversion
    ↓
Convert to ISO format (YYYY-MM-DD)
    ↓
onChange callback with ISO date
    ↓
Parent component receives date
```

#### **Components Using CustomDatePicker**
1. **AccountDetailsView** - Date range filters for transactions
2. **CreateAccountModal** - Opening balance reference date
3. **RulesManager** - Rule date range conditions

#### **Implementation Details**
- File: `frontend/src/components/CustomDatePicker.jsx`
- Exports: `DateInput.jsx` (backward compatible)
- Dependencies: `format.js` utilities, `useLanguage` hook
- Size: ~250 lines of well-commented code
- Styling: Tailwind CSS (fully responsive)

#### **Adding New Languages**
To add a new language (e.g., Spanish):

```javascript
// In CustomDatePicker.jsx
const monthNames = {
  en: ['January', 'February', ...],
  de: ['Januar', 'Februar', ...],
  es: ['Enero', 'Febrero', ...],  // ADD THIS
}

const dayNames = {
  en: ['Sun', 'Mon', ...],
  de: ['So', 'Mo', ...],
  es: ['Do', 'Lu', ...],  // ADD THIS
}

// For footer button (es = Spanish):
{currentLanguage === 'es' ? 'Hoy' : 'Today'}
```

#### **Styling Customization**
Calendar colors and styles can be customized via Tailwind classes:
- Selected date: `bg-blue-600`
- Today indicator: `border-blue-500`
- Hover effect: `hover:bg-gray-100`
- Font sizes: `text-sm` for days

Adjust these classes directly in the component for different styling.

#### **Browser Support**
✅ All modern browsers (Chrome, Firefox, Safari, Edge)
✅ Mobile browsers (iOS Safari, Chrome Mobile)
✅ Works inside modals and overlays
✅ Responsive design

#### **Backward Compatibility**
✅ **DateInput component still works exactly the same**
- All existing imports continue to work
- All existing props work identically
- Components need no code changes
- CustomDatePicker is transparently used





### **Backend Pagination (Best Practice)**

**All list views use backend pagination for efficiency and scalability.**

When building list views that display large datasets, always use backend pagination:

1. **Request Format:**
```javascript
// Always include pagination parameters
const params = new URLSearchParams()
params.append('page', String(currentPage))
params.append('page_size', String(itemsPerPage))
params.append('ordering', '-date')  // Optional: sorting

// Add filters as needed
if (filters.category) params.append('category', filters.category)
if (filters.search) params.append('search', filters.search)

const res = await axios.get(`/api/endpoint/?${params.toString()}`)
```

2. **Response Structure:**
```json
{
  "count": 1234,
  "next": "http://api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

3. **Frontend Handling:**
```javascript
const [currentPage, setCurrentPage] = useState(1)
const itemsPerPage = 25  // Standard page size
const [totalCount, setTotalCount] = useState(0)
const [items, setItems] = useState([])

// Calculate total pages
const totalPages = Math.ceil(totalCount / itemsPerPage)

// Load data when filters or page changes
useEffect(() => {
  loadData()
}, [filters, currentPage])
```

4. **Pagination Controls:**
- First page button (⏮)
- Previous button (←)
- Current page display (Page X of Y)
- Next button (→)
- Last page button (⏭)
- Disable buttons when not applicable

5. **Where Used:**
- ✅ TransactionsTable (25 items per page)
- ✅ RecurringTransactionsView (25 items per page)
- ✅ Categories list
- ✅ Rules list
- All future list views

### **Dashboard** (Landing)
- 3 summary cards (total balance, income, expenses)
- **Income/Expenses Period Selector with Comparison Percentages** ⭐ NEW
- **Category Expense Pie Chart with 7-Period Date Range Selector**
- Account management with balance display
- "Create Account" button
- Delete Account with confirmation dialog
- All values support Sensitive Mode (blur)

#### **Income/Expenses Period Selector with Comparison Percentages** (NEW)
The Income and Expenses cards now include a shared period selector that filters their values and calculates comparison percentages against the previous equivalent period.

**Supported Periods:**
1. **Current Month** (default) - 1st of current month to today, compares vs Last Month
2. **Last Month** - Full previous calendar month, compares vs Two Months Ago
3. **Current Week** - Monday of current week to today, compares vs Last Week
4. **Last Week** - Monday to Sunday of previous week, compares vs Two Weeks Ago
5. **Current Year** - Jan 1 of current year to today, compares vs Last Year
6. **Last Year** - Full previous calendar year, compares vs Two Years Ago
7. **All Time** - Entire transaction history (no comparison, percentage hidden)

**Comparison Percentage Logic:**
- If previous period value is 0 and current > 0: shows +100%
- If previous period value is 0 and current is 0: shows 0%
- Otherwise: calculates ((current - previous) / previous) * 100
- For "All Time": percentage indicator is hidden entirely

**Color Logic (Inverse for Expenses):**
- **Income Card (green background):**
  - Positive change (good): white badge on green
  - Negative change (bad): red badge for contrast
- **Expenses Card (red background):**
  - Decreased spending (good, negative %): green badge for contrast
  - Increased spending (bad, positive %): white badge on red

**User Experience:**
- Shared dropdown displayed below the 3 summary cards
- Defaults to "Current Month" on page load
- Selecting a period updates Income/Expenses cards with loading spinner
- Total Balance card is NOT affected (always shows all-time balance)
- Percentages update dynamically based on API response

**Backend Implementation:**
- **Updated File:** `backend/finance_project/apps/analytics/services/date_utils.py`
  - New `get_previous_period(period: str) -> Optional[str]` function
  - Maps each period to its comparison period (returns None for all_time)
  - Added support for `two_months_ago`, `two_weeks_ago`, `two_years_ago` periods

- **Updated View:** `OverviewStatsView`
  - Accepts `?period={period}` query parameter
  - Passes period to StatsService.overview()

- **Updated Service:** `StatsService.overview(user_id, period='current_month')`
  - New `period` parameter filters Income/Expense calculations
  - Calculates `income_change_percent` and `expense_change_percent`
  - Returns null for percentages when period is "all_time"
  - New helper `_calculate_income_expense()` for reuse

- **Updated Serializer:** `OverviewResponseSerializer`
  - Added `income_change_percent` (nullable float)
  - Added `expense_change_percent` (nullable float)

**Frontend Implementation:**
- **New State:** `incomeExpensePeriod` (default: 'current_month')
- **New State:** `incomeExpenseLoading` for loading indicator
- **New Handler:** `handleIncomeExpensePeriodChange(newPeriod)`
- **Updated Cards:** Display dynamic percentages with color logic
- **Removed:** Hardcoded "+" prefix from Income card value

#### **Category Expense Pie Chart - Date Range Selector**
The pie chart showing expenses by category now includes a dropdown selector for different time periods:

**Supported Periods:**
1. **Current Month** (default) - 1st of current month to today
2. **Last Month** - Full previous calendar month
3. **Current Week** - Monday of current week to today
4. **Last Week** - Monday to Sunday of previous week
5. **Current Year** - Jan 1 of current year to today
6. **Last Year** - Full previous calendar year
7. **All Time** - Entire transaction history (from 1900)

**User Experience:**
- Select dropdown displayed next to "Expenses by Category" title
- Defaults to "Current Month" on page load
- Clicking dropdown opens 7 options (localized in EN/DE)
- Selecting a period triggers chart update
- Loading spinner appears while fetching new data
- Chart smoothly transitions with new filtered data

**Backend Implementation:**
- **New File:** `backend/finance_project/apps/analytics/services/date_utils.py`
  - `get_date_range(period: str) -> Tuple[date, date]` function
  - Handles all date range calculations
  - Accounts for week boundaries, month lengths, etc.
  
- **Updated View:** `CategoryExpenseBreakdownView`
  - Accepts `?period={period}` query parameter
  - Validates period is one of allowed values
  - Defaults to 'current_month' if invalid
  
- **Updated Service:** `StatsService.category_expense_breakdown(user_id, period='current_month')`
  - New optional `period` parameter
  - Filters transactions by start_date and end_date
  - Returns same structure (labels, values, colors, items)

**Frontend Implementation:**
- **New State:** `selectedPeriod` (default: 'current_month')
- **New Handler:** `handlePeriodChange(newPeriod)`
  - Updates state
  - Fetches category data with new period
  - Sets `categoryLoading` to true while fetching
  - Updates chart when data arrives
  
- **Updated Render:**
  - Select dropdown with 7 options above pie chart
  - Loading spinner shows during fetch
  - Chart displays filtered data
  
- **Translations Added:** `en.json` and `de.json`
  - `dashboard.periodSelector` (label)
  - `dashboard.periodCurrentMonth`, `periodLastMonth`, etc. (options)

### **Transactions Table**
- Sortable columns (date, amount, description, category)
- Filters: date range, amount range, category, type, search
- Full-text search across all fields
- Edit inline: change category with dropdown
- **Backend pagination: 25 items per page** (with controls)
- Sensitive Mode: blur amounts
- Type badges: income (green), expense (red), transfer (gray)
- Page navigation with first/previous/next/last buttons

### **Recurring Transactions View**
- Account selector
- Summary cards (total subscriptions, active, monthly/yearly costs, overdue count)
- Frequency breakdown (visual cards for each frequency)
- Overdue alerts (yellow warning box)
- Searchable, filterable list with:
  - Merchant name, frequency, amount, next payment, confidence score
  - Ignore/unignore buttons per transaction
  - Add notes functionality
- **Backend pagination: 25 items per page** (with page navigation)
- Filters reset pagination to page 1
- Detect modal for triggering 5-year history analysis
- Admin dashboard for viewing/managing patterns

### **Account Details Modal**
- Wide balance-over-time line chart
- Transaction list for that account
- Filters affecting both chart and list
- Date range selection
- Search bar
- Real-time chart updates on filter change

### **Import Modal**
- Drag-drop file upload
- Auto-detects CSV or JSON by extension
- Field mapping for CSV headers
- Preview before import
- Shows number of rows to import
- Success message with count
- Error handling with details

### **Create Account Modal**
- Account name
- Institution name
- IBAN field
- Currency selector (auto-populated from Currencies API)
- Opening balance
- Opening balance date (optional)
- Form validation (required fields, IBAN format)
- Success toast notification

---

## 🔐 Sensitive Mode

### **What It Does**
- Blurs all financial values (amounts, balances)
- Still shows structure/layout
- Can be toggled on/off instantly
- Keyboard shortcut: `Ctrl+Alt+S` (or `Cmd+Alt+S` on Mac)
- Persists in localStorage

### **Implementation**
```javascript
// In utils/sensitive.js
export function SensitiveValue({ value, sensitiveMode }) {
  if (!sensitiveMode) return value
  return <span style={{filter: 'blur(5px)', userSelect: 'none'}}>
    {String(value).replace(/[0-9]/g, '*')}
  </span>
}

// In components, everywhere money is shown:
<SensitiveValue value={amount} sensitiveMode={sensitiveMode} />
```

### **Used In**
- Dashboard summary cards
- Transaction table amounts
- Account details balances
- Recurring transaction costs
- All monetary displays

---

## 🌙 Dark Mode

### **What It Does**
- Toggles between light and dark UI themes
- Applies dark colors to sidebar, header, modals, and all content areas
- Works with all other settings (sensitive mode, format preferences, etc.)
- Can be toggled on/off instantly
- Keyboard shortcut: `Alt+Shift+D`
- Persists in both localStorage (client) and UserProfile.preferences (server)

### **Implementation**

**Backend (UserProfile Model):**
```python
# Stored in UserProfile.preferences JSONField
profile.set_preference('darkMode', True)
profile.get_preference('darkMode', False)
```

**Frontend (React):**
```javascript
// State management
const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true')

// Sync to server whenever dark mode changes
useEffect(() => {
  axios.post('/api/accounts/auth/preferences/', { darkMode: darkMode })
}, [darkMode])

// Load from server on app start
axios.get('/api/accounts/auth/preferences/')
  .then(res => {
    const serverPrefs = res.data.preferences || {}
    if (serverPrefs.darkMode !== undefined) {
      setDarkMode(serverPrefs.darkMode)
    }
  })

// Dispatch custom event for real-time updates
window.dispatchEvent(new CustomEvent('darkModeChanged', { detail: { darkMode: newValue } }))

// Use hook to listen for changes
export function useDarkModeListener() {
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true')
  useEffect(() => {
    window.addEventListener('darkModeChanged', (e) => setDarkMode(e.detail.darkMode))
    return () => window.removeEventListener('darkModeChanged', handler)
  }, [])
  return darkMode
}
```

**Styling Convention:**
```jsx
// Apply dark mode classes based on state
<div className={darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}>
  {/* Content */}
</div>

// Color mapping:
// Light Mode → Dark Mode
// bg-gray-50 → bg-gray-900
// bg-white → bg-gray-800
// border-gray-200 → border-gray-700
// text-gray-900 → text-white
// text-gray-500 → text-gray-400
// bg-gray-100 → bg-gray-700
// hover:bg-gray-100 → hover:bg-gray-700
```

### **Settings Menu**
- Located in top-right settings button
- Toggle switch to turn dark mode on/off
- Instantly updates UI across entire application
- Changes are auto-saved to UserProfile.preferences on server

### **Keyboard Shortcut**
- `Alt+Shift+D` - Toggle dark mode on/off
- Works from any page when user is authenticated
- Updates both client and server preferences

---

## 💱 Format Preferences

### **Available Preferences**

**Date Formats:**
- MM/DD/YYYY (US)
- DD/MM/YYYY (EU)
- YYYY-MM-DD (ISO)
- DD.MM.YYYY (DE)
- Long (January 14, 2026)

**Time Formats:**
- 12-hour (e.g., 2:30 PM)
- 24-hour (e.g., 14:30)

**Currencies:**
- USD ($), EUR (€), GBP (£), CHF, CAD, AUD, JPY

**Number Formats:**
- 1,000.00 (US)
- 1.000,00 (DE)
- 1 000,00 (FR)
- 1 000.00 (SE)

### **Date Display & Input Format**

#### **Backend (ISO Format - Standard)**
All dates are stored and returned by the backend in ISO format:
- **DateField**: `YYYY-MM-DD` (e.g., "2026-01-14")
- **DateTimeField**: ISO 8601 (e.g., "2026-01-14T14:30:00Z")
- **Timezone**: Always UTC, converted to user's browser timezone on display

#### **Frontend Display (User Preferences)**
All dates displayed to users respect their format and timezone preferences:
```javascript
// Using formatDate for DateFields
formatDate("2026-01-14")
// Output with DD/MM/YYYY preference: "14/01/2026"

// Using formatDateTime for DateTimeFields
formatDateTime("2026-01-14T14:30:00Z")
// Output with DD/MM/YYYY + 12-hour: "14/01/2026 2:30 PM"
```

#### **Frontend Input (User Preferences)**
Date input fields accept dates in the user's preferred format and automatically convert to ISO format for submission:
```javascript
// User enters: "14/01/2026" (with DD/MM/YYYY preference)
inputDateToISO("14/01/2026")
// Returns: "2026-01-14" (sent to backend)

// Display existing date in user's format
dateToInputFormat("2026-01-14")
// Returns: "14/01/2026" (if DD/MM/YYYY preference)
```

### **Implementation**

#### **Preference Storage**
```javascript
// Format preferences stored in localStorage
{
  "dateFormat": "DD.MM.YYYY",        // How to display dates
  "timeFormat": "12-hour",           // How to display times
  "currencyCode": "EUR",             // Currency symbol
  "numberFormat": "1.000,00",        // Number separator style
  "language": "de"                   // UI language
}
```

#### **Utility Functions in utils/format.js**
```javascript
// Get user's format preferences
getFormatPreferences()
// Returns all preferences including dateFormat and timeFormat

// Format dates for display
formatDate(isoDateString)             // DateFields only (no time)
// Uses dateFormat preference

// Format datetimes for display
formatDateTime(isoDateTimeString)     // DateTimeFields (date + time)
// Uses dateFormat + timeFormat + browser timezone

// Convert user input to ISO format
inputDateToISO(userInputDate)         // Convert form input → backend
// Parses based on dateFormat preference, returns YYYY-MM-DD

// Convert ISO to user's display format
dateToInputFormat(isoDateString)      // Convert backend → form display
// Returns formatted date ready for form input field
```

#### **Component Usage**
```javascript
// Display a date
<div>{formatDate(transaction.date)}</div>

// Display a timestamp
<div>{formatDateTime(account.created_at)}</div>

// In a form input field (shows user's format, accepts user's format)
<input
  type="text"
  value={dateToInputFormat(form.opening_balance_date)}
  onChange={(e) => setForm({...form, opening_balance_date: inputDateToISO(e.target.value)})}
  placeholder="DD/MM/YYYY"
/>
```

#### **Components Using Date Formatting**
| Component | Date Fields | Format Function |
|-----------|------------|-----------------|
| TransactionsTable | transaction.date | formatDate() |
| RecurringTransactionsView | next_expected_date, last_occurrence_date | formatDate() |
| AccountDetailsView | transaction dates, chart labels | formatDate() |
| Dashboard | account.created_at | formatDateTime() |
| CreateAccountModal | opening_balance_date (input) | dateToInputFormat() / inputDateToISO() |
| RulesManager | date_from, date_to (inputs) | dateToInputFormat() / inputDateToISO() |
| AccountDetailsView | dateFrom, dateTo (filter inputs) | dateToInputFormat() / inputDateToISO() |

### **Where Stored**
- Backend: `UserProfile.preferences` JSON field
- Frontend: localStorage (synced on login)
- Persists across sessions
- Auto-converted on every display/input

### **Timezone Handling**
- Backend stores all timestamps in UTC (ISO 8601)
- Frontend automatically converts UTC → user's browser timezone
- Timezone detected from OS settings (no explicit picker)
- Changes immediately if user changes OS timezone

---

## 🌍 Internationalization (i18n)

### **Supported Languages**
- **English** (1000+ keys)
- **German** (1000+ keys)

### **Translation Keys Cover**
- All UI labels, buttons, messages
- Error messages
- Form labels and placeholders
- Table headers and filters
- Modal titles and content
- Help text and tooltips
- Success/error notifications
- Format preference labels (e.g., "Time Format")

### **Architecture**
```
frontend/src/
├─ locales/
│  ├─ en.json        # English (English)
│  └─ de.json        # German (Deutsch)
└─ utils/
   └─ i18n.js        # Translation lookup
└─ hooks/
   └─ useLanguage.jsx # React translation hook
```

### **Usage in Components**
```javascript
const t = useTranslate()  // Hook that triggers re-render on language change
return <h1>{t('dashboard.title')}</h1>
```

### **How It Works**
1. User selects language in Settings
2. Preference saved to localStorage
3. Language change event dispatched
4. All `useTranslate()` hooks re-render
5. Components display new language

### **Adding More Languages**
1. Copy `en.json` to `{lang}.json`
2. Translate all values including `settings.timeFormat`
3. Language automatically appears in selector

---

## 🐳 Docker Compose Setup

### **Services**

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| web | Custom (Django) | 8000 | Django + Gunicorn |
| db | postgres:16 | 5432 | PostgreSQL database |
| redis | redis:7 | 6379 | Cache & message broker |
| celery-worker | Custom | - | Async tasks |
| celery-beat | Custom | - | Scheduled tasks |
| ollama | ollama/ollama:latest | 11434 | LLM service |

### **Docker Compose File** (`deploy/docker-compose.yml`)
```yaml
services:
  db:
    image: postgres:16-alpine
    env_file: ./.env.local
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck: pg_isready check
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    healthcheck: redis-cli ping
    
  web:
    build:
      context: ..
      dockerfile: backend/docker/Dockerfile
    env_file: ./.env.local
    depends_on:
      db: service_healthy
      redis: service_healthy
    ports:
      - "8000:8000"
    command: gunicorn + collectstatic + migrate
    healthcheck: curl http://localhost:8000/health
    
  celery-worker:
    # Same build as web
    command: celery worker -l info --concurrency=4
    
  celery-beat:
    # Same build as web
    command: celery beat -l info
    
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"

volumes:
  db_data:
  ollama_data:
```

### **Common Commands**

```bash
# Build images
./dc.sh build web celery-worker celery-beat

# Start all services
./dc.sh up -d

# Stop all services
./dc.sh down

# View logs
./dc.sh logs web          # Web logs
./dc.sh logs celery-worker # Worker logs
./dc.sh logs -f web       # Follow logs

# Execute command in container
./dc.sh exec web bash
./dc.sh exec db psql -U postgres

# Rebuild after code changes
./dc.sh build web
./dc.sh up -d web
```

---

## 🔧 Environment Configuration

### **Required Environment Variables** (`.env.local`)

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=finance
DATABASE_URL=postgresql://postgres:password@db:5432/finance

# Redis
REDIS_URL=redis://redis:6379/0

# Google OAuth
SOCIALACCOUNT_PROVIDERS__GOOGLE__APP__CLIENT_ID=your-client-id.apps.googleusercontent.com
SOCIALACCOUNT_PROVIDERS__GOOGLE__APP__SECRET=your-secret

# OAuth Allowlist
ALLOWLIST_ENABLED=False
# (If enabled, add emails to AllowedGoogleUser model)

# Ollama/AI
OLLAMA_HOST=http://ollama:11434
ACTIVE_AI_PROVIDER=ollama

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Timezone
TIME_ZONE=UTC

# Logging
DJANGO_LOG_LEVEL=INFO
```

### **Development Setup**

```bash
# Create .env.local from template
cp deploy/.env.example deploy/.env.local

# Edit .env.local with your values
nano deploy/.env.local

# Build and start
./dc.sh build web celery-worker celery-beat
./dc.sh up -d
```

---

## ⚙️ Background Tasks (Celery)

### **Configuration** (`finance_project/celery.py`)
```python
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

app.conf.beat_schedule = {
    'generate_monthly_stats': {
        'task': 'finance_project.apps.analytics.tasks.generate_monthly_stats',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

### **Available Tasks**

**Banking App:**
- `import_transactions_task` - Import CSV/JSON files
- `apply_categorization_rules` - Auto-categorize new transactions
- `detect_recurring_transactions_task` - Find subscription patterns

**AI App:**
- `generate_categories_task` - Auto-create categories from transactions

**Analytics App:**
- `generate_monthly_stats` - Calculate monthly aggregates

### **Running Tasks**

```bash
# In development
celery -A finance_project worker -l info
celery -A finance_project beat -l info

# In Docker (already running)
./dc.sh logs celery-worker
./dc.sh logs celery-beat
```

---

## 🔄 Async Task Polling Pattern

### **Overview**

When implementing long-running background tasks (e.g., AI category generation, file imports), use the task polling pattern to:
- Keep modal/UI in loading state while task completes
- Wait for ACTUAL task completion (not fixed time)
- Handle timeouts gracefully
- Provide real-time user feedback

### **Implementation Pattern**

#### **1. Backend: Expose Task Status Endpoint**

**Location:** `backend/finance_project/apps/{app}/views.py`

```python
from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class TaskStatusView(APIView):
    """
    GET /api/{app}/task-status/<task_id>/
    
    Check the status of a background task.
    
    Returns:
        {
            "task_id": "abc-123-def",
            "status": "PENDING" | "PROGRESS" | "SUCCESS" | "FAILURE",
            "result": {...},  // Only if status is SUCCESS
            "error": "..."    // Only if status is FAILURE
        }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            task_result = AsyncResult(task_id)
            
            response_data = {
                'task_id': task_id,
                'status': task_result.status,
            }
            
            if task_result.status == 'SUCCESS':
                response_data['result'] = task_result.result
            elif task_result.status == 'FAILURE':
                response_data['error'] = str(task_result.info)
            
            return Response(response_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**Register URL:** `backend/finance_project/apps/{app}/urls.py`

```python
from django.urls import path
from .views import TaskStatusView

urlpatterns = [
    path("task-status/<str:task_id>", TaskStatusView.as_view(), name="task-status"),
]
```

#### **2. Backend: Start Task Endpoint**

Return `202 ACCEPTED` with task ID:

```python
class GenerateCategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Trigger async task
        task = generate_categories_task.delay(request.user.id)
        
        return Response({
            'message': 'Task started in background',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)
```

#### **3. Frontend: Poll for Task Completion**

**Location:** React component (e.g., `src/components/ModalWithAsyncTask.jsx`)

```javascript
const handleStartAsyncTask = async () => {
  setLoading(true)
  setError(null)
  setResult(null)
  
  try {
    // 1. Start the async task
    const response = await axios.post('/api/{app}/start-task', {
      /* request data */
    }, {
      headers: { 'X-CSRFToken': getCsrfToken() }
    })
    
    const taskId = response.data.task_id
    
    // 2. Poll for completion
    let completed = false
    let attempts = 0
    const maxAttempts = 300  // 5 minutes with 1-second polling
    
    while (!completed && attempts < maxAttempts) {
      attempts++
      
      try {
        // Check task status
        const statusResponse = await axios.get(
          `/api/{app}/task-status/${taskId}`,
          { headers: { 'X-CSRFToken': getCsrfToken() } }
        )
        
        const taskStatus = statusResponse.data.status
        
        if (taskStatus === 'SUCCESS') {
          // Task completed - reload data
          await loadData()
          completed = true
          
          setResult({
            message: t('task.success'),
            data: statusResponse.data.result
          })
        } else if (taskStatus === 'FAILURE') {
          // Task failed
          setError(statusResponse.data.error || t('task.failed'))
          completed = true
        } else if (taskStatus === 'PENDING' || taskStatus === 'PROGRESS') {
          // Still processing - wait and retry
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      } catch (err) {
        // Network error - retry after delay
        console.warn('Error checking task status:', err)
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    if (!completed && attempts >= maxAttempts) {
      setError(t('task.timeout'))
    }
    
    setLoading(false)
    
    // Auto-close after showing result
    if (completed && !error) {
      setTimeout(() => {
        closeModal()
      }, 3000)
    }
  } catch (err) {
    console.error('Error starting task:', err)
    setError(err.response?.data?.error || t('task.error'))
    setLoading(false)
  }
}
```

#### **4. Frontend: ESC Key to Close Modal**

```javascript
useEffect(() => {
  const handleEscKey = (event) => {
    if (event.key === 'Escape' && showModal) {
      closeModal()
    }
  }

  if (showModal) {
    document.addEventListener('keydown', handleEscKey)
    return () => {
      document.removeEventListener('keydown', handleEscKey)
    }
  }
}, [showModal])
```

### **Key Design Points**

| Point | Reason |
|-------|--------|
| **202 ACCEPTED** | HTTP standard for async operations |
| **1-second polling** | Responsive UX, not too many requests |
| **5-minute timeout** | Prevents infinite waiting |
| **Cleanup on unmount** | Prevents memory leaks |
| **Non-blocking sync** | Task check doesn't block UI |
| **Error states** | Clear user feedback |
| **Auto-close after success** | Smooth UX flow |

### **Real-World Examples in Project**

**AI Category Generation:**
- **Start endpoint:** `POST /api/ai/generate-categories`
- **Status endpoint:** `GET /api/ai/task-status/<task_id>`
- **Modal:** CategoriesManager AI generation modal
- **Files:** 
  - Backend: `apps/ai/views.py` (GenerateCategoriesView, TaskStatusView)
  - Frontend: `components/CategoriesManager.jsx` (startAIGeneration function)

### **Future Implementations**

For new async tasks, follow this pattern:
1. Create async Celery task in `tasks.py`
2. Add start endpoint returning `(task_id, 202 ACCEPTED)`
3. Add task status endpoint checking `AsyncResult(task_id)`
4. In frontend, use polling pattern above
5. Show modal with loading → success/error states
6. Auto-close or wait for user confirmation

---

## 🔄 Database Migrations

### **Creating Migrations**

```bash
# After modifying models.py
./dc.sh exec web python manage.py makemigrations

# Check what changed
./dc.sh exec web python manage.py showmigrations

# Apply migrations
./dc.sh exec web python manage.py migrate
```

### **Migration History**
```
0001_initial                   - Initial schema
0002_alter_transaction_...     - Extended transaction fields
0003_recurringtransaction      - Subscription detection model
0004_add_iban_to_bankaccount   - IBAN field
```

---

## 🎯 Design Decisions

### **Why Decimal for Money**
- Float has precision issues: `0.1 + 0.2 ≠ 0.3`
- Decimal type ensures exact financial calculations
- All amounts: `DecimalField(max_digits=12, decimal_places=2)`
- Conversions: `Decimal('100.50')` not `100.50`

### **Why Celery for Background Tasks**
- Long-running tasks don't block API requests
- Import 1000s of transactions without timeout
- Retry logic built-in
- Scheduled tasks (like monthly stats)

### **Why React over Django Templates**
- Interactive UI (filters, modals, instant updates)
- Component reusability
- Better state management
- Smooth user experience
- Works with JavaScript-disabled fallback

### **Why Fuzzy Matching for Merchants**
- Bank names vary: "NETFLIX", "Netflix.com", "NETFLIX INC"
- Fuzzy matching handles variations automatically
- No user configuration needed
- Better pattern detection

### **Why Opening Balance Date**
- Users may not import full history
- Need reference point for balance calculation
- Scenario: "Account balance is €500 on Jan 1, then import transactions from Jan 1 to now"
- Calculates current balance: opening_balance + sum(transactions since date)

### **Why Format Preferences**
- Users in different countries have different number formats
- EUR: "1.000,00" (comma for decimal)
- USD: "1,000.00" (comma for thousands)
- Provide flexibility without forcing defaults

### **Why Sensitive Mode**
- Financial data is sensitive
- Users may share screen/screenshots
- Blur feature allows showing without revealing numbers
- Keyboard shortcut for quick toggle

### **Why Reference Field (512 chars)**
- Bank transactions have unique reference/transaction IDs from importers
- Different banks use different field names: "reference", "referenceNumber", "transactionID", etc.
- Dedicated reference field (separate from description) provides:
  - **Primary display**: Shows reference as main identifier
  - **Tooltip description**: Shows full description on hover
  - **Search/filter**: Reference values are searchable in admin
  - **Flexibility**: Works with any import format via field mapping
  - **Persistence**: Rates stored in DB so API failures don't break app
  - **Hourly Updates**: Fetched every hour via Celery beat task
  - **Display-Only**: Exchange rates are for display purposes, not for trading
  - **Graceful Degradation**: If API fails, app continues using cached rates (no crashes)
  - **Global Singleton**: One ExchangeRate record (pk=1) serves entire system
  - **USD Base**: All rates relative to USD (API standard), conversion formula: `amount * (rate_target / rate_source)`
  - **Fallback Currency**: If user's currency not in API response, falls back to `SYSTEM_DEFAULT_CURRENCY` env var
  - **Age Display**: Shows rate freshness to users (e.g., "2h 15m ago") so they know conversion accuracy
  - **Backend Conversion**: Happens in serializer layer, never in database (avoids data inconsistency)
  - **API Integration**: Uses `API_OPEN_EXCHANGE_RATES_KEY_URL` env var (full URL with app_id)


```
<userPrompt>
Provide the fully rewritten file, incorporating the suggested code change. You must produce the complete file.
</userPrompt>
