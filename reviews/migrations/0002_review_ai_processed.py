from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reviews", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="review",
            name="ai_processed",
            field=models.BooleanField(default=False),
        ),
    ]
