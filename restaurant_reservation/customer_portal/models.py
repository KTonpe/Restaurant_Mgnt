from django.db import models

class Customer(models.Model):
    mobile_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=100)
