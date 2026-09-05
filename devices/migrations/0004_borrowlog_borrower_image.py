from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0003_borrow_approval_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowlog',
            name='borrower_image',
            field=models.ImageField(blank=True, null=True, upload_to='borrower_photos/', verbose_name='រូបភាពអ្នកខ្ចី'),
        ),
    ]
