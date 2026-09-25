from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reviews", "0002_review_ai_processed")]

    operations = [
        migrations.RemoveConstraint(model_name="trackedapp", name="unique_owner_package"),
        migrations.RenameField(model_name="trackedapp", old_name="owner", new_name="user"),
        migrations.RenameField(model_name="trackedapp", old_name="package_id", new_name="app_id"),
        migrations.RenameField(model_name="review", old_name="score", new_name="rating"),
        migrations.RenameField(model_name="review", old_name="thumbs_up_count", new_name="thumbs_up"),
        migrations.AddConstraint(
            model_name="trackedapp",
            constraint=models.UniqueConstraint(fields=("user", "app_id"), name="unique_user_app"),
        ),
    ]