# Recurring Transaction Detection Feature

## 🎯 Overview

The Recurring Transaction Detection system automatically identifies recurring payments and subscriptions in your bank account. It provides real value to users by helping them understand their recurring costs and identify opportunities for savings.

## 🔍 Detection Algorithm

### Supported Frequencies
- **Weekly**: Every 7 days
- **Bi-weekly**: Every 14 days
- **Monthly**: Same day each month (approximately 30 days)
- **Quarterly**: Every 3 months (approximately 90 days)
- **Yearly**: Same date each year (approximately 365 days)

### How It Works

1. **Description Grouping**: Transactions are grouped by similar merchant names/descriptions using fuzzy matching
   - Normalizes descriptions (removes domain suffixes, special characters)
   - Groups similar names (e.g., "NETFLIX", "NETFLIX.COM", "Netflix" are grouped)

2. **Pattern Detection**: For each group, the algorithm:
   - Calculates intervals between transactions
   - Checks if intervals match expected frequency (with 30% tolerance)
   - Verifies amount consistency (within 5% tolerance by default)
   - Requires minimum occurrences to confirm pattern:
     - Weekly: 3 occurrences (3 weeks)
     - Bi-weekly: 3 occurrences (6 weeks)
     - Monthly: 2 occurrences (2 months)
     - Quarterly: 2 occurrences (6 months)
     - Yearly: 1 occurrence (1 year)

3. **Confidence Scoring**: Each pattern gets a confidence score (0-1) based on:
   - Interval consistency (50% weight): How regularly spaced are the transactions
   - Amount consistency (30% weight): How consistent are the amounts
   - Occurrence ratio (20% weight): How many times has this pattern repeated

   Minimum confidence threshold: 0.6 (60%)

## 💾 Data Model

### RecurringTransaction Model

```python
class RecurringTransaction(models.Model):
    # Links
    account: ForeignKey(BankAccount)
    user: ForeignKey(User)
    
    # Pattern Details
    description: str (255 chars)
    merchant_name: str (255 chars, optional)
    amount: Decimal
    frequency: str ['weekly', 'bi-weekly', 'monthly', 'quarterly', 'yearly']
    
    # Timing
    next_expected_date: Date
    last_occurrence_date: Date
    
    # Statistics
    occurrence_count: int
    confidence_score: float (0-1)
    
    # User Control
    is_active: bool (default: True)
    is_ignored: bool (default: False)
    user_notes: str (optional)
    
    # Meta
    similar_descriptions: JSON list
    transaction_ids: JSON list
    detected_at: DateTime
    updated_at: DateTime
```

## 🚀 API Endpoints

### List All Recurring Transactions
```
GET /api/banking/recurring/
```

Query Parameters:
- `account_id`: Filter by account
- `frequency`: Filter by frequency (weekly, monthly, etc.)
- `is_active`: Filter by active status (true/false)
- `is_ignored`: Filter by ignored status (true/false)
- `ordering`: Sort by field (confidence_score, amount, next_expected_date, occurrence_count)

Response:
```json
[
  {
    "id": 1,
    "description": "netflix subscription",
    "merchant_name": "NETFLIX",
    "display_name": "NETFLIX",
    "amount": "12.99",
    "frequency": "monthly",
    "next_expected_date": "2026-02-14",
    "last_occurrence_date": "2026-01-14",
    "occurrence_count": 8,
    "confidence_score": 0.95,
    "is_active": true,
    "is_ignored": false,
    "user_notes": "Family subscription",
    "similar_descriptions": ["NETFLIX", "Netflix.com", "Netflix"],
    "transaction_ids": [123, 456, 789...],
    "is_overdue": false,
    "days_until_next": 31,
    "monthly_cost": 12.99,
    "yearly_cost": 155.88,
    "detected_at": "2026-01-14T10:30:00Z"
  }
]
```

### Get Summary Statistics
```
GET /api/banking/recurring/summary/
```

Query Parameters:
- `account_id` (optional): Filter by account

