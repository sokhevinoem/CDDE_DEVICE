from django import forms
from .models import BorrowLog, Device


class BorrowForm(forms.ModelForm):
    not_sure_return_date = forms.BooleanField(
        required=False,
        label="មិនទាន់ប្រាកដថ្ងៃសង",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'notSureCheckbox'})
    )

    class Meta:
        model = BorrowLog
        fields = ['device', 'borrowed_by', 'borrower_type', 'borrower_image', 'borrow_date', 'expected_return_date', 'reason', 'other_notes']
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select'}),
            'borrowed_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'បញ្ចូលឈ្មោះរបស់អ្នក'}),
            'borrower_type': forms.Select(attrs={'class': 'form-select'}),
            'borrower_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'borrow_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'returnDateField'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'បញ្ចូលមូលហេតុនៃការខ្ចី'}),
            'other_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'កំណត់សម្គាល់ផ្សេងៗ'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # មានតែឧបករណ៍ដែល "ទំនេរ" ប៉ុណ្ណោះទើបអាចជ្រើសរើសបាន (មិនរាប់បញ្ចូលកំពុងខ្ចី/កំពុងរង់ចាំការអនុម័ត/ជួសជុល)
        self.fields['device'].queryset = Device.objects.filter(status='Available').order_by('device_name')
        self.fields['device'].label = "ជ្រើសរើសឧបករណ៍"
        self.fields['device'].empty_label = "-- សូមជ្រើសរើសឧបករណ៍ --"
        self.fields['borrowed_by'].label = "ខ្ចីដោយ (ឈ្មោះបុគ្គលិក / ភ្ញៀវ)"
        self.fields['borrower_type'].label = "ប្រភេទអ្នកខ្ចី"
        self.fields['borrower_image'].label = "រូបភាពអ្នកខ្ចី (ស្រេចចិត្ត)"
        self.fields['borrower_image'].required = False
        self.fields['borrow_date'].label = "ថ្ងៃ ខែ ឆ្នាំ ខ្ចី"
        self.fields['expected_return_date'].label = "ថ្ងៃ ខែ ឆ្នាំ រំពឹងថានឹងសង"
        self.fields['reason'].label = "មូលហេតុ"
        self.fields['other_notes'].label = "ផ្សេងៗ"

    def clean(self):
        cleaned_data = super().clean()
        borrow_date = cleaned_data.get('borrow_date')
        expected_return_date = cleaned_data.get('expected_return_date')
        not_sure = cleaned_data.get('not_sure_return_date')

        if borrow_date and expected_return_date and not not_sure:
            if expected_return_date < borrow_date:
                self.add_error(
                    'expected_return_date',
                    "ថ្ងៃរំពឹងថានឹងសង មិនអាចមុនថ្ងៃខ្ចីបានទេ។"
                )
        return cleaned_data


class ReturnForm(forms.ModelForm):
    class Meta:
        model = BorrowLog
        fields = ['actual_return_date', 'return_condition', 'return_image', 'return_notes']
        widgets = {
            'actual_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'return_condition': forms.Select(attrs={'class': 'form-select'}),
            'return_image': forms.FileInput(attrs={'class': 'form-control'}),
            'return_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ចំណាំបន្ថែមពេលសង (បើមាន)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['actual_return_date'].label = "ថ្ងៃ ខែ ឆ្នាំ សងជាក់ស្តែង"
        self.fields['actual_return_date'].required = True
        self.fields['return_condition'].label = "ស្ថានភាពឧបករណ៍ពេលសង"
        self.fields['return_image'].label = "រូបភាពឧបករណ៍ពេលសង"
        self.fields['return_notes'].label = "កំណត់សម្គាល់បន្ថែម"

    def clean_actual_return_date(self):
        actual_return_date = self.cleaned_data.get('actual_return_date')
        borrow_date = getattr(self.instance, 'borrow_date', None)
        if actual_return_date and borrow_date and actual_return_date < borrow_date:
            raise forms.ValidationError("ថ្ងៃសងជាក់ស្តែង មិនអាចមុនថ្ងៃខ្ចីបានទេ។")
        return actual_return_date


class DeviceForm(forms.ModelForm):
    """សម្រាប់ Admin បន្ថែម/កែប្រែព័ត៌មានឧបករណ៍"""

    class Meta:
        model = Device
        fields = ['device_name', 'device_image', 'model', 'serial_number', 'capacity', 'status']
        widgets = {
            'device_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ឧ. Seagate External HDD'}),
            'device_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ឧ. Backup Plus Slim'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ឧ. SN-00123'}),
            'capacity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ឧ. 1TB'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['device_name'].label = "ឈ្មោះឧបករណ៍"
        self.fields['device_image'].label = "រូបភាពឧបករណ៍ (ស្រេចចិត្ត)"
        self.fields['device_image'].required = False
        self.fields['model'].label = "ម៉ូឌែល"
        self.fields['serial_number'].label = "លេខស៊េរី (Serial Number)"
        self.fields['capacity'].label = "ទំហំផ្ទុក"
        self.fields['status'].label = "ស្ថានភាព"


class BorrowLogAdminForm(forms.ModelForm):
    """សម្រាប់ Admin កែប្រែទិន្នន័យខ្ចី/សងទាំងស្រុង (កែកំហុស/បំពេញបន្ថែម)"""

    class Meta:
        model = BorrowLog
        fields = [
            'device', 'borrowed_by', 'borrower_type', 'borrower_image', 'borrow_date',
            'expected_return_date', 'reason', 'other_notes', 'borrow_status',
            'actual_return_date', 'return_condition', 'return_image',
            'return_notes', 'admin_note',
        ]
        widgets = {
            'device': forms.Select(attrs={'class': 'form-select'}),
            'borrowed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'borrower_type': forms.Select(attrs={'class': 'form-select'}),
            'borrower_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'borrow_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'other_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'borrow_status': forms.Select(attrs={'class': 'form-select'}),
            'actual_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'return_condition': forms.Select(attrs={'class': 'form-select'}),
            'return_image': forms.FileInput(attrs={'class': 'form-control'}),
            'return_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'admin_note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'កំណត់ចំណាំសម្រាប់ Admin (មិនបង្ហាញដល់អ្នកខ្ចី)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Admin អាចជ្រើសរើសឧបករណ៍ណាមួយក៏បាន (រួមទាំងកំពុងខ្ចី) ព្រោះកំពុងកែទិន្នន័យផ្ទាល់
        self.fields['device'].queryset = Device.objects.all().order_by('device_name')
        labels = {
            'device': 'ឧបករណ៍', 'borrowed_by': 'អ្នកខ្ចី', 'borrower_type': 'ប្រភេទអ្នកខ្ចី',
            'borrower_image': 'រូបភាពអ្នកខ្ចី',
            'borrow_date': 'ថ្ងៃខ្ចី', 'expected_return_date': 'ថ្ងៃរំពឹងថានឹងសង',
            'reason': 'មូលហេតុ', 'other_notes': 'កំណត់សម្គាល់ (ពេលស្នើសុំ)', 'borrow_status': 'ស្ថានភាព',
            'actual_return_date': 'ថ្ងៃសងជាក់ស្តែង', 'return_condition': 'ស្ថានភាពពេលសង',
            'return_image': 'រូបភាពពេលសង', 'return_notes': 'កំណត់សម្គាល់ (ពេលសង)', 'admin_note': 'មតិយោបល់ Admin',
        }
        for field, label in labels.items():
            self.fields[field].label = label
