from django.db import models

# Create your models here.

class Amount(models.Model):
    date = models.DateField(blank=True, null=True)
    amount = models.FloatField()

    def __str__(self):
        return f'date: {self.date} , Amount: {self.amount}'