Response:
```json
{
  "total_count": 15,
  "active_count": 14,
  "monthly_recurring_cost": "385.47",
  "yearly_recurring_cost": "4625.64",
  "by_frequency": {
    "weekly": {
      "count": 2,
      "total_amount": "50.00"
    },
    "monthly": {
      "count": 10,
      "total_amount": "250.00"
    },
    "yearly": {
      "count": 2,
      "total_amount": "200.00"
    }
  },
  "top_recurring": [...],
  "overdue_count": 2
}
```

### Manually Trigger Detection
```
POST /api/banking/recurring/detect/?account_id=1&days_back=365
```

Response:
```json
{
  "message": "Recurring transaction detection started",
  "account_id": 1,
  "days_back": 365,
  "status": "processing"
}
```

### Get Overdue Recurring Transactions
```
GET /api/banking/recurring/overdue/
```

### Get Upcoming Recurring Transactions
```
GET /api/banking/recurring/upcoming/?days=30
```

### Update Recurring Transaction
```
PATCH /api/banking/recurring/{id}/
```

Updatable fields:
- `merchant_name`: str
- `is_active`: bool
- `is_ignored`: bool
- `user_notes`: str

### Mark as Ignored
```
POST /api/banking/recurring/{id}/ignore/
```

### Unignore
```
POST /api/banking/recurring/{id}/unignore/
```

### Add Note
```
PATCH /api/banking/recurring/{id}/add_note/
Body: {"note": "My custom note"}
```

## 💡 User Value & Display

### 1. **Subscription Tracker Dashboard**
Display:
- All active recurring transactions
- Grouped by frequency (weekly, monthly, quarterly, yearly)
- Show next expected date for each
- Highlight overdue items (missed payments/cancelled subscriptions)

Value:
- Users see all their recurring costs at a glance
- Identifies subscriptions they might have forgotten about

### 2. **Monthly/Yearly Cost Summary**
Display:
- Total monthly recurring cost
- Total yearly recurring cost
- Breakdown by frequency
- Top recurring transactions by amount

Value:
- Users understand total committed spending
- Can make informed budget decisions
- Can identify areas to cut costs

