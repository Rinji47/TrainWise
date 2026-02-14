from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0004_alter_membersubscription_start_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='membershipplan',
            name='dodo_product_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
