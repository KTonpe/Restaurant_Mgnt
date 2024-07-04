from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.admin_register, name='admin_register'),
    path('login/', views.admin_login, name='admin_login'),
    path('restaurant/', views.add_restaurant, name='add_restaurant'),
    path('restaurant/<int:restaurant_id>/', views.update_restaurant, name='update_restaurant'),
    path('restaurant/<int:restaurant_id>/delete/', views.delete_restaurant, name='delete_restaurant'),
    path('reservation/', views.book_reservation, name='book_reservation'),
    path('delete_reservation/', views.delete_reservation, name='delete_reservation'),
    path('restaurant_reservations/<int:restaurant_id>/', views.get_reservations_by_restaurant, name='get_reservations_by_restaurant'),
]
