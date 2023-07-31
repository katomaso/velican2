from django.db import models
from django.db.models import Sum

from velican2.core import models as core

class Request(models.Model):
    site = models.ForeignKey(core.Site, on_delete=models.DO_NOTHING)
    created = models.DateField(auto_now=True)
    due = models.DateField()
    amount = models.FloatField()

    @property
    def paid(self):
        if getattr(self, "__paid", None):
            self.__paid = self.payment_set.aggregate(paid=Sum("amount"))["paid"]
        return self.__paid >= self.amount


class Payment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    amount = models.FloatField()
