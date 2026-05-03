from django.db import models

class Lead(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    interest = models.CharField(max_length=100)

    def __str__(self):
        return self.name