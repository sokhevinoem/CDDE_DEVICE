from django.db import models


class Device(models.Model):
name = models.CharField(max_length=100)
    # Correct: Uses default storage (Cloudinary) automatically
    image = models.ImageField(upload_to='devices/', blank=True, null=True)

    STATUS_CHOICES = [
        ('Available', 'ទំនេរ'),
        ('Reserved', 'កំពុងរង់ចាំការអនុម័ត'),
        ('Borrowed', 'កំពុងខ្ចី'),
        ('Maintenance', 'កំពុងជួសជុល'),
    ]

    HAS_DATA_CHOICES = [
        ('Yes', 'មានទិន្នន័យ'),
        ('No', 'មិនមានទិន្នន័យ'),
    ]

    device_name = models.CharField(max_length=255, verbose_name="ឈ្មោះឧបករណ៍")
    device_image = models.ImageField(upload_to='device_photos/', null=True, blank=True, verbose_name="រូបភាពឧបករណ៍")
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="លេខស៊េរី (Serial Number)")
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name="ម៉ូឌែល")
    capacity = models.CharField(max_length=50, blank=True, null=True, verbose_name="ទំហំផ្ទុក")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Available', verbose_name="ស្ថានភាព")
    has_data = models.CharField(max_length=10, choices=HAS_DATA_CHOICES, default='No', verbose_name="ស្ថានភាពទិន្នន័យ")

    class Meta:
        ordering = ['device_name']

    def __str__(self):
        return f"{self.device_name} ({self.capacity if self.capacity else ''})"


class BorrowLog(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'រង់ចាំការអនុម័ត (Pending)'),
        ('Borrowed', 'កំពុងខ្ចី (Borrowed)'),
        ('PendingReturn', 'រង់ចាំការបញ្ជាក់សង (Pending Return)'),
        ('Returned', 'បានសងរួច (Returned)'),
        ('Rejected', 'បដិសេធ (Rejected)'),
    ]

    CONDITION_CHOICES = [
        ('Good', 'ល្អ/ធម្មតា'),
        ('Damaged', 'ខូចខាត/មានបញ្ហា'),
    ]

    TYPE_CHOICES = [
        ('Internal', 'ខាងក្នុង (បុគ្គលិក)'),
        ('External', 'ខាងក្រៅ'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="ឧបករណ៍", related_name='borrow_logs')
    borrowed_by = models.CharField(max_length=255, verbose_name="ឈ្មោះបុគ្គលិកខ្ចី")
    borrower_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Internal', verbose_name="ប្រភេទអ្នកខ្ចី")
    borrower_image = models.ImageField(upload_to='borrower_photos/', null=True, blank=True, verbose_name="រូបភាពអ្នកខ្ចី")
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="ពេលវេលាស្នើសុំ")
    borrow_date = models.DateField(verbose_name="ថ្ងៃខ្ចី")

    # ថ្ងៃត្រូវសងដែលកំណត់ពេលខ្ចី (អាច Null បាន បើមិនទាន់ប្រាកដ)
    expected_return_date = models.DateField(null=True, blank=True, verbose_name="ថ្ងៃរំពឹងថានឹងសង")

    # ថ្ងៃសងជាក់ស្តែង និងព័ត៌មានពេលយកមកសង
    actual_return_date = models.DateField(null=True, blank=True, verbose_name="ថ្ងៃសងជាក់ស្តែង")
    return_condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='Good', null=True, blank=True, verbose_name="ស្ថានភាពឧបករណ៍ពេលសង")
    return_image = models.ImageField(upload_to='return_proofs/', null=True, blank=True, verbose_name="រូបភាពឧបករណ៍ពេលសង")

    reason = models.TextField(verbose_name="មូលហេតុខ្ចី")
    borrow_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending', verbose_name="ស្ថានភាពខ្ចី")
    other_notes = models.TextField(blank=True, null=True, verbose_name="កំណត់សម្គាល់ (ពេលស្នើសុំ)")
    return_notes = models.TextField(blank=True, null=True, verbose_name="កំណត់សម្គាល់ (ពេលសង)")

    admin_note = models.CharField(max_length=255, blank=True, null=True, verbose_name="មតិយោបល់ Admin")

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.borrowed_by} - {self.device.device_name}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return bool(
            self.borrow_status == 'Borrowed'
            and self.expected_return_date
            and self.expected_return_date < timezone.localdate()
        )