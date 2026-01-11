import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_stats_overview_requires_auth():
    c = APIClient()
    resp = c.get('/api/analytics/overview')
    assert resp.status_code in (401, 403)

@pytest.mark.django_db
def test_create_account_list():
    u = User.objects.create_user(username='u1', password='pw')
    c = APIClient()
    c.login(username='u1', password='pw')
    resp = c.post('/api/banking/accounts/', {"name": "Checking", "institution": "Bank"}, format='json')
    assert resp.status_code == 201
    resp = c.get('/api/banking/accounts/')
    assert resp.status_code == 200
    assert len(resp.json()['results']) == 1 or isinstance(resp.json(), list)

