from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_weightlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="must_set_password",
            field=models.BooleanField(default=False),
        ),
    ]
