from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('devices.urls')),  # ភ្ជាប់ទៅ devices/urls.py ដោយផ្ទាល់
]

# បង្ហាញ Media Files (Images) ពេល Run Local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)