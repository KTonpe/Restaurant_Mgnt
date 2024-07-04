from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.customer_register, name='customer_register'),
    path('login/', views.customer_login, name='customer_login'),
    path('availability/', views.check_availability, name='check_availability'),
    path('reservation/', views.book_reservation, name='book_reservation'),
    path('stats/<str:customer_mobile>/', views.reservation_stats, name='reservation_stats'),
]