from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_borrowlog_return_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='device_image',
            field=models.ImageField(blank=True, null=True, upload_to='device_photos/', verbose_name='រូបភាពឧបករណ៍'),
        ),
    ]
