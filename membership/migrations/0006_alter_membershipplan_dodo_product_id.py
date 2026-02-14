from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0005_membershipplan_dodo_product_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membershipplan',
            name='dodo_product_id',
            field=models.CharField(max_length=100),
        ),
    ]
