# API Error Fix - Recurring Transactions Summary Endpoint

## Problem
The `/api/banking/recurring/summary/` endpoint was throwing an `AttributeError: 'dict' object has no attribute 'get_display_name'` error.

## Root Cause
The error occurred in the serialization pipeline:

1. **In the viewset `summary()` method:**
   - We fetched top 5 recurring transactions: `top_recurring_qs`
   - We serialized them: `top_serializer = RecurringTransactionSerializer(top_recurring_qs, many=True)`
   - We got the serialized data: `top_recurring_data = top_serializer.data` (list of dicts)

2. **Then we tried to serialize again:**
   - We passed the dict data to `RecurringTransactionSummarySerializer`
   - The serializer tried to serialize `top_recurring` field again
   - It expected model instances but received dicts
   - When calling `get_display_name()` on a dict, it failed

## Solution
Changed the response to return the serialized data directly without re-serialization:

**Before (WRONG):**
```python
top_serializer = RecurringTransactionSerializer(top_recurring, many=True)

summary_data = {
    'top_recurring': top_serializer.data,  # Already serialized dicts
    # ... other fields
}

serializer = RecurringTransactionSummarySerializer(summary_data)
return Response(serializer.data)  # Tries to serialize dicts again!
```

**After (CORRECT):**
```python
top_recurring_qs = queryset.filter(is_active=True).order_by(
    '-confidence_score', '-occurrence_count'
)[:5]
top_recurring_data = RecurringTransactionSerializer(top_recurring_qs, many=True).data

return Response({
    'total_count': total_count,
    'active_count': active_count,
    'monthly_recurring_cost': str(...),
    'yearly_recurring_cost': str(...),
    'by_frequency': by_frequency,
    'top_recurring': top_recurring_data,  # Already serialized, return directly
    'overdue_count': overdue_count,
})
```

## Changes Made
**File:** `/backend/finance_project/apps/banking/views/recurring.py`

**Method:** `RecurringTransactionViewSet.summary()`

**Changes:**
- Removed `RecurringTransactionSummarySerializer` usage
- Return plain Python dict with `Response()` instead of using serializer
- The dict contains already-serialized data for `top_recurring`
- All other fields (counts, costs, breakdown) are native Python types

## Result
✅ The `/api/banking/recurring/summary/` endpoint now works correctly
✅ Returns properly serialized data without double-serialization
✅ No more `AttributeError` exceptions
✅ API response includes all expected fields:
   - `total_count`
   - `active_count`
   - `monthly_recurring_cost`
   - `yearly_recurring_cost`
   - `by_frequency` (breakdown by frequency type)
   - `top_recurring` (list of top 5 subscriptions)
   - `overdue_count`

## Files Modified
- `/backend/finance_project/apps/banking/views/recurring.py` - Fixed summary endpoint

## Notes
The `RecurringTransactionSummarySerializer` is no longer used since we return a raw dict response. This is fine because:
1. The data structure is simple and well-documented
2. It avoids the serialization issues
3. The frontend expects the exact structure we're now returning
4. No validation is needed on the response

If you want to keep the serializer, you could instead pass model instances to it, but returning a plain dict is simpler and more maintainable in this case.

