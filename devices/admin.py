from django.contrib import admin
from .models import Device, BorrowLog

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_name', 'model', 'serial_number', 'capacity', 'status')
    list_editable = ('status',)
    list_filter = ('status',)
    search_fields = ('device_name', 'serial_number', 'model')

@admin.register(BorrowLog)
class BorrowLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'device', 'borrowed_by', 'borrower_type', 'requested_at',
        'borrow_date', 'expected_return_date', 'actual_return_date',
        'borrow_status', 'return_condition',
    )
    list_filter = ('borrow_status', 'borrower_type', 'return_condition', 'borrow_date')
    search_fields = ('borrowed_by', 'reason', 'device__device_name')
    readonly_fields = ('requested_at',)
