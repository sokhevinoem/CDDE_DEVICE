from django import template

register = template.Library()

_BORROW_STATUS_BADGE = {
    'Pending': 'bg-warning text-dark',
    'Borrowed': 'bg-primary',
    'PendingReturn': 'bg-info text-dark',
    'Returned': 'bg-success',
    'Rejected': 'bg-secondary',
}

_DEVICE_STATUS_BADGE = {
    'Available': 'bg-success',
    'Reserved': 'bg-warning text-dark',
    'Borrowed': 'bg-primary',
    'Maintenance': 'bg-danger',
}


@register.filter
def borrow_status_badge(status):
    return _BORROW_STATUS_BADGE.get(status, 'bg-secondary')


@register.filter
def device_status_badge(status):
    return _DEVICE_STATUS_BADGE.get(status, 'bg-secondary')
