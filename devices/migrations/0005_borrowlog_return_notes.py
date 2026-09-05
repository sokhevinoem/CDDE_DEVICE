from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0004_borrowlog_borrower_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowlog',
            name='return_notes',
            field=models.TextField(blank=True, null=True, verbose_name='កំណត់សម្គាល់ (ពេលសង)'),
        ),
        migrations.AlterField(
            model_name='borrowlog',
            name='other_notes',
            field=models.TextField(blank=True, null=True, verbose_name='កំណត់សម្គាល់ (ពេលស្នើសុំ)'),
        ),
    ]
