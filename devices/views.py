from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import BorrowLog, Device
from .forms import BorrowForm, ReturnForm, DeviceForm, BorrowLogAdminForm


# ---------------------------------------------------------------------------
# ជំនួយក្នុងការធ្វើសមកាលកម្មស្ថានភាពឧបករណ៍ (Device.status) ជាមួយស្ថានភាពខ្ចី (BorrowLog.borrow_status)
# ---------------------------------------------------------------------------
def _apply_status_from_log(log):
    """កំណត់ស្ថានភាពឧបករណ៍ដោយផ្អែកលើកំណត់ត្រាខ្ចីនេះដោយផ្ទាល់ (ប្រើពេល Admin កែព័ត៌មានផ្ទាល់)"""
    device = log.device
    if log.borrow_status == 'Pending':
        device.status = 'Reserved'
    elif log.borrow_status in ('Borrowed', 'PendingReturn'):
        device.status = 'Borrowed'
    elif log.borrow_status == 'Returned':
        device.status = 'Maintenance' if log.return_condition == 'Damaged' else 'Available'
    elif log.borrow_status == 'Rejected':
        device.status = 'Available'
    device.save(update_fields=['status'])


def _recompute_device_status(device):
    """ពិនិត្យមើលកំណត់ត្រាខ្ចីដែលនៅសកម្មទាំងអស់លើឧបករណ៍នេះ ហើយកំណត់ស្ថានភាពសមស្រប
    (ប្រើពេលលុប/ផ្លាស់ប្តូរកំណត់ត្រា ដើម្បី "ដោះលែង" ឧបករណ៍មួយវិញ)"""
    if device.status == 'Maintenance':
        return  # ស្ថានភាព "កំពុងជួសជុល" ត្រូវបានកំណត់ដោយដៃ Admin មិនត្រូវសរសេរជាន់ដោយស្វ័យប្រវត្តិទេ
    if device.borrow_logs.filter(borrow_status__in=['Borrowed', 'PendingReturn']).exists():
        device.status = 'Borrowed'
    elif device.borrow_logs.filter(borrow_status='Pending').exists():
        device.status = 'Reserved'
    else:
        device.status = 'Available'
    device.save(update_fields=['status'])


# ---------------------------------------------------------------------------
# 0. ទំព័រសាធារណៈ៖ ស្ថានភាពឧបករណ៍ + កំពុងខ្ចីដោយអ្នកណា (មិនត្រូវការចូលគណនី)
# ---------------------------------------------------------------------------
def public_status_view(request):
    devices = Device.objects.all().order_by('device_name')
    query = request.GET.get('q')
    if query:
        devices = devices.filter(device_name__icontains=query)

    active_borrows = BorrowLog.objects.filter(
        borrow_status__in=['Borrowed', 'PendingReturn']
    ).select_related('device').order_by('device__device_name')

    today = timezone.localdate()
    for item in active_borrows:
        item.is_overdue_flag = bool(
            item.borrow_status == 'Borrowed'
            and item.expected_return_date
            and item.expected_return_date < today
        )

    device_counts = {
        'available': Device.objects.filter(status='Available').count(),
        'borrowed': Device.objects.filter(status='Borrowed').count(),
        'reserved': Device.objects.filter(status='Reserved').count(),
        'maintenance': Device.objects.filter(status='Maintenance').count(),
    }

    context = {
        'devices': devices,
        'query': query,
        'active_borrows': active_borrows,
        'device_counts': device_counts,
        'active_nav': 'status',
    }
    return render(request, 'devices/public_status.html', context)


