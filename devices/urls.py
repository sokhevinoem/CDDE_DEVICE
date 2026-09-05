from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    public_status_view,
    borrow_device_view,
    borrow_success_view,
    borrow_list_for_return,
    return_device_view,
    dashboard_view,
    approve_borrow_view,
    reject_borrow_view,
    approve_return_view,
    reject_return_view,
    return_detail_view,
    borrow_detail_view,
    record_detail_view,
    device_list_view,
    device_add_view,
    device_edit_view,
    device_delete_view,
    record_list_view,
    record_edit_view,
    record_delete_view,
    reports_view,
)

urlpatterns = [
    # --- សាធារណៈ (គ្មានត្រូវការចូលគណនី) ---
    path('', public_status_view, name='public_status'),
    path('borrow/', borrow_device_view, name='borrow_device'),
    path('borrow/success/', borrow_success_view, name='borrow_success'),
    path('return/', borrow_list_for_return, name='borrow_list_return'),
    path('return/<int:pk>/', return_device_view, name='return_device'),

    # --- ចូល / ចេញគណនី ---
    path('login/', auth_views.LoginView.as_view(template_name='devices/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- Admin (ត្រូវការចូលគណនីសិន) ---
    path('dashboard/', dashboard_view, name='dashboard'),
    path('borrow/<int:pk>/approve/', approve_borrow_view, name='approve_borrow'),
    path('borrow/<int:pk>/reject/', reject_borrow_view, name='reject_borrow'),
    path('borrow/<int:pk>/detail/', borrow_detail_view, name='borrow_detail'),
    path('return/<int:pk>/approve/', approve_return_view, name='approve_return'),
    path('return/<int:pk>/reject/', reject_return_view, name='reject_return'),
    path('return/<int:pk>/detail/', return_detail_view, name='return_detail'),

    path('devices/', device_list_view, name='device_list'),
    path('devices/add/', device_add_view, name='device_add'),
    path('devices/<int:pk>/edit/', device_edit_view, name='device_edit'),
    path('devices/<int:pk>/delete/', device_delete_view, name='device_delete'),

    path('records/', record_list_view, name='record_list'),
    path('records/<int:pk>/', record_detail_view, name='record_detail'),
    path('records/<int:pk>/edit/', record_edit_view, name='record_edit'),
    path('records/<int:pk>/delete/', record_delete_view, name='record_delete'),

    path('reports/', reports_view, name='reports'),
]
