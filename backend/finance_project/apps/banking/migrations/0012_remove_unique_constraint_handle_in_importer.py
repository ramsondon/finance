# Generated migration to remove UniqueConstraint and handle uniqueness in importer
# Date: 2026-01-25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("banking", "0011_anomaly_anomalynotification_useranomalypreferences_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="transaction",
            name="unique_transaction_per_account",
        ),
    ]