# ---------------------------------------------------------------------------
# 1. បុគ្គលិកស្នើសុំខ្ចីឧបករណ៍
# ---------------------------------------------------------------------------
def borrow_device_view(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                borrow_record = form.save(commit=False)

                if form.cleaned_data.get('not_sure_return_date'):
                    borrow_record.expected_return_date = None

                borrow_record.borrow_status = "Pending"
                borrow_record.save()

                # កក់ឧបករណ៍ទុក រង់ចាំការអនុម័តពី Admin
                device = borrow_record.device
                device.status = 'Reserved'
                device.save(update_fields=['status'])

            messages.success(
                request,
                f'បានផ្ញើការស្នើសុំខ្ចី "{borrow_record.device.device_name}" ដោយជោគជ័យ! សូមរង់ចាំការអនុម័តពី Admin។'
            )
            return redirect('borrow_success')
    else:
        form = BorrowForm(initial={'borrow_date': timezone.localdate()})

    return render(request, 'devices/borrow_form.html', {'form': form, 'active_nav': 'borrow'})


def borrow_success_view(request):
    return render(request, 'devices/borrow_success.html', {'active_nav': 'borrow'})


# ---------------------------------------------------------------------------
# 2. បញ្ជីឧបករណ៍កំពុងខ្ចី សម្រាប់ស្វែងរក/ជ្រើសរើសយកមកសង
# ---------------------------------------------------------------------------
def borrow_list_for_return(request):
    active_borrows = BorrowLog.objects.filter(
        borrow_status__in=['Borrowed', 'PendingReturn']
    ).select_related('device')

    query = request.GET.get('q')
    if query:
        active_borrows = active_borrows.filter(
            Q(borrowed_by__icontains=query) | Q(device__device_name__icontains=query)
        )

    borrows = list(active_borrows)
    today = timezone.localdate()
    for item in borrows:
        item.is_overdue_flag = bool(
            item.borrow_status == 'Borrowed'
            and item.expected_return_date
            and item.expected_return_date < today
        )

    overdue_count = sum(1 for b in borrows if b.is_overdue_flag)

    context = {
        'borrows': borrows,
        'query': query,
        'overdue_count': overdue_count,
        'active_nav': 'return',
    }
    return render(request, 'devices/borrow_list_return.html', context)


# ---------------------------------------------------------------------------
# 3. ទម្រង់សងឧបករណ៍ (បុគ្គលិកបំពេញ រួចត្រូវរង់ចាំ Admin បញ្ជាក់)
# ---------------------------------------------------------------------------
def return_device_view(request, pk):
    borrow_record = get_object_or_404(BorrowLog, pk=pk)

    if borrow_record.borrow_status != 'Borrowed':
        messages.warning(request, 'កំណត់ត្រានេះមិនអាចដាក់ស្នើសងបានទេ (ប្រហែលជាកំពុងរង់ចាំការបញ្ជាក់ ឬបានសងរួចហើយ)។')
        return redirect('borrow_list_return')

    if request.method == 'POST':
        form = ReturnForm(request.POST, request.FILES, instance=borrow_record)
        if form.is_valid():
            return_record = form.save(commit=False)
            return_record.borrow_status = "PendingReturn"
            return_record.save()

            messages.success(
                request,
                f'បានដាក់ស្នើសង "{borrow_record.device.device_name}" ដោយជោគជ័យ! សូមរង់ចាំការបញ្ជាក់ពី Admin។'
            )
            return redirect('borrow_list_return')
    else:
        form = ReturnForm(instance=borrow_record, initial={'actual_return_date': timezone.localdate()})

    context = {
        'form': form,
        'borrow_record': borrow_record,
        'active_nav': 'return',
    }
    return render(request, 'devices/return_form.html', context)


# ---------------------------------------------------------------------------
# 4. Dashboard (Admin - ត្រូវការចូលគណនី)
# ---------------------------------------------------------------------------
@login_required
def dashboard_view(request):
    devices_qs = Device.objects.all()
    device_stats = {
        'total': devices_qs.count(),
        'available': devices_qs.filter(status='Available').count(),
        'reserved': devices_qs.filter(status='Reserved').count(),
        'borrowed': devices_qs.filter(status='Borrowed').count(),
        'maintenance': devices_qs.filter(status='Maintenance').count(),
    }

    pending_borrows = BorrowLog.objects.filter(borrow_status='Pending').select_related('device').order_by('requested_at')
    pending_returns = BorrowLog.objects.filter(borrow_status='PendingReturn').select_related('device').order_by('actual_return_date')

    today = timezone.localdate()
    overdue = BorrowLog.objects.filter(
        borrow_status='Borrowed', expected_return_date__lt=today
    ).select_related('device')

    recent_activity = BorrowLog.objects.select_related('device').order_by('-requested_at')[:8]

    context = {
        'device_stats': device_stats,
        'pending_borrows': pending_borrows,
        'pending_returns': pending_returns,
        'overdue': overdue,
        'recent_activity': recent_activity,
        'active_nav': 'dashboard',
    }
    return render(request, 'devices/dashboard.html', context)


@login_required
@require_POST
def approve_borrow_view(request, pk):
    log = get_object_or_404(BorrowLog, pk=pk, borrow_status='Pending')
    with transaction.atomic():
        log.borrow_status = 'Borrowed'
        log.save(update_fields=['borrow_status'])
        device = log.device
        device.status = 'Borrowed'
        device.save(update_fields=['status'])
    messages.success(request, f'បានអនុម័តការខ្ចី "{log.device.device_name}" សម្រាប់ {log.borrowed_by}។')
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
@require_POST
def reject_borrow_view(request, pk):
    log = get_object_or_404(BorrowLog, pk=pk, borrow_status='Pending')
    with transaction.atomic():
        log.borrow_status = 'Rejected'
        log.save(update_fields=['borrow_status'])
        _recompute_device_status(log.device)
    messages.info(request, f'បានបដិសេធការស្នើសុំខ្ចី "{log.device.device_name}" សម្រាប់ {log.borrowed_by}។')
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
@require_POST
def approve_return_view(request, pk):
    log = get_object_or_404(BorrowLog, pk=pk, borrow_status='PendingReturn')
    with transaction.atomic():
        log.borrow_status = 'Returned'
        log.save(update_fields=['borrow_status'])
        device = log.device
        device.status = 'Maintenance' if log.return_condition == 'Damaged' else 'Available'
        device.save(update_fields=['status'])
    messages.success(request, f'បានបញ្ជាក់ការសង "{log.device.device_name}" ពី {log.borrowed_by}។')
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
@require_POST
def reject_return_view(request, pk):
    log = get_object_or_404(BorrowLog, pk=pk, borrow_status='PendingReturn')
    log.borrow_status = 'Borrowed'
    log.save(update_fields=['borrow_status'])
    messages.info(request, f'បានបញ្ជូនការសង "{log.device.device_name}" ត្រឡប់ទៅអ្នកខ្ចីវិញ ដើម្បីដាក់ស្នើម្តងទៀត។')
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
def return_detail_view(request, pk):
    record = get_object_or_404(BorrowLog.objects.select_related('device'), pk=pk)
    return render(request, 'devices/return_detail.html', {'record': record, 'active_nav': 'dashboard'})


@login_required
def borrow_detail_view(request, pk):
    record = get_object_or_404(BorrowLog.objects.select_related('device'), pk=pk)
    return render(request, 'devices/borrow_detail.html', {'record': record, 'active_nav': 'dashboard'})


@login_required
def record_detail_view(request, pk):
    record = get_object_or_404(BorrowLog.objects.select_related('device'), pk=pk)
    has_return_info = bool(
        record.actual_return_date or record.return_image or record.return_notes
        or record.borrow_status in ('PendingReturn', 'Returned')
    )
    return render(request, 'devices/record_detail.html', {
        'record': record,
        'has_return_info': has_return_info,
        'active_nav': 'records',
    })


# ---------------------------------------------------------------------------
# 5. Admin: គ្រប់គ្រងឧបករណ៍ (Add / Edit / Delete) - ត្រូវការចូលគណនី
# ---------------------------------------------------------------------------
@login_required
def device_list_view(request):
    devices = Device.objects.all()
    query = request.GET.get('q')
    if query:
        devices = devices.filter(
            Q(device_name__icontains=query) | Q(serial_number__icontains=query) | Q(model__icontains=query)
        )
    status_filter = request.GET.get('status')
    if status_filter:
        devices = devices.filter(status=status_filter)

    context = {
        'devices': devices,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Device.STATUS_CHOICES,
        'active_nav': 'devices',
    }
    return render(request, 'devices/device_list.html', context)


@login_required
def device_add_view(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'បានបន្ថែមឧបករណ៍ថ្មីដោយជោគជ័យ!')
            return redirect('device_list')
    else:
        form = DeviceForm()
    return render(request, 'devices/device_form.html', {'form': form, 'is_new': True, 'active_nav': 'devices'})


@login_required
def device_edit_view(request, pk):
    device = get_object_or_404(Device, pk=pk)
    if request.method == 'POST':
        form = DeviceForm(request.POST, request.FILES, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, f'បានកែប្រែព័ត៌មាន "{device.device_name}" ដោយជោគជ័យ!')
            return redirect('device_list')
    else:
        form = DeviceForm(instance=device)
    return render(request, 'devices/device_form.html', {'form': form, 'is_new': False, 'device': device, 'active_nav': 'devices'})


@login_required
def device_delete_view(request, pk):
    device = get_object_or_404(Device, pk=pk)
    related_count = device.borrow_logs.count()
    if request.method == 'POST':
        name = device.device_name
        device.delete()
        messages.success(request, f'បានលុបឧបករណ៍ "{name}" ដោយជោគជ័យ!')
        return redirect('device_list')
    return render(request, 'devices/device_confirm_delete.html', {
        'device': device, 'related_count': related_count, 'active_nav': 'devices',
    })


# ---------------------------------------------------------------------------
# 6. Admin: គ្រប់គ្រងកំណត់ត្រាខ្ចី-សងទាំងអស់ (Edit / Delete) - ត្រូវការចូលគណនី
# ---------------------------------------------------------------------------
@login_required
def record_list_view(request):
    records = BorrowLog.objects.select_related('device').all()

    query = request.GET.get('q')
    if query:
        records = records.filter(
            Q(borrowed_by__icontains=query) | Q(device__device_name__icontains=query)
        )
    status_filter = request.GET.get('status')
    if status_filter:
        records = records.filter(borrow_status=status_filter)
    type_filter = request.GET.get('type')
    if type_filter:
        records = records.filter(borrower_type=type_filter)

    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': BorrowLog.STATUS_CHOICES,
        'type_choices': BorrowLog.TYPE_CHOICES,
        'active_nav': 'records',
    }
    return render(request, 'devices/record_list.html', context)