### 3. **Smart Alerts**
Display:
- Overdue recurring transactions (payment hasn't appeared)
- Upcoming recurring transactions (next 30 days)
- Unusual amount variations (charged more/less than usual)

Value:
- Users catch cancelled subscriptions quickly
- Can prepare for upcoming expenses
- Spot fraud or pricing changes

### 4. **Savings Opportunities**
Display:
- "You're paying 3 different streaming services - total $47.97/month"
- "You renewed a magazine subscription but haven't read it in 6 months"
- "Cancel these subscriptions to save $X/month"

Value:
- Actionable insights to reduce spending
- Shows exact savings potential
- Motivates users to take action

### 5. **Customization & Control**
Features:
- Mark subscriptions as ignored (false positives)
- Add custom notes ("Family account", "Can cancel anytime", etc.)
- Toggle active/inactive status
- Edit merchant names for better organization

Value:
- Users feel in control
- System learns from feedback
- Builds trust in the feature

## 🔄 Background Tasks

### detect_recurring_transactions_task
Runs periodically or manually to detect patterns.

```python
from finance_project.apps.banking.tasks import detect_recurring_transactions_task

# Manually trigger
detect_recurring_transactions_task.delay(
    account_id=1,
    days_back=365  # Look back 1 year
)
```

### check_recurring_transaction_overdue_task
Runs daily to check for missed recurring transactions.

```python
# Add to celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'check-recurring-overdue': {
        'task': 'finance_project.apps.banking.tasks.check_recurring_transaction_overdue_task',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
```

## 📊 Frontend Display Ideas

### 1. Subscription Tracker Card
```
┌─ Subscriptions ─────────────────────┐
│ 💳 Netflix              $12.99/mo   │
│ ☁️  iCloud              $2.99/mo    │
│ 🎵 Spotify              $9.99/mo    │
│ 📰 Medium               $5.00/mo    │
│                                     │
│ Total: $385.47/mo                   │
│        $4,625.64/year               │
│                                     │
│ ⚠️ 2 items overdue                  │
│ 🔔 5 items next 30 days             │
└─────────────────────────────────────┘
```

### 2. Savings Opportunity Card
```
┌─ Save Money ─────────────────────────┐
│ 💡 You have 3 streaming services     │
│    Total: $47.97/month               │
│                                      │
│    Consider consolidating to save:   │
│    💰 Up to $24.99/month            │
│                                      │
│    [Learn More] [Dismiss]            │
└──────────────────────────────────────┘
```

### 3. Timeline View
```
Jan    Feb    Mar    Apr    May    Jun
 │      │      │      │      │      │
 ├──────┤
 Netflix
        ├──────┤
        Spotify
 ├──────────────────────┤
 Magazine (Quarterly)
```

### 4. Overdue Alert
```
⚠️ Missing Subscription
   Your Netflix payment is 3 days overdue
   Last occurred: Jan 11 (expected: Jan 14)
   
   [Check Account] [Mark as Ignored]
```

## 🎯 Implementation Roadmap

### Phase 1: Core Detection (Current)
- ✅ Detection algorithm
- ✅ Data model
- ✅ API endpoints
- ✅ Background tasks

### Phase 2: Frontend (Next)
- [ ] Subscription tracker dashboard
- [ ] Summary statistics card
- [ ] Overdue alerts
- [ ] Upcoming transactions timeline
- [ ] Custom notes & organization

### Phase 3: Intelligence
- [ ] Auto-generate savings suggestions
- [ ] Compare with similar users' spending
- [ ] Smart notifications (price changes, cancellations)
- [ ] Integration with budget planning

### Phase 4: Actions
- [ ] One-click subscription cancellation (if provider API available)
- [ ] Consolidation recommendations
- [ ] Spending analytics by subscription type

## 🔧 Configuration

### Sensitivity Settings (in settings.py)
```python
RECURRING_DETECTION = {
    'AMOUNT_TOLERANCE': 0.05,  # 5% variance allowed
    'INTERVAL_TOLERANCE': 0.3,  # 30% variance on interval
    'MIN_CONFIDENCE': 0.6,  # Minimum confidence score
    'MIN_OCCURRENCES': {
        'weekly': 3,
        'bi-weekly': 3,
        'monthly': 2,
        'quarterly': 2,
        'yearly': 1,
    }
}
```

### Celery Beat Schedule
```python
CELERY_BEAT_SCHEDULE = {
    # Run detection nightly
    'detect-recurring-daily': {
        'task': 'finance_project.apps.banking.tasks.detect_recurring_transactions_task',
        'schedule': crontab(hour=3, minute=0),  # 3 AM UTC
    },
    # Check for overdue daily at 6 AM
    'check-overdue-daily': {
        'task': 'finance_project.apps.banking.tasks.check_recurring_transaction_overdue_task',
        'schedule': crontab(hour=6, minute=0),  # 6 AM UTC
    },
}
```

## 📈 Performance Considerations

- **Indexing**: Queries on `user_id`, `account_id`, `is_active`, and `next_expected_date` are optimized
- **Caching**: Consider caching summary statistics (5-minute TTL)
- **Batch Processing**: Celery task processes accounts asynchronously
- **Query Optimization**: Uses `select_related` and `prefetch_related` where needed

## 🐛 Testing

```python
# test_recurring_detector.py
from finance_project.apps.banking.services.recurring_detector import RecurringTransactionDetector

def test_monthly_detection():
    detector = RecurringTransactionDetector(account_id=1)
    patterns = detector.detect(days_back=365)
    
    # Find Netflix subscription
    netflix = [p for p in patterns if 'netflix' in p.description.lower()]
    assert len(netflix) == 1
    assert netflix[0].frequency == 'monthly'
    assert netflix[0].confidence_score > 0.8
```

## 📝 Next Steps

1. Create frontend components for subscription tracker
2. Add translations for recurring transaction labels
3. Implement overdue notifications
4. Add CSV export for recurring transactions
5. Create savings opportunity cards

