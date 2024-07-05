from django.db import models

class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    location = models.CharField(max_length=255)
    tables_of_2 = models.IntegerField(default=0)
    tables_of_4 = models.IntegerField(default=0)
    tables_of_6 = models.IntegerField(default=0)
    waiting_seats = models.IntegerField(default=0)

class Reservation(models.Model):
    TABLE_CHOICES = (
        (2, 'Table of 2'),
        (4, 'Table of 4'),
        (6, 'Table of 6'),
    )
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer_mobile = models.CharField(max_length=15)
    num_people = models.IntegerField()
    reservation_time = models.DateTimeField()
    table_type = models.IntegerField(choices=TABLE_CHOICES, default=2)
    table_number = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=False)

class Admin(models.Model):
    employee_id = models.IntegerField(unique=True)
    password = models.CharField(max_length=100)
