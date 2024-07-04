from django.contrib import admin
from .models import Restaurant, Reservation, Admin

admin.site.register(Restaurant)
admin.site.register(Reservation)
admin.site.register(Admin)
