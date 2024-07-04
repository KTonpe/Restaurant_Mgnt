from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_portal/', include('admin_portal.urls')),
    path('customer_portal/', include('customer_portal.urls')),
]
