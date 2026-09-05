import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0002_remove_borrowlog_return_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowlog',
            name='borrower_type',
            field=models.CharField(choices=[('Internal', 'ខាងក្នុង (បុគ្គលិក)'), ('External', 'ខាងក្រៅ')], default='Internal', max_length=20, verbose_name='ប្រភេទអ្នកខ្ចី'),
        ),
        migrations.AddField(
            model_name='borrowlog',
            name='requested_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='ពេលវេលាស្នើសុំ'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='borrowlog',
            name='admin_note',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='មតិយោបល់ Admin'),
        ),
        migrations.AlterField(
            model_name='borrowlog',
            name='borrow_status',
            field=models.CharField(
                choices=[
                    ('Pending', 'រង់ចាំការអនុម័ត (Pending)'),
                    ('Borrowed', 'កំពុងខ្ចី (Borrowed)'),
                    ('PendingReturn', 'រង់ចាំការបញ្ជាក់សង (Pending Return)'),
                    ('Returned', 'បានសងរួច (Returned)'),
                    ('Rejected', 'បដិសេធ (Rejected)'),
                ],
                default='Pending',
                max_length=50,
                verbose_name='ស្ថានភាពខ្ចី',
            ),
        ),
        migrations.AlterField(
            model_name='borrowlog',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_logs', to='devices.device', verbose_name='ឧបករណ៍'),
        ),
        migrations.AlterField(
            model_name='device',
            name='status',
            field=models.CharField(
                choices=[
                    ('Available', 'ទំនេរ'),
                    ('Reserved', 'កំពុងរង់ចាំការអនុម័ត'),
                    ('Borrowed', 'កំពុងខ្ចី'),
                    ('Maintenance', 'កំពុងជួសជុល'),
                ],
                default='Available',
                max_length=50,
                verbose_name='ស្ថានភាព',
            ),
        ),
        migrations.AlterModelOptions(
            name='borrowlog',
            options={'ordering': ['-requested_at']},
        ),
        migrations.AlterModelOptions(
            name='device',
            options={'ordering': ['device_name']},
        ),
    ]
