from django.db import models

class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=100)

class Reservation(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer_mobile = models.CharField(max_length=15)
    num_people = models.IntegerField()
    reservation_time = models.DateTimeField()
    status = models.BooleanField(default=False)

class Admin(models.Model):
    employee_id = models.IntegerField(unique=True)
    password = models.CharField(max_length=100)