@login_required
def record_edit_view(request, pk):
    record = get_object_or_404(BorrowLog, pk=pk)
    old_device_id = record.device_id
    if request.method == 'POST':
        form = BorrowLogAdminForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save()
                _apply_status_from_log(updated)
                if old_device_id != updated.device_id:
                    old_device = Device.objects.filter(pk=old_device_id).first()
                    if old_device:
                        _recompute_device_status(old_device)
            messages.success(request, 'បានកែប្រែកំណត់ត្រាដោយជោគជ័យ!')
            return redirect('record_list')
    else:
        form = BorrowLogAdminForm(instance=record)
    return render(request, 'devices/record_form.html', {'form': form, 'record': record, 'active_nav': 'records'})


@login_required
def record_delete_view(request, pk):
    record = get_object_or_404(BorrowLog, pk=pk)
    if request.method == 'POST':
        device = record.device
        label = f"{record.borrowed_by} - {record.device.device_name}"
        record.delete()
        _recompute_device_status(device)
        messages.success(request, f'បានលុបកំណត់ត្រា "{label}" ដោយជោគជ័យ!')
        return redirect('record_list')
    return render(request, 'devices/record_confirm_delete.html', {'record': record, 'active_nav': 'records'})


# ---------------------------------------------------------------------------
# 7. របាយការណ៍ / នាំចេញ PDF (Admin - ត្រូវការចូលគណនី)
# ---------------------------------------------------------------------------
@login_required
def reports_view(request):
    records = BorrowLog.objects.select_related('device').all()

    query = request.GET.get('q')
    if query:
        records = records.filter(
            Q(borrowed_by__icontains=query) | Q(device__device_name__icontains=query)
        )
    status_filter = request.GET.get('status')
    if status_filter:
        records = records.filter(borrow_status=status_filter)
    type_filter = request.GET.get('type')
    if type_filter:
        records = records.filter(borrower_type=type_filter)
    date_from = request.GET.get('date_from')
    if date_from:
        records = records.filter(borrow_date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        records = records.filter(borrow_date__lte=date_to)

    records = records.order_by('-borrow_date')

    user_summary = records.values('borrowed_by', 'borrower_type').annotate(
        total=Count('id')
    ).order_by('-total', 'borrowed_by')

    context = {
        'records': records,
        'user_summary': user_summary,
        'query': query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': BorrowLog.STATUS_CHOICES,
        'type_choices': BorrowLog.TYPE_CHOICES,
        'generated_at': timezone.localtime(),
        'active_nav': 'reports',
    }
    return render(request, 'devices/reports.html', context)
